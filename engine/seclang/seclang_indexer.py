import json

import config
from engine.seclang.seclang_parser import RuleSetParser


def index(config_file=f"{config.BASE_PATH}/admin/engine/seclang/crs-config.json",
          base_path=f"{config.BASE_PATH}/modsec/coreruleset"):
    with open(config_file, "r", encoding="utf-8") as arq:
        meta = json.load(arq)
        for c in meta['categories']:
            parser = RuleSetParser()
            rules = parser.load(c['file'], base_path)
            c.update({"rules": rules})
            # logger.info(c)
