import json
from datetime import datetime, timedelta
from typing import Dict, Any

import config
from api.middleware.common_utils import replace_tz
from api.middleware.logging_manager import logger
from api.middleware.repository.duck_db import DuckDAO
from api.model.certificate_model import CertificateSchema


class CertificateDao(DuckDAO):

    CERTIFICATE_COLUMNS = {
        "_id",
        "name",
        "subjects",
        "chain",
        "certificate",
        "private_key",
        "ssl_client_ca",
        "not_before",
        "not_after",
        "status",
        "provider",
        "force_renew",
    }

    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="certificate",
            schema=CertificateSchema,
            conn=conn,
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subjects JSON NOT NULL,
                chain TEXT,
                certificate TEXT NOT NULL,
                private_key TEXT NOT NULL,
                ssl_client_ca TEXT,
                not_before TEXT,
                not_after TEXT,
                status TEXT,
                provider TEXT,
                force_renew BOOLEAN DEFAULT 0
            );
        """
        )

    def from_dict(self, vo: Dict[str, Any]) -> Dict[str, Any]:
        data = {k: v for k, v in vo.items() if k in self.CERTIFICATE_COLUMNS}
        if "subjects" in data and isinstance(data["subjects"], (list, dict)):
            data["subjects"] = json.dumps(data["subjects"])
        return super().from_dict(data)

    def to_dict(self, row):
        if not row:
            return row
        row["subjects"] = json.loads(row.get("subjects", "[]"))

        for key in ("not_before", "not_after"):
            date_str = row.get(key)
            if isinstance(date_str, str):
                try:
                    row[key] = datetime.fromisoformat(date_str)
                except Exception:
                    pass
        return super().to_dict(row)

    def persist(self, o: Dict[str, Any]) -> str:
        try:
            default_date = replace_tz((datetime.now() - timedelta(days=1))).replace(
                microsecond=0
            )
            if "not_after" not in o:
                o.update({"not_after": default_date})

            if "not_before" not in o:
                o.update({"not_before": default_date})
            return super().persist(o)
        except Exception as e:
            logger.error(f"Error persisting certificate: {str(e)}")
            raise
