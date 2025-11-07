import os
import sys

import config as config
import engine.admin as c_admin
from basic4web.middleware.logging import logger

APP_CONFIG_DIR = os.path.join(config.APP_BASE, "admin/config")


def install():
    logger.info(f"Installing NXGuard")
    os.makedirs(APP_CONFIG_DIR, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.sqlite"):
        os.remove(f"{config.DB_PATH}/app.sqlite")
    c_admin.install_from_json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "apply": c_admin.apply,
        "install": install
    }

    fn = switch.get(sys.argv[1])
    fn()
