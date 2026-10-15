import tempfile
import unittest
from pathlib import Path

from heart.actions import RiskLevel
from heart.security.audit import AuditLog
from heart.tools import Tool, ToolRegistry, ToolRouter, create_default_registry, create_notification_tool, create_run_script_tool, create_system_status_tool


class ToolRouterTests(unittest.TestCase):
    def make_router(self, registry: ToolRegistry) -> ToolRouter:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return ToolRouter(registry, audit=AuditLog(Path(directory.name) / "audit.jsonl"))

    def test_registers_and_lists_tools(self) -> None:
        self.assertEqual(create_default_registry().names(), ("run_script", "send_notification", "start_process", "system_status"))

    def test_unknown_tool_is_rejected(self) -> None:
        result = self.make_router(ToolRegistry()).dispatch({"tool": "missing", "arguments": {}})
        self.assertFalse(result.executed)
        self.assertIn("desconhecida", result.error)

    def test_arguments_are_validated(self) -> None:
        registry = ToolRegistry()
        registry.register(create_notification_tool())
        result = self.make_router(registry).dispatch({"tool": "send_notification", "arguments": {"text": "x"}})
        self.assertFalse(result.executed)
        self.assertIn("não permitidos", result.error)

    def test_system_status_executes(self) -> None:
        registry = ToolRegistry()
        registry.register(create_system_status_tool())
        result = self.make_router(registry).dispatch({"tool": "system_status", "arguments": {}})
        self.assertTrue(result.executed)
        self.assertIn("cpu_percent_estimate", result.result)

    def test_script_name_must_be_allowlisted(self) -> None:
        registry = ToolRegistry()
        registry.register(create_run_script_tool({"known": ("python3", "-c", "print('ok')")}))
        result = self.make_router(registry).dispatch({"tool": "run_script", "arguments": {"name": "arbitrary"}})
        self.assertFalse(result.executed)
        self.assertIn("Falha", result.error)

    def test_root_is_blocked(self) -> None:
        registry = ToolRegistry()
        registry.register(Tool("danger", "danger", RiskLevel.INFORMATION, lambda _: "bad"))
        result = self.make_router(registry).dispatch({"tool": "danger", "arguments": {}}, root=True)
        self.assertFalse(result.executed)
        self.assertIn("root", result.error)

    def test_confirmation_is_required_for_destructive_tool(self) -> None:
        registry = ToolRegistry()
        registry.register(Tool("delete", "delete", RiskLevel.DESTRUCTIVE, lambda _: "deleted"))
        router = self.make_router(registry)
        self.assertFalse(router.dispatch({"tool": "delete", "arguments": {}}).executed)
        self.assertTrue(router.dispatch({"tool": "delete", "arguments": {}}, confirmed=True).executed)

    def test_tool_failure_does_not_escape_router(self) -> None:
        registry = ToolRegistry()
        registry.register(Tool("broken", "broken", RiskLevel.INFORMATION, lambda _: 1 / 0))
        result = self.make_router(registry).dispatch({"tool": "broken", "arguments": {}})
        self.assertFalse(result.executed)
        self.assertIn("Falha na ferramenta", result.error)

    def test_script_timeout_is_reported_as_tool_failure(self) -> None:
        registry = ToolRegistry()
        registry.register(create_run_script_tool({"slow": ("python3", "-c", "import time; time.sleep(1)")}, timeout_seconds=0.01))
        result = self.make_router(registry).dispatch({"tool": "run_script", "arguments": {"name": "slow"}})
        self.assertFalse(result.executed)
        self.assertIn("Falha na ferramenta", result.error)

    def test_notification_uses_sink(self) -> None:
        messages: list[str] = []
        registry = ToolRegistry()
        registry.register(create_notification_tool(messages.append))
        result = self.make_router(registry).dispatch({"tool": "send_notification", "arguments": {"message": "oi"}})
        self.assertTrue(result.executed)
        self.assertEqual(messages, ["Heart: oi"])


if __name__ == "__main__":
    unittest.main()
