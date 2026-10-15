from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Context:
    last_intent: dict[str, Any] | None = None
    last_tool: str | None = None
    last_result: Any = None
    recent_events: list[str] = field(default_factory=list)
    conversation_turns: list[dict[str, Any]] = field(default_factory=list)

    def remember(self, *, intent: dict[str, Any] | None = None, tool: str | None = None, result: Any = None, event: str | None = None, message: str | None = None) -> None:
        if intent is not None:
            self.last_intent = intent
        if tool is not None:
            self.last_tool = tool
        if result is not None:
            self.last_result = result
        if event is not None:
            self.recent_events.append(event)
            self.recent_events = self.recent_events[-10:]
        if message is not None:
            self.conversation_turns.append({"message": message})
            self.conversation_turns = self.conversation_turns[-10:]

    def summary(self) -> dict[str, Any]:
        return {
            "last_intent": self.last_intent,
            "last_tool": self.last_tool,
            "last_result": self.last_result,
            "recent_events": self.recent_events,
            "conversation_turns": self.conversation_turns,
        }
