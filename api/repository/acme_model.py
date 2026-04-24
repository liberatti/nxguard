from typing import Optional, Dict, Any

from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO
from flask_marshmallow import Schema
from marshmallow import EXCLUDE, fields

import config as config


class ChallengeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    key = fields.String()
    content = fields.String()


class ChallengeDao(SQLite3DAO):

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="challenge"
        )

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT,
                content TEXT
            );
        """)

    def get_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"select * from {self.table_name} where key = ?"
            rs = self._query(query, (key,))
            return self.to_dict(rs)
        except Exception as e:
            logger.error(f"Error retrieving challenge by key: {str(e)}")
            raise
