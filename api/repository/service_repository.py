import json
from typing import Dict, Any, List, Optional

import config
from nxcore.middleware.logging_manager import logger
from api.repository.duck_db import DuckDAO
from api.repository.certificate_repository import CertificateDao
from api.repository.route_repository import RouteDao
from api.model.service_model import ServiceSchema


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

    def to_dict(
        self, vo: Optional[Dict[str, Any]], dependents: bool = True
    ) -> Optional[Dict[str, Any]]:
        if not vo:
            return vo
        super().to_dict(vo)

        if "certificate_id" in vo:
            crt_id = vo.pop("certificate_id")
            if crt_id:
                if dependents:
                    vo["certificate"] = self.certificateDao.get_by_id(crt_id)
                else:
                    vo["certificate"] = self.certificateDao.get_desc_by_id(crt_id) or {
                        "_id": crt_id
                    }

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
        vo["routes"] = self.routeDao.get_all_by_service_id(
            vo["_id"], dependents=dependents
        )
        return vo

    def get_all(
        self, pagination=None, order_by=None, dependents: bool = True
    ) -> Dict[str, Any]:
        sql = f"SELECT * FROM {self.table_name}"
        if order_by:
            sql += f" ORDER BY {order_by}"

        count_sql = f"SELECT COUNT(*) as total FROM {self.table_name}"
        total = self._query(count_sql, fetch=True)[0]["total"]

        if pagination:
            page = pagination.get("page", 1)
            per_page = pagination.get("per_page", 10)
            offset = (page - 1) * per_page
            sql += f" LIMIT {per_page} OFFSET {offset}"
            pagination["total_elements"] = total
        else:
            pagination = {"total_elements": total, "page": 1, "per_page": total}

        rs = self._query(sql, fetch=True)
        rows = [self.to_dict(row, dependents=dependents) for row in rs] if rs else []

        return {"metadata": pagination, "data": rows}

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
            if not sans:
                return None
            conditions = " OR ".join(
                [f"CAST(sans AS TEXT) LIKE '%{s}%'" for s in sans if s]
            )
            if not conditions:
                return None
            query = f"SELECT * from {self.table_name} WHERE ({conditions})"
            if active is not None:
                query += f" AND active = {1 if active else 0}"

            logger.debug(query)
            rows = self._query(query, fetch=True)
            if not rows:
                return None
            vo = rows[0]
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

    def search(
        self, query: str = None, pagination: dict = None, order_by: str = None
    ) -> dict:
        if not query or not query.strip():
            return self.get_all(pagination=pagination, order_by=order_by)

        term = f"%{query.strip().lower()}%"
        where_clause = "WHERE LOWER(name) LIKE ? OR LOWER(CAST(sans AS TEXT)) LIKE ?"
        params = (term, term)

        count_sql = f"SELECT COUNT(*) AS total FROM {self.table_name} {where_clause}"
        total = self._query(count_sql, params, fetch=True)[0]["total"]

        sql = f"SELECT * FROM {self.table_name} {where_clause}"
        if order_by:
            sql += f" ORDER BY {order_by}"

        if pagination:
            page = pagination.get("page", 1)
            per_page = pagination.get("per_page", 10)
            offset = (page - 1) * per_page
            sql += f" LIMIT {per_page} OFFSET {offset}"
            pagination["total_elements"] = total
        else:
            pagination = {"total_elements": total, "page": 1, "per_page": total}

        rs = self._query(sql, params, fetch=True)
        rows = [self.to_dict(row) for row in rs] if rs else []
        return {
            "metadata": pagination,
            "data": rows,
        }
