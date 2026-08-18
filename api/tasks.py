import datetime
import os
import time
import traceback

import requests
from nxcore.common_utils import get_server_id
from nxcore.middleware.logging_manager import logger

import config
import engine.admin as c_admin
import engine.build as c_builder
import engine.seclang.seclang_indexer as seclang_indexer
from api.model.config_model import ConfigBackupDao, ConfigDao
from api.model.upstream_model import NodeStatusDao


def update_node_config() -> None:
    """Fetches configuration from the main NXGuard endpoint and updates local node if SCN changes."""
    with ConfigDao() as config_dao:
        local_scn = config_dao.get_active_scn()

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
                    if local_scn != remote_cnf["scn"]:
                        logger.info(
                            f"New config SCN detected ({remote_cnf['scn']}). Applying to node..."
                        )
                        val = c_admin.validate(remote_cnf)
                        if val and val.get("status") == "ok":
                            cst = c_admin.apply(remote_cnf)
                            if cst and cst.get("status") == "ok":
                                with ConfigBackupDao() as backup_dao:
                                    backup_dao.persist(
                                        {
                                            "scn": remote_cnf["scn"],
                                            "created_at": datetime.datetime.now(),
                                            "data": remote_cnf,
                                        }
                                    )
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
    with ConfigDao() as config_dao:
        scn = config_dao.get_active_scn()

    node = {
        "status": st,
        "scn": scn,
        "last_check": datetime.datetime.now(config.TZ).isoformat(),
        "version": config.APP_VERSION,
        "net_recv": 0,
        "net_send": 0,
    }

    with NodeStatusDao() as node_dao:
        node_dao.register_node(k, node)


def update_main_config():
    """Applies configuration in background thread when ConfigDao SCN differs from latest ConfigBackupDao SCN."""
    with ConfigDao() as config_dao, ConfigBackupDao() as backup_dao:
        active_scn = config_dao.get_active_scn()
        latest_backup = backup_dao.get_latest()
        backup_scn = latest_backup.get("scn") if latest_backup else None

    if not latest_backup or active_scn != backup_scn:
        logger.info("Configuration change detected. Rebuilding config...")
        conf = c_builder.get_config()
        val = c_admin.validate(conf)
        if val and val.get("status") == "ok":
            cst = c_admin.apply(val["scn"])
            if cst and cst.get("status") == "ok":
                logger.info(f"Main config applied successfully: {cst.get('scn')}")


def install():
    """Initializes NXGuard database schema and indexes SecLanguage rules."""
    logger.info("Installing NXGuard")
    os.makedirs(config.DB_PATH, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.duckdb"):
        os.remove(f"{config.DB_PATH}/app.duckdb")
    c_builder.create_db()
    seclang_indexer.index()
