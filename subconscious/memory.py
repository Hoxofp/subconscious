"""
Subconscious — Memory Store

İki katmanlı bellek sistemi:
  - STM (Short-Term Memory):  SQLite → son konuşmalar, geçici çağrışımlar
  - LTM (Long-Term Memory):   ChromaDB → vektör embedding ile semantik bellek
"""
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional

import chromadb

from config import settings


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Memory:
    """Tek bir anı/bellek birimi."""
    content: str
    memory_type: str  # "conversation", "association", "intuition"
    emotional_weight: float = 0.5   # 0.0 (nötr) → 1.0 (çok güçlü)
    tags: list[str] = field(default_factory=list)
    source: str = ""                # hangi konuşmadan geldi
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0           # kaç kez hatırlandı

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tags"] = json.dumps(d["tags"])
        return d


# ─── Short-Term Memory (SQLite) ──────────────────────────────────────────────

class ShortTermMemory:
    """
    SQLite tabanlı kısa süreli bellek.
    Son konuşmaları ve geçici çağrışımları tutar.
    Kapasite aşılınca en eski kayıtlar LTM'ye taşınır.
    """

    def __init__(self):
        self.db_path = settings.DB_PATH
        self._init_db()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id    TEXT PRIMARY KEY,
                    content      TEXT NOT NULL,
                    memory_type  TEXT NOT NULL,
                    emotional_weight REAL DEFAULT 0.5,
                    tags         TEXT DEFAULT '[]',
                    source       TEXT DEFAULT '',
                    timestamp    REAL NOT NULL,
                    access_count INTEGER DEFAULT 0
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def store(self, memory: Memory):
        """Yeni anı kaydet."""
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memories
                   (memory_id, content, memory_type, emotional_weight,
                    tags, source, timestamp, access_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (memory.memory_id, memory.content, memory.memory_type,
                 memory.emotional_weight, json.dumps(memory.tags),
                 memory.source, memory.timestamp, memory.access_count)
            )

    def recall_recent(self, limit: int = 10) -> list[Memory]:
        """En son anıları getir."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def recall_by_type(self, memory_type: str, limit: int = 10) -> list[Memory]:
        """Belirli tipteki anıları getir."""
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM memories WHERE memory_type = ? ORDER BY timestamp DESC LIMIT ?",
                (memory_type, limit)
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def get_overflow(self) -> list[Memory]:
        """Kapasiteyi aşan en eski anıları döndür (LTM'ye taşınmak üzere)."""
        count = self.count()
        if count <= settings.STM_CAPACITY:
            return []
        overflow = count - settings.STM_CAPACITY
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY timestamp ASC LIMIT ?",
                (overflow,)
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def delete(self, memory_id: str):
        with self._conn() as conn:
            conn.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))

    def clear(self):
        with self._conn() as conn:
            conn.execute("DELETE FROM memories")

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            memory_id=row["memory_id"],
            content=row["content"],
            memory_type=row["memory_type"],
            emotional_weight=row["emotional_weight"],
            tags=json.loads(row["tags"]),
            source=row["source"],
            timestamp=row["timestamp"],
            access_count=row["access_count"],
        )


# ─── Long-Term Memory (ChromaDB) ─────────────────────────────────────────────

class LongTermMemory:
    """
    ChromaDB tabanlı uzun süreli bellek.
    Vektör embedding'ler ile semantik arama yapabilir.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
        self.collection = self.client.get_or_create_collection(
            name="subconscious_ltm",
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, memory: Memory):
        """Anıyı embedding ile kaydet."""
        self.collection.upsert(
            ids=[memory.memory_id],
            documents=[memory.content],
            metadatas=[{
                "memory_type": memory.memory_type,
                "emotional_weight": memory.emotional_weight,
                "tags": json.dumps(memory.tags),
                "source": memory.source,
                "timestamp": memory.timestamp,
                "access_count": memory.access_count,
            }],
        )

    def search(self, query: str, n_results: int = 5,
               min_similarity: Optional[float] = None) -> list[dict]:
        """
        Semantik arama — verilen sorguya en yakın anıları bul.
        Döndürülen her sonuç: {content, memory_id, similarity, metadata}
        """
        if self.collection.count() == 0:
            return []

        n = min(n_results, self.collection.count())
        results = self.collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )

        matches = []
        for i in range(len(results["ids"][0])):
            # ChromaDB cosine distance → similarity
            similarity = 1.0 - results["distances"][0][i]
            if min_similarity and similarity < min_similarity:
                continue
            matches.append({
                "memory_id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "similarity": round(similarity, 4),
                "metadata": results["metadatas"][0][i],
            })
        return matches

    def count(self) -> int:
        return self.collection.count()

    def clear(self):
        """Tüm uzun süreli belleği sil."""
        self.client.delete_collection("subconscious_ltm")
        self.collection = self.client.get_or_create_collection(
            name="subconscious_ltm",
            metadata={"hnsw:space": "cosine"},
        )


# ─── Unified Memory Manager ──────────────────────────────────────────────────

class MemoryManager:
    """
    STM + LTM birleşik bellek yöneticisi.
    Otomatik taşma (overflow) yönetimi:
      STM dolunca eski anılar LTM'ye taşınır.
    """

    def __init__(self):
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()

    def remember(self, content: str, memory_type: str = "conversation",
                 emotional_weight: float = 0.5, tags: list[str] = None,
                 source: str = "") -> Memory:
        """Yeni bir anı oluştur ve STM'ye kaydet."""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            emotional_weight=emotional_weight,
            tags=tags or [],
            source=source,
        )
        self.stm.store(memory)
        # LTM'ye de kaydet (semantik arama için)
        self.ltm.store(memory)
        # Taşma kontrolü
        self._consolidate()
        return memory

    def recall(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantik arama ile ilgili anıları hatırla."""
        return self.ltm.search(
            query,
            n_results=n_results,
            min_similarity=settings.ASSOCIATION_THRESHOLD,
        )

    def recent(self, limit: int = 10) -> list[Memory]:
        """En son anıları getir."""
        return self.stm.recall_recent(limit)

    def _consolidate(self):
        """STM taşma kontrolü — eski anıları STM'den sil (LTM'de zaten var)."""
        overflow = self.stm.get_overflow()
        for mem in overflow:
            self.stm.delete(mem.memory_id)

    def stats(self) -> dict:
        return {
            "stm_count": self.stm.count(),
            "ltm_count": self.ltm.count(),
            "stm_capacity": settings.STM_CAPACITY,
        }
