from __future__ import annotations

from typing import Any

from .state import SystemState
from ..events import Event, EventBus
from ..events.rules import CooldownRule
from ..memory import EventStore
from ..perception import collect_system_snapshot
from ..tools import ToolRequest, ToolResult, ToolRouter, create_default_registry


class Heart:
    def __init__(self, store: EventStore | None = None, *, event_cooldown_seconds: float = 300, tool_router: ToolRouter | None = None) -> None:
        self.events = EventBus()
        self.store = store or EventStore()
        self.events.subscribe("*", self.store.append)
        self._cooldown = CooldownRule(event_cooldown_seconds)
        self.tool_router = tool_router or ToolRouter(create_default_registry())
        self.last_snapshot: dict[str, Any] | None = None
        self.state = SystemState()

    def dispatch_tool(self, request: ToolRequest | dict[str, Any], *, confirmed: bool = False, root: bool = False) -> ToolResult:
        return self.tool_router.dispatch(request, confirmed=confirmed, root=root)

    def emit(self, event: Event) -> bool:
        if not self._cooldown.allow(event):
            return False
        self.events.publish(event)
        return True

    def observe(self) -> dict[str, Any]:
        snapshot = collect_system_snapshot()
        self.last_snapshot = snapshot
        self.state = SystemState.from_snapshot(snapshot)
        self.emit(Event("system.snapshot", snapshot))
        self._emit_alerts(snapshot)
        return snapshot

    def _emit_alerts(self, snapshot: dict[str, Any]) -> None:
        cpu = snapshot["cpu_percent_estimate"]
        memory = snapshot["memory_percent"]
        temperature = snapshot["temperature_c"]
        if cpu >= 90:
            self.emit(Event("system.cpu_high", {"cpu_percent": cpu}))
        if memory is not None and memory >= 90:
            self.emit(Event("system.memory_high", {"memory_percent": memory}))
        if temperature is not None and temperature >= 80:
            self.emit(Event("system.temperature_high", {"temperature_c": temperature}))

    def status(self) -> str:
        snapshot = self.last_snapshot or self.observe()
        temperature = snapshot["temperature_c"]
        temp_text = f", temperatura em {temperature:.0f} C" if temperature is not None else ""
        return (
            f"CPU em {snapshot['cpu_percent_estimate']:.1f}%, "
            f"memoria em {snapshot['memory_percent'] or 0:.1f}%, "
            f"disco em {snapshot['disk_percent']:.1f}%{temp_text}."
        )
