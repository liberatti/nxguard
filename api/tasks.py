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
import engine.seclang.seclang_indexer as indexer


def update_node_config() -> None:
    cnf = c_builder.read_from_json("config.json")
    attempt = 0
    while attempt < config.REPLICATE_MAX_RETRIES:
        try:
            resp = requests.get(
                f"{config.NXGUARD_ENDPOINT}/api/config/health",
                headers=config.API_HEADERS,
            )
            if resp.status_code in [200, 201]:
                check = resp.json()
                if cnf and "scn" in cnf:
                    if "scn" not in check or not check["scn"] in cnf["scn"]:
                        resp = requests.get(
                            f"{config.NXGUARD_ENDPOINT}/api/config",
                            headers=config.API_HEADERS,
                        )
                        if resp.status_code in [200, 201]:
                            cnf = resp.json()
                            cst = c_admin.apply(cnf)
                            if "ok" in cst["status"]:
                                c_builder.export_config_json(cnf, "config.json")
                            break
            else:
                logger.error(
                    f"[{resp.status_code}] Config, check {config.NXGUARD_ENDPOINT}"
                )
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            attempt += 1
            time.sleep(30)


def update_node_status() -> None:
    k = f"node:{get_server_id()}"
    st = "ACTIVE" if c_admin.is_running() else "STOPPED"
    node = {
        "status": st,
        "scn": None,
        "last_check": datetime.datetime.now(config.TZ).isoformat(),
        "version": config.APP_VERSION,
        "net_recv": 0,
        "net_send": 0,
    }
    if os.path.exists(os.path.join(config.DB_PATH, "config.json")):
        active_cnf = c_builder.read_from_json("config.json")
        node.update({"scn": active_cnf["scn"]})

    config.cache_db.setex(k, 60, json.dumps(node))
    config.cache_db.sadd("idx:nodes", k)


def update_main_config():
    """Apply configuration in background thread to avoid blocking server startup"""
    if os.path.exists(os.path.join(config.DB_PATH, "config.json")):
        cnf = c_builder.read_from_json("config.json")
        logger.info(f"Loading last active config: {cnf['scn']}")
        c_admin.apply(cnf)
    return schedule.CancelJob


def install():
    logger.info(f"Installing NXGuard")
    os.makedirs(config.DB_PATH, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.sqlite"):
        os.remove(f"{config.DB_PATH}/app.sqlite")
    c_builder.create_db()
    indexer.index()
    if os.path.exists(f"{config.DB_PATH}/init-data.json"):
        c_builder.init_from_json("init-data.json")
    indexer.index()


def apply():
    conf = c_builder.create()
    conf = c_builder.validate(conf)
    c_admin.apply(conf)
