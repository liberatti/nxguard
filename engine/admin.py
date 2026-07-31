"""Engine administration module for testing, applying, reloading, and checking status of Nginx."""

import datetime
import os
import subprocess
import json
import psutil
from nxcore.common_utils import gen_random_string
from nxcore.middleware.logging_manager import logger

import engine.render as c_render
from api.model.config_model import ConfigBackupDao, ConfigDao
from config import BASE_PATH


def validate(conf):
    """Tests the new configuration."""
    c_render.generate(conf, test=True)
    try:
        result = subprocess.Popen(
            f"sudo {BASE_PATH}/nginx/sbin/nginx -c {BASE_PATH}/nginx/conf/tests/nginx.conf -t",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = result.communicate()
        if result.returncode != 0:
            msg = {"status": "error", "message": stderr.decode().split("\n")}
            logger.error(msg)
            return msg
    finally:
        pass
        # TODO enable test cleanup
        # c_render.clean(conf, test=True)

    with ConfigBackupDao() as backup_dao:
        scn = gen_random_string(16)
        backup_dao.persist(
            {
                "scn": scn,
                "created_at": datetime.datetime.now(),
                "data": conf,
            }
        )
    return {"status": "ok", "scn": scn}


def apply(scn):
    """Tests the new configuration, and if valid, cleans old files, generates new ones, and reloads Nginx."""
    with ConfigBackupDao() as backup_dao:
        backup = backup_dao.get_by_scn(scn)
        conf = json.loads(backup["data"]) if backup else None

    if not conf:
        logger.error(f"Configuration with SCN {scn} not found in ConfigBackupDao.")
        return {"status": "error", "message": f"SCN {scn} not found"}

    c_render.clean(conf, test=False)
    c_render.generate(conf)

    restart()
    if is_running():
        with ConfigDao() as config_dao:
            active_config = config_dao.get_active()
            if active_config:
                config_dao.update_by_id(active_config["_id"], {"active_scn": scn})

    return {"status": "ok", "scn": scn}


def is_running() -> bool:
    """Checks if the Nginx master process is running based on its PID file."""
    pid_file = f"{BASE_PATH}/run/nginx.pid"
    try:
        if os.path.exists(pid_file):
            with open(pid_file, "r") as file:
                content = file.read().strip()
                if not content.isdigit():
                    raise ValueError(f"PID inválido no arquivo: {content!r}")
                pid = int(content)
                if pid:
                    process = psutil.Process(pid)
                    is_r = process.is_running()
                    if not is_r:
                        os.remove(pid_file)
                    return is_r
    except Exception as e:
        logger.warn("Failed to check engine, %s", e)
    return False


def restart():
    """Reloads Nginx if running, or starts Nginx if stopped."""
    subprocess.run(f"sudo chmod -R 777 {BASE_PATH}/logs", shell=True)
    if is_running():
        logger.info("Nginx is running, reload required")
        result = subprocess.Popen(
            f"sudo {BASE_PATH}/nginx/sbin/nginx -s reload",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = result.communicate()
        if result.returncode == 0:
            return
        logger.warn("Nginx reload failed: %s", stderr.decode().strip())

    logger.info("Nginx is not running, start required")
    result = subprocess.Popen(
        f"sudo {BASE_PATH}/nginx/sbin/nginx -c {BASE_PATH}/nginx/conf/enabled/nginx.conf",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = result.communicate()
    if result.returncode != 0:
        logger.error("Failed to start Nginx: %s", stderr.decode().strip())
