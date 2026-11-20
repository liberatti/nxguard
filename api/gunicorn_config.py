"""Gunicorn configuration file managing process lifecycle hooks and background schedulers."""

try:
    import gevent.monkey

    gevent.monkey.patch_all()
except ImportError:
    pass

import os
import threading
import time
import traceback
import schedule
from api.middleware.logging_manager import logger, LoggingManager

import config as _config

import engine.admin as c_admin
import engine.build as c_builder
from api.repository.upstream_repository import UpstreamStatesDao
from api.tasks import (
    update_node_status,
    update_upstream_states,
    update_node_config,
    update_main_config,
    renew_certificates,
    install,
)

LoggingManager(loglevel=_config.LOGLEVEL)

stop_event = threading.Event()


def _scheduler():
    """Runs scheduled background jobs until stop_event is signaled."""
    while not stop_event.is_set():
        try:
            schedule.run_pending()
        except Exception as ex:
            traceback.print_exception(ex)
            logger.error(f"Error running scheduled task: {ex}")
        time.sleep(1)


def _ensure_storage_permissions():
    """Ensures database and log directories exist and are writable by nxguard."""
    import subprocess
    for path in [_config.DB_PATH, "/opt/nxguard/logs", "/opt/nxguard/data"]:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        if not os.access(path, os.W_OK):
            try:
                subprocess.run(["sudo", "chown", "-R", "nxguard:nxguard", path], check=False)
                subprocess.run(["sudo", "chmod", "-R", "777", path], check=False)
            except Exception as e:
                logger.warning(f"Could not adjust permissions on {path}: {e}")


def on_starting(server):
    """Gunicorn master process initialization hook."""
    _ensure_storage_permissions()


def post_fork(server, worker):
    """Gunicorn post-fork hook initializing instance roles, tasks, and background threads."""
    _ensure_storage_permissions()
    is_main = os.environ.get("NXGUARD_ROLE") == "main"
    logger.info("NXGuard instance is main: %s", is_main)
    if is_main:
        if not os.path.exists(f"{_config.DB_PATH}/app.duckdb"):
            install()
            init_path = (
                _config.DB_PATH
                if os.path.exists(f"{_config.DB_PATH}/init-data.json")
                else "engine"
            )
            c_builder.init_from_data(data_dir=init_path)
        conf = c_builder.get_config()
        val = c_admin.validate(conf)
        if val and val.get("status") == "ok":
            c_admin.apply(val["scn"])
        else:
            logger.error(f"Failed to apply config: {val['message']}")
        schedule.every(10).seconds.do(update_main_config)
        schedule.every(1).days.do(renew_certificates)
        with UpstreamStatesDao() as states_dao:
            states_dao.delete_all()
    else:
        update_node_config()
        schedule.every(60).seconds.do(update_node_config)
    schedule.every(30).seconds.do(update_node_status)
    schedule.every(30).seconds.do(update_upstream_states)
    threading.Thread(target=_scheduler, daemon=True).start()


def on_reload(server):
    """Gunicorn hook executed on server reload to stop background threads."""
    stop_event.set()


def on_exit(server):
    """Gunicorn hook executed on server shutdown."""
    stop_event.set()


workers = 1
worker_class = "gevent"
async_mode = "gevent"
preload_app = False
bind = "0.0.0.0:5000"
scheduler_started = False
accesslog = "-"
errorlog = "-"
loglevel = _config.LOGLEVEL
