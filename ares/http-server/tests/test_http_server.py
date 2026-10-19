"""Real-socket integration tests. Bind is loopback-only and uses an ephemeral port."""
import re
import select
import signal
import socket
import subprocess
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "build" / "ares"


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proc = subprocess.Popen([str(BIN), "--port", "0"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        ready, _, _ = select.select([cls.proc.stdout], [], [], 4)
        if not ready:
            cls.proc.kill()
            cls.proc.communicate(timeout=2)
            raise RuntimeError("ARES never announced readiness")
        line = cls.proc.stdout.readline()
        match = re.fullmatch(r"ARES v0\.3 listening on http://127\.0\.0\.1:(\d+)\n", line)
        if not match:
            cls.proc.kill()
            cls.proc.communicate(timeout=2)
            raise RuntimeError(f"unexpected start: {line!r}")
        cls.port = int(match.group(1))

    @classmethod
    def tearDownClass(cls):
        cls.proc.send_signal(signal.SIGTERM)
        try:
            _, err = cls.proc.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
            cls.proc.communicate(timeout=2)
            raise
        if cls.proc.returncode != 0:
            raise AssertionError(f"server exited with {cls.proc.returncode}: {err}")

    def request(self, *chunks):
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as sock:
            sock.settimeout(4)
            for chunk in chunks:
                sock.sendall(chunk)
            sock.shutdown(socket.SHUT_WR)
            data = bytearray()
            while True:
                buf = sock.recv(4096)
                if not buf:
                    return bytes(data)
                data.extend(buf)

    def parse(self, *chunks):
        raw = self.request(*chunks)
        self.assertIn(b"\r\n\r\n", raw)
        head, body = raw.split(b"\r\n\r\n", 1)
        lines = head.decode("ascii").split("\r\n")
        headers = dict(line.split(": ", 1) for line in lines[1:])
        return lines[0], headers, body

    def test_get_root(self):
        line, headers, body = self.parse(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertIn(b"ARES v0.3", body)
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertEqual(headers["Connection"], "close")
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertIn("GMT", headers["Date"])

    def test_health_json(self):
        line, headers, body = self.parse(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertTrue(headers["Content-Type"].startswith("application/json"))
        self.assertIn(b'"status":"ok"', body)

    def test_about_and_http10(self):
        line, _, body = self.parse(b"GET /about HTTP/1.0\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertIn(b"Parser", body)

    def test_fragmented_request(self):
        line, _, body = self.parse(b"GET /he", b"alth HTTP/1.1\r", b"\nHost: local", b"host\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertIn(b'"status":"ok"', body)

    def test_head_no_body_but_correct_length(self):
        _, get_headers, get_body = self.parse(b"GET /health HTTP/1.1\r\nHost: x\r\n\r\n")
        line, headers, body = self.parse(b"HEAD /health HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(body, b"")
        self.assertEqual(headers["Content-Length"], str(len(get_body)))
        self.assertEqual(get_headers["Content-Length"], headers["Content-Length"])

    def test_missing_route_no_reflection(self):
        line, headers, body = self.parse(b"GET /%3Cscript%3E HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")
        self.assertNotIn(b"script", body)
        self.assertEqual(headers["Content-Type"], "text/plain; charset=utf-8")

    def test_unknown_method(self):
        line, headers, body = self.parse(b"POST / HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 405 Method Not Allowed")
        self.assertEqual(headers["Allow"], "GET, HEAD")
        self.assertIn(b"405", body)

    def test_http11_host_required(self):
        line, _, _ = self.parse(b"GET / HTTP/1.1\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 400 Bad Request")

    def test_host_duplicate(self):
        line, _, _ = self.parse(b"GET / HTTP/1.1\r\nHost: x\r\nHost: x\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 400 Bad Request")

    def test_chunked_rejected(self):
        line, _, _ = self.parse(b"POST / HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 501 Not Implemented")

    def test_body_framing_rejected(self):
        line, _, _ = self.parse(b"POST / HTTP/1.1\r\nHost: x\r\nContent-Length: 4\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 501 Not Implemented")

    def test_zero_length_body_allowed(self):
        line, _, _ = self.parse(b"GET / HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 200 OK")

    def test_invalid_method(self):
        line, _, _ = self.parse(b"G[T / HTTP/1.1\r\nHost: x\r\n\r\n")
        self.assertEqual(line, "HTTP/1.1 400 Bad Request")

    def test_too_many_headers(self):
        data = b"GET / HTTP/1.1\r\nHost: x\r\n" + b"X-A: x\r\n" * 32 + b"\r\n"
        line, _, _ = self.parse(data)
        self.assertEqual(line, "HTTP/1.1 431 Request Header Fields Too Large")

    def test_partial_request_eof(self):
        line, _, _ = self.parse(b"GET / HTTP/1.1\r\nHost: x\r\n")
        self.assertEqual(line, "HTTP/1.1 400 Bad Request")

    def test_server_continues_after_errors(self):
        self.test_host_duplicate()
        self.test_get_root()


if __name__ == "__main__":
    unittest.main()
