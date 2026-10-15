from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..actions import RiskLevel
from ..perception import collect_system_snapshot
from .registry import Tool


def system_status(_: dict[str, Any]) -> dict[str, Any]:
    snapshot = collect_system_snapshot()
    try:
        snapshot["uptime_seconds"] = float(Path("/proc/uptime").read_text().split()[0])
    except (FileNotFoundError, OSError, ValueError, IndexError):
        snapshot["uptime_seconds"] = None
    snapshot["process_count"] = sum(1 for entry in Path("/proc").iterdir() if entry.name.isdigit())
    snapshot["network_interfaces"] = _network_interfaces()
    return snapshot


def _network_interfaces() -> list[str]:
    try:
        lines = Path("/proc/net/dev").read_text().splitlines()[2:]
    except (FileNotFoundError, OSError):
        return []
    return [line.split(":", 1)[0].strip() for line in lines if ":" in line]


def create_system_status_tool() -> Tool:
    return Tool("system_status", "Retorna o estado atual da máquina", RiskLevel.INFORMATION, system_status)
