import datetime
import json
import time
import traceback

import requests

import config
import engine.admin as c_admin
import engine.build as c_builder
from api.repository.redis_cache import RedisCache
from basic4web.common_utils import get_server_id
from basic4web.middleware.logging import logger


def update_node_config() -> None:
    cnf = c_builder.read_from_json('active.json')
    attempt = 0
    while attempt < config.REPLICATE_MAX_RETRIES:
        try:
            resp = requests.get(
                f"{config.CLUSTER_ENDPOINT}/api/config/health", headers=config.API_HEADERS
            )
            if resp.status_code in [200, 201]:
                check = resp.json()
                if not cnf or not check["scn"] in cnf["scn"]:
                    resp = requests.get(
                        f"{config.CLUSTER_ENDPOINT}/api/config",
                        headers=config.API_HEADERS,
                    )
                    if resp.status_code in [200, 201]:
                        cnf = resp.json()
                        cst = c_admin.apply(cnf)
                        if "ok" in cst['status']:
                            c_builder.export_config_json(cnf, 'active.json')
                        break
            else:
                logger.error(f"[{resp.status_code}] Config, check {config.CLUSTER_ENDPOINT}")
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            attempt += 1
            time.sleep(30)


def update_node_status() -> None:
    if config.NXGUARD_ROLE == "main":
        with RedisCache() as cache:
            st = "ACTIVE" if c_admin.is_running() else "STOPPED"
            cnf = c_builder.read_from_json("active.json")
            node = {
                "_id": get_server_id(),
                "status": st,
                "scn": cnf['scn'],
                "role": config.NXGUARD_ROLE,
                "last_check": datetime.datetime.now(config.TZ).isoformat(),
                "version": config.APP_VERSION,
                "net_recv": 0,
                "net_send": 0
            }
            cache.persist(f"node_{get_server_id()}", json.dumps(node), expire=120)
