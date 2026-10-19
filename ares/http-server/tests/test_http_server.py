"""Real-socket integration tests. Bind is loopback-only and uses an ephemeral port."""
import re
import os
import tempfile
import select
import signal
import socket
import subprocess
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
BIN = BASE / "build" / "ares"


class HttpServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.external = tempfile.TemporaryDirectory(prefix="ares-outside-")
        cls.fixture = tempfile.TemporaryDirectory(prefix="ares-fixture-", dir=BASE / "public")
        cls.urlprefix = "/static/" + Path(cls.fixture.name).name + "/"
        cls.content_dir = Path(cls.fixture.name)
        (Path(cls.external.name) / "private.txt").write_text("TOP SECRET NEVER SERVE", encoding="utf-8")
        (cls.content_dir / "hello.txt").write_bytes(b"Hello from v0.4!\n")
        (cls.content_dir / "data.json").write_bytes(b'{"ok": true}\n')
        (cls.content_dir / "pixel.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (cls.content_dir / "huge.txt").write_bytes(b"X" * (256 * 1024 + 1))
        (cls.content_dir / "edge.txt").write_bytes(b"Y" * (256 * 1024))
        (cls.content_dir / "custom.xyz").write_bytes(b"unsupported")
        (cls.content_dir / ".hidden.txt").write_bytes(b"hidden")
        (cls.content_dir / "outside.txt").symlink_to(Path(cls.external.name) / "private.txt")
        (cls.content_dir / "nested-link").symlink_to(Path(cls.external.name), target_is_directory=True)
        (cls.content_dir / "nested").mkdir()
        (cls.content_dir / "nested" / "file.css").write_bytes(b"h1{color:tomato}")
        os.mkfifo(cls.content_dir / "blocking.txt")
        cls.proc = subprocess.Popen([str(BIN), "--port", "0"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=BASE)
        ready, _, _ = select.select([cls.proc.stdout], [], [], 4)
        if not ready:
            cls.proc.kill()
            cls.proc.communicate(timeout=2)
            raise RuntimeError("ARES never announced readiness")
        line = cls.proc.stdout.readline()
        match = re.fullmatch(r"ARES v0\.4 listening on http://127\.0\.0\.1:(\d+)\n", line)
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
        cls.fixture.cleanup()
        cls.external.cleanup()
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
        self.assertIn(b"ARES v0.4", body)
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

    def static_request(self, target, method="GET"):
        request = (method + " " + target + " HTTP/1.1\r\nHost: localhost\r\n\r\n").encode("ascii")
        return self.parse(request)

    def test_static_index_html(self):
        line, headers, body = self.static_request("/static/index.html")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(headers["Content-Type"], "text/html; charset=utf-8")
        self.assertEqual(headers["Content-Length"], str(len(body)))
        self.assertIn(b"ARES v0.4", body)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_css_in_nested_directory(self):
        line, headers, body = self.static_request(self.urlprefix + "nested/file.css")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(headers["Content-Type"], "text/css; charset=utf-8")
        self.assertEqual(body, b"h1{color:tomato}")

    def test_json_mime_type(self):
        line, headers, body = self.static_request(self.urlprefix + "data.json")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(body, b'{"ok": true}\n')

    def test_png_binary_delivery(self):
        line, headers, body = self.static_request(self.urlprefix + "pixel.png")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(headers["Content-Type"], "image/png")
        self.assertEqual(body, b"\x89PNG\r\n\x1a\n")

    def test_static_head_content_length(self):
        get_line, get_headers, data = self.static_request(self.urlprefix + "hello.txt")
        line, headers, body = self.static_request(self.urlprefix + "hello.txt", "HEAD")
        self.assertEqual(get_line, "HTTP/1.1 200 OK")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(body, b"")
        self.assertEqual(headers["Content-Length"], str(len(data)))
        self.assertEqual(headers["Content-Length"], get_headers["Content-Length"])

    def test_missing_file(self):
        line, _, body = self.static_request(self.urlprefix + "nope.txt")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")
        self.assertEqual(body, b"404 Not Found\n")

    def test_dotdot_and_nested_dotdot(self):
        for path in ("/static/../robots.txt", "/static/assets/../../secret.txt",
                     self.urlprefix + "../hello.txt", self.urlprefix + "nested/../hello.txt"):
            with self.subTest(path=path):
                line, _, body = self.static_request(path)
                self.assertEqual(line, "HTTP/1.1 404 Not Found")
                self.assertNotIn(b"SECRET", body)

    def test_percent_encoded_traversal_and_backslash(self):
        for path in ("/static/%2e%2e/private.txt", "/static/%2fetc%2fpasswd",
                     "/static/%5c..%5cprivate.txt", "/static/..\\secret.txt",
                     "/static//assets/site.css", "/static/index.html?x=1"):
            with self.subTest(path=path):
                line, _, _ = self.static_request(path)
                self.assertEqual(line, "HTTP/1.1 404 Not Found")

    def test_hidden_file_denied(self):
        line, _, _ = self.static_request(self.urlprefix + ".hidden.txt")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")

    def test_final_symlink_cannot_escape(self):
        line, _, body = self.static_request(self.urlprefix + "outside.txt")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")
        self.assertNotIn(b"TOP SECRET", body)

    def test_intermediate_symlink_cannot_escape(self):
        line, _, body = self.static_request(self.urlprefix + "nested-link/private.txt")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")
        self.assertNotIn(b"TOP SECRET", body)

    def test_fifo_cannot_block_the_server(self):
        line, _, _ = self.static_request(self.urlprefix + "blocking.txt")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")

    def test_unknown_mime_extension(self):
        line, _, _ = self.static_request(self.urlprefix + "custom.xyz")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")

    def test_directory_is_not_served(self):
        line, _, _ = self.static_request(self.urlprefix + "nested")
        self.assertEqual(line, "HTTP/1.1 404 Not Found")

    def test_file_limit_over_256_kib(self):
        line, headers, body = self.static_request(self.urlprefix + "huge.txt")
        self.assertEqual(line, "HTTP/1.1 403 Forbidden")
        self.assertEqual(body, b"403 Forbidden\n")
        self.assertEqual(headers["Content-Length"], str(len(body)))

    def test_exact_file_limit_allowed(self):
        line, headers, body = self.static_request(self.urlprefix + "edge.txt")
        self.assertEqual(line, "HTTP/1.1 200 OK")
        self.assertEqual(len(body), 256 * 1024)
        self.assertEqual(int(headers["Content-Length"]), len(body))
        self.assertEqual(body[:5], b"YYYYY")

    def test_static_post_denied(self):
        line, headers, _ = self.static_request("/static/index.html", "POST")
        self.assertEqual(line, "HTTP/1.1 405 Method Not Allowed")
        self.assertEqual(headers["Allow"], "GET, HEAD")

    def test_server_continues_after_errors(self):
        self.test_host_duplicate()
        self.test_get_root()


if __name__ == "__main__":
    unittest.main()
