"""CLI inbound adapter. Wiring lives at the edge, never in the domain layer."""
import argparse
from dataclasses import asdict
import json
import sqlite3
from ..domain import DomainValidationError
from ..usecases import CreateReservation, CreateReservationCommand, GetReservation, ReservationNotFound
from .ids import UUID4Ids
from .memory import InMemoryReservations
from .sqlite import SQLiteReservations


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="CERBERUS_02 demo — local only")
    parser.add_argument("--backend", choices=("memory", "sqlite"), default="memory")
    parser.add_argument("--db", default="cerberus02.sqlite3", help="local SQLite file (sqlite backend)")
    sub = parser.add_subparsers(dest="action", required=True)
    create = sub.add_parser("create", help="create a reservation")
    create.add_argument("--event", required=True)
    create.add_argument("--guest", required=True)
    create.add_argument("--seats", type=int, required=True)
    lookup = sub.add_parser("get", help="fetch by id (use sqlite for multi-run persistence)")
    lookup.add_argument("--id", required=True)
    args = parser.parse_args(argv)
    repository = SQLiteReservations(args.db) if args.backend == "sqlite" else InMemoryReservations()
    try:
        if args.action == "create":
            result = CreateReservation(repository, UUID4Ids()).execute(
                CreateReservationCommand(args.event, args.guest, args.seats)
            )
        else:
            result = GetReservation(repository).execute(args.id)
        print(json.dumps(asdict(result), ensure_ascii=False))
        return 0
    except (DomainValidationError, ReservationNotFound) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    except sqlite3.Error:
        print(json.dumps({"error": "storage unavailable"}))
        return 1
    finally:
        if hasattr(repository, "close"):
            repository.close()


if __name__ == "__main__":
    raise SystemExit(main())
