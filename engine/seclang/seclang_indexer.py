import json

import config
from engine.seclang.seclang_parser import RuleSetParser
from api.model.seclang_model import RuleCategoryDao, RuleDao


def index(config_file=f"{config.BASE_PATH}/admin/engine/seclang/crs-config.json",
          base_path=f"{config.BASE_PATH}/modsec/coreruleset"):
    with open(config_file, "r", encoding="utf-8") as arq:
        meta = json.load(arq)

    with RuleCategoryDao() as cat_dao, RuleDao() as rule_dao:
        cat_dao.create_schema()
        rule_dao.create_schema()

        # Clear existing data
        cat_dao.delete_all()
        rule_dao.delete_all()

        for c in meta['categories']:
            parser = RuleSetParser()
            rules = parser.load(c['file'], base_path)

            # Determine category phase based on rules, default to 2
            cat_phase = 2
            for rule in rules:
                if rule.get("schema_type") == "SecRule" and rule.get("phase"):
                    cat_phase = rule.get("phase")
                    break

            cat_id = c['name']
            category_doc = {
                "_id": cat_id,
                "name": c['name'],
                "phase": cat_phase,
                "file": c['file'],
                "exclusions": c.get("exclusions", [])
            }
            cat_dao.persist(category_doc)

            for rule in rules:
                if rule.get("schema_type") == "SecRule":
                    rule_doc = {
                        "_id": f"{cat_id}_{rule.get('code')}",
                        "code": rule.get("code"),
                        "category_id": cat_id,
                        "action": rule.get("action"),
                        "scope": rule.get("scope"),
                        "msg": rule.get("msg"),
                        "logdata": rule.get("logdata"),
                        "raw": rule.get("raw"),
                        "phase": rule.get("phase")
                    }
                    rule_dao.persist(rule_doc)
