import json
from datetime import datetime, timedelta
from typing import Dict, Any

from basic4web.common_utils import replace_tz
from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class CertificateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    subjects = fields.List(fields.String())
    chain = fields.String()
    certificate = fields.String()
    private_key = fields.String()
    ssl_client_ca = fields.String()
    not_before = fields.DateTime(format=config.DATETIME_FMT, allow_none=True, required=False)
    not_after = fields.DateTime(format=config.DATETIME_FMT, allow_none=True, required=False)
    status = fields.String(required=False)
    provider = fields.String(required=False)
    force_renew = fields.Boolean(required=False, load_default=False, dump_default=False)


class CertificateDao(SQLite3DAO):

    def __init__(self, conn=None):
        super().__init__(
            db_path=config.DB_PATH
            , table_name="certificate"
            , schema=CertificateSchema
            , conn=conn
        )

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subjects TEXT NOT NULL,
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
        """)

    def from_dict(self, vo):
        if "subjects" in vo:
            vo.update({"subjects": json.dumps(vo.pop("subjects"))})
        return super().from_dict(vo)

    def persist(self, o: Dict[str, Any]) -> str:
        try:
            default_date = (
                replace_tz((datetime.now() - timedelta(days=1)))
                .replace(microsecond=0)
            )
            if "not_after" not in o:
                o.update({"not_after": default_date})

            if "not_before" not in o:
                o.update({"not_before": default_date})
            return super().persist(o)
        except Exception as e:
            logger.error(f"Error persisting certificate: {str(e)}")
            raise
