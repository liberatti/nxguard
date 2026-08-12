import json
from typing import Dict, Any, List, Optional

from marshmallow import EXCLUDE, Schema, fields
from nxcore.middleware.logging_manager import logger

import config
from .duck_db import DuckDAO
from api.model.upstream_model import UpstreamDao, UpstreamSchema
from api.model.sensor_model import SensorDao, SensorSchema


class RedirectSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    code = fields.Integer()
    url = fields.String()


class RouteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    service_id = fields.Integer(allow_none=True)
    name = fields.String()
    type = fields.String()
    paths = fields.List(fields.String())
    allowed_methods = fields.Raw(allow_none=True)
    allowed_content_type = fields.Raw(allow_none=True)
    upstream = fields.Nested(UpstreamSchema)
    redirect = fields.Nested(RedirectSchema)
    sensor = fields.Nested(SensorSchema)
    monitor_only = fields.Boolean()
    cache_methods = fields.List(fields.String())


class RouteDao(DuckDAO):
    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH, table_name="routes", schema=RouteSchema, conn=conn
        )
        self.upstreamDao = UpstreamDao()
        self.sensorDao = SensorDao()

    def connect(self) -> None:
        super().connect()
        self.upstreamDao.conn = self.conn
        self.sensorDao.conn = self.conn

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
            if isinstance(ups, dict) and ups and "_id" in ups:
                vo["upstream_id"] = ups["_id"]
            elif ups is not None and not isinstance(ups, dict):
                vo["upstream_id"] = ups
            elif "upstream_id" not in vo:
                vo["upstream_id"] = None

        if "sensor" in vo:
            sns = vo.pop("sensor")
            if isinstance(sns, dict) and sns and "_id" in sns:
                vo["sensor_id"] = sns["_id"]
            elif sns is not None and not isinstance(sns, dict):
                vo["sensor_id"] = sns
            elif "sensor_id" not in vo:
                vo["sensor_id"] = None

        return super().from_dict(vo)

    def to_dict(self, vo: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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
        return vo

    def get_all_by_service_id(self, service_id: Any) -> List[Dict[str, Any]]:
        try:
            query = f"SELECT * FROM {self.table_name} WHERE service_id = ?"
            logger.debug(query)
            rows = self._query(query, (int(service_id),), fetch=True)
            return [self.to_dict(r) for r in rows] if rows else []
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
