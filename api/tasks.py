from datetime import datetime, timedelta
import os
import socket
import subprocess
import time
import traceback

import requests
from nxcore.common_utils import get_server_id, replace_tz
from nxcore.middleware.logging_manager import logger

import config
import engine.admin as c_admin
import engine.build as c_builder
import engine.seclang.seclang_indexer as seclang_indexer
from api.model.config_model import ConfigBackupDao, ConfigDao
from api.model.upstream_model import NodeStatusDao, UpstreamDao, UpstreamStatesDao
from api.model.certificate_model import CertificateDao
from api.model.service_model import ServiceDao
from api.tools.acme_tool import AcmeTool


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
                                            "created_at": datetime.now(),
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
        "last_check": datetime.now(config.TZ).isoformat(),
        "version": config.APP_VERSION,
        "net_recv": 0,
        "net_send": 0,
    }

    with NodeStatusDao() as node_dao:
        node_dao.register_node(k, node)


def update_upstream_states() -> None:
    """Performs health checks on backend upstream targets and records state for the local node."""
    node_id = get_server_id()
    now_iso = datetime.now(config.TZ).isoformat()

    with UpstreamDao() as upstream_dao, UpstreamStatesDao() as states_dao:
        upstreams_resp = upstream_dao.get_all()
        upstreams = (
            upstreams_resp.get("data", [])
            if isinstance(upstreams_resp, dict)
            else (upstreams_resp or [])
        )

        for u in upstreams:
            if not isinstance(u, dict):
                continue
            u_type = (u.get("type") or "backend").lower()
            if u_type != "backend":
                continue

            u_id = u.get("_id")
            if not u_id:
                continue

            targets = u.get("targets") or []
            targets_status = []
            conn_timeout = u.get("conn_timeout") or 2

            for t in targets:
                if not isinstance(t, dict):
                    continue
                host = t.get("host")
                port = t.get("port")
                if not host or not port:
                    continue

                endpoint = f"{host}:{port}"
                start_time = time.time()
                is_healthy = False
                error_msg = None

                try:
                    with socket.create_connection(
                        (host, int(port)), timeout=float(conn_timeout)
                    ):
                        is_healthy = True
                except Exception as e:
                    is_healthy = False
                    error_msg = str(e)

                latency_ms = round((time.time() - start_time) * 1000, 2)
                targets_status.append(
                    {
                        "host": host,
                        "port": port,
                        "endpoint": endpoint,
                        "healthy": is_healthy,
                        "latency_ms": latency_ms,
                        "error": error_msg,
                    }
                )

            total_targets = len(targets_status)
            healthy_targets = sum(1 for t in targets_status if t.get("healthy"))
            if total_targets == 0:
                node_healthy = "invalid"
            elif healthy_targets == total_targets:
                node_healthy = "healthy"
            elif healthy_targets == 0:
                node_healthy = "unhealthy"
            else:
                node_healthy = "partially_healthy"

            state_record = {
                "node_id": node_id,
                "upstream_id": int(u_id),
                "healthy": node_healthy,
                "last_check": now_iso,
                "targets": targets_status,
            }
            states_dao.register_state(node_id, int(u_id), state_record)


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
    try:
        subprocess.run(f"sudo chmod -R 777 {config.DB_PATH}", shell=True)
    except Exception:
        pass
    os.makedirs(config.DB_PATH, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.duckdb"):
        try:
            os.remove(f"{config.DB_PATH}/app.duckdb")
        except Exception:
            subprocess.run(f"sudo rm -f {config.DB_PATH}/app.duckdb", shell=True)
    c_builder.create_db()
    seclang_indexer.index()


def renew_certificates():
    with CertificateDao() as dao_c, ServiceDao() as dao_s:
        crt_c1 = 0
        crt_c2 = 0
        certificates = dao_c.get_all()["data"]
        for cert in certificates:
            if cert["provider"] in ["SELF", "MANAGED"]:
                renew_date = datetime.now() - timedelta(days=config.CERTIFICATE_RENEW)
                renew_date = replace_tz(renew_date)
                if cert["force_renew"] or replace_tz(cert["not_after"]) < renew_date:
                    try:
                        if "MANAGED" in cert["provider"]:
                            AcmeTool.renew_lets(cert)
                            crt_c2 += 1
                        if "SELF" in cert["provider"]:
                            AcmeTool.renew_self(cert)
                            crt_c1 += 1
                    except Exception as e:
                        stack_trace = traceback.format_exc()
                        logger.error(f"{e}, {stack_trace}")

    AcmeTool.clean_expired_challenges()
    if crt_c1 > 0 or crt_c2 > 0:
        logger.info(
            f"{crt_c1} SELF certificates renewed, {crt_c2} MANAGED certificates renewed"
        )
        update_main_config()
