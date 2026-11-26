"""Interface de operação local."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import stat
import sys

from . import core, service


def read_key(path):
    with path.open("rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise core.Rejected("a chave exige arquivo regular privado do operador")
        key = stream.read(33)
    if len(key) != 32:
        raise core.Rejected("a chave precisa ter 32 bytes")
    return key


def main():
    parser = argparse.ArgumentParser(prog="python3 -m cerberus")
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--db", type=Path, default=Path("cerberus.sqlite"))
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("keygen", "init", "status"):
        commands.add_parser(command)
    serve = commands.add_parser("serve")
    serve.add_argument("--port", type=int, default=8765, choices=range(65536), metavar="0-65535")
    seal = commands.add_parser("seal")
    seal.add_argument("--expected", type=int, required=True)
    seal.add_argument("policy", type=Path)
    apply = commands.add_parser("apply")
    apply.add_argument("envelope", type=Path)
    restore = commands.add_parser("restore")
    restore.add_argument("--expected", type=int, required=True)
    restore.add_argument("generation", type=int)
    args = parser.parse_args()

    os.umask(0o077)
    try:
        if args.command == "keygen":
            fd = os.open(args.key, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as stream:
                stream.write(os.urandom(32))
            result = {"created": True}
        else:
            key = read_key(args.key)
            if args.command == "serve":
                with service.PolicyService(args.port, args.db, key) as server:
                    host, port = server.server_address
                    print(json.dumps({"host": host, "port": port}), flush=True)
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        pass
                return 0
            if args.command == "init":
                result = core.initialize(args.db, key)
            elif args.command == "status":
                result = core.status(args.db, key)
            elif args.command == "restore":
                result = core.restore(args.db, key, args.generation, args.expected)
            elif args.command == "seal":
                with args.policy.open("rb") as stream:
                    result = core.seal(key, args.expected, core.read_json(stream))
            else:
                with args.envelope.open("rb") as stream:
                    result = core.apply(args.db, key, core.read_json(stream))
        print(json.dumps(result, sort_keys=True))
    except (ValueError, OSError, sqlite3.Error, RecursionError) as exc:
        print(f"CERBERUS recusou a operação ({exc})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
