"""CERBERUS_03: SQLite outbox + loopback HTTP demonstrator.

This is a laboratory, not a production queue: delivery is sequential and initiated
manually, with no scheduler, TLS, authentication or concurrent broker workers.
"""
from contextlib import closing
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import urlsplit

_SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_MAX_BODY = 4096
_NOT_GIVEN = object()


class ConflictError(ValueError):
    pass


def _validate(event_id, event_code, seats=_NOT_GIVEN):
    if not isinstance(event_id, str) or not _SAFE_ID.fullmatch(event_id):
        raise ValueError("event_id: expected 1-64 letters, digits, _ or -")
    if not isinstance(event_code, str) or not _SAFE_ID.fullmatch(event_code):
        raise ValueError("event_code: expected 1-64 letters, digits, _ or -")
    if seats is not _NOT_GIVEN and (type(seats) is not int or not 1 <= seats <= 6):
        raise ValueError("seats: expected integer 1-6")


def _open(path):
    con = sqlite3.connect(path, timeout=3.0)
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=3000")
    return con


class ReservationStore:
    """Reservation and outbox inserts share a single SQLite transaction."""

    def __init__(self, path):
        self.path = str(Path(path))
        with closing(_open(self.path)) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS reservations (
                    event_id TEXT PRIMARY KEY,
                    event_code TEXT NOT NULL,
                    seats INTEGER NOT NULL CHECK (seats BETWEEN 1 AND 6)
                );
                CREATE TABLE IF NOT EXISTS outbox (
                    event_id TEXT PRIMARY KEY REFERENCES reservations(event_id),
                    event_code TEXT NOT NULL,
                    acknowledged INTEGER NOT NULL DEFAULT 0 CHECK (acknowledged IN (0,1))
                );
            """)

    def reserve(self, event_id, event_code, seats, *, fail_after_insert=False):
        _validate(event_id, event_code, seats)
        with closing(_open(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT event_code,seats FROM reservations WHERE event_id=?", (event_id,)
            ).fetchone()
            if row:
                if (row[0], row[1]) != (event_code, seats):
                    raise ConflictError("event_id reused with different payload")
                return False
            db.execute(
                "INSERT INTO reservations(event_id,event_code,seats) VALUES(?,?,?)",
                (event_id, event_code, seats),
            )
            if fail_after_insert:
                raise RuntimeError("simulated crash inside transaction")
            db.execute(
                "INSERT INTO outbox(event_id,event_code) VALUES(?,?)",
                (event_id, event_code),
            )
            return True

    def pending(self):
        with closing(_open(self.path)) as db:
            return [
                {"event_id": event_id, "event_code": event_code}
                for event_id, event_code in db.execute(
                    "SELECT event_id,event_code FROM outbox "
                    "WHERE acknowledged=0 ORDER BY event_id"
                ).fetchall()
            ]

    def acknowledge(self, event_id):
        with closing(_open(self.path)) as db, db:
            db.execute(
                "UPDATE outbox SET acknowledged=1 WHERE event_id=?", (event_id,)
            )

    def counts(self):
        with closing(_open(self.path)) as db:
            return {
                "reservations": db.execute("SELECT count(*) FROM reservations").fetchone()[0],
                "pending": db.execute(
                    "SELECT count(*) FROM outbox WHERE acknowledged=0"
                ).fetchone()[0],
            }


class ConsumerStore:
    """A distinct SQLite database deduplicates remote side effects by event_id."""

    def __init__(self, path):
        self.path = str(Path(path))
        with closing(_open(self.path)) as db, db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS notifications ("
                "event_id TEXT PRIMARY KEY, event_code TEXT NOT NULL)"
            )

    def accept(self, event_id, event_code):
        _validate(event_id, event_code)
        with closing(_open(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT event_code FROM notifications WHERE event_id=?", (event_id,)
            ).fetchone()
            if row:
                if row[0] != event_code:
                    raise ConflictError("event_id reused with different event_code")
                return False
            db.execute(
                "INSERT INTO notifications(event_id,event_code) VALUES(?,?)",
                (event_id, event_code),
            )
            return True

    def count(self):
        with closing(_open(self.path)) as db:
            return db.execute("SELECT count(*) FROM notifications").fetchone()[0]


class ConsumerHandler(BaseHTTPRequestHandler):
    """Loopback-only HTTP receiver. No CORS or public network exposure."""

    def _reply(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/events":
            return self._reply(404, {"error": "not found"})
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self._reply(415, {"error": "application/json required"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._reply(400, {"error": "invalid content length"})
        if not 0 < length <= _MAX_BODY:
            return self._reply(413, {"error": "payload size must be 1..4096 bytes"})
        try:
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or set(payload) != {"event_id", "event_code"}:
                raise ValueError("two expected fields required")
            created = self.server.sink.accept(payload["event_id"], payload["event_code"])
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            code = 409 if isinstance(exc, ConflictError) else 400
            return self._reply(code, {"error": str(exc)})
        return self._reply(201 if created else 200, {"status": "created" if created else "duplicate"})

    def do_GET(self):
        return self._reply(405, {"error": "POST only"})

    def do_HEAD(self):
        return self._reply(405, {"error": "POST only"})

    def log_message(self, *_args):
        pass  # Avoid echoing events to logs; tests remain deterministic.


def consumer_server(sink):
    """Caller must invoke shutdown() and server_close()."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), ConsumerHandler)
    server.daemon_threads = True
    server.sink = sink
    return server


def dispatch(store, base_url, *, fail_before_send=False, fail_after_delivery=False, timeout=2.0):
    """Sequential at-least-once attempt; ack only after HTTP success.

    fail_after_delivery simulates the sender dying *after* the consumer has
    committed but *before* the sender has persisted its acknowledgement.
    """
    url = urlsplit(base_url)
    try:
        port = url.port
    except ValueError as exc:
        raise ValueError("invalid loopback port") from exc
    if (url.scheme != "http" or url.hostname != "127.0.0.1" or port is None
            or url.username or url.password or url.query or url.fragment
            or url.path not in ("", "/")):
        raise ValueError("only http://127.0.0.1:<port> is permitted")
    delivered = 0
    for event in store.pending():
        if fail_before_send:
            raise RuntimeError("simulated failure before send")
        body = json.dumps(event).encode("utf-8")
        # Direct socket to loopback: HTTP redirects and proxy environment cannot
        # change the destination to a remote host.
        conn = HTTPConnection("127.0.0.1", port, timeout=timeout)
        try:
            conn.request("POST", "/events", body=body,
                         headers={"Content-Type": "application/json"})
            result = conn.getresponse()
            result.read(_MAX_BODY)
            if result.status not in (200, 201):
                raise RuntimeError(f"HTTP {result.status} not acknowledged")
        finally:
            conn.close()
        if fail_after_delivery:
            raise RuntimeError("simulated failure after remote commit before local ack")
        store.acknowledge(event["event_id"])
        delivered += 1
    return delivered
