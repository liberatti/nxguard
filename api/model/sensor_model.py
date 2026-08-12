import json
from typing import Dict, Any, Optional

from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class SensorSecuritySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    geo_codes = fields.List(fields.String(), allow_none=True)
    reputation = fields.List(fields.String(), allow_none=True)
    trusted = fields.List(fields.String(), allow_none=True)


class SensorScoreSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    inbound = fields.Integer(allow_none=True)
    outbound = fields.Integer(allow_none=True)


class SensorVariablesSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    allowed_http_versions = fields.Raw(allow_none=True)
    max_file_size = fields.Integer(allow_none=True)
    restricted_extensions = fields.Raw(allow_none=True)
    max_num_args = fields.Integer(allow_none=True)
    arg_name_length = fields.Integer(allow_none=True)
    arg_length = fields.Integer(allow_none=True)


class SensorInspectionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    score = fields.Nested(SensorScoreSchema, allow_none=True)
    level = fields.Integer(allow_none=True)
    variables = fields.Nested(SensorVariablesSchema, allow_none=True)


class SensorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True)
    categories = fields.List(fields.String(), allow_none=True)
    exclusions = fields.List(fields.Raw(), allow_none=True)
    security = fields.Nested(SensorSecuritySchema, allow_none=True)
    inspection = fields.Nested(SensorInspectionSchema, allow_none=True)


class SensorDao(DuckDAO):
    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="sensor",
            schema=SensorSchema,
            conn=conn,
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                categories JSON,
                exclusions JSON,
                security JSON,
                inspection JSON
            );
        """
        )

    def to_dict(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row:
            row["categories"] = json.loads(row.get("categories", "[]"))
            row["exclusions"] = json.loads(row.get("exclusions", "[]"))
            row["security"] = json.loads(row.get("security", "{}"))
            row["inspection"] = json.loads(row.get("inspection", "{}"))
        return super().to_dict(row)
