from __future__ import annotations

from .applications import create_start_process_tool
from .notifications import create_notification_tool
from .registry import ToolRegistry
from .scripts import create_run_script_tool
from .system import create_system_status_tool


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(create_system_status_tool())
    registry.register(create_run_script_tool())
    registry.register(create_start_process_tool())
    registry.register(create_notification_tool())
    return registry
