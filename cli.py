"""CLI entrypoint for managing NXGuard installation, configuration apply, and SecLanguage indexing."""

import sys
import requests

import engine.seclang.seclang_indexer as indexer
from api.tasks import install, update_main_config


def health_check():
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        if response.status_code == 200:
            sys.exit(0)
        else:
            print(f"Health check failed with status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "apply": update_main_config,
        "install": install,
        "index": indexer.index,
        "healthcheck": health_check,
        "health_check": health_check,
    }

    fn = switch.get(sys.argv[1])
    if fn:
        fn()
    else:
        print(f"Comando desconhecido: {sys.argv[1]}")
        sys.exit(1)
