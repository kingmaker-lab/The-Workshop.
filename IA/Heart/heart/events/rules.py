from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import Event


class CooldownRule:
    """Allows an event kind through only once during its cooldown window."""

    def __init__(self, cooldown_seconds: float = 300) -> None:
        self.cooldown = timedelta(seconds=cooldown_seconds)
        self._last_emitted: dict[str, datetime] = {}

    def allow(self, event: Event) -> bool:
        now = event.timestamp
        previous = self._last_emitted.get(event.kind)
        if previous is not None and now - previous < self.cooldown:
            return False
        self._last_emitted[event.kind] = now
        return True
