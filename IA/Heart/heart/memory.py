from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .events import Event


class EventStore:
    def __init__(self, path: str | Path = "data/heart.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS events ("
            "id INTEGER PRIMARY KEY, kind TEXT NOT NULL, timestamp TEXT NOT NULL, payload TEXT NOT NULL)"
        )
        self.connection.commit()

    def append(self, event: Event) -> None:
        self.connection.execute(
            "INSERT INTO events(kind, timestamp, payload) VALUES (?, ?, ?)",
            (event.kind, event.timestamp.isoformat(), json.dumps(event.payload, sort_keys=True)),
        )
        self.connection.commit()

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            "SELECT kind, timestamp, payload FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [{"kind": kind, "timestamp": timestamp, "payload": json.loads(payload)} for kind, timestamp, payload in rows]

    def close(self) -> None:
        self.connection.close()
