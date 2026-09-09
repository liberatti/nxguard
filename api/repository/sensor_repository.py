import json
from typing import Dict, Any, Optional

import config
from api.repository.duck_db import DuckDAO
from api.model.sensor_model import SensorSchema


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

    def search(self, query: str = None, pagination: dict = None, order_by: str = None) -> dict:
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
