from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..security.audit import AuditLog
from ..security.permissions import PermissionPolicy
from .registry import ToolRegistry


@dataclass(frozen=True)
class ToolRequest:
    tool: str
    arguments: dict[str, Any]

    @classmethod
    def from_dict(cls, request: dict[str, Any]) -> "ToolRequest":
        tool = request.get("tool")
        arguments = request.get("arguments", {})
        if not isinstance(tool, str) or not tool:
            raise ValueError("'tool' deve ser um nome não vazio")
        if not isinstance(arguments, dict):
            raise ValueError("'arguments' deve ser um objeto")
        return cls(tool, arguments)


@dataclass(frozen=True)
class ToolResult:
    tool: str
    executed: bool
    result: Any
    error: str | None = None


class ToolRouter:
    """The only gateway from structured intent to side effects."""

    def __init__(self, registry: ToolRegistry, *, audit: AuditLog | None = None, policy: PermissionPolicy | None = None) -> None:
        self.registry = registry
        self.audit = audit or AuditLog()
        self.policy = policy or PermissionPolicy()

    def dispatch(self, request: ToolRequest | dict[str, Any], *, confirmed: bool = False, root: bool = False) -> ToolResult:
        try:
            parsed = request if isinstance(request, ToolRequest) else ToolRequest.from_dict(request)
        except (TypeError, ValueError) as exc:
            return ToolResult("<invalid>", False, None, str(exc))

        tool = self.registry.get(parsed.tool)
        if tool is None:
            return self._fail(parsed, f"Ferramenta desconhecida: {parsed.tool}")
        validation_error = tool.validate(parsed.arguments)
        if validation_error:
            return self._fail(parsed, validation_error)
        decision = self.policy.check(tool.risk, confirmed=confirmed, root=root)
        if not decision.allowed:
            return self._fail(parsed, decision.reason)
        try:
            result = tool.handler(parsed.arguments)
        except Exception as exc:  # tool failures must not kill the engine
            return self._fail(parsed, f"Falha na ferramenta: {exc}")
        self.audit.record(intent="tool_request", tool=parsed.tool, arguments=parsed.arguments, result="executed", executed=True)
        return ToolResult(parsed.tool, True, result)

    def _fail(self, request: ToolRequest, message: str) -> ToolResult:
        self.audit.record(intent="tool_request", tool=request.tool, arguments=request.arguments, result=message, executed=False)
        return ToolResult(request.tool, False, None, message)
