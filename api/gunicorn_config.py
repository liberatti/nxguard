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
from nxcore.middleware.logging_manager import logger, LoggingManager

import config as _config

import engine.admin as c_admin
import engine.build as c_builder
from api.tasks import (
    update_node_status,
    update_node_config,
    update_main_config,
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


def post_fork(server, worker):
    """Gunicorn post-fork hook initializing instance roles, tasks, and background threads."""
    is_main = os.environ.get("NXGUARD_ROLE") == "main"
    logger.info("NXGuard instance is main: %s", is_main)
    if is_main:
        if not os.path.exists(f"{_config.DB_PATH}/app.duckdb"):
            install()
            if os.path.exists(f"{_config.DB_PATH}/init-data.json"):
                c_builder.init_from_data()
        conf = c_builder.get_config()
        val = c_admin.validate(conf)
        if val and val.get("status") == "ok":
            c_admin.apply(val["scn"])
        else:
            logger.error(f"Failed to apply config: {val['message']}")
        schedule.every(10).seconds.do(update_main_config)
    else:
        update_node_config()
        schedule.every(60).seconds.do(update_node_config)
    schedule.every(30).seconds.do(update_node_status)
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
