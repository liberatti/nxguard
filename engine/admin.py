"""Engine administration module for testing, applying, reloading, and checking status of Nginx."""

import datetime
import json
import os
import subprocess
import time
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
    """Checks if the Nginx master process is running based on its PID file and process table."""
    pid_file = f"{BASE_PATH}/run/nginx.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as file:
                content = file.read().strip()
                if content.isdigit():
                    pid = int(content)
                    if pid and psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        if process.is_running() and "nginx" in process.name().lower():
                            return True
            try:
                os.remove(pid_file)
            except OSError:
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            try:
                os.remove(pid_file)
            except OSError:
                pass
        except Exception as e:
            logger.warn("Failed to check engine PID file, %s", e)

    try:
        for proc in psutil.process_iter(["name"]):
            try:
                name = proc.info.get("name") or ""
                if "nginx" in name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.warn("Failed to check running processes for engine, %s", e)

    return False


def restart():
    """Reloads Nginx if running, or starts Nginx if stopped."""
    subprocess.run(f"sudo chmod -R 777 {BASE_PATH}/logs", shell=True)
    if is_running():
        logger.info("Nginx is running, reload required")
        result = subprocess.Popen(
            f"sudo {BASE_PATH}/nginx/sbin/nginx -c {BASE_PATH}/nginx/conf/enabled/nginx.conf -s reload",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = result.communicate()
        if result.returncode == 0:
            return
        logger.warn("Nginx reload failed: %s. Attempting clean restart...", stderr.decode().strip())
        subprocess.run("sudo pkill -9 nginx", shell=True)
        time.sleep(0.5)

    logger.info("Nginx is not running, start required")
    result = subprocess.Popen(
        f"sudo {BASE_PATH}/nginx/sbin/nginx -c {BASE_PATH}/nginx/conf/enabled/nginx.conf",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = result.communicate()
    if result.returncode != 0:
        err_msg = stderr.decode().strip()
        logger.error("Failed to start Nginx: %s", err_msg)
        if "Address already in use" in err_msg:
            logger.info("Address already in use. Killing rogue nginx processes and retrying...")
            subprocess.run("sudo pkill -9 nginx", shell=True)
            time.sleep(0.5)
            retry = subprocess.Popen(
                f"sudo {BASE_PATH}/nginx/sbin/nginx -c {BASE_PATH}/nginx/conf/enabled/nginx.conf",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, retry_err = retry.communicate()
            if retry.returncode != 0:
                logger.error("Retry start Nginx failed: %s", retry_err.decode().strip())

