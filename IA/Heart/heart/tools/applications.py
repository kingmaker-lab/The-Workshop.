from __future__ import annotations

import subprocess
from typing import Any

from ..actions import RiskLevel
from .registry import Tool


DEFAULT_PROCESSES: dict[str, tuple[str, ...]] = {
    "heart-worker": ("python3", "-m", "heart", "--once"),
}


def create_start_process_tool(allowed_processes: dict[str, tuple[str, ...]] | None = None) -> Tool:
    processes = dict(allowed_processes or DEFAULT_PROCESSES)

    def start_process(arguments: dict[str, Any]) -> dict[str, Any]:
        name = arguments["name"]
        process = subprocess.Popen(processes[name], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"name": name, "pid": process.pid}

    return Tool("start_process", "Inicia um processo previamente permitido", RiskLevel.KNOWN_SCRIPT, start_process, frozenset({"name"}), frozenset({"name"}))
