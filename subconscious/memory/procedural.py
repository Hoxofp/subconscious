"""
Subconscious — Procedural Memory

"Nasıl yapılır" bilgisi — başarılı çözüm kalıpları ve tekrarlayan eylem şablonları.
SQLite destekli.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Optional

from subconscious.core.types import MemoryRecord, MemoryType
from subconscious.core.config import settings


class ProceduralMemory:
    """
    İşlemsel bellek — başarılı pattern'lar ve çözüm şablonları.

    "Bu tür problemde şu yaklaşım işe yaradı" bilgisini tutar.
    Tekrarlanan başarılı stratejiler güçlenir (reinforcement).
    """

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or str(settings.DATA_DIR / "procedural.db")
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS procedures (
                memory_id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                pattern_type TEXT DEFAULT 'solution',
                domain TEXT DEFAULT '',
                tags TEXT DEFAULT '[]',
                success_count INTEGER DEFAULT 1,
                fail_count INTEGER DEFAULT 0,
                importance REAL DEFAULT 0.5,
                timestamp REAL NOT NULL,
                last_used REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_proc_domain
            ON procedures(domain)
        """)
        conn.commit()

    def store(self, record: MemoryRecord, pattern_type: str = "solution"):
        """Başarılı pattern'ı kaydet."""
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO procedures
               (memory_id, content, pattern_type, domain, tags, success_count,
                fail_count, importance, timestamp, last_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.memory_id,
                record.content,
                pattern_type,
                record.domain,
                json.dumps(record.tags),
                1, 0,
                record.importance,
                record.timestamp,
                record.timestamp,
            ),
        )
        conn.commit()

    def reinforce(self, memory_id: str, success: bool = True):
        """Pattern kullanıldı — başarılı veya başarısız olarak güçlendir/zayıflat."""
        conn = self._get_conn()
        if success:
            conn.execute(
                """UPDATE procedures SET success_count = success_count + 1,
                   importance = MIN(1.0, importance + 0.05),
                   last_used = strftime('%s','now')
                   WHERE memory_id = ?""",
                (memory_id,),
            )
        else:
            conn.execute(
                """UPDATE procedures SET fail_count = fail_count + 1,
                   importance = MAX(0.0, importance - 0.03),
                   last_used = strftime('%s','now')
                   WHERE memory_id = ?""",
                (memory_id,),
            )
        conn.commit()

    def recall_by_domain(self, domain: str, limit: int = 5) -> list[MemoryRecord]:
        """Belirli bir alandaki pattern'ları getir (başarı oranına göre)."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT *, (CAST(success_count AS REAL) / MAX(success_count + fail_count, 1)) as success_rate
               FROM procedures WHERE domain = ?
               ORDER BY success_rate DESC, importance DESC LIMIT ?""",
            (domain, limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def recall_best(self, limit: int = 10) -> list[MemoryRecord]:
        """En başarılı pattern'ları getir."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT * FROM procedures
               ORDER BY importance DESC, success_count DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def search_content(self, query: str, limit: int = 5) -> list[MemoryRecord]:
        """İçerikte arama."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM procedures WHERE content LIKE ? ORDER BY importance DESC LIMIT ?",
            (f"%{query}%", limit),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def count(self) -> int:
        conn = self._get_conn()
        return conn.execute("SELECT COUNT(*) FROM procedures").fetchone()[0]

    def clear(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM procedures")
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
            memory_type=MemoryType.PROCEDURAL,
            importance=row["importance"],
            domain=row["domain"],
            tags=tags,
            source=f"success:{row['success_count']} fail:{row['fail_count']}",
            timestamp=row["timestamp"],
            access_count=row["success_count"],
        )
