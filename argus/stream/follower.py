"""ARGUS v0.3: bounded polling follower for trusted, local rotating log files.

Not a network collector. Checkpoints are transactional in the SQLite database,
and each complete line receives a deterministic source-offset event ID.
Correlation and anomaly baselines are intentionally volatile across restarts.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import stat
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

from argus.collectors.network import adapt_network_record
from argus.collectors.syslog import parse_syslog_line
from argus.core.correlator import CorrelationEngine
from argus.core.normalizer import normalize_event
from argus.models.alert import Alert
from argus.storage.database import Database


@contextmanager
def exclusive_stream_lock(database_path: str) -> Iterator[None]:
    """Prevent competing watchers sharing this local database."""
    if database_path == ":memory:":
        raise ValueError("stream watcher requires a persistent SQLite database")
    lock_path = os.path.abspath(database_path) + ".stream.lock"
    flags = os.O_CREAT | os.O_RDWR | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(lock_path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("stream lock must be a regular file")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("another ARGUS stream watcher already holds the lock") from error
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


class FileFollower:
    """Read completed log lines with bounded memory and atomic checkpoints."""

    FORMATS = {"auto", "jsonl", "syslog", "network"}

    def __init__(
        self,
        path: str | Path,
        database: Database,
        engine: CorrelationEngine,
        *,
        input_format: str = "auto",
        max_line_bytes: int = 65536,
        batch_size: int = 200,
        from_end: bool = False,
        emit: Callable[[Alert], None] | None = None,
    ) -> None:
        if input_format not in self.FORMATS:
            raise ValueError("unsupported streaming format")
        if type(max_line_bytes) is not int or not 1024 <= max_line_bytes <= 1048576:
            raise ValueError("max_line_bytes must be in [1024, 1048576]")
        if type(batch_size) is not int or not 1 <= batch_size <= 1000:
            raise ValueError("batch_size must be in [1, 1000]")
        self.path = os.path.abspath(os.fspath(path))
        self.database = database
        self.engine = engine
        self.max_line_bytes = max_line_bytes
        self.batch_size = batch_size
        self.from_end = bool(from_end)
        self.emit = emit
        self.input_format = input_format
        if input_format == "auto":
            self.input_format = "syslog" if Path(self.path).suffix in (".log", ".syslog") else "jsonl"

    def _record(self, line: bytes) -> dict:
        decoded = line.decode("utf-8", errors="replace" if self.input_format == "syslog" else "strict")
        if self.input_format == "syslog":
            return parse_syslog_line(decoded)
        record = json.loads(decoded)
        if not isinstance(record, dict):
            raise ValueError("JSONL entry must be an object")
        return adapt_network_record(record) if self.input_format == "network" else record

    def poll(self) -> tuple[int, int, int]:
        """Process at most batch_size completed lines: (events, alerts, skipped)."""
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(self.path, flags)
        except FileNotFoundError:
            return 0, 0, 0
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("source must be a regular file, not a device or pipe")
            checkpoint = self.database.stream_checkpoint(self.path)
            identity = (info.st_dev, info.st_ino)
            if checkpoint is None and self.from_end:
                self.database.commit_stream_line(
                    self.path, None, (*identity, info.st_size),
                )
                return 0, 0, 0
            if checkpoint is not None and checkpoint[:2] == identity and info.st_size >= checkpoint[2]:
                offset = checkpoint[2]
            else:
                # A different inode or smaller file means rotation/truncation.
                # No checkpoint is persisted until the reset is committed.
                offset = 0
                if checkpoint is not None:
                    self.database.commit_stream_line(
                        self.path, checkpoint, (*identity, offset),
                    )
                    checkpoint = (*identity, offset)

            stream.seek(offset)
            processed = alerts = skipped = 0
            for _ in range(self.batch_size):
                start = stream.tell()
                line = stream.readline(self.max_line_bytes + 1)
                if not line:
                    break
                if len(line) > self.max_line_bytes:
                    raise ValueError("log line exceeds max_line_bytes; watcher stopped without advancing offset")
                if not line.endswith(b"\n"):
                    # Wait for the rest of the line; never persist partial content.
                    break
                finish = stream.tell()
                event = alert = None
                if not line.strip():
                    skipped += 1
                else:
                    try:
                        record = self._record(line)
                        # The offset-derived ID prevents input-supplied ID collisions.
                        identity_token = f"{self.path}\0{identity[0]}\0{identity[1]}\0{start}"
                        record["id"] = "stream-" + hashlib.sha256(
                            identity_token.encode("utf-8")
                        ).hexdigest()
                        event = normalize_event(record)
                    except (UnicodeError, ValueError, TypeError, OverflowError) as error:
                        # Never print untrusted log contents to stderr.
                        print(f"ARGUS stream: discarded invalid record at offset {start}: {type(error).__name__}",
                              file=sys.stderr)
                        skipped += 1
                    else:
                        alert = self.engine.process(event)
                        processed += 1
                        if alert is not None:
                            alerts += 1
                self.database.commit_stream_line(
                    self.path, checkpoint, (*identity, finish), event, alert,
                )
                checkpoint = (*identity, finish)
                if alert is not None and self.emit is not None:
                    self.emit(alert)
            return processed, alerts, skipped
