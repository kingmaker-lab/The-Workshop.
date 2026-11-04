import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DEFAULT = {"length": "normal", "emojis": True, "steps": False}
TTL = 90 * 86400


class Store:
    """Single-process SQLite store; no message content or model output is persisted."""

    def __init__(self, path, clock=time.time):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS preferences (
              bot TEXT, guild TEXT, user TEXT, value TEXT, enabled INTEGER, updated REAL,
              PRIMARY KEY(bot,guild,user));
            CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, expires REAL);
            CREATE TABLE IF NOT EXISTS limits (key TEXT PRIMARY KEY, value TEXT);
        """)

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def get_style(self, bot, guild, user):
        key = (bot, guild, user)
        row = self.db.execute("SELECT value,enabled,updated FROM preferences WHERE bot=? AND guild=? AND user=?", key).fetchone()
        if row and row[1] and row[2] < self.clock() - TTL:
            self.db.execute("DELETE FROM preferences WHERE bot=? AND guild=? AND user=?", key)
            row = None
        return (json.loads(row[0]) if row and row[1] else dict(DEFAULT), bool(row and row[1]))

    def set_style(self, bot, guild, user, patch, *, activate=False):
        if set(patch) - set(DEFAULT):
            raise ValueError("Unknown preference")
        if "length" in patch and patch["length"] not in ("curto", "normal", "detalhado"):
            raise ValueError("Invalid length")
        if any(k in patch and type(patch[k]) is not bool for k in ("emojis", "steps")):
            raise ValueError("Invalid boolean preference")
        row = self.db.execute("SELECT enabled FROM preferences WHERE bot=? AND guild=? AND user=?", (bot, guild, user)).fetchone()
        if row and not row[0] and not activate:
            return False
        style, _ = self.get_style(bot, guild, user)
        style.update(patch)
        self.db.execute("INSERT OR REPLACE INTO preferences VALUES (?,?,?,?,1,?)",
                        (bot, guild, user, json.dumps(style), self.clock()))
        return True

    def erase_style(self, bot, guild, user):
        # A minimal opt-out marker prevents natural feedback from silently re-enabling storage.
        self.db.execute("INSERT OR REPLACE INTO preferences VALUES (?,?,?,NULL,0,?)",
                        (bot, guild, user, self.clock()))

    def sweep(self):
        now = self.clock()
        self.db.execute("DELETE FROM preferences WHERE enabled=1 AND updated<?", (now - TTL,))
        self.db.execute("DELETE FROM events WHERE expires<?", (now,))
        for key, raw in self.db.execute("SELECT key,value FROM limits WHERE key!='budget'").fetchall():
            value = json.loads(raw)
            last = max(value, default=0) if isinstance(value, list) else value
            if last < now - 86400:
                self.db.execute("DELETE FROM limits WHERE key=?", (key,))
        self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def claim(self, event_id):
        result = self.db.execute("INSERT OR IGNORE INTO events VALUES (?,?)", (event_id, self.clock() + 86400))
        return result.rowcount == 1

    def reserve(self, guild, channel, user, casual, daily_limit):
        """Atomically reserve budget and both global-channel and user cooldowns."""
        now = self.clock()
        day = int(now // 86400)
        with self.transaction():
            def read(key, default):
                row = self.db.execute("SELECT value FROM limits WHERE key=?", (key,)).fetchone()
                return json.loads(row[0]) if row else default

            budget = read("budget", [day, 0])
            if budget[0] != day:
                budget = [day, 0]
            if budget[1] >= daily_limit:
                return False
            uk, ck = f"u:{guild}:{user}", f"c:{guild}:{channel}"
            last = read(uk, 0)
            recent = [t for t in read(ck, []) if now - t < 900]
            if now - last < 8 or (casual and (len(recent) >= 3 or (recent and now - recent[-1] < 120))):
                return False
            updates = [("budget", [day, budget[1] + 1]), (uk, now)]
            if casual:
                updates.append((ck, recent + [now]))
            for key, value in updates:
                self.db.execute("INSERT OR REPLACE INTO limits VALUES (?,?)", (key, json.dumps(value)))
            return True

    def close(self):
        self.db.close()
