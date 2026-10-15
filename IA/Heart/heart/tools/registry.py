from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from ..actions import RiskLevel

ToolHandler = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    risk: RiskLevel
    handler: ToolHandler
    allowed_arguments: frozenset[str] = frozenset()
    required_arguments: frozenset[str] = frozenset()

    def validate(self, arguments: dict[str, Any]) -> str | None:
        unknown = set(arguments) - self.allowed_arguments
        if unknown:
            return f"Argumentos não permitidos: {', '.join(sorted(unknown))}"
        missing = self.required_arguments - set(arguments)
        if missing:
            return f"Argumentos obrigatórios ausentes: {', '.join(sorted(missing))}"
        return None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if not tool.name or tool.name in self._tools:
            raise ValueError(f"Ferramenta inválida ou duplicada: {tool.name!r}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
