import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class TransactionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer(required=False)
    logtime = fields.Raw(required=False)
    unique_id = fields.String(required=False)
    server_id = fields.String(required=False)
    service = fields.Dict(required=False)
    action = fields.String(required=False)
    limit_req_status = fields.String(required=False)
    geoip_status = fields.String(required=False)
    rbl_status = fields.String(required=False)
    ipxa = fields.String(required=False)
    rate_limit = fields.Dict(required=False)
    geoip = fields.Dict(required=False)
    reputation = fields.Dict(required=False)
    mtls = fields.Dict(required=False)
    user_agent = fields.Dict(required=False)
    source = fields.Dict(required=False)
    destination = fields.Dict(required=False)
    http = fields.Dict(required=False)
    route_name = fields.String(required=False)
    sensor = fields.Dict(required=False)
    upstream = fields.Dict(required=False)
    audit = fields.Dict(required=False)
    score = fields.Integer(required=False)
    archived = fields.Boolean(required=False)


class TransactionDao(DuckDAO):
    """
    DAO for managing transaction log records using DuckDB.
    """

    ALLOWED_COLUMNS = {
        "_id",
        "logtime",
        "unique_id",
        "server_id",
        "service_id",
        "action",
        "limit_req_status",
        "geoip_status",
        "rbl_status",
        "ipxa",
        "route_name",
        "sensor_id",
        "upstream_id",
        "score",
        "archived",
        "user_agent_json",
        "source_json",
        "destination_json",
        "http_json",
        "upstream_json",
        "service_json",
        "sensor_json",
        "rate_limit_json",
        "geoip_json",
        "reputation_json",
        "mtls_json",
        "audit_json",
    }

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="transaction_logs",
            schema=TransactionSchema,
            db_name="log.duckdb",
        )
        self.create_schema()

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                logtime TEXT,
                unique_id TEXT,
                server_id TEXT,
                service_id TEXT,
                action TEXT,
                limit_req_status TEXT,
                geoip_status TEXT,
                rbl_status TEXT,
                ipxa TEXT,
                route_name TEXT,
                sensor_id TEXT,
                upstream_id TEXT,
                score INTEGER,
                archived BOOLEAN DEFAULT 0,
                user_agent_json JSON,
                source_json JSON,
                destination_json JSON,
                http_json JSON,
                upstream_json JSON,
                service_json JSON,
                sensor_json JSON,
                rate_limit_json JSON,
                geoip_json JSON,
                reputation_json JSON,
                mtls_json JSON,
                audit_json JSON
            );
        """
        )
        # Migrate existing table if missing new columns
        new_columns = [
            ("ipxa", "TEXT"),
            ("service_json", "JSON"),
            ("sensor_json", "JSON"),
            ("rate_limit_json", "JSON"),
            ("geoip_json", "JSON"),
            ("reputation_json", "JSON"),
            ("mtls_json", "JSON"),
        ]
        for col_name, col_type in new_columns:
            try:
                self.ddl(
                    f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type};"
                )
            except Exception:
                pass

    @staticmethod
    def _normalize_filters(filters) -> Dict[str, Any]:
        if not filters:
            return {}
        if isinstance(filters, dict):
            return filters
        if isinstance(filters, list):
            merged = {}
            for item in filters:
                if isinstance(item, str):
                    try:
                        parsed = json.loads(item)
                        if isinstance(parsed, dict):
                            merged.update(parsed)
                    except Exception:
                        pass
                elif isinstance(item, dict):
                    merged.update(item)
            return merged
        return {}

    _FILTER_FIELD_MAP = {
        "server_id": "server_id",
        "action": "action",
        "service_id": "service_id",
        "service._id": "service_id",
        "service.id": "service_id",
        "service.name": "service_id",
        "sensor_id": "sensor_id",
        "sensor._id": "sensor_id",
        "sensor.id": "sensor_id",
        "upstream_id": "upstream_id",
        "upstream._id": "upstream_id",
        "upstream.id": "upstream_id",
        "rbl_status": "rbl_status",
        "geoip_status": "geoip_status",
        "ipxa": "ipxa",
        "archived": "archived",
        "route_name": "route_name",
        "unique_id": "unique_id",
        "score": "score",
        "limit_req_status": "limit_req_status",
        "source_ip": "json_extract_string(CAST(source_json AS JSON), '$.ip')",
        "source.ip": "json_extract_string(CAST(source_json AS JSON), '$.ip')",
        "source_port": "TRY_CAST(json_extract_string(CAST(source_json AS JSON), '$.port') AS INTEGER)",
        "source.port": "TRY_CAST(json_extract_string(CAST(source_json AS JSON), '$.port') AS INTEGER)",
        "country": "COALESCE(json_extract_string(CAST(source_json AS JSON), '$.geo.country'), json_extract_string(CAST(geoip_json AS JSON), '$.country_code'))",
        "source.geo.country": "COALESCE(json_extract_string(CAST(source_json AS JSON), '$.geo.country'), json_extract_string(CAST(geoip_json AS JSON), '$.country_code'))",
        "geoip.country_code": "COALESCE(json_extract_string(CAST(source_json AS JSON), '$.geo.country'), json_extract_string(CAST(geoip_json AS JSON), '$.country_code'))",
        "destination_host": "json_extract_string(CAST(destination_json AS JSON), '$.host')",
        "destination.host": "json_extract_string(CAST(destination_json AS JSON), '$.host')",
        "destination_ip": "json_extract_string(CAST(destination_json AS JSON), '$.ip')",
        "destination.ip": "json_extract_string(CAST(destination_json AS JSON), '$.ip')",
        "destination_port": "TRY_CAST(json_extract_string(CAST(destination_json AS JSON), '$.port') AS INTEGER)",
        "destination.port": "TRY_CAST(json_extract_string(CAST(destination_json AS JSON), '$.port') AS INTEGER)",
        "method": "json_extract_string(CAST(http_json AS JSON), '$.request.method')",
        "http_method": "json_extract_string(CAST(http_json AS JSON), '$.request.method')",
        "http.request.method": "json_extract_string(CAST(http_json AS JSON), '$.request.method')",
        "uri": "json_extract_string(CAST(http_json AS JSON), '$.request.uri')",
        "http_uri": "json_extract_string(CAST(http_json AS JSON), '$.request.uri')",
        "http.request.uri": "json_extract_string(CAST(http_json AS JSON), '$.request.uri')",
        "status": "TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.response.status_code') AS INTEGER)",
        "status_code": "TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.response.status_code') AS INTEGER)",
        "http.response.status_code": "TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.response.status_code') AS INTEGER)",
        "duration": "TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.duration') AS DOUBLE)",
        "http.duration": "TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.duration') AS DOUBLE)",
        "rate_limit": "COALESCE(json_extract_string(CAST(rate_limit_json AS JSON), '$.action'), limit_req_status)",
        "rate_limit.action": "COALESCE(json_extract_string(CAST(rate_limit_json AS JSON), '$.action'), limit_req_status)",
        "user_agent": "json_extract_string(CAST(user_agent_json AS JSON), '$.family')",
        "user_agent.family": "json_extract_string(CAST(user_agent_json AS JSON), '$.family')",
        "mtls_verified": "TRY_CAST(json_extract_string(CAST(mtls_json AS JSON), '$.verified') AS BOOLEAN)",
        "mtls.verified": "TRY_CAST(json_extract_string(CAST(mtls_json AS JSON), '$.verified') AS BOOLEAN)",
    }

    _LIKE_FIELD_MAP = {
        "rule_code": "json_extract_string(CAST(audit_json AS JSON), '$.messages')",
        "audit.rule_code": "json_extract_string(CAST(audit_json AS JSON), '$.messages')",
        "audit.messages.rule_code": "json_extract_string(CAST(audit_json AS JSON), '$.messages')",
    }

    @classmethod
    def _append_dict_condition(cls, expr: str, val: dict, where_clauses: List[str], params: List[Any]):
        op_map = {"$ne": "!=", "$gte": ">=", "$lte": "<=", "$gt": ">", "$lt": "<"}
        for op, op_val in val.items():
            if op in op_map:
                where_clauses.append(f"{expr} {op_map[op]} ?")
                params.append(op_val)
            elif op in ["$like", "$contains"]:
                where_clauses.append(f"{expr} LIKE ?")
                params.append(f"%{op_val}%" if not str(op_val).startswith("%") else op_val)
            elif op == "$in" and isinstance(op_val, list):
                placeholders = ", ".join(["?"] * len(op_val))
                where_clauses.append(f"{expr} IN ({placeholders})")
                params.extend(op_val)

    @classmethod
    def _build_filter_clauses(cls, filters) -> Tuple[List[str], List[Any]]:
        where_clauses = []
        params = []
        filter_dict = cls._normalize_filters(filters)
        if not filter_dict:
            return where_clauses, params

        for key, val in filter_dict.items():
            expr = cls._FILTER_FIELD_MAP.get(key)
            is_like = False
            if not expr and key in cls._LIKE_FIELD_MAP:
                expr = cls._LIKE_FIELD_MAP[key]
                is_like = True

            if not expr:
                continue

            if isinstance(val, list):
                placeholders = ", ".join(["?"] * len(val))
                where_clauses.append(f"{expr} IN ({placeholders})")
                params.extend(val)
            elif isinstance(val, dict):
                cls._append_dict_condition(expr, val, where_clauses, params)
            elif is_like:
                where_clauses.append(f"{expr} LIKE ?")
                params.append(f"%{val}%")
            else:
                where_clauses.append(f"{expr} = ?")
                params.append(val)

        return where_clauses, params

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(vo)
        if "logtime" in data:
            if isinstance(data["logtime"], datetime):
                data["logtime"] = data["logtime"].strftime(config.DATETIME_FMT)
            elif isinstance(data["logtime"], str):
                data["logtime"] = data["logtime"]

        if "service" in data and data["service"]:
            if isinstance(data["service"], dict):
                data["service_id"] = str(
                    data["service"].get("_id")
                    or data["service"].get("id")
                    or data["service"].get("name")
                    or ""
                )
            else:
                data["service_id"] = str(data["service"])
                data["service"] = {"_id": str(data["service"]), "name": str(data["service"])}

        if "sensor" in data and data["sensor"]:
            if isinstance(data["sensor"], dict):
                data["sensor_id"] = str(
                    data["sensor"].get("_id")
                    or data["sensor"].get("id")
                    or data["sensor"].get("name")
                    or ""
                )
            else:
                data["sensor_id"] = str(data["sensor"])
                data["sensor"] = {"_id": str(data["sensor"]), "name": str(data["sensor"])}

        if "upstream" in data and data["upstream"]:
            if isinstance(data["upstream"], dict):
                data["upstream_id"] = str(
                    data["upstream"].get("_id")
                    or data["upstream"].get("id")
                    or data["upstream"].get("name")
                    or ""
                )
            else:
                data["upstream_id"] = str(data["upstream"])
                data["upstream"] = {
                    "_id": str(data["upstream"]),
                    "name": str(data["upstream"]),
                }

        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.strftime(config.DATETIME_FMT)
            raise TypeError(f"Type {type(obj)} not serializable")

        json_keys = [
            "user_agent",
            "source",
            "destination",
            "http",
            "upstream",
            "service",
            "sensor",
            "rate_limit",
            "geoip",
            "reputation",
            "mtls",
            "audit",
        ]
        for key in json_keys:
            if key in data:
                data[f"{key}_json"] = json.dumps(data.pop(key), default=datetime_handler)

        cleaned = {k: v for k, v in data.items() if k in self.ALLOWED_COLUMNS}
        return super().from_dict(cleaned)

    def to_dict(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row:
            if "logtime" in row and isinstance(row["logtime"], datetime):
                row["logtime"] = row["logtime"].strftime(config.DATETIME_FMT)
            elif "logtime" in row and row["logtime"] is not None:
                row["logtime"] = str(row["logtime"])

            json_keys = [
                "user_agent",
                "source",
                "destination",
                "http",
                "upstream",
                "service",
                "sensor",
                "rate_limit",
                "geoip",
                "reputation",
                "mtls",
                "audit",
            ]
            for key in json_keys:
                json_key = f"{key}_json"
                if json_key in row:
                    val = row.pop(json_key)
                    row[key] = json.loads(val) if val else {}

            if "service_id" in row:
                svc_id = row.pop("service_id", None)
                if not row.get("service"):
                    row["service"] = {"_id": svc_id, "name": svc_id} if svc_id else None
                elif isinstance(row["service"], dict) and svc_id and "_id" not in row["service"]:
                    row["service"]["_id"] = svc_id

            if "sensor_id" in row:
                sns_id = row.pop("sensor_id", None)
                if not row.get("sensor"):
                    row["sensor"] = {"_id": sns_id, "name": sns_id} if sns_id else None
                elif isinstance(row["sensor"], dict) and sns_id and "_id" not in row["sensor"]:
                    row["sensor"]["_id"] = sns_id

            if "upstream_id" in row:
                ups_id = row.pop("upstream_id", None)
                if not row.get("upstream"):
                    row["upstream"] = {"_id": ups_id, "name": ups_id} if ups_id else None
                elif isinstance(row["upstream"], dict) and ups_id and "_id" not in row["upstream"]:
                    row["upstream"]["_id"] = ups_id

        return super().to_dict(row)

    def get_by_unique_id(self, unique_id: str) -> Optional[Dict[str, Any]]:
        if not unique_id:
            return None
        sql = f"SELECT * FROM {self.table_name} WHERE unique_id = ? LIMIT 1"
        res = self._query(sql, (unique_id,), fetch=True)
        if res and len(res) > 0:
            return self.to_dict(res[0])
        return None

    def upsert_by_unique_id(self, vo: Dict[str, Any]):
        unique_id = vo.get("unique_id")
        if unique_id:
            existing = self.get_by_unique_id(unique_id)
            if existing and "_id" in existing:
                self.update_by_id(existing["_id"], vo)
                return existing["_id"]
        return self.persist(vo)

    def update(self, _id, vo):
        return self.update_by_id(_id, vo)

    def get_all(self, pagination=None, dt_start=None, dt_end=None, filters=None):
        start_str = dt_start.strftime(config.DATETIME_FMT) if dt_start else None
        end_str = dt_end.strftime(config.DATETIME_FMT) if dt_end else None

        where_clauses = []
        params = []

        if start_str:
            where_clauses.append("logtime >= ?")
            params.append(start_str)
        if end_str:
            where_clauses.append("logtime <= ?")
            params.append(end_str)

        f_clauses, f_params = self._build_filter_clauses(filters)
        where_clauses.extend(f_clauses)
        params.extend(f_params)

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        count_sql = f"SELECT COUNT(*) AS total FROM {self.table_name}{where_sql}"
        total = self._query(count_sql, params, fetch=True)[0]["total"]

        sql = f"SELECT * FROM {self.table_name}{where_sql} ORDER BY logtime DESC"

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

        return {"metadata": pagination, "data": rows}

    def get_tpm(self, st_date, ed_date, filters=None) -> List[Dict[str, Any]]:
        start_str = st_date.strftime(config.DATETIME_FMT) if st_date else None
        end_str = ed_date.strftime(config.DATETIME_FMT) if ed_date else None

        where_clauses = []
        params = []

        if start_str:
            where_clauses.append("logtime >= ?")
            params.append(start_str)
        if end_str:
            where_clauses.append("logtime <= ?")
            params.append(end_str)

        f_clauses, f_params = self._build_filter_clauses(filters)
        where_clauses.extend(f_clauses)
        params.extend(f_params)

        where_sql = ""
        if where_clauses:
            where_sql = " WHERE " + " AND ".join(where_clauses)

        query = f"""
            SELECT
                EXTRACT(year FROM CAST(logtime AS TIMESTAMP)) AS year,
                EXTRACT(month FROM CAST(logtime AS TIMESTAMP)) AS month,
                EXTRACT(day FROM CAST(logtime AS TIMESTAMP)) AS day,
                EXTRACT(hour FROM CAST(logtime AS TIMESTAMP)) AS hour,
                EXTRACT(minute FROM CAST(logtime AS TIMESTAMP)) AS minute,
                COALESCE(UPPER(action), 'PASSED') AS action,
                COUNT(*) AS count,
                COALESCE(SUM(TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.request.bytes') AS UBIGINT)), 0) AS bytes_in,
                COALESCE(SUM(TRY_CAST(json_extract_string(CAST(http_json AS JSON), '$.response.bytes') AS UBIGINT)), 0) AS bytes_out
            FROM {self.table_name}
            {where_sql}
            GROUP BY year, month, day, hour, minute, COALESCE(UPPER(action), 'PASSED')
            ORDER BY year, month, day, hour, minute
        """
        rs = self._query(query, params, fetch=True)
        tpm_map = {}
        if rs:
            for r in rs:
                key = (
                    int(r["year"]) if r["year"] is not None else 0,
                    int(r["month"]) if r["month"] is not None else 0,
                    int(r["day"]) if r["day"] is not None else 0,
                    int(r["hour"]) if r["hour"] is not None else 0,
                    int(r["minute"]) if r["minute"] is not None else 0,
                )
                action = str(r["action"]).upper() if r.get("action") else "PASSED"
                count = int(r["count"]) if r["count"] is not None else 0
                bytes_in = int(r["bytes_in"]) if r.get("bytes_in") is not None else 0
                bytes_out = int(r["bytes_out"]) if r.get("bytes_out") is not None else 0

                if key not in tpm_map:
                    tpm_map[key] = {
                        "_id": {
                            "year": key[0],
                            "month": key[1],
                            "day": key[2],
                            "hour": key[3],
                            "minute": key[4],
                        },
                        "count": 0,
                        "bytes_in": 0,
                        "bytes_out": 0,
                        "actions": {},
                    }
                tpm_map[key]["count"] += count
                tpm_map[key]["bytes_in"] += bytes_in
                tpm_map[key]["bytes_out"] += bytes_out
                tpm_map[key]["actions"][action] = (
                    tpm_map[key]["actions"].get(action, 0) + count
                )

        return list(tpm_map.values())

    def get_node_bandwidth(self, node_name: str) -> List[Dict[str, Any]]:
        try:
            query = f"""
                SELECT
                    COALESCE(SUM(CAST(json_extract_string(CAST(http_json AS JSON), '$.request.bytes') AS UBIGINT)), 0) AS net_recv_bytes,
                    COALESCE(SUM(CAST(json_extract_string(CAST(http_json AS JSON), '$.response.bytes') AS UBIGINT)), 0) AS net_send_bytes
                FROM {self.table_name}
                WHERE server_id = ?
            """
            rs = self._query(query, (node_name,), fetch=True)
            if rs:
                row = rs[0]
                net_recv = (row["net_recv_bytes"] or 0) / 1048576.0
                net_send = (row["net_send_bytes"] or 0) / 1048576.0
                return [{"net_recv": net_recv, "net_send": net_send}]
            return [{"net_recv": 0.0, "net_send": 0.0}]
        except Exception as e:
            logger.error(f"Error calculating node bandwidth: {e}")
            raise

    def purge_before_date(self, limit_date) -> int:
        try:
            limit_str = (
                limit_date.strftime(config.DATETIME_FMT)
                if hasattr(limit_date, "strftime")
                else str(limit_date)
            )
            count_query = (
                f"SELECT COUNT(*) AS total FROM {self.table_name} WHERE logtime < ?"
            )
            count_res = self._query(count_query, (limit_str,), fetch=True)
            to_delete = count_res[0]["total"] if count_res else 0

            if to_delete > 0:
                delete_query = f"DELETE FROM {self.table_name} WHERE logtime < ?"
                self._query(delete_query, (limit_str,))
                if self.auto_commit:
                    self.commit()
            return to_delete
        except Exception as e:
            logger.error(f"Error purging transactions: {e}")
            raise
