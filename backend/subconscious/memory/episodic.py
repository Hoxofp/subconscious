"""
Subconscious — Episodic Memory

"Ne oldu, ne zaman" — zaman damgalı deneyim belleği.
SQLite tabanlı, FIFO taşma yönetimli.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Optional

from subconscious.core.types import MemoryRecord, MemoryType
from subconscious.core.config import settings


class EpisodicMemory:
    """
    Olaysal bellek — konuşmalar, deneyimler, olaylar.

    SQLite destekli, thread-safe.
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or str(settings.DATA_DIR / "episodic.db")
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                memory_type TEXT DEFAULT 'episodic',
                importance REAL DEFAULT 0.5,
                domain TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT '',
                timestamp REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_timestamp
            ON episodes(timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_episodes_importance
            ON episodes(importance DESC)
        """)
        conn.commit()

    def store(self, record: MemoryRecord):
        """Olayı kaydet."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO episodes
               (memory_id, content, memory_type, importance, domain, tags, source, timestamp, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.memory_id,
                record.content,
                record.memory_type.value if isinstance(record.memory_type, MemoryType) else record.memory_type,
                record.importance,
                record.domain,
                json.dumps(record.tags),
                record.source,
                record.timestamp,
                record.access_count,
            ),
        )
        conn.commit()

    def recall_recent(self, limit: int = 10) -> list[MemoryRecord]:
        """En son olayları getir."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def recall_by_domain(self, domain: str, limit: int = 10) -> list[MemoryRecord]:
        """Belirli bir alan (domain) için olayları getir."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM episodes WHERE domain = ? ORDER BY timestamp DESC LIMIT ?",
            (domain, limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def recall_important(self, limit: int = 10, min_importance: float = 0.7) -> list[MemoryRecord]:
        """Önem derecesine göre olayları getir."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM episodes WHERE importance >= ? ORDER BY importance DESC LIMIT ?",
            (min_importance, limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def search_content(self, query: str, limit: int = 10) -> list[MemoryRecord]:
        """İçerikte metin arama."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM episodes WHERE content LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def touch(self, memory_id: str):
        """Erişim sayacını artır (hatırlanmayı güçlendir)."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE episodes SET access_count = access_count + 1 WHERE memory_id = ?",
            (memory_id,),
        )
        conn.commit()

    def delete(self, memory_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM episodes WHERE memory_id = ?", (memory_id,))
        conn.commit()

    def prune(self, keep: int = 500) -> int:
        """En düşük önemli kayıtları sil, keep kadar tut."""
        conn = self._get_conn()
        count_before = self.count()
        if count_before <= keep:
            return 0
        conn.execute(
            """DELETE FROM episodes WHERE memory_id NOT IN
               (SELECT memory_id FROM episodes ORDER BY importance DESC, timestamp DESC LIMIT ?)""",
            (keep,),
        )
        conn.commit()
        return count_before - self.count()

    def count(self) -> int:
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]

    def clear(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM episodes")
        conn.commit()

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        tags = row["tags"]
        if isinstance(tags, str):
            try:
                tags = json.loads(tags)
            except json.JSONDecodeError:
                tags = []
        return MemoryRecord(
            memory_id=row["memory_id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]) if row["memory_type"] in MemoryType.__members__.values() else MemoryType.EPISODIC,
            importance=row["importance"],
            domain=row["domain"],
            tags=tags,
            source=row["source"],
            timestamp=row["timestamp"],
            access_count=row["access_count"],
        )
