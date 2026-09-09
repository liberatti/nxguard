from typing import Dict, Any, Optional

import config
from nxcore.middleware.logging_manager import logger
from api.repository.duck_db import DuckDAO
from api.model.oauth_model import UserSchema


class UserDao(DuckDAO):
    def create_schema(self):
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
        super().__init__(db_path=config.DB_PATH, table_name="users", schema=UserSchema)

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
