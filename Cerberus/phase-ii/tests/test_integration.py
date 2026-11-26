import json
from pathlib import Path
import signal
import selectors
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest


class CerberusIntegration(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        self.key = root / "operator.key"
        self.db = root / "state #1.sqlite"
        self.policy = root / "policy.json"
        self.envelope = root / "change.json"
        self.cli = [sys.executable, "-m", "cerberus", "--key", str(self.key),
                    "--db", str(self.db)]
        self.run_cli("keygen")
        self.initial = self.run_cli("init")
        self.candidate = {"maintenance": True, "max_connections": 200}
        self.policy.write_text(json.dumps(self.candidate))
        self.sealed = self.run_cli("seal", "--expected", "0", self.policy)
        self.envelope.write_text(json.dumps(self.sealed))

    def run_cli(self, *args, error=None):
        run = subprocess.run([*self.cli, *args], capture_output=True, text=True, timeout=8)
        if error is not None:
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertIn(error, run.stderr)
            self.assertEqual(run.stdout, "")
            return
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def test_apply_and_restore(self):
        applied = self.run_cli("apply", self.envelope)
        self.assertEqual(applied["policy"], self.candidate)
        self.assertEqual(applied["generation"], 1)
        restored = self.run_cli("restore", "--expected", "1", "0")
        self.assertEqual(restored, {"generation": 2, "policy": self.initial["policy"],
                                    "action": "restore", "source": 0})
        self.assertEqual(self.run_cli("status"), restored)
        self.run_cli("apply", self.envelope, error="geração esperada diverge")
        self.assertEqual(self.run_cli("status"), restored)

    def test_rejects_tampered_manifest(self):
        self.sealed["policy"]["max_connections"] = 250
        self.envelope.write_text(json.dumps(self.sealed))
        self.run_cli("apply", self.envelope, error="autenticação recusada")
        self.assertEqual(self.run_cli("status"), self.initial)

    def test_rejects_untrusted_json(self):
        for raw, error in [
            (b'{"expected":0,"expected":1}', "campo JSON duplicado"),
            (b" " * 65537, "excede 64 KiB"),
            (b"\xff", "utf-8"),
            (b"{", "Expecting property name"),
        ]:
            with self.subTest(error=error):
                self.envelope.write_bytes(raw)
                self.run_cli("apply", self.envelope, error=error)
        self.policy.write_text('{"maintenance":false,"max_connections":true}')
        self.run_cli("seal", "--expected", "0", self.policy, error="tipo inválido")
        self.assertEqual(self.run_cli("status"), self.initial)

    def test_refuses_public_key_file_and_preserves_existing_key(self):
        original = self.key.read_bytes()
        self.run_cli("keygen", error="File exists")
        self.assertEqual(self.key.read_bytes(), original)
        self.key.chmod(0o644)
        self.run_cli("status", error="arquivo regular privado")

    def test_corrupted_snapshot_blocks_restore(self):
        applied = self.run_cli("apply", self.envelope)
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE revisions SET mac = ? WHERE generation = 0", ("0" * 64,))
        self.run_cli("restore", "--expected", "1", "0", error="integridade")
        self.assertEqual(self.run_cli("status"), applied)

    def test_corrupted_active_state_blocks_apply(self):
        with sqlite3.connect(self.db) as db:
            db.execute("UPDATE revisions SET mac = ? WHERE generation = 0", ("0" * 64,))
        self.run_cli("status", error="integridade")
        self.run_cli("apply", self.envelope, error="integridade")
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM revisions").fetchone(), (1,))

    def test_concurrent_writers_commit_once(self):
        command = [*self.cli, "apply", self.envelope]
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as first:
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as second:
                outputs = [process.communicate(timeout=8) for process in (first, second)]
                self.assertEqual(sorted([first.returncode, second.returncode]), [0, 1])
        self.assertIn("geração esperada diverge", b"".join(err for _, err in outputs).decode())
        self.assertEqual(self.run_cli("status")["generation"], 1)

    def test_sigkill_during_apply_rolls_back_and_allows_retry(self):
        # Interrompe o processo depois do INSERT real e antes do COMMIT.
        script = """
import os
import signal
import selectors
import socket
import sys
from cerberus import core
from cerberus.__main__ import main
record = core.record
def interrupt_after_insert(*args, **kwargs):
    record(*args, **kwargs)
    os.kill(os.getpid(), signal.SIGKILL)
core.record = interrupt_after_insert
sys.exit(main())
"""
        killed = subprocess.run([sys.executable, "-c", script, *self.cli[3:],
                                 "apply", self.envelope], timeout=8)
        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.assertEqual(self.run_cli("status"), self.initial)
        self.assertEqual(self.run_cli("apply", self.envelope)["generation"], 1)

    def test_lock_timeout_allows_retry(self):
        with sqlite3.connect(self.db) as db:
            db.execute("BEGIN IMMEDIATE")
            self.run_cli("apply", self.envelope, error="database is locked")
        self.assertEqual(self.run_cli("status"), self.initial)
        self.assertEqual(self.run_cli("apply", self.envelope)["generation"], 1)

    def test_live_service_enforces_and_restores_policy(self):
        with subprocess.Popen([*self.cli, "serve", "--port", "0"], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE) as server:
            try:
                with selectors.DefaultSelector() as waiting:
                    waiting.register(server.stdout, selectors.EVENT_READ)
                    self.assertTrue(waiting.select(5), "serviço não iniciou")
                endpoint = json.loads(server.stdout.readline())
                address = (endpoint["host"], endpoint["port"])
                self.assertEqual(address[0], "127.0.0.1")

                def change(expected, policy):
                    self.policy.write_text(json.dumps(policy))
                    signed = self.run_cli("seal", "--expected", str(expected), self.policy)
                    self.envelope.write_text(json.dumps(signed))
                    return self.run_cli("apply", self.envelope)

                def admission(expected):
                    with socket.create_connection(address, timeout=4) as client:
                        with client.makefile("rb") as stream:
                            self.assertEqual(json.loads(stream.readline()), expected)

                change(0, {"maintenance": False, "max_connections": 1})
                with socket.create_connection(address, timeout=4) as held:
                    with held.makefile("rb") as stream:
                        self.assertEqual(json.loads(stream.readline()),
                                         {"status": 200, "generation": 1})
                        admission({"status": 429, "reason": "capacity", "generation": 1})
                        held.sendall(b"PING\n")
                        self.assertEqual(json.loads(stream.readline()),
                                         {"status": 200, "response": "PONG"})

                change(1, {"maintenance": True, "max_connections": 1})
                admission({"status": 503, "reason": "maintenance", "generation": 2})
                self.run_cli("restore", "--expected", "2", "0")
                admission({"status": 200, "generation": 3})

                with sqlite3.connect(self.db) as db:
                    db.execute("UPDATE revisions SET mac = ? WHERE generation = 3", ("0" * 64,))
                admission({"status": 503, "reason": "policy_unavailable"})
            finally:
                server.terminate()
                server.communicate(timeout=5)
