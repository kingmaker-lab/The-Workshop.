"""Loopback-only integration tests for ARES TCP Foundation v0.1."""
import re
import select
import signal
import socket
import subprocess
import unittest
from pathlib import Path

BINARY = Path(__file__).resolve().parents[1] / "build" / "ares-tcp"


class TestTCPFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = subprocess.Popen(
            [str(BINARY), "--port", "0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        ready, _, _ = select.select([cls.server.stdout], [], [], 4)
        if not ready:
            cls.server.kill()
            cls.server.communicate(timeout=2)
            raise RuntimeError("ARES did not announce readiness")
        startup = cls.server.stdout.readline()
        match = re.fullmatch(r"ARES TCP v0\.1 listening on 127\.0\.0\.1:(\d+)\n", startup)
        if not match:
            cls.server.kill()
            cls.server.communicate(timeout=2)
            raise RuntimeError(f"unexpected startup message: {startup!r}")
        cls.port = int(match.group(1))

    @classmethod
    def tearDownClass(cls):
        cls.server.send_signal(signal.SIGTERM)
        try:
            cls.server.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.communicate(timeout=2)
            raise
        if cls.server.returncode != 0:
            raise AssertionError(f"server exit was {cls.server.returncode}")

    def exchange(self, chunks, shutdown=False):
        with socket.create_connection(("127.0.0.1", self.port), timeout=2) as sock:
            sock.settimeout(2)
            for chunk in chunks:
                sock.sendall(chunk)
            if shutdown:
                sock.shutdown(socket.SHUT_WR)
            response = bytearray()
            while True:
                data = sock.recv(4096)
                if not data:
                    return bytes(response)
                response.extend(data)

    def test_basic_echo(self):
        self.assertEqual(self.exchange([b"Hello ARES!\n"]), b"ARES/0.1 ECHO: Hello ARES!\n")

    def test_fragmented_tcp_stream(self):
        self.assertEqual(self.exchange([b"Hel", b"lo", b"\n"]), b"ARES/0.1 ECHO: Hello\n")

    def test_empty_line(self):
        self.assertEqual(self.exchange([b"\n"]), b"ARES/0.1 ECHO: \n")

    def test_512_bytes_allowed(self):
        self.assertEqual(self.exchange([b"a" * 512 + b"\n"]), b"ARES/0.1 ECHO: " + b"a" * 512 + b"\n")

    def test_rejects_longer_lines(self):
        self.assertEqual(self.exchange([b"b" * 513 + b"\n"]), b"ERR line too long\n")

    def test_nonprintable_rejected(self):
        self.assertEqual(self.exchange([b"abc\x00def\n"]), b"ERR printable ASCII only\n")

    def test_partial_line_and_half_close(self):
        self.assertEqual(self.exchange([b"unfinished"], shutdown=True), b"ERR expected newline\n")

    def test_multiple_clients_sequentially(self):
        for word in (b"one", b"two", b"three"):
            self.assertEqual(self.exchange([word + b"\n"]), b"ARES/0.1 ECHO: " + word + b"\n")


if __name__ == "__main__":
    unittest.main()
