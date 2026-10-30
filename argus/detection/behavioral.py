from bisect import insort
from collections import defaultdict
from datetime import datetime, timedelta

from argus.models.alert import Detection
from argus.models.event import Event


class BehavioralEngine:
    def __init__(self, failure_threshold: int = 15, window_seconds: int = 30) -> None:
        if failure_threshold < 1 or window_seconds < 1:
            raise ValueError("failure threshold and window must be positive")
        self.failure_threshold = failure_threshold
        self.window = timedelta(seconds=window_seconds)
        self._failures: dict[str, list[datetime]] = defaultdict(list)
        self._brute_force_reported: set[str] = set()
        self._sources: dict[str, list[tuple[datetime, str]]] = defaultdict(list)

    def process(self, event: Event) -> list[Detection]:
        if event.src_ip is None:
            return []
        timestamp = event.timestamp
        cutoff = timestamp - self.window
        failures = self._failures[event.src_ip]
        failures[:] = [seen_at for seen_at in failures if cutoff <= seen_at <= timestamp]
        detections = []

        if event.event_type == "authentication" and event.result == "failed":
            insort(failures, timestamp)
            if len(failures) >= self.failure_threshold and event.src_ip not in self._brute_force_reported:
                self._brute_force_reported.add(event.src_ip)
                detections.append(
                    self._detection(
                        event,
                        "ssh_brute_force",
                        "high",
                        55,
                        {"failed_attempts": len(failures), "window_seconds": int(self.window.total_seconds())},
                    )
                )
            elif len(failures) < self.failure_threshold:
                # Re-arm only when the current sequence falls below the threshold.
                # Otherwise every second failure would trigger a duplicate alert.
                self._brute_force_reported.discard(event.src_ip)
        elif event.event_type == "authentication" and event.result == "success":
            if len(failures) >= self.failure_threshold:
                detections.append(
                    self._detection(
                        event,
                        "successful_login_after_brute_force",
                        "critical",
                        35,
                        {"preceding_failures": len(failures), "window_seconds": int(self.window.total_seconds())},
                    )
                )
                failures.clear()
                self._brute_force_reported.discard(event.src_ip)
        elif len(failures) < self.failure_threshold:
            self._brute_force_reported.discard(event.src_ip)

        detections.extend(self._detect_cross_source_activity(event, cutoff))
        return detections

    def _detect_cross_source_activity(self, event: Event, cutoff: datetime) -> list[Detection]:
        observations = self._sources[event.src_ip]
        observations[:] = [item for item in observations if cutoff <= item[0] <= event.timestamp]
        previous_sources = {source for _, source in observations}
        insort(observations, (event.timestamp, event.source))
        if previous_sources and event.source not in previous_sources:
            return [
                self._detection(
                    event,
                    "ip_seen_across_sources",
                    "low",
                    10,
                    {"sources": sorted(previous_sources | {event.source})},
                )
            ]
        return []

    @staticmethod
    def _detection(
        event: Event,
        name: str,
        severity: str,
        score: int,
        details: dict[str, object],
    ) -> Detection:
        return Detection(
            name=name,
            severity=severity,
            score=score,
            event_id=event.event_id,
            timestamp=event.to_dict()["timestamp"],
            src_ip=event.src_ip,
            details=details,
        )