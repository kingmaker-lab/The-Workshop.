"""ARGUS v0.3 streaming ingestion regression and hostile-input tests."""
import json
import os
import io
from contextlib import redirect_stderr, redirect_stdout
import tempfile
import unittest
from pathlib import Path

from argus.main import PROJECT_DIR, build_engine
from argus.storage.database import Database
from argus.stream.follower import FileFollower, exclusive_stream_lock


def authentication(second: int, result: str = "failed") -> str:
    record = {
        "timestamp": f"2026-11-03T12:00:{second:02d}Z",
        "source": "linux",
        "event": "authentication",
        "src_ip": "192.0.2.10",
        "user": "alice",
        "result": result,
    }
    return json.dumps(record) + "\n"


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root = Path(self.folder.name)
        self.path = root / "events.jsonl"
        self.db_path = root / "argus.db"
        self.database = Database(self.db_path)
        self.output = []
        self.path.write_bytes(b"")

    def follower(self, *, fmt="jsonl", **options):
        engine = build_engine(
            PROJECT_DIR / "rules/default.yaml",
            {"failure_threshold": 15, "window_seconds": 30, "risk_window_seconds": 300},
        )
        return FileFollower(self.path, self.database, engine, input_format=fmt,
                            emit=self.output.append, **options)

    def append(self, data):
        with self.path.open("ab") as file:
            file.write(data if isinstance(data, bytes) else data.encode("utf-8"))

    def test_partial_line_waits_and_restart_does_not_replay(self):
        follow = self.follower()
        self.append(authentication(0)[:-1])
        self.assertEqual(follow.poll(), (0, 0, 0))
        self.assertIsNone(self.database.stream_checkpoint(str(self.path)))
        self.append("\n")
        self.assertEqual(follow.poll(), (1, 0, 0))
        checkpoint = self.database.stream_checkpoint(str(self.path))
        self.assertEqual(checkpoint[2], self.path.stat().st_size)
        self.assertEqual(self.follower().poll(), (0, 0, 0))
        self.assertEqual(len(self.database.timeline()), 1)

    def test_bounded_batches_cross_threshold_without_duplicate_alerts(self):
        follow = self.follower(batch_size=3)
        self.append("".join(authentication(i) for i in range(16)))
        totals = [follow.poll() for _ in range(6)]
        self.assertEqual(sum(p for p, a, s in totals), 16)
        self.assertEqual(sum(a for p, a, s in totals), 1)
        self.assertEqual(len(self.output), 1)
        self.assertEqual(follow.poll(), (0, 0, 0))
        self.assertEqual(self.follower().poll(), (0, 0, 0))
        self.assertEqual(len(self.database.list_alerts()), 1)

    def test_invalid_json_is_skipped_without_echoing_user_content(self):
        follow = self.follower()
        self.append(b'{"very_private":"secret-to-not-log"\n')
        self.append(authentication(1))
        self.assertEqual(follow.poll(), (1, 0, 1))
        self.assertEqual(len(self.database.timeline()), 1)

    def test_oversized_line_stops_without_advancing_offset(self):
        follow = self.follower(max_line_bytes=1024)
        self.append("X" * 1024 + "\n")
        with self.assertRaisesRegex(ValueError, "max_line_bytes"):
            follow.poll()
        self.assertIsNone(self.database.stream_checkpoint(str(self.path)))
        self.path.write_text(authentication(1), encoding="utf-8")
        self.assertEqual(follow.poll(), (1, 0, 0))

    def test_from_end_is_only_applied_before_first_checkpoint(self):
        self.append(authentication(0))
        follow = self.follower(from_end=True)
        self.assertEqual(follow.poll(), (0, 0, 0))
        self.assertEqual(self.database.stream_checkpoint(str(self.path))[2],
                         self.path.stat().st_size)
        self.append(authentication(1))
        self.assertEqual(follow.poll(), (1, 0, 0))
        self.assertEqual(self.follower(from_end=True).poll(), (0, 0, 0))

    def test_rename_rotation_and_copytruncate_increment_generation(self):
        follow = self.follower()
        self.append(authentication(0))
        self.assertEqual(follow.poll(), (1, 0, 0))
        first = self.database.stream_checkpoint(str(self.path))
        rotated = self.path.with_name("events.jsonl.1")
        self.path.rename(rotated)
        self.path.write_text(authentication(1), encoding="utf-8")
        self.assertEqual(follow.poll(), (1, 0, 0))
        second = self.database.stream_checkpoint(str(self.path))
        self.assertNotEqual(first[1], second[1])
        self.assertEqual(second[3], first[3] + 1)
        # Observe truncation while the original inode is still in use.
        self.path.write_bytes(b"")
        self.assertEqual(follow.poll(), (0, 0, 0))
        third = self.database.stream_checkpoint(str(self.path))
        self.assertEqual(third[3], second[3] + 1)
        self.append(authentication(2))
        self.assertEqual(follow.poll(), (1, 0, 0))
        self.assertEqual(len(self.database.timeline()), 3)

    def test_transaction_rejects_stale_checkpoint_and_rolls_back(self):
        follow = self.follower()
        self.append(authentication(0))
        self.assertEqual(follow.poll(), (1, 0, 0))
        checkpoint = self.database.stream_checkpoint(str(self.path))
        with self.assertRaisesRegex(ValueError, "checkpoint modified"):
            self.database.commit_stream_line(str(self.path), None,
                                             (checkpoint[0], checkpoint[1], 0, 0))
        self.assertEqual(self.database.stream_checkpoint(str(self.path)), checkpoint)

    def test_symlink_and_fifo_are_not_consumed(self):
        outside = self.path.with_name("outside.jsonl")
        outside.write_text(authentication(0), encoding="utf-8")
        self.path.unlink()
        self.path.symlink_to(outside)
        with self.assertRaises(OSError):
            self.follower().poll()
        self.path.unlink()
        if hasattr(os, "mkfifo"):
            os.mkfifo(self.path)
            with self.assertRaisesRegex(ValueError, "regular file"):
                self.follower().poll()

    def test_network_zeek_adapter_is_available_in_stream_mode(self):
        record = {"ts": 1793707200, "id.orig_h": "192.0.2.33",
                  "id.resp_h": "198.51.100.10", "orig_bytes": 128}
        self.append(json.dumps(record) + "\n")
        self.assertEqual(self.follower(fmt="network").poll(), (1, 0, 0))
        timeline = self.database.timeline()
        self.assertEqual(timeline[0]["event"], "network_connection")
        self.assertEqual(timeline[0]["orig_bytes"], 128)

    def test_writer_lock_is_nonblocking_and_exclusive(self):
        with exclusive_stream_lock(str(self.db_path)):
            with self.assertRaisesRegex(ValueError, "already holds the lock"):
                with exclusive_stream_lock(str(self.db_path)):
                    pass

    def test_cli_watch_honors_total_line_budget(self):
        from argus.main import watch

        self.append("".join(authentication(i) for i in range(6)))
        stdout = io.StringIO()
        for _ in range(3):
            with redirect_stdout(stdout):
                watch(
                    self.path, "jsonl", self.database,
                    PROJECT_DIR / "rules/default.yaml",
                    {"failure_threshold": 15, "window_seconds": 30, "risk_window_seconds": 300},
                    {}, once=True, poll_interval=.1, batch_size=20,
                    max_line_bytes=65536, max_lines=2, from_end=False,
                )
        self.assertEqual(len(self.database.timeline()), 6)
        self.assertEqual(stdout.getvalue().count('"processed": 2'), 3)

    def test_cli_rejects_unsafe_watch_budgets(self):
        from argus.main import watch

        with self.assertRaises(ValueError):
            watch(self.path, "jsonl", self.database,
                  PROJECT_DIR / "rules/default.yaml", {}, {},
                  once=True, poll_interval=.01, batch_size=2,
                  max_line_bytes=65536, max_lines=10, from_end=False)
        with self.assertRaises(ValueError):
            watch(self.path, "jsonl", self.database,
                  PROJECT_DIR / "rules/default.yaml", {}, {},
                  once=True, poll_interval=.5, batch_size=2,
                  max_line_bytes=65536, max_lines=0, from_end=False)

    def test_bad_limits_fail_closed(self):
        with self.assertRaises(ValueError):
            self.follower(max_line_bytes=100)
        with self.assertRaises(ValueError):
            self.follower(batch_size=0)
        with self.assertRaises(ValueError):
            self.follower(batch_size=1001)
        with self.assertRaises(ValueError):
            self.follower(fmt="unknown")


if __name__ == "__main__":
    unittest.main()
