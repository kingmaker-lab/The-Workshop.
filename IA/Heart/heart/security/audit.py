from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    timestamp: str
    intent: str
    tool: str
    arguments: dict[str, Any]
    result: str
    executed: bool


class AuditLog:
    def __init__(self, path: str | Path = "data/heart-audit.jsonl") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, *, intent: str, tool: str, arguments: dict[str, Any], result: str, executed: bool) -> AuditEntry:
        entry = AuditEntry(datetime.now(timezone.utc).isoformat(), intent, tool, arguments, result, executed)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(entry), ensure_ascii=True) + "\n")
        return entry
