import datetime
import json
from typing import Dict, Any, Optional

import config
from nxcore.middleware.logging_manager import logger
from api.repository.duck_db import DuckDAO
from api.model.config_model import ConfigSchema, ConfigBackupSchema, ChangeSchema


class ConfigBackupDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH,
            table_name="config_backup",
            schema=ConfigBackupSchema,
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                scn TEXT,
                created_at TIMESTAMP,
                data JSON
            );
        """
        )

    def to_dict(self, row):
        if row and "data" in row:
            if isinstance(row["data"], str):
                try:
                    row["data"] = json.loads(row["data"])
                except Exception:
                    pass
            if isinstance(row["data"], dict) and "services" in row["data"]:
                try:
                    for s in row["data"]["services"]:
                        c = s.pop("certificate", None)
                        if c:
                            s.update(
                                {
                                    "certificate": {
                                        "name": c["name"] if isinstance(c, dict) else c
                                    }
                                }
                            )
                except Exception:
                    pass
        return super().to_dict(row)

    def get_latest(self) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * FROM {self.table_name} ORDER BY _id DESC LIMIT 1"
            rs = self._query(query, fetch=True)
            return self.to_dict(rs[0]) if rs else None
        except Exception as e:
            logger.error(f"Error retrieving latest backup configuration: {str(e)}")
            return None

    def get_by_scn(self, scn: str) -> Optional[Dict[str, Any]]:
        try:
            query = f"SELECT * FROM {self.table_name} WHERE scn = ?"
            rs = self._query(query, (scn,), fetch=True)
            return self.to_dict(rs[0]) if rs else None
        except Exception as e:
            logger.error(
                f"Error retrieving backup configuration by SCN {scn}: {str(e)}"
            )
            return None

    def from_dict(self, vo):
        if "created_at" not in vo:
            vo.update({"created_at": datetime.datetime.now()})
        if "data" in vo and isinstance(vo["data"], dict):
            vo["data"] = json.dumps(vo["data"], default=str)
        return super().from_dict(vo)


class ConfigDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="config", schema=ConfigSchema
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                cluster_id TEXT,
                ca_certificate TEXT,
                ca_private TEXT,
                acme_directory_url TEXT,
                archive_json TEXT,
                logging_json TEXT,
                cache_json TEXT,
                purge_json TEXT,
                dns_resolver TEXT,
                ipxa_json TEXT,
                active_scn TEXT
            );
        """
        )
        try:
            self.ddl(f"ALTER TABLE {self.table_name} ADD COLUMN IF NOT EXISTS logging_json TEXT;")
        except Exception:
            pass

    def from_dict(self, vo):
        if "archive" in vo:
            vo.update({"archive_json": json.dumps(vo.pop("archive"), default=str)})
        if "logging" in vo:
            vo.update({"logging_json": json.dumps(vo.pop("logging"), default=str)})
        if "purge" in vo:
            vo.update({"purge_json": json.dumps(vo.pop("purge"), default=str)})
        if "cache" in vo:
            vo.update({"cache_json": json.dumps(vo.pop("cache"), default=str)})
        if "ipxa" in vo:
            vo.update({"ipxa_json": json.dumps(vo.pop("ipxa"), default=str)})
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            if "archive_json" in row:
                val = row.pop("archive_json")
                row.update({"archive": json.loads(val) if val else None})
            if "logging_json" in row:
                val = row.pop("logging_json")
                row.update({"logging": json.loads(val) if val else None})
            if "purge_json" in row:
                val = row.pop("purge_json")
                row.update({"purge": json.loads(val) if val else None})
            if "cache_json" in row:
                val = row.pop("cache_json")
                row.update({"cache": json.loads(val) if val else None})
            if "ipxa_json" in row:
                val = row.pop("ipxa_json")
                row.update({"ipxa": json.loads(val) if val else None})
        return super().to_dict(row)

    def get_active(self) -> Optional[Dict[str, Any]]:
        try:
            query = f"select * from {self.table_name}"
            rs = self._query(query, fetch=True)
            return self.to_dict(rs[0]) if rs else None
        except Exception as e:
            logger.error(f"Error retrieving active configuration: {str(e)}")
            raise

    def get_active_scn(self) -> Optional[str]:
        active = self.get_active()
        return active.get("active_scn") if active else None


class ChangeDao(DuckDAO):
    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="changes", schema=ChangeSchema
        )

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            );
        """
        )

    def has_certificate_change(self) -> bool:
        try:
            query = f"SELECT COUNT(*) as count FROM {self.table_name} WHERE name = 'certificate'"
            rs = self._query(query, fetch=True)
            return rs[0]["count"] > 0
        except Exception as e:
            logger.error(f"Error checking for certificate change: {str(e)}")
            return False
