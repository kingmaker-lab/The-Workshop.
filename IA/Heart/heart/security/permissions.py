from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


class PermissionPolicy:
    def check(self, risk: int, *, confirmed: bool = False, root: bool = False) -> PermissionDecision:
        if root:
            return PermissionDecision(False, "Execução como root bloqueada por padrão")
        if risk >= 2 and not confirmed:
            return PermissionDecision(False, "Confirmação explícita necessária")
        return PermissionDecision(True, "Permitido")
