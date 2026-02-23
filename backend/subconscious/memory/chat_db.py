"""
Subconscious — Chat Session Database

Simple SQLite-backed database to persist user chat sessions and messages.
"""
import sqlite3
import time
import json
import uuid
from typing import Optional

from subconscious.core.config import settings

class ChatDB:
    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or str(settings.DATA_DIR / "chat.db")
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    meta TEXT DEFAULT '{}',
                    created_at REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at ASC)")

    # ─── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, title: str = "New Chat") -> str:
        session_id = str(uuid.uuid4())
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now)
            )
        return session_id

    def list_sessions(self, limit: int = 50) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    def update_session_title(self, session_id: str, title: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (title, time.time(), session_id))

    def touch_session(self, session_id: str):
        with self._get_conn() as conn:
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (time.time(), session_id))

    # ─── Messages ─────────────────────────────────────────────────────────────

    def add_message(self, session_id: str, role: str, content: str, meta: dict = None) -> str:
        msg_id = str(uuid.uuid4())
        now = time.time()
        meta_str = json.dumps(meta or {})
        
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO messages (id, session_id, role, content, meta, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (msg_id, session_id, role, content, meta_str, now)
            )
            conn.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))
            
        return msg_id

    def get_messages(self, session_id: str) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,)).fetchall()
        
        messages = []
        for r in rows:
            msg = dict(r)
            try:
                msg["meta"] = json.loads(msg["meta"])
            except json.JSONDecodeError:
                msg["meta"] = {}
            messages.append(msg)
        return messages
