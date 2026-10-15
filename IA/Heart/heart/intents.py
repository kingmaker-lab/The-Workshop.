from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tools import ToolRouter, create_default_registry


@dataclass(frozen=True)
class Intent:
    type: str
    tool: str | None = None
    arguments: dict[str, Any] | None = None
    content: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"type": self.type}
        if self.tool is not None:
            payload["tool"] = self.tool
        if self.arguments is not None:
            payload["arguments"] = self.arguments
        if self.content is not None:
            payload["content"] = self.content
        if self.message is not None:
            payload["message"] = self.message
        return payload


@dataclass(frozen=True)
class ToolCallIntent(Intent):
    def __init__(self, *, tool: str, arguments: dict[str, Any] | None = None) -> None:
        super().__init__(type="tool_call", tool=tool, arguments=arguments or {})


class IntentEngine:
    def __init__(self, router: ToolRouter | None = None) -> None:
        self.router = router or ToolRouter(create_default_registry())

    def from_text(self, text: str) -> dict[str, Any]:
        lowered = text.lower()
        if "máquina" in lowered or "maquina" in lowered or "status" in lowered or "como está" in lowered or "como esta" in lowered:
            return ToolCallIntent(tool="system_status", arguments={}).to_dict()
        if "notific" in lowered:
            return ToolCallIntent(tool="send_notification", arguments={"message": "Notificação solicitada"}).to_dict()
        return Intent(type="response", content="Posso ajudar, mas ainda não tenho uma intenção explícita para isso.").to_dict()

    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return Intent(type="error", message="Payload inválido.").to_dict()
        if payload.get("type") == "tool_call":
            tool = payload.get("tool")
            arguments = payload.get("arguments", {})
            if not isinstance(tool, str) or not tool:
                return Intent(type="error", message="Campo 'tool' ausente ou inválido.").to_dict()
            if not isinstance(arguments, dict):
                return Intent(type="error", message="Campo 'arguments' deve ser um objeto.").to_dict()
            result = self.router.dispatch({"tool": tool, "arguments": arguments})
            if result.executed:
                return {"type": "response", "content": result.result}
            return {"type": "error", "message": result.error or "Falha ao executar a ferramenta."}
        if payload.get("type") == "response":
            return payload
        if payload.get("type") == "error":
            return payload
        return Intent(type="error", message="Tipo de intenção desconhecido.").to_dict()


def parse_intent(payload: dict[str, Any]) -> Intent:
    if not isinstance(payload, dict):
        raise ValueError("Payload inválido")
    intent_type = payload.get("type")
    if intent_type == "tool_call":
        return ToolCallIntent(tool=str(payload["tool"]), arguments=dict(payload.get("arguments", {})))
    if intent_type == "response":
        return Intent(type="response", content=str(payload.get("content") or ""))
    if intent_type == "error":
        return Intent(type="error", message=str(payload.get("message") or "Erro desconhecido."))
    raise ValueError(f"Tipo de intenção inválido: {intent_type!r}")


def create_tool_call_intent(tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    return ToolCallIntent(tool=tool, arguments=arguments).to_dict()
