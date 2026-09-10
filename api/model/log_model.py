import queue
import threading
from typing import Any, List


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
