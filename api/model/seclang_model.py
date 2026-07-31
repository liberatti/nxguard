import json
from typing import List, Dict, Any, Optional

import config
from api.model.duck_db import DuckDAO
from engine.seclang.seclang_schema import RuleCategorySchema, SecRule


class RuleDao(DuckDAO):
    """
    Data Access Object for ModSecurity rules.
    """

    def __init__(self):
        super().__init__(db_path=config.DB_PATH, table_name="rules", schema=SecRule)

    def _query(self, sql, params=(), fetch=False):
        if not self.is_connected():
            self.connect()
        return super()._query(sql, params, fetch)

    def __del__(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id TEXT PRIMARY KEY,
                code INTEGER,
                category_id TEXT,
                action TEXT,
                scope_json TEXT,
                msg TEXT,
                logdata TEXT,
                raw TEXT,
                attachment TEXT,
                phase INTEGER,
                seq INTEGER,
                tags_json TEXT
            );
        """
        )

    def from_dict(self, vo):
        vo = vo.copy()
        if "scope" in vo:
            vo.update({"scope_json": json.dumps(vo.pop("scope"))})
        if "tags" in vo:
            vo.update({"tags_json": json.dumps(vo.pop("tags"))})
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            row = row.copy()
            if "scope_json" in row:
                val = row.pop("scope_json")
                row.update({"scope": json.loads(val) if val else []})
            if "tags_json" in row:
                val = row.pop("tags_json")
                row.update({"tags": json.loads(val) if val else []})
        return super().to_dict(row)

    def get_by_code(self, rule_code: int) -> Optional[Dict[str, Any]]:
        sql = f"SELECT * FROM {self.table_name} WHERE code = ? LIMIT 1"
        rs = self._query(sql, (rule_code,), fetch=True)
        return self.to_dict(rs[0]) if rs else None

    def get_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        sql = f"SELECT * FROM {self.table_name} WHERE category_id = ?"
        rs = self._query(sql, (category_id,), fetch=True)
        return [self.to_dict(row) for row in rs]


class RuleCategoryDao(DuckDAO):
    """
    Data Access Object for rule categories.
    """

    def __init__(self):
        super().__init__(
            db_path=config.DB_PATH, table_name="categories", schema=RuleCategorySchema
        )

    def _query(self, sql, params=(), fetch=False):
        if not self.is_connected():
            self.connect()
        return super()._query(sql, params, fetch)

    def __del__(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass

    def create_schema(self):
        self.ddl(
            f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                _id TEXT PRIMARY KEY,
                name TEXT,
                phase INTEGER,
                file TEXT,
                exclusions_json TEXT DEFAULT '[]',
                scope TEXT,
                seq INTEGER,
                system BOOLEAN DEFAULT FALSE
            );
        """
        )

    def from_dict(self, vo):
        vo = vo.copy()
        if "exclusions" in vo:
            vo.update({"exclusions_json": json.dumps(vo.pop("exclusions"))})
        # Exclude nested rules from direct serialization to rule_category table
        vo.pop("rules", None)
        return super().from_dict(vo)

    def to_dict(self, row):
        if row:
            row = row.copy()
            if "exclusions_json" in row:
                val = row.pop("exclusions_json")
                row.update({"exclusions": json.loads(val) if val else []})
            # Retrieve associated rules from the rule table
            with RuleDao() as rule_dao:
                row["rules"] = rule_dao.get_by_category(row["_id"])
        return super().to_dict(row)

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        sql = f"SELECT * FROM {self.table_name} WHERE name = ? LIMIT 1"
        rs = self._query(sql, (name,), fetch=True)
        return self.to_dict(rs[0]) if rs else None

    def get_by_name_and_phases(
        self, name: str, phases: List[int]
    ) -> List[Dict[str, Any]]:
        if not phases:
            sql = f"SELECT * FROM {self.table_name} WHERE name LIKE ?"
            params = [f"%{name}%"]
        else:
            placeholders = ", ".join(["?"] * len(phases))
            sql = f"SELECT * FROM {self.table_name} WHERE name LIKE ? AND phase IN ({placeholders})"
            params = [f"%{name}%"] + phases
        rs = self._query(sql, params, fetch=True)
        return [self.to_dict(row) for row in rs]

    def get_by_phases(self, phases: List[int]) -> List[Dict[str, Any]]:
        if not phases:
            sql = f"SELECT * FROM {self.table_name}"
            rs = self._query(sql, fetch=True)
        else:
            placeholders = ", ".join(["?"] * len(phases))
            sql = f"SELECT * FROM {self.table_name} WHERE phase IN ({placeholders})"
            rs = self._query(sql, phases, fetch=True)
        return [self.to_dict(row) for row in rs]
