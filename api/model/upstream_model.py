import json
from typing import Dict, Any, List
import datetime

from marshmallow import EXCLUDE, Schema, fields

import config as config
from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO


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


class UpstreamDao(DuckDAO):

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="upstream", schema=UpstreamSchema
        )

    def create_schema(self):
        self.ddl(
            f"""
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
        """
        )

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
        if "targets" in vo:
            vo.update({"targets_json": json.dumps(vo.pop("targets"))})
        if "persist" in vo:
            vo.update({"persist_json": json.dumps(vo.pop("persist"))})

        if "type" not in vo:
            vo.update({"type": "backend"})
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            targets_val = row.pop("targets_json") if "targets_json" in row else None
            persist_val = row.pop("persist_json") if "persist_json" in row else None
            row.update(
                {
                    "targets": json.loads(targets_val) if targets_val else [],
                    "persist": json.loads(persist_val) if persist_val else {},
                }
            )
        return super().to_dict(row)


class NodeStatusSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    status = fields.String()
    scn = fields.String(allow_none=True)
    last_check = fields.String()
    version = fields.String()
    net_recv = fields.Float()
    net_send = fields.Float()


class NodeStatusDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="node_status", schema=NodeStatusSchema
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id TEXT PRIMARY KEY,
                status TEXT,
                scn TEXT,
                last_check TEXT,
                version TEXT,
                net_recv DOUBLE,
                net_send DOUBLE
            );
        """
        )

    def register_node(self, k: str, node: dict):
        self.connect()
        if self.get_by_id(k):
            self.update_by_id(k, node)
        else:
            node_copy = node.copy()
            node_copy["_id"] = k
            self.persist(node_copy)

    def get_active_nodes(self) -> list:
        limit_time = (
            datetime.datetime.now(config.TZ) - datetime.timedelta(seconds=60)
        ).isoformat()
        self.connect()
        # Clean up nodes older than 60 seconds
        delete_sql = f"DELETE FROM {self.table_name} WHERE last_check < ?"
        self._query(delete_sql, (limit_time,))
        if self.auto_commit:
            self.commit()
        # Get remaining nodes
        sql = f"SELECT * FROM {self.table_name}"
        rs = self._query(sql, fetch=True)
        return [self.to_dict(row) for row in rs] if rs else []

    def purge_before_date(self, limit_date):
        try:
            limit_str = (
                limit_date.isoformat()
                if hasattr(limit_date, "isoformat")
                else str(limit_date)
            )
            self.connect()
            count_query = (
                f"SELECT COUNT(*) AS total FROM {self.table_name} WHERE last_check < ?"
            )
            count_res = self._query(count_query, (limit_str,), fetch=True)
            to_delete = count_res[0]["total"] if count_res else 0

            if to_delete > 0:
                delete_query = f"DELETE FROM {self.table_name} WHERE last_check < ?"
                self._query(delete_query, (limit_str,))
                if self.auto_commit:
                    self.commit()
            return to_delete
        except Exception as e:
            logger.error(f"Error purging node status: {e}")
            raise
