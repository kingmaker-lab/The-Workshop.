from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..actions import RiskLevel
from .registry import Tool


DEFAULT_SCRIPTS: dict[str, tuple[str, ...]] = {
    "sentinel": ("python3", "sentinel/main.py"),
    "healthcheck": ("python3", "-m", "heart", "--once"),
}


def create_run_script_tool(allowed_scripts: dict[str, tuple[str, ...]] | None = None, *, timeout_seconds: float = 30) -> Tool:
    scripts = dict(allowed_scripts or DEFAULT_SCRIPTS)

    def run_script(arguments: dict[str, Any]) -> dict[str, Any]:
        name = arguments["name"]
        command = scripts[name]
        completed = subprocess.run(command, cwd=Path.cwd(), capture_output=True, text=True, timeout=timeout_seconds, check=False)
        return {"name": name, "return_code": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]}

    return Tool("run_script", "Executa um script previamente permitido", RiskLevel.KNOWN_SCRIPT, run_script, frozenset({"name"}), frozenset({"name"}))
