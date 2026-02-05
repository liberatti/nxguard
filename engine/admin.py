import os
import subprocess

import psutil
from basic4web.common_utils import gen_random_string
from basic4web.middleware.logging import logger

import engine.build as c_builder
import engine.render as c_render
from config import (
    APP_BASE
)


def apply(conf):
    # logger.info(conf)
    c_render.generate(conf, test=True)
    result = subprocess.Popen(
        f"sudo {APP_BASE}/nginx/sbin/nginx -c {APP_BASE}/nginx/conf/test-nginx.conf -t",
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = result.communicate()

    if result.returncode == 0:
        c_render.clean(conf, test=True)
        logger.info(f"Config OK")

        c_render.clean(conf, test=False)
        c_render.generate(conf)

        restart()
        if is_running():
            conf.update({"scn": gen_random_string()})
            c_builder.export_config_json(conf, "active.json")
        return {"status": "ok", "scn": conf['scn']}
    msg = {"status": "error", "message": stderr.decode().split('\n')}
    logger.error(msg)
    return msg


def is_running() -> bool:
    pid_file = f"{APP_BASE}/run/nginx.pid"
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
    # subprocess.run(f"sudo chmod -R 777 {APP_BASE}/logs", shell=True)
