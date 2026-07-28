import json
from typing import Dict, Any, Optional

from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class SensorBlockedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    geo_codes = fields.List(fields.String(), allow_none=True)
    reputations = fields.List(fields.String(), allow_none=True)
    trusted = fields.List(fields.String(), allow_none=True)


class SensorScoreSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    inbound = fields.Integer(allow_none=True)
    outbound = fields.Integer(allow_none=True)


class SensorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    description = fields.String(allow_none=True, load_default="", dump_default="")
    categories = fields.List(fields.String(), allow_none=True)
    exclusions = fields.List(fields.Integer(), allow_none=True)
    blocked = fields.Nested(SensorBlockedSchema, allow_none=True)
    bypass_src = fields.List(fields.String(), allow_none=True)
    score = fields.Nested(SensorScoreSchema, allow_none=True)
    inspect_level = fields.Integer(allow_none=True)


class SensorDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="sensor",
            schema=SensorSchema
        )

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT,
                categories_json TEXT,
                exclusions_json TEXT,
                security_json TEXT,
                score_json TEXT,
                inspect_level INTEGER
            );
        """)

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        if "categories" in vo:
            vo.update({"categories_json": json.dumps(vo.pop('categories'))})
        if "exclusions" in vo:
            vo.update({"exclusions_json": json.dumps(vo.pop('exclusions'))})
        if "security" in vo:
            vo.update({"security_json": json.dumps(vo.pop('security'))})
        if "score" in vo:
            vo.update({"score_json": json.dumps(vo.pop('score'))})
        return super().from_dict(vo)

    def to_dict(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row:
            if "categories_json" in row:
                val = row.pop('categories_json')
                row.update({"categories": json.loads(val) if val else []})
            if "exclusions_json" in row:
                val = row.pop('exclusions_json')
                row.update({"exclusions": json.loads(val) if val else []})
            if "security_json" in row:
                val = row.pop('security_json')
                row.update({"security": json.loads(val) if val else {}})
            if "score_json" in row:
                val = row.pop('score_json')
                row.update({"score": json.loads(val) if val else {}})
        return super().to_dict(row)
