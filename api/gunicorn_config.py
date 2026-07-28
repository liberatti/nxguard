"""Gunicorn configuration file managing process lifecycle hooks and background schedulers."""

try:
    import gevent.monkey

    gevent.monkey.patch_all()
except ImportError:
    pass

import fcntl
import os
import threading
import time
import traceback

import schedule
from nxcore.middleware.logging_manager import logger

import config as _config
import engine.admin as c_admin
import engine.build as c_builder
from api.tasks import (
    update_node_status,
    update_node_config,
    update_main_config,
    install,
)

stop_event = threading.Event()

lock_handle = open(os.path.join(_config.DB_PATH, "nxguard.lock"), "a+")

try:
    fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    logger.info("Lock acquired, NXGuard is the main instance")
    is_main = True
except BlockingIOError:
    is_main = False


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
    nxg_role = "worker"
    if is_main:
        logger.info("Lock acquired, NXGuard is the main instance")
        if not os.path.exists(f"{_config.DB_PATH}/app.duckdb"):
            install()
            if os.path.exists(f"{_config.DB_PATH}/init-data.json"):
                conf = c_builder.read_from_json("init-data.json")
                c_builder.init_from_data(conf)
        schedule.every(10).seconds.do(update_main_config)
        nxg_role = "main"
    else:
        schedule.every(60).seconds.do(update_node_config)
    c_admin.apply(c_builder.get_config())
    schedule.every(30).seconds.do(update_node_status)
    threading.Thread(target=_scheduler, daemon=True).start()
    logger.info(f"NXGuard started as {nxg_role}")


def on_reload(server):
    """Gunicorn hook executed on server reload to stop background threads."""
    global scheduler_started
    stop_event.set()
    scheduler_started = False


def on_exit(server):
    """Gunicorn hook executed on server shutdown."""
    stop_event.set()
    logger.info("NXGuard stopped")


workers = 1
worker_class = "gevent"
async_mode = "gevent"
preload_app = False
bind = "0.0.0.0:5000"
scheduler_started = False
accesslog = "-"
errorlog = "-"
loglevel = _config.LOGLEVEL
