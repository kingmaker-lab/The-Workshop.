"""Opt-in online anomaly detection for bounded numeric network telemetry.

The baseline learns only from numeric samples. It starts alerting after warmup
and updates its state after evaluating the current sample. Not a trained ML
model and not intended as a substitute for an analyst.
"""

from math import isfinite

from argus.detection.anomaly import OnlineBaseline
from argus.models.alert import Detection
from argus.models.event import Event


class AnomalyEngine:
    """Per-source, per-metric anomaly detector for network events."""

    SUPPORTED_METRICS = frozenset({"duration", "orig_bytes", "resp_bytes"})

    def __init__(
        self,
        *,
        metrics: tuple[str, ...] = ("orig_bytes", "resp_bytes"),
        minimum_samples: int = 20,
        z_threshold: float = 4.0,
    ) -> None:
        if not metrics or not set(metrics) <= self.SUPPORTED_METRICS:
            raise ValueError("unsupported anomaly metric")
        if minimum_samples < 5:
            raise ValueError("minimum_samples must be at least 5")
        if not isfinite(z_threshold) or z_threshold < 2:
            raise ValueError("z_threshold must be finite and at least 2")
        self.metrics = tuple(dict.fromkeys(metrics))
        self.z_threshold = z_threshold
        self.baseline = OnlineBaseline(minimum_samples=minimum_samples)

    def process(self, event: Event) -> list[Detection]:
        if event.event_type != "network_connection":
            return []

        findings = []
        for metric in self.metrics:
            value = event.fields.get(metric)
            # bool is a subclass of int, so explicitly reject it.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            number = float(value)
            if not isfinite(number) or number < 0:
                continue
            key = (event.source, metric)
            z_score = self.baseline.observe(key, number)
            if z_score is None or z_score < self.z_threshold:
                continue
            findings.append(
                Detection(
                    name=f"network_anomaly_{metric}",
                    severity="medium",
                    score=25,
                    event_id=event.event_id,
                    timestamp=event.to_dict()["timestamp"],
                    src_ip=event.src_ip,
                    details={
                        "metric": metric,
                        "value": number,
                        "z_score": min(z_score, 999.0),
                        "baseline": "welford",
                        "scope": "source_metric",
                    },
                )
            )
        return findings
