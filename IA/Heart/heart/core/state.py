from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SystemState:
    cpu: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    disk: dict[str, Any] = field(default_factory=dict)
    temperature: dict[str, Any] = field(default_factory=dict)
    network: dict[str, Any] = field(default_factory=dict)
    processes: dict[str, Any] = field(default_factory=dict)
    last_update: datetime | None = None

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> "SystemState":
        return cls(
            cpu={"usage": snapshot.get("cpu_percent_estimate"), "load": snapshot.get("load_1m")},
            memory={"usage": snapshot.get("memory_percent")},
            disk={"usage": snapshot.get("disk_percent")},
            temperature={"cpu": snapshot.get("temperature_c")},
            last_update=datetime.now(timezone.utc),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "temperature": self.temperature,
            "network": self.network,
            "processes": self.processes,
            "last_update": self.last_update.isoformat() if self.last_update else None,
        }
