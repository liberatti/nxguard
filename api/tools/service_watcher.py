import queue
import threading
from typing import Any, List
from nxcore.middleware.logging_manager import logger
from api.tools.log_tool import LogParserTool
from config import BASE_PATH


class LogCache:
    """Thread-safe bounded FIFO buffer for log processing between tailers and correlation workers."""

    def __init__(self, maxsize: int = 50000):
        self.access_log: queue.Queue = queue.Queue(maxsize=maxsize)
        self.audit_log: queue.Queue = queue.Queue(maxsize=maxsize)
        self.error_log: queue.Queue = queue.Queue(maxsize=maxsize)
        self.lock = threading.Lock()

    def push_many(self, log_type: str, records: List[Any]) -> None:
        """Pushes multiple records into the respective queue without blocking."""
        if log_type == "ACCESS":
            target = self.access_log
        elif log_type == "AUDIT":
            target = self.audit_log
        elif log_type == "ERROR":
            target = self.error_log
        else:
            return

        for record in records:
            try:
                target.put_nowait(record)
            except queue.Full:
                # Discard oldest item if queue is full to prevent OOM
                try:
                    target.get_nowait()
                    target.put_nowait(record)
                except Exception:
                    pass

    def drain(self, log_type: str, max_items: int = 2000) -> List[Any]:
        """Drains up to max_items from the respective queue in a thread-safe manner."""
        if log_type == "ACCESS":
            target = self.access_log
        elif log_type == "AUDIT":
            target = self.audit_log
        elif log_type == "ERROR":
            target = self.error_log
        else:
            return []

        items = []
        while not target.empty() and len(items) < max_items:
            try:
                items.append(target.get_nowait())
            except queue.Empty:
                break
        return items

    def drain_all(self, log_type: str) -> List[Any]:
        """Drains all remaining items from the respective queue until empty."""
        return self.drain(log_type, max_items=1000000)


class ServiceWatcher:
    def __init__(self, service):
        self.service = service
        self.w_threads = []
        self.cache = LogCache()

    def stop(self):
        if not self.w_threads:
            return
        service_name = self.service.get("render_name") or (
            f"{self.service.get('name')}_{self.service.get('_id')}"
            if self.service.get("_id")
            else self.service.get("name")
        )
        logger.info(f"[stop watcher] {service_name}")
        for t in self.w_threads:
            setattr(t, "active", False)

        for t in self.w_threads:
            if t.is_alive():
                t.join(timeout=1.0)
        self.w_threads = []

    def start(self):
        service_name = self.service.get("render_name") or (
            f"{self.service.get('name')}_{self.service.get('_id')}"
            if self.service.get("_id")
            else self.service.get("name")
        )
        logger.info(f"[start watcher] {service_name}")
        self.stop()
        cache = self.cache

        access_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/access-{service_name}.log",
                "ACCESS",
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(access_log)

        error_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/error-{service_name}.log",
                "ERROR",
                cache,
            ),
            daemon=True,
        )
        self.w_threads.append(error_log)

        audit_log = threading.Thread(
            target=LogParserTool.follow_file,
            args=(
                f"{BASE_PATH}/logs/audit-{service_name}.log",
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
