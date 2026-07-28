import datetime
import os
import time
import traceback

import requests
import schedule
from nxcore.common_utils import get_server_id
from nxcore.middleware.logging_manager import logger

import config
import engine.admin as c_admin
import engine.build as c_builder
import engine.seclang.seclang_indexer as seclang_indexer
from api.model.upstream_model import NodeStatusDao


def update_node_config() -> None:
    """Fetches configuration from the main NXGuard endpoint and updates local node if SCN changes."""
    if not c_admin.ACTIVE_SCN and os.path.exists(
        os.path.join(config.DB_PATH, "config.json")
    ):
        cnf = c_builder.read_from_json("config.json")
        if cnf and "scn" in cnf:
            c_admin.ACTIVE_SCN = cnf["scn"]

    attempt = 0
    while attempt < config.REPLICATE_MAX_RETRIES:
        try:
            resp = requests.get(
                f"{config.NXGUARD_ENDPOINT}/api/config",
                headers=config.API_HEADERS,
            )
            if resp.status_code in [200, 201]:
                remote_cnf = resp.json()
                if remote_cnf and "scn" in remote_cnf:
                    if c_admin.ACTIVE_SCN != remote_cnf["scn"]:
                        logger.info(
                            f"New config SCN detected ({remote_cnf['scn']}). Applying to node..."
                        )
                        cst = c_admin.apply(remote_cnf)
                        if cst and cst.get("status") == "ok":
                            c_builder.export_config_json(remote_cnf, "config.json")
                            c_admin.ACTIVE_SCN = remote_cnf["scn"]
                break
            else:
                logger.error(
                    f"[{resp.status_code}] Config check failed for {config.NXGUARD_ENDPOINT}"
                )
        except requests.RequestException as e:
            logger.error("Request failed: %s", e)
            stack_trace = traceback.format_exc()
            logger.error(stack_trace)
            attempt += 1
            time.sleep(30)


def update_node_status() -> None:
    """Registers the node's current status, active SCN, and timestamp in the database."""
    k = f"node:{get_server_id()}"
    st = "ACTIVE" if c_admin.is_running() else "STOPPED"
    node = {
        "status": st,
        "scn": c_admin.ACTIVE_SCN,
        "last_check": datetime.datetime.now(config.TZ).isoformat(),
        "version": config.APP_VERSION,
        "net_recv": 0,
        "net_send": 0,
    }

    with NodeStatusDao() as node_dao:
        node_dao.register_node(k, node)


def update_main_config():
    """Applies configuration in background thread when pending changes exist."""
    config_file_exists = os.path.exists(os.path.join(config.DB_PATH, "config.json"))
    if c_admin.PENDING_CONFIG_UPDATE or not config_file_exists:
        logger.info("Pending configuration update detected. Rebuilding config...")
        conf = c_builder.get_config()
        cst = c_admin.apply(conf)
        if cst and cst.get("status") == "ok":
            c_admin.PENDING_CONFIG_UPDATE = False
            logger.info(f"Main config applied successfully: {c_admin.ACTIVE_SCN}")


def install():
    """Initializes NXGuard database schema and indexes SecLanguage rules."""
    logger.info("Installing NXGuard")
    os.makedirs(config.DB_PATH, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.duckdb"):
        os.remove(f"{config.DB_PATH}/app.duckdb")
    c_builder.create_db()
    seclang_indexer.index()


def apply():
    """Creates, validates, and applies the initial default configuration."""
    conf = c_builder.create()
    conf = c_builder.validate(conf)
    c_admin.apply(conf)
