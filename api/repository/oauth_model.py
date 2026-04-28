from typing import Dict, Any, Optional

from nxcore.middleware.logging import logger
from nxcore.repository.sqlite3_base_dao import SQLite3DAO
from marshmallow import EXCLUDE, Schema, fields

import config as config


class OIDCToken(Schema):
    access_token = fields.String()
    refresh_token = fields.String()
    token_type = fields.String(load_default="Bearer", dump_default="Bearer")
    expires_in = fields.Integer()
    provider = fields.String()


class UserSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.Integer()
    name = fields.String()
    email = fields.String()
    password = fields.String()
    locale = fields.String(required=False)
    role = fields.String()


class UserDao(SQLite3DAO):
    def create_schema(self):
        # self.ddl(f"DROP TABLE {self.table_name};")
        self.ddl(
            f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        _id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        role TEXT
                    );
                """
        )

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="users",
            schema=UserSchema
        )

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * from {self.table_name} WHERE email = ?"
            v = self._query(query, (email,), fetch=True)
            if v and v[0]:
                return super().to_dict(v[0])
            return None
        except Exception as e:
            logger.error(f"Error retrieving user by email: {str(e)}")
            raise
