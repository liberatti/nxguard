import os
import schedule
import threading
import time
import traceback

import config as _config
import engine.admin as c_admin
import engine.build as c_builder
from api.tools.tasks import update_node_status, update_node_config
from basic4web.middleware.logging import logger
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


def _apply_config_async():
    """Apply configuration in background thread to avoid blocking server startup"""
    try:
        if _config.NXGUARD_ROLE == "main":
            if not os.path.exists(f"{_config.DB_PATH}/app.sqlite"):
                install()
            if os.path.exists(os.path.join(_config.APP_CONFIG_DIR, "active.json")):
                cnf = c_builder.read_from_json("active.json")
                c_admin.apply(cnf)
            else:
                c_admin.apply()
        else:
            update_node_config()
    except Exception as ex:
        logger.error(f"Error applying config in background: {ex}")


def when_ready(server):
    global scheduler_started
    if not scheduler_started:
        scheduler_started = True
        schedule.every(30).seconds.do(update_node_status)
        schedule.every(60).seconds.do(update_node_config)
        threading.Thread(target=_scheduler, daemon=True).start()
        threading.Thread(target=_apply_config_async, daemon=True).start()
        print("[Master] Scheduler único iniciado após preload")


def on_reload(server):
    global scheduler_started
    stop_event.set()
    scheduler_started = False
    print("[Master] Reiniciando scheduler após reload")
    when_ready(server)


def on_exit(server):
    stop_event.set()
    print("[Master] Scheduler encerrado")


# post_fork hook removed - monkey patching is now done in main.py before Flask imports
# This ensures the patch is applied before any Flask/Werkzeug objects are created


worker_class = "eventlet"
workers = 4
preload_app = False  # Disabled to allow monkey_patch to run before Flask imports in workers only
bind = "0.0.0.0:5000"
scheduler_started = False
accesslog = "-"
errorlog = "-"
loglevel = "info"
