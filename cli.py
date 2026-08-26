"""CLI entrypoint for managing NXGuard installation, configuration apply, and SecLanguage indexing."""

import sys

import engine.seclang.seclang_indexer as indexer
from api.tasks import install, update_main_config


def health_check():
    try:
        with urlopen("http://localhost:5000", timeout=5) as response:
            if response.getcode() != 200:
                print("Health check failed")
            else:
                print("Health check passed")
    except Exception as e:
        print(f"Health check failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "apply": update_main_config,
        "install": install,
        "index": indexer.index,
        "healthcheck": health_check,
    }

    fn = switch.get(sys.argv[1])
    fn()
