import threading
from nxcore.middleware.logging_manager import logger
from api.tools.log_tool import LogParserTool
from config import BASE_PATH


class LogCache:
    def __init__(self):
        self.access_log = []
        self.audit_log = []
        self.error_log = []
        self.lock = threading.Lock()


class ServiceWatcher:
    def __init__(self, service):
        self.service = service
        self.w_threads = []
        self.cache = LogCache()

    def stop(self):
        service_name = self.service.get("name") or self.service.get("_id")
        logger.info(f"[stop watcher] {service_name}")
        for t in self.w_threads:
            setattr(t, "active", False)

        for t in self.w_threads:
            if t.is_alive():
                t.join(timeout=1.0)
        self.w_threads = []

    def start(self):
        service_name = self.service.get("name") or self.service.get("_id")
        logger.info(f"[start watcher] {service_name}")
        self.stop()
        cache = self.cache

        access_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/access.json",
                "ACCESS",
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(access_log)

        error_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/error.log",
                "ERROR",
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(error_log)

        audit_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/audit_log-{service_name}.log",
                "AUDIT",
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(audit_log)

        merge = threading.Thread(
            target=LogParserTool.merge_transactions,
            args=(
                service_name,
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(merge)

        for thread in self.w_threads:
            setattr(thread, "active", True)
            thread.start()
