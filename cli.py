import os
import sys

from basic4web.middleware.logging import logger

import config as config
import engine.admin as c_admin
import engine.build as c_builder


def install():
    logger.info(f"Installing NXGuard")
    os.makedirs(config.APP_CONFIG_DIR, exist_ok=True)
    if os.path.exists(f"{config.DB_PATH}/app.sqlite"):
        os.remove(f"{config.DB_PATH}/app.sqlite")
    c_builder.create_db()
    if os.path.exists(f"{config.APP_CONFIG_DIR}/init-data.json"):
        c_builder.init_from_json("init-data.json")


def apply():
    conf = c_builder.create()
    conf = c_builder.validate(conf)
    c_admin.apply(conf)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "apply": apply,
        "install": install
    }

    fn = switch.get(sys.argv[1])
    fn()
