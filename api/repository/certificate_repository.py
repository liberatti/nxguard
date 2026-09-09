import json
from datetime import datetime, timedelta
from typing import Dict, Any

import config
from nxcore.common_utils import replace_tz
from nxcore.middleware.logging_manager import logger
from api.repository.duck_db import DuckDAO
from api.model.certificate_model import CertificateSchema


class CertificateDao(DuckDAO):

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
