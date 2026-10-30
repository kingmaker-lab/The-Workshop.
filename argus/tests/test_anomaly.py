"""Tests for ARGUS v0.2 opt-in statistical network detections."""

import unittest
from datetime import datetime, timedelta, timezone

from argus.core.correlator import CorrelationEngine
from argus.core.scoring import RiskScorer
from argus.detection.anomaly_engine import AnomalyEngine
from argus.detection.behavioral import BehavioralEngine
from argus.detection.rules import RuleEngine
from argus.models.event import Event


def network_event(index: int, value: object, source: str = "zeek-a") -> Event:
    return Event(
        timestamp=datetime(2026, 10, 30, tzinfo=timezone.utc) + timedelta(seconds=index),
        source=source,
        event_type="network_connection",
        src_ip="192.0.2.10",
        fields={"orig_bytes": value},
    )


class AnomalyEngineTests(unittest.TestCase):
    def test_opt_in_and_warmup(self) -> None:
        without_anomaly = CorrelationEngine(RuleEngine([]), BehavioralEngine(), RiskScorer())
        self.assertIsNone(without_anomaly.process(network_event(0, 1_000)))

        engine = AnomalyEngine(metrics=("orig_bytes",), minimum_samples=5, z_threshold=4.0)
        for index in range(5):
            self.assertEqual(engine.process(network_event(index, 100)), [])
        detection = engine.process(network_event(6, 10_000))
        self.assertEqual(len(detection), 1)
        self.assertEqual(detection[0].name, "network_anomaly_orig_bytes")
        self.assertLessEqual(detection[0].details["z_score"], 999.0)

    def test_non_numeric_and_negative_are_ignored(self) -> None:
        engine = AnomalyEngine(metrics=("orig_bytes",), minimum_samples=5)
        for value in (True, "200", None, -1, float("nan"), float("inf")):
            self.assertEqual(engine.process(network_event(0, value)), [])

    def test_per_host_isolated_baselines(self) -> None:
        engine = AnomalyEngine(metrics=("orig_bytes",), minimum_samples=5)
        for index in range(5):
            self.assertEqual(engine.process(network_event(index, 50, "node-a")), [])
        self.assertEqual(engine.process(network_event(6, 10_000, "node-b")), [])

    def test_detection_is_scored_and_serializable(self) -> None:
        correlation = CorrelationEngine(
            RuleEngine([]),
            BehavioralEngine(),
            RiskScorer(),
            anomaly=AnomalyEngine(metrics=("orig_bytes",), minimum_samples=5),
        )
        for index in range(5):
            self.assertIsNone(correlation.process(network_event(index, 50)))
        alert = correlation.process(network_event(6, 90_000))
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "medium")
        self.assertEqual(alert.risk_score, 25)
        import json
        json.dumps(alert.to_dict(), allow_nan=False)

    def test_configuration_guards(self) -> None:
        invalid = (
            {"metrics": ("not_a_metric",)},
            {"metrics": ()},
            {"minimum_samples": 0},
            {"z_threshold": float("inf")},
            {"z_threshold": 0},
        )
        for params in invalid:
            with self.subTest(params=params), self.assertRaises(ValueError):
                AnomalyEngine(**params)


if __name__ == "__main__":
    unittest.main()
