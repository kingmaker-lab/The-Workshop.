import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from heart.actions import Action, ActionEngine, RiskLevel
from heart.core import Heart
from heart.events import Event
from heart.events.rules import CooldownRule
from heart.memory import EventStore
from heart.security.audit import AuditLog


class HeartTests(unittest.TestCase):
    def test_observation_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventStore(Path(directory) / "events.db")
            heart = Heart(store)
            snapshot = heart.observe()
            self.assertIn("disk_percent", snapshot)
            self.assertTrue(any(event["kind"] == "system.snapshot" for event in store.recent(10)))
            store.close()

    def test_high_risk_action_requires_confirmation(self) -> None:
        engine = ActionEngine()
        engine.register(Action("delete_data", RiskLevel.DESTRUCTIVE, lambda: "deleted"))
        blocked = engine.execute("delete_data")
        allowed = engine.execute("delete_data", confirmed=True)
        self.assertFalse(blocked.executed)
        self.assertTrue(allowed.executed)

    def test_unknown_action_is_not_executed(self) -> None:
        result = ActionEngine().execute("not_registered")
        self.assertFalse(result.executed)

    def test_root_action_is_blocked_and_audited(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = ActionEngine(audit=AuditLog(Path(directory) / "audit.jsonl"))
            engine.register(Action("safe_tool", RiskLevel.INFORMATION, lambda: "ok"))
            result = engine.execute("safe_tool", root=True)
            self.assertFalse(result.executed)
            self.assertIn("root", result.message)
            self.assertEqual(len(Path(directory, "audit.jsonl").read_text().splitlines()), 1)

    def test_event_cooldown_suppresses_repeated_kind(self) -> None:
        rule = CooldownRule(cooldown_seconds=60)
        timestamp = datetime.now(timezone.utc)
        first = Event("CPU_HIGH", {"value": 95}, timestamp)
        second = Event("CPU_HIGH", {"value": 96}, timestamp + timedelta(seconds=1))
        self.assertTrue(rule.allow(first))
        self.assertFalse(rule.allow(second))

    def test_heart_exposes_structured_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = EventStore(Path(directory) / "events.db")
            heart = Heart(store)
            heart.observe()
            self.assertIn("usage", heart.state.cpu)
            self.assertIsNotNone(heart.state.last_update)
            store.close()

    def test_heart_routes_tool_requests_through_tool_router(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            heart = Heart(EventStore(Path(directory) / "events.db"))
            result = heart.dispatch_tool({"tool": "system_status", "arguments": {}})
            self.assertTrue(result.executed)
            heart.store.close()


if __name__ == "__main__":
    unittest.main()
