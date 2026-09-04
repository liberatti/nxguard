import json
from typing import Dict, Any, List, Optional
import datetime

from marshmallow import (
    EXCLUDE,
    Schema,
    fields,
    pre_load,
    validates_schema,
    ValidationError,
)

import config as config
from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO


class UpstreamTargetSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    host = fields.String()
    port = fields.Integer()
    weight = fields.Integer()
    state = fields.String(allow_none=True)
    healthy = fields.Boolean(allow_none=True)


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

    _id = fields.Integer(required=False, allow_none=True)
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
    index = fields.String(allow_none=True)
    content = fields.Raw(allow_none=True)
    healthy = fields.String(allow_none=True)

    @pre_load
    def process_id(self, data, **kwargs):
        if isinstance(data, dict):
            if data.get("_id") == "" or data.get("_id") is None:
                data.pop("_id", None)
        return data

    @validates_schema
    def validate_backend_targets(self, data, **kwargs):
        upstream_type = (data.get("type") or "backend").lower()
        if upstream_type == "backend":
            if data.get("_id") and "targets" not in data:
                return
            targets = data.get("targets")
            if not targets or len(targets) == 0:
                raise ValidationError(
                    "Backend upstream requires at least one target.", "targets"
                )


class UpstreamDao(DuckDAO):

    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="upstream",
            schema=UpstreamSchema,
            conn=conn,
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
                targets JSON,
                persist JSON,
                "index" TEXT,
                content TEXT
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

    def search(
        self, query: str = None, pagination: dict = None, order_by: str = None
    ) -> dict:
        if not query or not query.strip():
            return self.get_all(pagination=pagination, order_by=order_by)

        term = f"%{query.strip().lower()}%"
        where_clause = "WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?"
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

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        vo = dict(vo)
        if "type" not in vo:
            vo.update({"type": "backend"})
        if "targets" in vo and isinstance(vo["targets"], list):
            vo["targets"] = json.dumps(vo["targets"])
        if "persist" in vo and isinstance(vo["persist"], dict):
            vo["persist"] = json.dumps(vo["persist"])
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            row = dict(row)
            if isinstance(row.get("targets"), str):
                row["targets"] = json.loads(row.get("targets") or "[]")
            if isinstance(row.get("persist"), str):
                row["persist"] = json.loads(row.get("persist") or "{}")

            upstream_id = row.get("_id")
            if upstream_id:
                try:
                    limit_time = (
                        datetime.datetime.now(config.TZ)
                        - datetime.timedelta(seconds=60)
                    ).isoformat()
                    sql = "SELECT healthy, targets FROM upstream_states WHERE upstream_id = ? AND last_check >= ?"
                    states = self._query(
                        sql, (int(upstream_id), limit_time), fetch=True
                    )
                    if states:
                        targets_node_checks = {}
                        for s in states:
                            st_targets = s.get("targets")
                            if isinstance(st_targets, str):
                                st_targets = json.loads(st_targets or "[]")
                            for t in st_targets or []:
                                endpoint = (
                                    t.get("endpoint")
                                    or f"{t.get('host')}:{t.get('port')}"
                                )
                                is_t_healthy = bool(t.get("healthy", False))
                                if endpoint not in targets_node_checks:
                                    targets_node_checks[endpoint] = []
                                targets_node_checks[endpoint].append(is_t_healthy)

                        targets_list = row.get("targets") or []
                        for t in targets_list:
                            endpoint = f"{t.get('host')}:{t.get('port')}"
                            checks = targets_node_checks.get(endpoint, [])
                            t["healthy"] = all(checks) if checks else False

                        all_checks = [
                            c for checks in targets_node_checks.values() for c in checks
                        ]
                        total = len(all_checks)
                        healthy_count = sum(1 for c in all_checks if c)
                        if total == 0:
                            row["healthy"] = "invalid"
                        elif healthy_count == total:
                            row["healthy"] = "healthy"
                        elif healthy_count == 0:
                            row["healthy"] = "unhealthy"
                        else:
                            row["healthy"] = "partially_healthy"
                    else:
                        is_static = row.get("type") == "static"
                        row["healthy"] = "healthy" if is_static else "invalid"
                        for t in row.get("targets") or []:
                            t["healthy"] = False
                except Exception as e:
                    logger.debug(
                        f"Could not load upstream state for {upstream_id}: {e}"
                    )
                    row["healthy"] = (
                        "healthy" if (row.get("type") == "static") else "invalid"
                    )
            else:
                row["healthy"] = (
                    "healthy" if (row.get("type") == "static") else "invalid"
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


class UpstreamStatesSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    node_id = fields.String()
    upstream_id = fields.Integer()
    healthy = fields.String()
    last_check = fields.String()
    targets = fields.List(fields.Dict(), allow_none=True)


class UpstreamStatesDao(DuckDAO):
    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="upstream_states",
            schema=UpstreamStatesSchema,
            conn=conn,
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT,
                upstream_id INTEGER,
                healthy TEXT,
                last_check TEXT,
                targets JSON
            );
        """
        )

    def register_state(self, node_id: str, upstream_id: int, state: dict):
        self.connect()
        sql = f"SELECT * FROM {self.table_name} WHERE node_id = ? AND upstream_id = ?"
        rs = self._query(sql, (node_id, upstream_id), fetch=True)
        if rs:
            row_id = rs[0]["_id"]
            state_copy = state.copy()
            state_copy["_id"] = row_id
            state_copy["node_id"] = node_id
            state_copy["upstream_id"] = upstream_id
            self.update_by_id(row_id, state_copy)
        else:
            state_copy = state.copy()
            state_copy["node_id"] = node_id
            state_copy["upstream_id"] = upstream_id
            state_copy.pop("_id", None)
            self.persist(state_copy)

    def get_by_node_and_upstream(self, node_id: str, upstream_id: int):
        self.connect()
        sql = f"SELECT * FROM {self.table_name} WHERE node_id = ? AND upstream_id = ?"
        rs = self._query(sql, (node_id, upstream_id), fetch=True)
        return self.to_dict(rs[0]) if rs else None

    def get_active_states(self, node_id: Optional[str] = None) -> list:
        limit_time = (
            datetime.datetime.now(config.TZ) - datetime.timedelta(seconds=60)
        ).isoformat()
        self.connect()
        # Clean up stale states older than 60 seconds
        delete_sql = f"DELETE FROM {self.table_name} WHERE last_check < ?"
        self._query(delete_sql, (limit_time,))
        if self.auto_commit:
            self.commit()
        if node_id:
            sql = f"SELECT * FROM {self.table_name} WHERE node_id = ?"
            rs = self._query(sql, (node_id,), fetch=True)
        else:
            sql = f"SELECT * FROM {self.table_name}"
            rs = self._query(sql, fetch=True)
        return [self.to_dict(row) for row in rs] if rs else []

    def get_states_by_upstream_id(self, upstream_id: int) -> list:
        self.connect()
        sql = f"SELECT * FROM {self.table_name} WHERE upstream_id = ?"
        rs = self._query(sql, (upstream_id,), fetch=True)
        return [self.to_dict(row) for row in rs] if rs else []

    def delete_by_upstream_id(self, upstream_id: int):
        self.connect()
        sql = f"DELETE FROM {self.table_name} WHERE upstream_id = ?"
        self._query(sql, (int(upstream_id),))
        if self.auto_commit:
            self.commit()

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        vo = dict(vo)
        if "targets" in vo and isinstance(vo["targets"], list):
            vo["targets"] = json.dumps(vo["targets"])
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            row = dict(row)
            if isinstance(row.get("targets"), str):
                row["targets"] = json.loads(row.get("targets") or "[]")
        return super().to_dict(row)
