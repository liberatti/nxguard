import json
from typing import Dict, Any, List

from marshmallow import EXCLUDE, Schema, fields

import config as config
from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO


class UpstreamTargetSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    host = fields.String()
    port = fields.Integer()
    weight = fields.Integer()
    state = fields.String()


class UpstreamPersistSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.String(required=False)
    cookie_name = fields.String(required=False)
    cookie_domain = fields.String(required=False)
    cookie_path = fields.String(required=False)
    cookie_expire = fields.Integer(required=False)


class UpstreamSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    description = fields.String()
    retry = fields.Integer()
    retry_timeout = fields.Integer()
    conn_timeout = fields.Integer()
    protocol = fields.String()  # AJP, HTTP, HTTPS
    script_path = fields.String()  # fastcgi
    type = fields.String()  # backend, static
    targets = fields.List(fields.Nested(UpstreamTargetSchema))
    persist = fields.Nested(UpstreamPersistSchema)
    target_index = fields.String()
    target_content = fields.Raw()


class UpstreamDao(SQLite3DAO):

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="upstream",
            schema=UpstreamSchema
        )

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                retry INTEGER,
                retry_timeout INTEGER,
                conn_timeout INTEGER,
                protocol TEXT,
                script_path TEXT,
                type TEXT,
                targets_json TEXT,
                persist_json TEXT,
                target_index TEXT,
                target_content TEXT
            );
        """)

    def get_all_by_type(self, t: str) -> List[Dict[str, Any]]:
        try:
            query = f"SELECT * from {self.table_name} WHERE type = ?"
            rows = list(self._query(query, (t,), fetch=True))
            for r in rows:
                r.update(self.to_dict(r))
            return rows
        except Exception as e:
            logger.error(f"Error retrieving upstreams by type: {str(e)}")
            raise

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        if 'targets' in vo:
            vo.update({
                "targets_json": json.dumps(vo.pop('targets'))
            })
        if 'persist' in vo:
            vo.update({
                "persist_json": json.dumps(vo.pop('persist'))
            })

        if "type" not in vo:
            vo.update({"type": "backend"})
        return super().from_dict(vo)

    def to_dict(self, row):
        row.update({
            "targets": json.loads(row.pop("targets_json")),
            "persist": json.loads(row.pop("persist_json"))
        })
        return super().to_dict(row)
