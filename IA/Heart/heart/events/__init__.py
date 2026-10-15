from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass(frozen=True)
class Event:
    kind: str
    payload: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, kind: str, handler: Callable[[Event], None]) -> None:
        self._handlers[kind].append(handler)

    def publish(self, event: Event) -> None:
        for handler in (*self._handlers.get(event.kind, []), *self._handlers.get("*", [])):
            handler(event)
