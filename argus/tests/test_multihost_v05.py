"""ARGUS v0.5: opt-in cross-host correlation, bounded state, and CLI regression."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argus.detection.multihost_v05 import MultiHostCorrelationV05
from argus.main import build_engine
from argus.models.event import Event


ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "argus" / "rules" / "default.yaml"
SAMPLE = ROOT / "argus" / "samples" / "multihost_auth_v05.jsonl"
CONFIG = ROOT / "argus" / "config-v05-demo.yaml"


class MultiHostV05Tests(unittest.TestCase):
    start = datetime(2026, 11, 24, 12, tzinfo=timezone.utc)

    def event(self, index: int, host: str, ip: str = "192.0.2.70",
              result: str = "failed", **overrides) -> Event:
        data = {
            "timestamp": self.start + timedelta(seconds=index),
            "source": host,
            "event_type": "authentication",
            "src_ip": ip,
            "user": "test",
            "result": result,
            "event_id": f"v05-test-{ip}-{index}-{host}",
        }
        data.update(overrides)
        return Event(**data)

    def test_default_config_disables_only_new_engine(self):
        original = build_engine(RULES, {})
        self.assertIsNone(original.temporal_v05)
        self.assertIsNone(MultiHostCorrelationV05.from_config({}))
        self.assertIsNone(MultiHostCorrelationV05.from_config({"enabled": False}))
        self.assertIsNotNone(original.behavior)
        self.assertIsNotNone(original.rules)

    def test_opt_in_six_failures_three_hosts_one_new_detection(self):
        engine = build_engine(
            RULES, {}, temporal_v05_config={
                "enabled": True, "window_seconds": 120,
                "min_hosts": 3, "min_failures": 6,
            })
        events = ["node-a", "node-b", "node-a", "node-c", "node-b", "node-c",
                  "node-c", "node-a"]
        multi = []
        for index, host in enumerate(events):
            alert = engine.process(self.event(index, host))
            if alert:
                multi.extend(d for d in alert.detections
                             if d.name == "multi_host_failed_auth_burst")
        self.assertEqual(len(multi), 1)
        self.assertEqual(multi[0].severity, "medium")
        self.assertEqual(multi[0].score, 30)
        self.assertEqual(multi[0].details["distinct_sources"], 3)
        self.assertEqual(multi[0].details["failed_attempts"], 6)
        self.assertEqual(multi[0].details["sources"], ["node-a", "node-b", "node-c"])

    def test_same_host_success_unknown_source_and_missing_ip_do_not_trigger(self):
        model = MultiHostCorrelationV05()
        for i in range(16):
            self.assertFalse(model.process(self.event(i, "node-a")))
        self.assertFalse(model.process(self.event(18, "node-b", result="success")))
        self.assertFalse(model.process(self.event(19, "node-b", ip=None)))
        self.assertFalse(model.process(self.event(20, "unknown")))
        self.assertFalse(model.process(self.event(21, "node-c", event_type="network_connection")))

    def test_duplicate_event_id_cannot_trigger_burst(self):
        model = MultiHostCorrelationV05()
        for i in range(3):
            original = self.event(i, ["node-a", "node-b", "node-c"][i],
                                  event_id="shared-event")
            self.assertEqual(model.process(original), [])
        self.assertEqual(len(model._states["192.0.2.70"].failures), 1)

    def test_out_of_order_events_are_skipped_without_poisoning_future_state(self):
        model = MultiHostCorrelationV05()
        self.assertFalse(model.process(self.event(10, "node-a")))
        self.assertFalse(model.process(self.event(9, "node-b")))
        self.assertEqual(len(model._states["192.0.2.70"].failures), 1)
        for i, host in enumerate(["node-a", "node-b", "node-c", "node-a", "node-b"], 11):
            result = model.process(self.event(i, host))
        self.assertEqual([d.name for d in result], ["multi_host_failed_auth_burst"])

    def test_expired_burst_rearms_when_evidence_ages_out(self):
        model = MultiHostCorrelationV05(window_seconds=10, min_hosts=3,
                                        min_failures=3)
        for idx, host in enumerate(["a", "b", "c"]):
            found = model.process(self.event(idx, host))
        self.assertEqual(len(found), 1)
        self.assertEqual(model.process(self.event(3, "c")), [])
        for idx, host in enumerate(["a", "b", "c"], 30):
            found = model.process(self.event(idx, host))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "multi_host_failed_auth_burst")

    def test_bounded_ip_cardinality_and_window_history(self):
        model = MultiHostCorrelationV05(window_seconds=120, min_hosts=2,
                                        min_failures=2, max_ips=2,
                                        max_events_per_ip=3)
        for ip in ("192.0.2.1", "192.0.2.2", "192.0.2.3"):
            for i in range(20):
                model.process(self.event(i, f"h{i % 3}", ip=ip))
                self.assertLessEqual(len(model._states), 2)
                for state in model._states.values():
                    self.assertLessEqual(len(state.failures), 3)
        self.assertNotIn("192.0.2.1", model._states)

    def test_config_strictness_and_types(self):
        bad = [
            {"enabled": "true"}, {"enabled": 1},
            {"enable": True}, {"window_seconds": True},
            {"window_seconds": 0}, {"window_seconds": 99999},
            {"min_hosts": 1}, {"min_hosts": 20},
            {"max_ips": -1}, {"max_ips": 5000},
            {"max_events_per_ip": 257},
            {"min_hosts": 6, "min_failures": 5},
            {"max_events_per_ip": 3, "min_failures": 6},
        ]
        for case in bad:
            with self.subTest(case=case), self.assertRaises(ValueError):
                MultiHostCorrelationV05.from_config(case)
        with self.assertRaises(ValueError):
            MultiHostCorrelationV05.from_config([])

    def test_existing_engine_unaffected_when_disabled(self):
        normal = build_engine(RULES, {})
        disabled = build_engine(RULES, {}, temporal_v05_config={"enabled": False})
        events = [self.event(i, ["a", "b", "a", "c", "b", "c"][i])
                  for i in range(6)]
        first = [normal.process(x) for x in events]
        second = [disabled.process(x) for x in events]
        summary = lambda seq: [
            sorted(d.name for d in alert.detections) if alert else []
            for alert in seq
        ]
        self.assertEqual(summary(first), summary(second))
        self.assertFalse(any("multi_host_failed_auth_burst" in names
                             for names in summary(first)))

    def test_cli_batch_and_watch_smoke_remain_local(self):
        with tempfile.TemporaryDirectory() as directory:
            db_batch = Path(directory) / "batch.db"
            db_watch = Path(directory) / "watch.db"
            def cli(*arguments: str):
                return subprocess.run(
                    [sys.executable, "-m", "argus.main",
                     "--config", str(CONFIG), *arguments],
                    cwd=ROOT, text=True, capture_output=True, timeout=20)
            batch = cli("analyze", str(SAMPLE), "--db", str(db_batch))
            self.assertEqual(batch.returncode, 0, batch.stderr)
            self.assertEqual(batch.stdout.count('"multi_host_failed_auth_burst"'), 1)
            self.assertIn('"processed": 8', batch.stdout)

            first = cli("watch", str(SAMPLE), "--db", str(db_watch),
                        "--batch-size", "100", "--once")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout.count('"multi_host_failed_auth_burst"'), 1)
            self.assertIn('"processed": 8', first.stdout)
            second = cli("watch", str(SAMPLE), "--db", str(db_watch), "--once")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn('"processed": 0', second.stdout)

            # No event data or models were published to any network endpoint.
            self.assertFalse(db_batch == db_watch)


if __name__ == "__main__":
    unittest.main()
