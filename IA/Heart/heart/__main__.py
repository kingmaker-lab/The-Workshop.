from __future__ import annotations

import argparse
import json

from .core import Heart


def main() -> None:
    parser = argparse.ArgumentParser(description="Heart local runtime")
    parser.add_argument("--once", action="store_true", help="coleta uma observacao e termina")
    args = parser.parse_args()

    heart = Heart()
    try:
        snapshot = heart.observe()
        print(json.dumps(snapshot, indent=2, ensure_ascii=True))
        print(heart.status())
    finally:
        heart.store.close()


if __name__ == "__main__":
    main()
