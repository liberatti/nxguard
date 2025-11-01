import json
import os
import sys

import config as config
import engine.admin as c_admin
import engine.build as c_builder
import engine.render as c_render
from basic4web.middleware.logging import logger

APP_CONFIG_DIR = os.path.join(config.APP_BASE, "admin/config")


def apply(conf=None):
    if not conf:
        conf = c_builder.create()

    c_render.generate(c_builder.validate(conf))
    c_admin.restart()
    if c_admin.is_running():
        c_builder.export_config_json(conf, os.path.join(config.APP_BASE, "active.json"))


def test_config(config_file=os.path.join(APP_CONFIG_DIR, "init-data.json")):
    with open(config_file, "r") as f:
        data = json.load(f)
        conf = c_builder.validate(data)
        conf.update({
            "IS_TEST": True,
            "APP_BASE": config.APP_BASE
        })

        c_render.generate(conf, output_dir=os.path.join(config.APP_BASE, "test"))
        test_result = c_admin.test_config()
        logger.info(f"Test configuration. {test_result}")
        return "ok" in test_result['status']


def install():
    logger.info(f"Installing NXGuard")
    os.makedirs(APP_CONFIG_DIR, exist_ok=True)

    os.remove(f"/data/app.sqlite")
    c_builder.init_from_json(os.path.join(APP_CONFIG_DIR, "init-data.json"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "test": test_config,
        "apply": apply,
        "install": install
    }

    fn = switch.get(sys.argv[1])
    fn()
