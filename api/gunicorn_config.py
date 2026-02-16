import fcntl
import os
import threading
import time
import traceback

import schedule
from basic4web.middleware.logging import logger

import config as _config
import engine.admin as c_admin
import engine.build as c_builder
from api.tasks import update_node_status, update_node_config, update_main_config, install

stop_event = threading.Event()


def _scheduler():
    while not stop_event.is_set():
        try:
            schedule.run_pending()
        except Exception as ex:
            traceback.print_exception(ex)
            logger.error(f"Error running scheduled task: {ex}")
        time.sleep(1)


def when_ready(server):
    nxg_role = "worker"
    lock_file = os.path.join(_config.DB_PATH, "db.lock")
    with open(lock_file, "a+") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.info("Lock acquired, NXGuard is the main instance")
            if not os.path.exists(f"{_config.DB_PATH}/app.sqlite"):
                install()
                if os.path.exists(f"{_config.DB_PATH}/init-data.json"):
                    conf = c_builder.init_from_json(f"{_config.DB_PATH}/init-data.json")
                    c_admin.apply(conf)
            if os.path.exists(f"{_config.DB_PATH}/config.json"):
                conf = c_builder.read_from_json(f"config.json")
                c_admin.apply(conf)

            schedule.every(10).seconds.do(update_main_config)
            nxg_role = "main"
        except BlockingIOError:
            schedule.every(60).seconds.do(update_node_config)
            return
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    schedule.every(30).seconds.do(update_node_status)
    threading.Thread(target=_scheduler, daemon=True).start()
    logger.info(f"NXGuard started as {nxg_role}")


def on_reload(server):
    global scheduler_started
    stop_event.set()
    scheduler_started = False
    when_ready(server)


def on_exit(server):
    stop_event.set()
    logger.info(f"NXGuard stopped")


workers = 4
threads = 8
preload_app = False
bind = "0.0.0.0:5000"
scheduler_started = False
accesslog = "-"
errorlog = "-"
loglevel = _config.LOGLEVEL
