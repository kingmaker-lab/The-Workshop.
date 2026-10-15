from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any


def _read_meminfo() -> dict[str, int]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, raw = line.split(":", 1)
            values[key] = int(raw.strip().split()[0]) * 1024
    except (FileNotFoundError, OSError, ValueError):
        return values
    return values


def collect_system_snapshot() -> dict[str, Any]:
    cpu_count = os.cpu_count() or 1
    load_1m = os.getloadavg()[0]
    memory = _read_meminfo()
    total = memory.get("MemTotal", 0)
    available = memory.get("MemAvailable", memory.get("MemFree", 0))
    disk = shutil.disk_usage(Path.cwd())
    temperatures: list[float] = []
    for path in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            temperatures.append(int(path.read_text().strip()) / 1000)
        except (OSError, ValueError):
            continue

    return {
        "cpu_percent_estimate": round(min(load_1m / cpu_count * 100, 100), 1),
        "load_1m": round(load_1m, 2),
        "memory_percent": round((1 - available / total) * 100, 1) if total else None,
        "disk_percent": round(disk.used / disk.total * 100, 1),
        "temperature_c": round(max(temperatures), 1) if temperatures else None,
        "cpu_count": cpu_count,
    }
