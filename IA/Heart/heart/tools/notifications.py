from __future__ import annotations

from typing import Any, Callable

from ..actions import RiskLevel
from .registry import Tool


def create_notification_tool(sink: Callable[[str], None] | None = None) -> Tool:
    notify = sink or print

    def send_notification(arguments: dict[str, Any]) -> dict[str, str]:
        message = arguments["message"]
        notify(f"Heart: {message}")
        return {"message": message}

    return Tool("send_notification", "Envia uma notificação ao usuário", RiskLevel.INFORMATION, send_notification, frozenset({"message"}), frozenset({"message"}))
