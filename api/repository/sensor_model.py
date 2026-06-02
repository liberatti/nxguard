import json
from typing import Dict, Any, Optional

from nxcore.middleware.logging import logger
from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class SensorBlockedSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    geo_codes = fields.List(fields.String(), allow_none=True)
    rbl = fields.List(fields.String(), allow_none=True)


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
                blocked_json TEXT,
                bypass_src_json TEXT,
                score_json TEXT,
                inspect_level INTEGER
            );
        """)

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        if "categories" in vo:
            vo.update({"categories_json": json.dumps(vo.pop('categories'))})
        if "exclusions" in vo:
            vo.update({"exclusions_json": json.dumps(vo.pop('exclusions'))})
        if "blocked" in vo:
            vo.update({"blocked_json": json.dumps(vo.pop('blocked'))})
        if "bypass_src" in vo:
            vo.update({"bypass_src_json": json.dumps(vo.pop('bypass_src'))})
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
            if "blocked_json" in row:
                val = row.pop('blocked_json')
                row.update({"blocked": json.loads(val) if val else {}})
            if "bypass_src_json" in row:
                val = row.pop('bypass_src_json')
                row.update({"bypass_src": json.loads(val) if val else []})
            if "score_json" in row:
                val = row.pop('score_json')
                row.update({"score": json.loads(val) if val else {}})
        return super().to_dict(row)
