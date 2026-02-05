import fcntl
import os
import threading
import time
import traceback

import schedule
from basic4web.middleware.logging import logger

import config as _config
from api.tasks import update_node_status, update_node_config, update_main_config
from cli import install

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
    global scheduler_started
    if not scheduler_started:
        scheduler_started = True
        lock_file = os.path.join(_config.DB_PATH, "db.lock")
        with open(lock_file, "a+") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if not os.path.exists(f"{_config.DB_PATH}/app.sqlite"):
                    install()
                schedule.every(10).seconds.do(update_main_config)
                # threading.Thread(target=update_main_config, daemon=True).start()
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
preload_app = False
bind = "0.0.0.0:5000"
scheduler_started = False
accesslog = "-"
errorlog = "-"
loglevel = _config.LOGLEVEL
