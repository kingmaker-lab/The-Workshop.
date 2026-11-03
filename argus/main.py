import argparse
import json
import math
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from argus.api.server import serve
from argus.collectors.jsonl import JSONLCollector
from argus.collectors.network import NetworkCollector
from argus.collectors.syslog import SyslogCollector
from argus.core.correlator import CorrelationEngine
from argus.core.normalizer import normalize_event
from argus.core.scoring import RiskScorer
from argus.detection.anomaly_engine import AnomalyEngine
from argus.detection.behavioral import BehavioralEngine
from argus.detection.rules import RuleEngine
from argus.storage.database import Database
from argus.stream.follower import FileFollower, exclusive_stream_lock


PROJECT_DIR = Path(__file__).resolve().parent


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as input_file:
        configuration = yaml.safe_load(input_file) or {}
    if not isinstance(configuration, dict):
        raise ValueError("configuration must be a YAML mapping")
    configuration["_base_dir"] = str(config_path.parent)
    return configuration


def _configured_path(configuration: dict[str, Any], key: str, fallback: str) -> Path:
    base_dir = Path(configuration["_base_dir"])
    configured = Path(configuration.get(key, fallback))
    return configured if configured.is_absolute() else base_dir / configured


def _collector(input_path: Path, input_format: str):
    if input_format == "auto":
        input_format = "syslog" if input_path.suffix in {".log", ".syslog"} else "jsonl"
    if input_format == "syslog":
        return SyslogCollector(input_path)
    if input_format == "network":
        return NetworkCollector(input_path)
    return JSONLCollector(input_path)


def analyze(
    input_path: str | Path,
    input_format: str,
    database_path: str | Path,
    rules_path: str | Path,
    correlation_config: dict[str, Any],
    anomaly_config: dict[str, Any] | None = None,
) -> tuple[int, int]:
    database = Database(database_path)
    engine = build_engine(rules_path, correlation_config, anomaly_config)
    collector = _collector(Path(input_path), input_format)
    processed = 0
    alert_count = 0
    for raw_record in collector.records():
        try:
            event = normalize_event(raw_record)
        except (TypeError, ValueError) as error:
            print(f"Skipping invalid event: {error}", file=sys.stderr)
            continue
        database.record_event(event)
        processed += 1
        alert = engine.process(event)
        if alert is not None:
            database.record_alert(alert)
            alert_count += 1
            print(json.dumps(alert.to_dict(), sort_keys=True))
    return processed, alert_count


def build_engine(
    rules_path: str | Path,
    correlation_config: dict[str, Any],
    anomaly_config: dict[str, Any] | None = None,
) -> CorrelationEngine:
    rules = RuleEngine.from_yaml(rules_path)
    window_seconds = int(correlation_config.get("window_seconds", 30))
    threshold = int(correlation_config.get("failure_threshold", 15))
    risk_window_seconds = int(correlation_config.get("risk_window_seconds", 300))
    anomaly_config = anomaly_config or {}
    anomaly = None
    if anomaly_config.get("enabled", False):
        anomaly = AnomalyEngine(
            metrics=tuple(anomaly_config.get("metrics", ["orig_bytes", "resp_bytes"])),
            minimum_samples=int(anomaly_config.get("minimum_samples", 20)),
            z_threshold=float(anomaly_config.get("z_threshold", 4.0)),
        )
    return CorrelationEngine(
        rules,
        BehavioralEngine(threshold, window_seconds),
        RiskScorer(risk_window_seconds),
        anomaly=anomaly,
    )

def watch(
    input_path: Path,
    input_format: str,
    database: Database,
    rules_path: Path,
    correlation_config: dict[str, Any],
    anomaly_config: dict[str, Any],
    *,
    once: bool,
    poll_interval: float,
    batch_size: int,
    max_line_bytes: int,
    from_end: bool,
) -> None:
    """Follow trusted local log files without opening a network port."""
    if not math.isfinite(poll_interval) or not 0.1 <= poll_interval <= 60:
        raise ValueError("poll_interval must be finite in [0.1, 60] seconds")
    engine = build_engine(rules_path, correlation_config, anomaly_config)
    follower = FileFollower(
        input_path,
        database,
        engine,
        input_format=input_format,
        batch_size=batch_size,
        max_line_bytes=max_line_bytes,
        from_end=from_end,
        emit=lambda alert: print(json.dumps(alert.to_dict(), sort_keys=True), flush=True),
    )
    with exclusive_stream_lock(database.path):
        while True:
            processed, alerts, skipped = follower.poll()
            if processed or alerts or skipped or once:
                print(json.dumps({"processed": processed, "alerts": alerts, "skipped": skipped},
                                 sort_keys=True), flush=True)
            if once:
                return
            time.sleep(poll_interval)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Defensive event hunting and correlation")
    parser.add_argument("--config", default=str(PROJECT_DIR / "config.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="analyze a local event file")
    analyze_parser.add_argument("input", type=Path)
    analyze_parser.add_argument("--format", choices=("auto", "jsonl", "syslog", "network"), default="auto")
    analyze_parser.add_argument("--db", type=Path)

    watch_parser = subparsers.add_parser("watch", help="follow a local growing log file (v0.3)")
    watch_parser.add_argument("input", type=Path)
    watch_parser.add_argument("--format", choices=("auto", "jsonl", "syslog", "network"), default="auto")
    watch_parser.add_argument("--db", type=Path)
    watch_parser.add_argument("--poll-interval", type=float, default=0.5)
    watch_parser.add_argument("--batch-size", type=int, default=200)
    watch_parser.add_argument("--max-line-bytes", type=int, default=65536)
    watch_parser.add_argument("--from-end", action="store_true",
                              help="start with new lines only if no checkpoint exists")
    watch_parser.add_argument("--once", action="store_true",
                              help="process one bounded poll, then exit")

    serve_parser = subparsers.add_parser("serve", help="start the read-only local API")
    serve_parser.add_argument("--db", type=Path)
    serve_parser.add_argument("--host")
    serve_parser.add_argument("--port", type=int)

    timeline_parser = subparsers.add_parser("timeline", help="show events and alerts")
    timeline_parser.add_argument("--src-ip")
    timeline_parser.add_argument("--limit", type=int, default=100)
    timeline_parser.add_argument("--db", type=Path)
    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()
    try:
        configuration = load_config(arguments.config)
        database_path = arguments.db or _configured_path(configuration, "database", "argus.db")
        database = Database(database_path)

        if arguments.command == "analyze":
            rules_path = _configured_path(configuration, "rules", "rules/default.yaml")
            processed, alert_count = analyze(
                arguments.input,
                arguments.format,
                database_path,
                rules_path,
                configuration.get("correlation", {}),
                configuration.get("anomaly", {}),
            )
            print(json.dumps({"processed": processed, "alerts": alert_count}, sort_keys=True))
        elif arguments.command == "watch":
            rules_path = _configured_path(configuration, "rules", "rules/default.yaml")
            watch(
                arguments.input,
                arguments.format,
                database,
                rules_path,
                configuration.get("correlation", {}),
                configuration.get("anomaly", {}),
                once=arguments.once,
                poll_interval=arguments.poll_interval,
                batch_size=arguments.batch_size,
                max_line_bytes=arguments.max_line_bytes,
                from_end=arguments.from_end,
            )
        elif arguments.command == "serve":
            api_config = configuration.get("api", {})
            serve(
                database,
                arguments.host or api_config.get("host", "127.0.0.1"),
                arguments.port or int(api_config.get("port", 8765)),
            )
        else:
            print(json.dumps({"timeline": database.timeline(arguments.src_ip, arguments.limit)}, sort_keys=True))
    except KeyboardInterrupt:
        return 0
    except (OSError, ValueError, sqlite3.Error, yaml.YAMLError) as error:
        print(f"argus: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())