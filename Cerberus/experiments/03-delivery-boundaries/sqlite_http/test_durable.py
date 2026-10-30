"""Deterministic end-to-end CERBERUS_03 experiments using local SQLite and HTTP."""
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from durable import (
    ConflictError, ConsumerStore, ReservationStore,
    consumer_server, dispatch,
)


@contextmanager
def running_consumer(sink):
    server = consumer_server(sink)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


class DurableDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.producer_db = str(Path(self.tmp.name) / "producer.sqlite")
        self.consumer_db = str(Path(self.tmp.name) / "consumer.sqlite")
        self.producer = ReservationStore(self.producer_db)
        self.consumer = ConsumerStore(self.consumer_db)

    def test_sqlite_persists_reservation_and_outbox_across_restart(self):
        self.assertTrue(self.producer.reserve("evt1", "wolfcon", 2))
        reopened = ReservationStore(self.producer_db)
        self.assertEqual(reopened.counts(), {"reservations": 1, "pending": 1})
        self.assertEqual(reopened.pending(), [{"event_id": "evt1", "event_code": "wolfcon"}])

    def test_reservation_and_outbox_are_atomic_on_failure(self):
        with self.assertRaisesRegex(RuntimeError, "inside transaction"):
            self.producer.reserve("evt2", "wolfcon", 2, fail_after_insert=True)
        reopened = ReservationStore(self.producer_db)
        self.assertEqual(reopened.counts(), {"reservations": 0, "pending": 0})

    def test_request_idempotency_and_conflict(self):
        self.assertTrue(self.producer.reserve("evt1", "wolfcon", 2))
        self.assertFalse(self.producer.reserve("evt1", "wolfcon", 2))
        self.assertEqual(self.producer.counts(), {"reservations": 1, "pending": 1})
        with self.assertRaises(ConflictError):
            self.producer.reserve("evt1", "wolfcon", 3)
        self.assertEqual(self.producer.counts(), {"reservations": 1, "pending": 1})

    def test_invalid_input_never_writes_database(self):
        for args in [
            ("", "wolfcon", 2),
            ("../../evt", "wolfcon", 2),
            ("evt1", "bad/code", 2),
            ("evt1", "wolfcon", True),
            ("evt1", "wolfcon", None),
            ("evt1", "wolfcon", 7),
        ]:
            with self.assertRaises(ValueError):
                self.producer.reserve(*args)
        self.assertEqual(self.producer.counts(), {"reservations": 0, "pending": 0})

    def test_http_delivery_acknowledges_and_persists_both_databases(self):
        self.producer.reserve("evt1", "wolfcon", 2)
        with running_consumer(self.consumer) as url:
            self.assertEqual(dispatch(self.producer, url), 1)
            self.assertEqual(dispatch(self.producer, url), 0)
        self.assertEqual(ReservationStore(self.producer_db).counts(),
                         {"reservations": 1, "pending": 0})
        self.assertEqual(ConsumerStore(self.consumer_db).count(), 1)

    def test_sender_crash_after_remote_commit_is_safe_to_retry_after_restart(self):
        self.producer.reserve("evt1", "wolfcon", 2)
        with running_consumer(self.consumer) as url:
            with self.assertRaisesRegex(RuntimeError, "before local ack"):
                dispatch(self.producer, url, fail_after_delivery=True)
        self.assertEqual(self.producer.counts()["pending"], 1)
        self.assertEqual(self.consumer.count(), 1)
        # Simulate restarting BOTH application processes and reopening BOTH DBs.
        restarted_producer = ReservationStore(self.producer_db)
        restarted_consumer = ConsumerStore(self.consumer_db)
        with running_consumer(restarted_consumer) as url:
            self.assertEqual(dispatch(restarted_producer, url), 1)
        self.assertEqual(restarted_producer.counts()["pending"], 0)
        self.assertEqual(restarted_consumer.count(), 1)

    def test_failure_before_send_does_not_remove_pending_event(self):
        self.producer.reserve("evt1", "wolfcon", 2)
        with running_consumer(self.consumer) as url:
            with self.assertRaisesRegex(RuntimeError, "before send"):
                dispatch(self.producer, url, fail_before_send=True)
            self.assertEqual(self.consumer.count(), 0)
            self.assertEqual(self.producer.counts()["pending"], 1)
            self.assertEqual(dispatch(self.producer, url), 1)

    def test_conflicting_delivery_returns_409_and_keeps_outbox_pending(self):
        self.producer.reserve("evt1", "wolfcon", 2)
        self.consumer.accept("evt1", "othercode")
        with running_consumer(self.consumer) as url:
            with self.assertRaisesRegex(RuntimeError, "HTTP 409"):
                dispatch(self.producer, url)
        self.assertEqual(self.producer.counts()["pending"], 1)
        self.assertEqual(self.consumer.count(), 1)

    def test_http_rejects_malformed_content_and_unknown_route(self):
        with running_consumer(self.consumer) as url:
            def call(path, body, content_type="application/json"):
                request = Request(
                    url + path, data=body, method="POST",
                    headers={"Content-Type": content_type},
                )
                try:
                    with urlopen(request, timeout=2) as response:
                        return response.status
                except HTTPError as ex:
                    return ex.code

            self.assertEqual(call("/events", b'{"event_id":"x"}'), 400)
            self.assertEqual(call("/events", b"x" * 4097), 413)
            self.assertEqual(call("/events", b"not json"), 400)
            self.assertEqual(call("/events", b"{}", "text/plain"), 415)
            self.assertEqual(call("/unknown", b"{}"), 404)
            self.assertEqual(self.consumer.count(), 0)

    def test_dispatch_prevents_remote_hosts_and_redirects(self):
        self.producer.reserve("evt1", "wolfcon", 2)
        for base_url in [
            "https://127.0.0.1:9999",
            "http://example.com:9999",
            "http://localhost:9999",
            "http://127.0.0.1:9999/redirect",
            "http://user@127.0.0.1:9999",
            "http://127.0.0.1:9999?x=1",
        ]:
            with self.assertRaises(ValueError, msg=base_url):
                dispatch(self.producer, base_url)
        self.assertEqual(self.producer.counts()["pending"], 1)

    def test_http_redirect_is_not_followed_and_event_stays_pending(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        class RedirectHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.send_response(302)
                self.send_header("Location", "https://example.invalid/unsafe")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.producer.reserve("evt1", "wolfcon", 2)
            with self.assertRaisesRegex(RuntimeError, "HTTP 302"):
                dispatch(self.producer, f"http://127.0.0.1:{server.server_port}")
            self.assertEqual(self.producer.counts()["pending"], 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_duplicate_delivery_over_http_returns_200_not_second_effect(self):
        self.consumer.accept("evt1", "wolfcon")
        payload = json.dumps({"event_id": "evt1", "event_code": "wolfcon"}).encode()
        with running_consumer(self.consumer) as url:
            request = Request(
                url + "/events", data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=2) as result:
                self.assertEqual(result.status, 200)
                self.assertEqual(json.load(result)["status"], "duplicate")
        self.assertEqual(self.consumer.count(), 1)


if __name__ == "__main__":
    unittest.main()
