"""Regression tests for correlation deduplication and the local read-only API."""

import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from argus.api.server import _APIHandler
from argus.detection.behavioral import BehavioralEngine
from argus.models.event import Event
from argus.storage.database import Database


class BehavioralDeduplicationTests(unittest.TestCase):
    def test_continuous_brute_force_generates_only_one_alert(self) -> None:
        engine = BehavioralEngine(failure_threshold=3, window_seconds=30)
        start = datetime(2026, 10, 30, tzinfo=timezone.utc)
        detections = []
        for index in range(9):
            event = Event(
                timestamp=start + timedelta(seconds=index),
                source="sshd",
                event_type="authentication",
                src_ip="192.0.2.10",
                result="failed",
            )
            detections.extend(engine.process(event))
        self.assertEqual([d.name for d in detections], ["ssh_brute_force"])

    def test_alert_rearms_after_window_expiry(self) -> None:
        engine = BehavioralEngine(failure_threshold=3, window_seconds=10)
        start = datetime(2026, 10, 30, tzinfo=timezone.utc)
        detections = []
        for offset in (0, 1, 2, 30, 31, 32):
            event = Event(
                timestamp=start + timedelta(seconds=offset),
                source="sshd",
                event_type="authentication",
                src_ip="192.0.2.10",
                result="failed",
            )
            detections.extend(engine.process(event))
        self.assertEqual([d.name for d in detections], ["ssh_brute_force", "ssh_brute_force"])


class LocalAPITests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        database = Database(Path(self.directory.name) / "argus.db")
        handler = partial(_APIHandler, database=database)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)
        self.directory.cleanup()

    def test_health_response_is_not_cacheable(self) -> None:
        with urlopen(self.base + "/health", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")

    def test_rejects_invalid_and_oversized_limits(self) -> None:
        invalid_paths = (
            "/alerts?limit=0",
            "/alerts?limit=-1",
            "/alerts?limit=501",
            "/alerts?limit=abc",
            "/alerts?limit=1&limit=2",
            "/timeline?limit=0",
            "/timeline?limit=2001",
        )
        for path in invalid_paths:
            with self.subTest(path=path), self.assertRaises(HTTPError) as caught:
                urlopen(self.base + path, timeout=5)
            self.assertEqual(caught.exception.code, 400)

    def test_accepts_valid_boundary_limits(self) -> None:
        for path in ("/alerts?limit=1", "/alerts?limit=500", "/timeline?limit=2000"):
            with self.subTest(path=path), urlopen(self.base + path, timeout=5) as response:
                self.assertEqual(response.status, 200)


if __name__ == "__main__":
    unittest.main()
