import os
import sys

import config as config
import engine.build as c_builder

APP_CONFIG_DIR = os.path.join(config.APP_BASE, "admin/config")

def render_config():
    c_builder.run()
    #c_render.parse()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
       "render": render_config
    }

    fn = switch.get(sys.argv[1])
    fn()
