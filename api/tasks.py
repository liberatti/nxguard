import datetime
import json
import os
import time
import traceback

import requests
import schedule
from basic4web.common_utils import get_server_id
from basic4web.middleware.logging import logger

import config
import engine.admin as c_admin
import engine.build as c_builder
from api.repository.redis_cache import RedisCache


def update_node_config() -> None:
    cnf = c_builder.read_from_json("active.json")
    attempt = 0
    while attempt < config.REPLICATE_MAX_RETRIES:
        try:
            resp = requests.get(
                f"{config.NXGUARD_ADMIN_ENDPOINT}/api/config/health",
                headers=config.API_HEADERS,
            )
            if resp.status_code in [200, 201]:
                check = resp.json()
                if cnf and "scn" in cnf:
                    if "scn" not in check or not check["scn"] in cnf["scn"]:
                        resp = requests.get(
                            f"{config.NXGUARD_ADMIN_ENDPOINT}/api/config",
                            headers=config.API_HEADERS,
                        )
                        if resp.status_code in [200, 201]:
                            cnf = resp.json()
                            cst = c_admin.apply(cnf)
                            if "ok" in cst["status"]:
                                c_builder.export_config_json(cnf, "active.json")
                            break
            else:
                logger.error(
                    f"[{resp.status_code}] Config, check {config.NXGUARD_ADMIN_ENDPOINT}"
                )
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            attempt += 1
            time.sleep(30)


def update_node_status() -> None:
    with RedisCache() as cache:
        st = "ACTIVE" if c_admin.is_running() else "STOPPED"
        node = {
            "_id": get_server_id(),
            "status": st,
            "scn": None,
            "last_check": datetime.datetime.now(config.TZ).isoformat(),
            "version": config.APP_VERSION,
            "net_recv": 0,
            "net_send": 0,
        }
        if os.path.exists(os.path.join(config.APP_CONFIG_DIR, 'active.json')):
            cnf = c_builder.read_from_json("active.json")
            node.update({"scn": cnf["scn"]})
        cache.persist(f"node_{get_server_id()}", json.dumps(node), expire=120)


def update_main_config():
    """Apply configuration in background thread to avoid blocking server startup"""
    if os.path.exists(os.path.join(config.APP_CONFIG_DIR, "active.json")):
        cnf = c_builder.read_from_json("active.json")
        logger.info(f"Loading last active config: {cnf['scn']}")
        c_admin.apply(cnf)
    return schedule.CancelJob
