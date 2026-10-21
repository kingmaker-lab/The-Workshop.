"""HEART_002: persistent conversational history, separate from event telemetry."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ConversationStore:
    VALID_ROLES = frozenset({"system", "user", "assistant", "tool"})

    def __init__(self, path: str | Path = "data/heart.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=10)
        self.connection.execute("PRAGMA busy_timeout=10000")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS conversations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "conversation_id INTEGER NOT NULL REFERENCES conversations(id), "
            "role TEXT NOT NULL CHECK(role IN ('system','user','assistant','tool')), "
            "content TEXT NOT NULL, "
            "created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')))"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_conversation "
            "ON messages(conversation_id, id)"
        )
        self.connection.commit()

    def create_conversation(self) -> int:
        with self.connection:
            cursor = self.connection.execute("INSERT INTO conversations DEFAULT VALUES")
        return int(cursor.lastrowid)

    def add_message(self, conversation_id: int, role: str, content: str) -> int:
        if role not in self.VALID_ROLES:
            raise ValueError("Invalid message role")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Message must be nonempty text")
        if not isinstance(conversation_id, int) or conversation_id <= 0:
            raise ValueError("Invalid conversation ID")
        if self.connection.execute("SELECT 1 FROM conversations WHERE id=?", (conversation_id,)).fetchone() is None:
            raise ValueError("Conversation does not exist")
        with self.connection:
            cursor = self.connection.execute(
                "INSERT INTO messages(conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
        return int(cursor.lastrowid)

    def recent(self, conversation_id: int, limit: int = 20) -> list[dict[str, Any]]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        rows = self.connection.execute(
            "SELECT id, role, content, created_at FROM ("
            " SELECT id, role, content, created_at FROM messages "
            " WHERE conversation_id=? ORDER BY id DESC LIMIT ?"
            ") ORDER BY id ASC",
            (conversation_id, limit),
        ).fetchall()
        return [
            {"id": row[0], "role": row[1], "content": row[2], "created_at": row[3]}
            for row in rows
        ]

    def search(self, conversation_id: int, term: str, limit: int = 20) -> list[dict[str, Any]]:
        """Literal substring search; safe from SQL wildcards and SQL injection."""
        if not term or not 1 <= limit <= 1000:
            raise ValueError("Invalid search arguments")
        rows = self.connection.execute(
            "SELECT id, role, content, created_at FROM messages "
            "WHERE conversation_id=? AND instr(lower(content), lower(?)) > 0 "
            "ORDER BY id DESC LIMIT ?",
            (conversation_id, term, limit),
        ).fetchall()
        return [
            {"id": row[0], "role": row[1], "content": row[2], "created_at": row[3]}
            for row in rows
        ]

    def close(self) -> None:
        self.connection.close()
