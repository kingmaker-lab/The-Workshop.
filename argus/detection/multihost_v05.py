"""ARGUS v0.5 | bounded, opt-in, local-only cross-host auth failure correlation.

Correlates repeated FAILED authentication events attributed to a common source
IP across several distinct normalized 'source' identities within a time window.
A 'source' is the operator-configured normalized host identity; a service name
is NOT a trustworthy host identity. No external enrichment, Sigma aggregation,
remote collection, API changes or automatic containment.

Out-of-order observations for one source IP are conservatively skipped.
All states are volatile and discarded on restart (including watch resume).
"""
from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address

from argus.models.alert import Detection
from argus.models.event import Event


@dataclass(slots=True)
class _IPState:
    failures: deque[tuple[datetime, str, str]] = field(default_factory=deque)
    last_seen: datetime | None = None
    reported: bool = False


class MultiHostCorrelationV05:
    """Bounded streaming correlation with one alert per qualifying active burst."""

    MAX_IPS = 4096
    MAX_EVENTS_PER_IP = 256
    CONFIG_KEYS = frozenset({
        "enabled", "window_seconds", "min_hosts", "min_failures",
        "max_ips", "max_events_per_ip",
    })

    def __init__(
        self, *, window_seconds: int = 120,
        min_hosts: int = 3, min_failures: int = 6,
        max_ips: int = 1024, max_events_per_ip: int = 128,
    ) -> None:
        values = {
            "window_seconds": (window_seconds, 10, 3600),
            "min_hosts": (min_hosts, 2, 16),
            "min_failures": (min_failures, 2, 128),
            "max_ips": (max_ips, 1, self.MAX_IPS),
            "max_events_per_ip": (max_events_per_ip, 2, self.MAX_EVENTS_PER_IP),
        }
        for name, (value, lo, hi) in values.items():
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"temporal_v05.{name} must be an integer in [{lo},{hi}]")
        if not min_hosts <= min_failures <= max_events_per_ip:
            raise ValueError("temporal_v05 requires min_hosts <= min_failures <= max_events_per_ip")
        self.window_seconds = window_seconds
        self.window = timedelta(seconds=window_seconds)
        self.min_hosts = min_hosts
        self.min_failures = min_failures
        self.max_ips = max_ips
        self.max_events_per_ip = max_events_per_ip
        self._states: OrderedDict[str, _IPState] = OrderedDict()

    @classmethod
    def from_config(cls, options: dict) -> "MultiHostCorrelationV05 | None":
        if not isinstance(options, dict):
            raise ValueError("temporal_v05 must be a YAML mapping")
        unknown = set(options) - cls.CONFIG_KEYS
        if unknown:
            raise ValueError("unknown temporal_v05 options: " + ", ".join(sorted(map(str, unknown))))
        enabled = options.get("enabled", False)
        if type(enabled) is not bool:
            raise ValueError("temporal_v05.enabled must be a boolean")
        parameters = {key: value for key, value in options.items() if key != "enabled"}
        # Even when disabled, invalid values fail closed rather than silently lurk.
        engine = cls(**parameters)
        return engine if enabled else None

    def process(self, event: Event) -> list[Detection]:
        """Only normalized failed logins with explicit host identities are eligible."""
        if (event.event_type != "authentication" or event.result != "failed"
                or not event.src_ip or not isinstance(event.source, str)
                or event.source.strip().lower() in ("", "unknown")
                or len(event.source) > 128 or not isinstance(event.event_id, str)
                or len(event.event_id) > 128):
            return []
        try:
            address = str(ip_address(event.src_ip))
        except ValueError:
            return []
        ts = event.timestamp
        if ts.tzinfo is None or ts.utcoffset() is None:
            return []
        ts = ts.astimezone(timezone.utc)
        state = self._states.get(address)
        if state is None:
            if len(self._states) == self.max_ips:
                self._states.popitem(last=False)
            state = _IPState()
            self._states[address] = state
        else:
            self._states.move_to_end(address)

        if state.last_seen is not None and ts < state.last_seen:
            # Do not change state using older records; avoids rearming/false alerts.
            return []
        cutoff = ts - self.window
        while state.failures and state.failures[0][0] < cutoff:
            state.failures.popleft()
        if any(previous_id == event.event_id for _, _, previous_id in state.failures):
            # A repeated record/ID cannot inflate the failure threshold.
            return []
        state.last_seen = ts
        state.failures.append((ts, event.source, event.event_id))
        while len(state.failures) > self.max_events_per_ip:
            state.failures.popleft()

        hosts = sorted({host for _, host, _ in state.failures})
        qualified = len(state.failures) >= self.min_failures and len(hosts) >= self.min_hosts
        if not qualified:
            state.reported = False
            return []
        if state.reported:
            return []
        state.reported = True
        return [Detection(
            name="multi_host_failed_auth_burst",
            severity="medium",
            score=30,
            event_id=event.event_id,
            timestamp=event.to_dict()["timestamp"],
            src_ip=address,
            details={
                "failed_attempts": len(state.failures),
                "distinct_sources": len(hosts),
                "sources": hosts,
                "window_seconds": self.window_seconds,
                "assumption": "normalized source uniquely identifies a host",
                "scope": "local_experimental",
            },
        )]
