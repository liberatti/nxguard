import fcntl
import os

from basic4web.middleware.logging import logger

LOCK_FILE = "/tmp/gunicorn_scheduler.lock"

# Gunicorn configuration
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120  # Increase timeout to 120 seconds
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True


def acquire_lock():
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.write(fd, str(os.getpid()).encode())
        return True
    except BlockingIOError:
        return False


def on_starting(server):
    """Start server and apply config in background"""
    logger.info("Gunicorn starting - master PID %s", os.getpid())


def when_ready(server):
    logger.info("Gunicorn when_ready - master PID %s", server.pid)
