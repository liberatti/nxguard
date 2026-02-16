import sys

import engine.seclang.seclang_indexer as indexer
from api.tasks import install, apply

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python cli.py <update> [options]")
        sys.exit(1)

    switch = {
        "apply": apply,
        "install": install,
        "index": indexer.index
    }

    fn = switch.get(sys.argv[1])
    fn()
