"""Black-box validation of the stdin inspector (no network, no HTTP server)."""
import subprocess
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "build" / "ares-http-inspect"


class ParserCLITests(unittest.TestCase):
    def run_case(self, request: bytes):
        return subprocess.run([str(BIN)], input=request, capture_output=True, timeout=3)

    def test_valid_http11(self):
        p = self.run_case(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn(b"PARSE: COMPLETE", p.stdout)
        self.assertIn(b"TARGET: /health", p.stdout)

    def test_malformed_line(self):
        p = self.run_case(b"GET / HTTP/2.0\r\nHost: localhost\r\n\r\n")
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"BAD_REQUEST", p.stderr)

    def test_partial_request(self):
        p = self.run_case(b"GET / HTTP/1.1\r\nHost: localhost\r\n")
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"incomplete", p.stderr)

    def test_pipeline_rejected(self):
        request = (b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
                   b"GET /next HTTP/1.1\r\nHost: localhost\r\n\r\n")
        p = self.run_case(request)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"extra bytes", p.stderr)

    def test_content_length_rejected(self):
        p = self.run_case(b"POST / HTTP/1.1\r\nHost: localhost\r\nContent-Length: 3\r\n\r\nabc")
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"UNSUPPORTED_BODY", p.stderr)


if __name__ == "__main__":
    unittest.main()
