import json
from typing import Dict, Any, List, Optional

import config
from nxcore.middleware.logging_manager import logger
from api.repository.duck_db import DuckDAO
from api.repository.upstream_repository import UpstreamDao
from api.repository.sensor_repository import SensorDao
from api.model.route_model import RouteSchema


class RouteDao(DuckDAO):
    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH, table_name="routes", schema=RouteSchema, conn=conn
        )
        self.upstreamDao = UpstreamDao(conn=self.conn)
        self.sensorDao = SensorDao(conn=self.conn)
        self.create_schema()

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_id INTEGER,
                upstream_id INTEGER,
                sensor_id INTEGER,
                monitor_only BOOLEAN,
                name TEXT,
                type TEXT,
                paths JSON,
                cache_methods JSON,
                allowed_methods JSON,
                allowed_content_type JSON,
                redirect JSON
            );
        """
        )

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        vo = vo.copy()
        for field in [
            "paths",
            "allowed_methods",
            "allowed_content_type",
            "redirect",
            "cache_methods",
        ]:
            if field in vo and vo[field] is not None and not isinstance(vo[field], str):
                vo[field] = json.dumps(vo[field])

        if "upstream" in vo:
            ups = vo.pop("upstream")
            if ups:
                if "_id" in ups:
                    vo["upstream_id"] = ups["_id"]
                elif "name" in ups:
                    upstream_record = self.upstreamDao.get_by_name(ups["name"])
                    if upstream_record:
                        vo["upstream_id"] = upstream_record["_id"]

        if "sensor" in vo:
            sns = vo.pop("sensor")
            if sns:
                if "_id" in sns:
                    vo["sensor_id"] = sns["_id"]
                elif "name" in sns:
                    sensor_record = self.sensorDao.get_by_name(sns["name"])
                    if sensor_record:
                        vo["sensor_id"] = sensor_record["_id"]

        return super().from_dict(vo)

    def to_dict(self, vo: Optional[Dict[str, Any]], dependents: bool = True) -> Optional[Dict[str, Any]]:
        if not vo:
            return vo
        super().to_dict(vo)
        for field in [
            "paths",
            "allowed_methods",
            "allowed_content_type",
            "redirect",
            "cache_methods",
        ]:
            if field in vo and isinstance(vo[field], str):
                try:
                    vo[field] = json.loads(vo[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        upstream_id = vo.pop("upstream_id", None)
        if upstream_id:
            if dependents:
                vo["upstream"] = self.upstreamDao.get_by_id(upstream_id)
            else:
                vo["upstream"] = self.upstreamDao.get_desc_by_id(upstream_id) or {"_id": upstream_id}
        sensor_id = vo.pop("sensor_id", None)
        if sensor_id:
            if dependents:
                vo["sensor"] = self.sensorDao.get_by_id(sensor_id)
            else:
                vo["sensor"] = self.sensorDao.get_desc_by_id(sensor_id) or {"_id": sensor_id}
        vo.pop("service_id", None)
        return vo

    def get_all_by_service_id(self, service_id: Any, dependents: bool = True) -> List[Dict[str, Any]]:
        try:
            query = f"SELECT * FROM {self.table_name} WHERE service_id = ?"
            logger.debug(query)
            rows = self._query(query, (int(service_id),), fetch=True)
            return [self.to_dict(r, dependents=dependents) for r in rows] if rows else []
        except Exception as e:
            logger.error(f"Error retrieving routes by service_id: {str(e)}")
            raise

    def delete_by_service_id(self, service_id: Any) -> bool:
        try:
            query = f"DELETE FROM {self.table_name} WHERE service_id = ?"
            logger.debug(query)
            self._query(query, (int(service_id),))
            if self.auto_commit:
                self.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting routes by service_id: {str(e)}")
            raise
