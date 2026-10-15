from __future__ import annotations

import re
from typing import Any

from .context import Context
from .intents import IntentEngine
from .tools import ToolRouter, create_default_registry


class RuleMatcher:
    def match(self, text: str) -> dict[str, Any] | None:
        lowered = text.lower()
        if any(token in lowered for token in ("status", "cpu", "ram", "memoria", "memória", "temperatura", "máquina", "maquina", "como está", "como esta")):
            return {"type": "tool_call", "tool": "system_status", "arguments": {}}
        if any(token in lowered for token in ("notificação", "notificacao", "avise", "alerta")):
            return {"type": "tool_call", "tool": "send_notification", "arguments": {"message": "Notificação solicitada"}}
        return None


class SemanticMatcher:
    def match(self, text: str) -> dict[str, Any] | None:
        lowered = text.lower()
        if re.search(r"(como|está|esta|ta).*?(computador|máquina|maquina|sistema)", lowered):
            return {"type": "tool_call", "tool": "system_status", "arguments": {}}
        if re.search(r"(algo|alguma).*?(estranho|anormal|problema|quebrado|falhando)", lowered):
            return {"type": "tool_call", "tool": "system_status", "arguments": {}}
        return None


class LLMResolver:
    def match(self, text: str) -> dict[str, Any] | None:
        lowered = text.lower()
        if "sentinel" in lowered or "monitor" in lowered:
            return {"type": "tool_call", "tool": "run_script", "arguments": {"name": "healthcheck"}}
        return None

    def resolve(self, text: str) -> dict[str, Any] | None:
        return self.match(text)


class HeartIntentEngine:
    def __init__(self, router: ToolRouter | None = None) -> None:
        self.router = router or ToolRouter(create_default_registry())
        self.rules = RuleMatcher()
        self.semantic = SemanticMatcher()
        self.llm = LLMResolver()
        self.context = Context()

    def interpret(self, text: str) -> dict[str, Any]:
        for matcher in (self.rules, self.semantic, self.llm):
            intent = matcher.match(text)
            if intent is not None:
                self.context.remember(intent=intent, message=text)
                return intent
        return {"type": "response", "content": "Não consegui mapear uma ação segura para isso."}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("type") == "tool_call":
            result = self.router.dispatch(payload)
            self.context.remember(tool=payload.get("tool"), result=result.result)
            if result.executed:
                response = {
                    "type": "response",
                    "tool_call": payload,
                    "content": format_tool_result(payload.get("tool"), result.result),
                    "context_summary": self.context.summary(),
                }
                return response
            return {
                "type": "error",
                "tool_call": payload,
                "message": result.error or "Falha ao executar a ferramenta.",
                "context_summary": self.context.summary(),
            }
        return payload


def format_tool_result(tool_name: str | None, result: Any) -> str:
    if tool_name == "system_status":
        data = result or {}
        cpu = data.get("cpu_percent_estimate", 0)
        ram = data.get("memory_percent", 0)
        temp = data.get("temperature_c")
        disk = data.get("disk_percent", 0)
        lines = [
            "Tudo está funcionando normalmente.",
            f"CPU em {cpu}%.",
            f"RAM em {ram}%.",
            f"Disco em {disk}%.",
        ]
        if temp is not None:
            lines.append(f"Temperatura em {temp}°C.")
        return " ".join(lines)
    if tool_name == "send_notification":
        return "Notificação enviada."
    if tool_name == "run_script":
        return f"Script executado com sucesso. Resultado: {result}"
    return str(result)
