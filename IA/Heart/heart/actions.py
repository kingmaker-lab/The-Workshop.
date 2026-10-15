from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

from .security.audit import AuditLog
from .security.permissions import PermissionPolicy


class RiskLevel(IntEnum):
    INFORMATION = 0
    KNOWN_SCRIPT = 1
    CONFIGURATION = 2
    DESTRUCTIVE = 3


@dataclass(frozen=True)
class Action:
    name: str
    risk: RiskLevel
    handler: Callable[[], str]


@dataclass(frozen=True)
class ActionResult:
    name: str
    executed: bool
    message: str


class ActionEngine:
    def __init__(self, *, audit: AuditLog | None = None, policy: PermissionPolicy | None = None) -> None:
        self._actions: dict[str, Action] = {}
        self.audit = audit or AuditLog()
        self.policy = policy or PermissionPolicy()

    def register(self, action: Action) -> None:
        self._actions[action.name] = action

    def execute(self, name: str, *, confirmed: bool = False, root: bool = False) -> ActionResult:
        action = self._actions.get(name)
        if action is None:
            result = ActionResult(name, False, "Ação desconhecida")
            self.audit.record(intent="unknown", tool=name, arguments={}, result=result.message, executed=False)
            return result
        decision = self.policy.check(action.risk, confirmed=confirmed, root=root)
        if not decision.allowed:
            result = ActionResult(name, False, decision.reason)
            self.audit.record(intent="execute", tool=name, arguments={}, result=result.message, executed=False)
            return result
        result = ActionResult(name, True, action.handler())
        self.audit.record(intent="execute", tool=name, arguments={}, result=result.message, executed=True)
        return result
