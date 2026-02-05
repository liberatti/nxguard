import json
from typing import Dict, Any, List, Optional

from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO
from marshmallow import EXCLUDE, Schema, fields

import config
from api.repository.certificate_model import CertificateDao, CertificateSchema
from api.repository.upstream_model import UpstreamSchema


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
    ssl_upgrade = fields.Boolean()


class RedirectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    code = fields.Integer()
    url = fields.String()


class RouteFilterSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    description = fields.String()
    type = fields.String()  # SSL_CLIENT_AUTH, LDAP_AUTH
    ssl_dn_regex = fields.String()
    ssl_fingerprints = fields.List(fields.String())
    ldap_host = fields.String()
    ldap_base_dn = fields.String()
    ldap_bind_dn = fields.String()
    ldap_bind_password = fields.String()
    ldap_group_dn = fields.String()


class RouteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    name = fields.String()
    type = fields.String()
    paths = fields.List(fields.String())
    methods = fields.List(fields.String())
    upstream = fields.Nested(UpstreamSchema)
    redirect = fields.Nested(RedirectSchema)
    # sensor = fields.Nested(SensorSchema)
    monitor_only = fields.Boolean()
    cache_methods = fields.List(fields.String())
    filters = fields.Nested(RouteFilterSchema, many=True)


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
    routes = fields.Nested(RouteSchema, many=True)
    compression = fields.Boolean()
    compression_types = fields.List(fields.String())
    rate_limit = fields.Boolean()
    rate_limit_per_sec = fields.Integer()
    sans = fields.List(fields.String())
    ssl_protocols = fields.List(fields.String())
    certificate = fields.Nested(CertificateSchema)
    ssl_client_ca = fields.String()
    ssl_client_auth = fields.Boolean(load_default=False, dump_default=False)


class RouteFilterDao(SQLite3DAO):

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH
            , table_name="route_filters"
            , schema=RouteFilterSchema
        )

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                type TEXT, 
                ssl_dn_regex TEXT,
                ssl_fingerprints TEXT,
                ldap_host TEXT,
                ldap_base_dn TEXT,
                ldap_bind_dn TEXT,
                ldap_bind_password TEXT,
                ldap_group_dn TEXT
            );
        """)


class ServiceDao(SQLite3DAO):
    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="service", schema=ServiceSchema)
        self.certificateDao = CertificateDao()
        self.certificateDao.connect()

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                body_limit INTEGER,
                timeout INTEGER,
                active BOOLEAN,
                buffer INTEGER,
                bindings_json TEXT,
                headers_json TEXT,
                routes_json TEXT,
                compression BOOLEAN,
                compression_types_json TEXT,
                rate_limit BOOLEAN,
                rate_limit_per_sec INTEGER,
                sans_json TEXT,
                ssl_protocols_json TEXT,
                certificate_id TEXT,
                ssl_client_ca TEXT,
                ssl_client_auth BOOLEAN DEFAULT 0
            );
        """)

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        if "certificate" in vo:
            certificate = vo.pop("certificate")
            if "_id" in certificate:
                vo.update({"certificate_id": certificate["_id"]})
            if "name" in certificate:
                vo.update({"certificate_id": self.certificateDao.get_by_name(certificate["name"])["_id"]})

        if "routes" in vo:
            vo.update({"routes_json": json.dumps(vo.pop('routes'))})

        if "bindings" in vo:
            vo.update({"bindings_json": json.dumps(vo.pop('bindings'))})

        if "compression_types" in vo:
            vo.update({"compression_types_json": json.dumps(vo.pop('compression_types'))})

        if "sans" in vo:
            vo.update({"sans_json": json.dumps(vo.pop('sans'))})

        if "headers" in vo:
            vo.update({"headers_json": json.dumps(vo.pop('headers'))})

        if "ssl_protocols" in vo:
            vo.update({"ssl_protocols_json": json.dumps(vo.pop('ssl_protocols'))})
        return super().from_dict(vo)

    def to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        super().to_dict(vo)

        if "certificate_id" in vo:
            crt_id = vo.pop("certificate_id")
            vo.update({"certificate": self.certificateDao.get_by_id(crt_id)})

        if "routes_json" in vo:
            vo.update({"routes": json.loads(vo.pop("routes_json"))})

        if "bindings_json" in vo:
            vo.update({"bindings": json.loads(vo.pop("bindings_json"))})

        if "headers_json" in vo:
            vo.update({"headers": json.loads(vo.pop("headers_json"))})

        if "compression_types_json" in vo:
            vo.update({"compression_types": json.loads(vo.pop('compression_types_json'))})

        if "sans_json" in vo:
            logger.info(vo)
            vo.update({"sans": json.loads(vo.pop('sans_json'))})

        if "ssl_protocols_json" in vo:
            vo.update({"ssl_protocols": json.loads(vo.pop('ssl_protocols_json'))})

        # if "sensor_id" in route:
        #    sensor_id = route.pop("sensor_id")
        #    sen_dao = SensorDao()
        #    route.update({"sensor": sen_dao.get_descr_by_id(sensor_id)})
        return vo

    def get_by_sans(self, sans: List[str], active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * from {self.table_name} WHERE sans_json LIKE '%{sans[0]}%'"
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
