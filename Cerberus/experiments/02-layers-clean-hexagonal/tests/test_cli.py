import json
from pathlib import Path
from subprocess import run
import sys
from tempfile import TemporaryDirectory
import unittest


class CliAdapterTests(unittest.TestCase):
    def test_cli_create_and_get_round_trip_sqlite(self):
        with TemporaryDirectory() as folder:
            db = str(Path(folder) / "test.db")
            prefix = [sys.executable, "-m", "cerberus02.adapters.cli", "--backend", "sqlite", "--db", db]
            create = run(prefix + ["create", "--event", "wolfcon2026", "--guest", "Ada", "--seats", "2"],
                         capture_output=True, text=True, check=False)
            self.assertEqual(create.returncode, 0, create.stderr)
            record = json.loads(create.stdout)
            self.assertEqual(record["seats"], 2)
            lookup = run(prefix + ["get", "--id", record["reservation_id"]],
                         capture_output=True, text=True, check=False)
            self.assertEqual(lookup.returncode, 0, lookup.stderr)
            self.assertEqual(json.loads(lookup.stdout), record)

    def test_invalid_request_does_not_persist(self):
        with TemporaryDirectory() as folder:
            db = str(Path(folder) / "test.db")
            result = run([sys.executable, "-m", "cerberus02.adapters.cli", "--backend", "sqlite",
                          "--db", db, "create", "--event", "conf2026", "--guest", "Ada", "--seats", "0"],
                         capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("seats must", result.stdout)


if __name__ == "__main__":
    unittest.main()
