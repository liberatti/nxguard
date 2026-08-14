import json
from typing import Dict, Any, List, Optional

from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields, post_load

import config
from api.model.certificate_model import CertificateDao, CertificateSchema
from api.model.route_model import (
    RouteDao,
    RouteSchema,
    RedirectSchema,
)


class HeaderSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    content = fields.String()


class BindSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    port = fields.Integer()
    protocol = fields.String()
    ssl_upgrade = fields.Boolean(
        allow_none=True, load_default=False, dump_default=False
    )
    ssl_upgrade_port = fields.Integer(
        allow_none=True, load_default=443, dump_default=443
    )

    @post_load
    def make_bind(self, data, **kwargs):
        if data.get("ssl_upgrade") is None:
            data["ssl_upgrade"] = False
        if data.get("ssl_upgrade_port") is None:
            data["ssl_upgrade_port"] = 443
        return data


class ServiceSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    body_limit = fields.Integer()
    timeout = fields.Integer()
    active = fields.Boolean()
    buffer = fields.Integer()
    bindings = fields.Nested(BindSchema, many=True)
    headers = fields.Nested(HeaderSchema, many=True)
    routes = fields.Nested(RouteSchema, many=True, allow_none=True, load_default=[])
    compression_types = fields.List(fields.String())
    rate_limit_per_sec = fields.Integer()
    sans = fields.List(fields.String())
    ssl_protocols = fields.List(fields.String())
    certificate = fields.Nested(CertificateSchema)
    ssl_client_ca = fields.String()
    ssl_client_auth = fields.Boolean(load_default=False, dump_default=False)


class ServiceDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="service", schema=ServiceSchema
        )
        self.certificateDao = CertificateDao(conn=self.conn)
        self.routeDao = RouteDao(conn=self.conn)

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_id INTEGER,
                name TEXT,
                body_limit INTEGER,
                timeout INTEGER,
                active BOOLEAN,
                buffer INTEGER,
                rate_limit_per_sec INTEGER,
                bindings JSON,
                headers JSON,
                compression_types JSON,
                sans JSON,
                ssl_protocols JSON,
                ssl_client_ca TEXT,
                ssl_client_auth BOOLEAN DEFAULT 0
            );
        """
        )
        self.routeDao.create_schema()

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        vo = dict(vo)
        for field in [
            "bindings",
            "headers",
            "compression_types",
            "sans",
            "ssl_protocols",
        ]:
            if field in vo and vo[field] is not None and not isinstance(vo[field], str):
                vo[field] = json.dumps(vo[field])

        if "certificate" in vo:
            cert = vo.pop("certificate")
            if cert:
                if "_id" in cert:
                    vo["certificate_id"] = cert["_id"]
                elif "name" in cert:
                    crt = self.certificateDao.get_by_name(cert["name"])
                    if crt:
                        vo["certificate_id"] = crt["_id"]
            else:
                vo["certificate_id"] = None

        return super().from_dict(vo)

    def to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not vo:
            return vo
        super().to_dict(vo)

        if "certificate_id" in vo:
            crt_id = vo.pop("certificate_id")
            vo["certificate"] = self.certificateDao.get_by_id(crt_id)

        vo["bindings"] = (
            json.loads(vo.get("bindings", "[]"))
            if isinstance(vo.get("bindings"), str)
            else vo.get("bindings", [])
        )
        vo["compression_types"] = (
            json.loads(vo.get("compression_types", "[]"))
            if isinstance(vo.get("compression_types"), str)
            else vo.get("compression_types", [])
        )
        vo["sans"] = (
            json.loads(vo.get("sans", "[]"))
            if isinstance(vo.get("sans"), str)
            else vo.get("sans", [])
        )
        vo["headers"] = (
            json.loads(vo.get("headers", "[]"))
            if isinstance(vo.get("headers"), str)
            else vo.get("headers", [])
        )
        vo["ssl_protocols"] = (
            json.loads(vo.get("ssl_protocols", "[]"))
            if isinstance(vo.get("ssl_protocols"), str)
            else vo.get("ssl_protocols", [])
        )
        vo["routes"] = self.routeDao.get_all_by_service_id(vo["_id"])
        return vo

    def persist(self, vo: Dict[str, Any]) -> Optional[Any]:
        routes = vo.pop("routes", None)
        pk_val = super().persist(vo)
        if pk_val and routes is not None:
            self.routeDao.delete_by_service_id(pk_val)
            for route in routes:
                route.pop("_id", None)
                route.update({"service_id": pk_val})
                self.routeDao.persist(route)
        return pk_val

    def persist_many(self, arr: List[Dict[str, Any]]):
        if not arr:
            return False
        pks = []
        for s in arr:
            pk_val = self.persist(s)
            if pk_val:
                pks.append(pk_val)
        return pks

    def update_by_id(self, id: str, vo: Dict[str, Any]) -> bool:
        routes = vo.pop("routes", None)
        result = super().update_by_id(id, vo)
        if result and routes is not None:
            self.routeDao.delete_by_service_id(id)
            for route in routes:
                route.pop("_id", None)
                route.update({"service_id": int(id)})
                self.routeDao.persist(route)
        return result

    def delete_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        self.routeDao.delete_by_service_id(id)
        return super().delete_by_id(id)

    def delete_all(self):
        self.routeDao.delete_all()
        super().delete_all()

    def get_by_sans(
        self, sans: List[str], active: Optional[bool] = None
    ) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * from {self.table_name} WHERE sans LIKE '%{sans[0]}%'"
            if active is not None:
                query += f" AND active = {active}"

            logger.debug(query)
            vo = self._query(query, fetch=True)[0]
            return self.to_dict(vo) if vo else None
        except Exception as e:
            logger.error(f"Error retrieving service by SANs: {str(e)}")
            raise

    def get_all_by_certificate_id(self, certificate_id: str) -> List[Dict[str, Any]]:
        try:
            query = f"SELECT * from {self.table_name} where certificate_id = '{certificate_id}' and active = 1"
            logger.debug(query)
            rows = list(self._query(query, fetch=True))
            for r in rows:
                self.to_dict(r)
            return rows
        except Exception as e:
            logger.error(f"Error retrieving services by certificate: {str(e)}")
            raise
