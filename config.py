"""Global configuration variables and environment settings for NXGuard."""

import json
import os
import secrets

import pytz

APP_BASE = os.environ.get("APP_BASE", ".")
APP_CONTEXT = os.getenv("APP_CONTEXT", "/nxg")
try:
    APP_VERSION = json.load(open(os.path.join(APP_BASE, "package.json")))["version"]
except Exception:
    APP_VERSION = "develop"

API_HEADERS = {"User-Agent": f"NXGuard/{APP_VERSION}"}

BASE_PATH = "/opt/nxguard"
LUA_LIBS_PATH = f"{BASE_PATH}/luajit/share/lua/5.1"
DB_PATH = os.environ.get("BASE_PATH", "/data")

ENGINE_BASE = f"{BASE_PATH}/nginx"
ENGINE_VERSION = "1.27.1"

REPLICATE_MAX_RETRIES = 3
DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
TZ = pytz.timezone("UTC")

TELEMETRY_ENABLE = bool(os.environ.get("TELEMETRY_ENABLE", "false"))
TELEMETRY_INTERVAL = int(
    os.environ.get("TELEMETRY_INTERVAL", "60")
)  # in transaction merge (10 minutes)
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "https://nxguard.app.br")

MAINTENANCE_WINDOW = "01:00"
CERTIFICATE_RENEW = int(os.environ.get("CERTIFICATE_RENEW", "7"))

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()

# Security config
SECURITY_ENABLED = bool(os.environ.get("SECURITY_ENABLED", "true"))
KEY_SIZE = 2048
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_EXPIRE = 3600
JWT_AUD = "nxg"

# Cluster config
NXGUARD_ENDPOINT = os.environ.get("NXGUARD_ENDPOINT", "http://localhost:5000/nxg")
NXGUARD_API_KEY = os.environ.get("NXGUARD_API_KEY", secrets.token_urlsafe(32))
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

MASKED_HEADERS = [
    "Authorization",
    "X-Requested-With",
    "Account-ID",
    "Refresh-Token",
    "Cookie",
]
