import json
from typing import Dict, Any, Optional

from marshmallow import EXCLUDE, Schema, fields

import config as config
from basic4web.middleware.logging import logger
from basic4web.repository.sqlite3_base_dao import SQLite3DAO


class ConfigArchiveSchema(Schema):
    enabled = fields.Boolean()
    archive_after = fields.Integer()  # minutes
    purge_after = fields.Integer()  # days
    type = fields.String()  # elastic_search, opensearch, syslog
    url = fields.String()
    username = fields.String()
    password = fields.String()


class ConfigPurgeSchema(Schema):
    enabled = fields.Boolean()
    purge_after = fields.Integer()  # days


class ConfigSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    _id = fields.String()
    cluster_id = fields.String()
    maxmind_key = fields.String()
    ca_certificate = fields.String()
    ca_private = fields.String()
    acme_directory_url = fields.String()
    archive = fields.Nested(ConfigArchiveSchema)
    purge = fields.Nested(ConfigPurgeSchema)


class ConfigDao(SQLite3DAO):
    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="config", schema=ConfigSchema)

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id TEXT,
                maxmind_key TEXT,
                ca_certificate TEXT,
                ca_private TEXT,
                acme_directory_url TEXT,
                archive_json TEXT,
                purge_json TEXT
            );
        """)

    def from_dict(self, vo):
        if "archive" in vo:
            vo.update({"archive_json": json.dumps(vo.pop('archive'))})
        if "purge" in vo:
            vo.update({"purge_json": json.dumps(vo.pop('purge'))})
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            if "archive_json" in row:
                row.update({"archive": json.load(row.pop('archive_json'))})
            if "purge_json" in row:
                row.update({"purge": json.load(row.pop('purge_json'))})
        return super().to_dict(row)
        
    def get_active(self) -> Optional[Dict[str, Any]]:
        try:
            query = f"select * from {self.table_name}"
            rs = self._query(query, many=False)
            return self.to_dict(rs)
        except Exception as e:
            logger.error(f"Error retrieving active configuration: {str(e)}")
            raise


class ChangeDao(SQLite3DAO):
    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="changes", schema=ConfigSchema)

    def create_schema(self):
        self.ddl(f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            );
        """)
