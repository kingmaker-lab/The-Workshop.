from uuid import uuid4

from argus.core.scoring import RiskScorer
from argus.detection.anomaly_engine import AnomalyEngine
from argus.detection.behavioral import BehavioralEngine
from argus.detection.rules import RuleEngine
from argus.models.alert import Alert
from argus.models.event import Event


class CorrelationEngine:
    def __init__(
        self,
        rules: RuleEngine,
        behavior: BehavioralEngine,
        scorer: RiskScorer,
        anomaly: AnomalyEngine | None = None,
    ) -> None:
        self.rules = rules
        self.behavior = behavior
        self.scorer = scorer
        self.anomaly = anomaly

    def process(self, event: Event) -> Alert | None:
        detections = self.rules.evaluate(event)
        detections.extend(self.behavior.process(event))
        if self.anomaly is not None:
            detections.extend(self.anomaly.process(event))
        if not detections:
            return None
        risk_score = self.scorer.score(event.src_ip, event.timestamp, detections)
        event_data = event.to_dict()
        return Alert(
            alert_id=str(uuid4()),
            event_id=event.event_id,
            timestamp=event_data["timestamp"],
            src_ip=event.src_ip,
            risk_score=risk_score,
            severity=self.scorer.severity(risk_score),
            detections=detections,
            event=event_data,
        )