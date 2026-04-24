import json
import os

import pytz
import redis

APP_BASE = os.environ.get("APP_BASE", ".")
APP_CONTEXT = os.getenv("APP_CONTEXT", "/nxg")
APP_VERSION = json.load(open(os.path.join(APP_BASE, "package.json")))['version']
API_HEADERS = {"User-Agent": f"NXGuard/{APP_VERSION}"}

BASE_PATH = "/opt/nxguard"
DB_PATH = os.environ.get("BASE_PATH", "/data")

ENGINE_BASE = f"{BASE_PATH}/nginx"
ENGINE_VERSION = "1.27.1"

REPLICATE_MAX_RETRIES = 3
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
TZ = pytz.timezone("UTC")

TELEMETRY_ENABLE = bool(os.environ.get("TELEMETRY_ENABLE", "true"))
TELEMETRY_INTERVAL = int(
    os.environ.get("TELEMETRY_INTERVAL", "60")
)  # in transaction merge (10 minutes)
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "https://nxguard.app.br")

MAINTENANCE_WINDOW = "01:00"

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()

# Security config
SECURITY_ENABLED = True
KEY_SIZE = 2048
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev")
JWT_EXPIRE = 3600
JWT_AUD = "nxg"

# Cluster config
NXGUARD_ENDPOINT = os.environ.get("NXGUARD_ENDPOINT", "http://localhost:5000/nxg")
NXGUARD_API_KEY = os.environ.get("NXGUARD_API_KEY", "DEV")

REDIS_CACHE_HOST = os.environ.get("REDIS_CACHE_HOST", "127.0.0.1")
REDIS_CACHE_PORT = int(os.environ.get("REDIS_CACHE_PORT", 6379))
REDIS_CACHE_PASS = os.environ.get("REDIS_CACHE_PASS", None)

cache_db = redis.Redis(
    host=REDIS_CACHE_HOST,
    port=REDIS_CACHE_PORT,
    password=REDIS_CACHE_PASS,
    db=0,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)

CORS = {
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Account-ID",
            "Refresh-Token",
            "pragma",
        ],
        "expose_headers": [
            "Content-Type",
            "Authorization",
            "X-Total-Count",
            "X-Page",
            "X-Size",
        ],
        "supports_credentials": True,
        "max_age": 3600,
    }
}
