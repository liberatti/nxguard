import os
import pytz

APP_CONTEXT = os.getenv('APP_CONTEXT',"/")
APP_VERSION = os.getenv('APP_VERSION',"v1.0.4")
APP_PUBLIC_URL = os.getenv('APP_PUBLIC_URL',f"http://localhost:4200{APP_CONTEXT}")
API_HEADERS = {"User-Agent": f"NXGuard/{APP_VERSION}"}

APP_BASE = "/opt/nxguard"
ENGINE_BASE = f"{APP_BASE}/nginx"
ENGINE_VERSION = "1.27.1"

DATETIME_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
TZ = pytz.timezone("UTC")

TELEMETRY_ENABLE = bool(os.environ.get('TELEMETRY_ENABLE','true'))
TELEMETRY_INTERVAL = int(os.environ.get("TELEMETRY_INTERVAL", "60")) # in transaction merge (10 minutes)
TELEMETRY_URL = os.environ.get("TELEMETRY_URL", "https://nxguard.app.br")

MAINTENANCE_WINDOW = "01:00"

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

# Config database (MongoDB)
MONGO_HOST = os.environ.get("MONGO_HOST",'127.0.0.1')
MONGO_PORT = os.environ.get("MONGO_PORT",27017)
MONGO_DB = os.environ.get("MONGO_DB",'nxguard')
MONGO_USER = os.environ.get("MONGO_USER","dev_usr")
MONGO_PASS = os.environ.get("MONGO_PASS","dev_psw")
MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# Security config
SECURITY_ENABLED = True
KEY_SIZE = 2048
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev")
JWT_EXPIRE = 3600
JWT_AUD = "nxguard"

# Cluster config
CLUSTER_ENDPOINT = os.environ.get("CLUSTER_ENDPOINT")
NXGUARD_ROLE = os.environ.get("NXGUARD_ROLE", "main")
NXGUARD_API_KEY = os.environ.get("NXGUARD_API_KEY", "DEV")

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
            "pragma"
        ],
        "expose_headers": [
            "Content-Type", 
            "Authorization",
            "X-Total-Count",
            "X-Page",
            "X-Size"
        ],
        "supports_credentials": True,
        "max_age": 3600
    }
}