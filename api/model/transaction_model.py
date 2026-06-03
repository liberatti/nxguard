import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from nxcore.middleware.logging import logger
from .duck_db import DuckDAO
from marshmallow import EXCLUDE, Schema, fields

import config as config
from config import DATETIME_FMT


class TransactionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer(required=False)
    logtime = fields.DateTime(format=DATETIME_FMT)
    unique_id = fields.String(required=False)
    server_id = fields.String(required=False)
    service = fields.Dict(required=False)
    action = fields.String(required=False)
    limit_req_status = fields.String(required=False)
    geoip_status = fields.String(required=False)
    rbl_status = fields.String(required=False)
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

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="transaction_logs",
            schema=TransactionSchema
        )

    def create_schema(self):
        self.ddl(f"""
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
                route_name TEXT,
                sensor_id TEXT,
                upstream_id TEXT,
                score INTEGER,
                archived BOOLEAN DEFAULT 0,
                user_agent_json TEXT,
                source_json TEXT,
                destination_json TEXT,
                http_json TEXT,
                upstream_json TEXT,
                audit_json TEXT
            );
        """)

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        if "logtime" in vo and isinstance(vo["logtime"], datetime):
            vo["logtime"] = vo["logtime"].strftime(config.DATETIME_FMT)

        if "service" in vo and vo["service"]:
            vo["service_id"] = str(vo["service"].get("_id", ""))
        if "sensor" in vo and vo["sensor"]:
            vo["sensor_id"] = str(vo["sensor"].get("_id", ""))
        if "upstream" in vo and vo["upstream"]:
            vo["upstream_id"] = str(vo["upstream"].get("_id", ""))

        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.strftime(config.DATETIME_FMT)
            raise TypeError(f"Type {type(obj)} not serializable")

        for key in ["user_agent", "source", "destination", "http", "upstream", "audit"]:
            if key in vo:
                vo[f"{key}_json"] = json.dumps(vo.pop(key), default=datetime_handler)
        return super().from_dict(vo)

    def to_dict(self, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row:
            for key in ["user_agent", "source", "destination", "http", "upstream", "audit"]:
                json_key = f"{key}_json"
                if json_key in row:
                    val = row.pop(json_key)
                    row[key] = json.loads(val) if val else {}

            if "service_id" in row:
                svc_id = row.pop("service_id")
                row["service"] = {"_id": svc_id} if svc_id else None
            if "sensor_id" in row:
                sns_id = row.pop("sensor_id")
                row["sensor"] = {"_id": sns_id} if sns_id else None
            if "upstream_id" in row:
                ups_id = row.pop("upstream_id")
                if "upstream" not in row or not row["upstream"]:
                    row["upstream"] = {"_id": ups_id} if ups_id else None
                elif ups_id:
                    row["upstream"]["_id"] = ups_id
        return super().to_dict(row)

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

        if filters:
            for key, val in filters.items():
                col = None
                if key == "server_id":
                    col = "server_id"
                elif key == "action":
                    col = "action"
                elif key in ["service._id", "service.id", "service_id"]:
                    col = "service_id"
                elif key in ["sensor._id", "sensor.id", "sensor_id"]:
                    col = "sensor_id"
                elif key in ["upstream._id", "upstream.id", "upstream_id"]:
                    col = "upstream_id"
                elif key == "rbl_status":
                    col = "rbl_status"
                elif key == "geoip_status":
                    col = "geoip_status"
                elif key == "archived":
                    col = "archived"

                if col:
                    if isinstance(val, list):
                        placeholders = ", ".join(["?"] * len(val))
                        where_clauses.append(f"{col} IN ({placeholders})")
                        params.extend(val)
                    else:
                        where_clauses.append(f"{col} = ?")
                        params.append(val)

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

        return {
            "metadata": pagination,
            "data": rows
        }

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

        if filters:
            for key, val in filters.items():
                col = None
                if key == "server_id":
                    col = "server_id"
                elif key == "action":
                    col = "action"
                elif key in ["service._id", "service.id", "service_id"]:
                    col = "service_id"
                elif key in ["sensor._id", "sensor.id", "sensor_id"]:
                    col = "sensor_id"
                elif key in ["upstream._id", "upstream.id", "upstream_id"]:
                    col = "upstream_id"
                elif key == "rbl_status":
                    col = "rbl_status"
                elif key == "geoip_status":
                    col = "geoip_status"
                elif key == "archived":
                    col = "archived"

                if col:
                    if isinstance(val, list):
                        placeholders = ", ".join(["?"] * len(val))
                        where_clauses.append(f"{col} IN ({placeholders})")
                        params.extend(val)
                    else:
                        where_clauses.append(f"{col} = ?")
                        params.append(val)

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
                COUNT(*) AS count
            FROM {self.table_name}
            {where_sql}
            GROUP BY year, month, day, hour, minute
            ORDER BY year, month, day, hour, minute
        """
        rs = self._query(query, params, fetch=True)
        tpm = []
        if rs:
            for r in rs:
                tpm.append({
                    "_id": {
                        "year": int(r["year"]) if r["year"] is not None else 0,
                        "month": int(r["month"]) if r["month"] is not None else 0,
                        "day": int(r["day"]) if r["day"] is not None else 0,
                        "hour": int(r["hour"]) if r["hour"] is not None else 0,
                        "minute": int(r["minute"]) if r["minute"] is not None else 0
                    },
                    "count": int(r["count"]) if r["count"] is not None else 0
                })
        return tpm

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
            limit_str = limit_date.strftime(config.DATETIME_FMT) if hasattr(limit_date, 'strftime') else str(limit_date)
            count_query = f"SELECT COUNT(*) AS total FROM {self.table_name} WHERE logtime < ?"
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
