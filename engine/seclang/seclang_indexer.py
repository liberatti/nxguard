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
            cat_dao.persist(c)
            parser = RuleSetParser()
            rules = parser.load(c['file'], base_path)
            s = 1
            for rule in rules:
                if rule.get("schema_type") == "SecRule":
                    rule_doc = {
                        "_id": f"{rule.get('code')}",
                        "code": rule.get("code"),
                        "category_id": c['_id'],
                        "raw": rule.get("raw"),
                        "attachment": rule.get("attachment"),
                        "action": rule.get("action"),
                        "scope": rule.get("scope"),
                        "tags": rule.get("tags"),
                        "msg": rule.get("msg"),
                        "logdata": rule.get("logdata"),
                        "phase": rule.get("phase"),
                        "seq": s
                    }
                    rule_dao.persist(rule_doc)
                    s += 1
