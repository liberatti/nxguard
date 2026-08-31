from datetime import datetime
from typing import Optional, Dict, Any

from nxcore.middleware.logging_manager import logger
from .duck_db import DuckDAO
from flask_marshmallow import Schema
from marshmallow import EXCLUDE, fields

import config as config


class ChallengeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    key = fields.String()
    content = fields.String()
    issued = fields.DateTime()


class ChallengeDao(DuckDAO):

    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="challenge")
        self.create_schema()

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                content TEXT,
                issued TIMESTAMP
            );
        """
        )
        try:
            self.ddl(
                f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS issued TIMESTAMP;"
            )
        except Exception:
            pass

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"select * from {self.table_name} where key = ?"
            rs = self._query(query, (key,), fetch=True)
            return self.to_dict(rs[0]) if rs else None
        except Exception as e:
            logger.error(f"Error retrieving challenge by key: {str(e)}")
            raise

    def delete_issued_before(self, dt: datetime) -> None:
        try:
            query = f"DELETE FROM {self.table_name} WHERE issued < ?"
            self._query(query, (dt,))
        except Exception as e:
            logger.error(f"Error deleting expired challenges: {str(e)}")
            raise
