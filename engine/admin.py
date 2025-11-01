import os
import subprocess

import psutil

from basic4web.middleware.logging import logger
from config import (
    APP_BASE
)


def test_config():
    # -p {APP_BASE}/test/nginx
    result = subprocess.Popen(
        f"sudo {APP_BASE}/nginx/sbin/nginx -c {APP_BASE}/test/nginx/conf/nginx.conf -t",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = result.communicate()
    if result.returncode != 0:
        logger.error(f"Nginx config test failed, {stderr.decode()}")
        return {
            "status": "error",
            "message": stderr.decode().split('\n')
        }
    return {
        "status": "ok"
    }


def is_running():
    pid_file = f"{APP_BASE}/run/nginx.pid"
    try:
        if os.path.exists(pid_file):
            with open(pid_file, "r") as file:
                pid = int("".join(file.readlines()))
                if pid:
                    process = psutil.Process(pid)
                    is_running = process.is_running()
                    if not is_running:
                        os.remove(pid_file)
                    return is_running
    except Exception as e:
        logger.error("Failed to check engine, %s", e)
    return False


def restart():
    subprocess.run(f"sudo chmod -R 777 {APP_BASE}/logs", shell=True)
    if is_running():
        logger.info(f"Nginx is running, reload required")
        result = subprocess.Popen(
            f"sudo {APP_BASE}/nginx/sbin/nginx -s reload",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not is_running():
            logger.info(f"Nginx reload failed, start required")
            result = subprocess.Popen(
                f"sudo {APP_BASE}/nginx/sbin/nginx",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    else:
        logger.info(f"Nginx is not running, start required")
        result = subprocess.Popen(
            f"sudo {APP_BASE}/nginx/sbin/nginx",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    stdout, stderr = result.communicate()
    subprocess.run(f"sudo chmod -R 777 {APP_BASE}/logs", shell=True)
