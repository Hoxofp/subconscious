"""
Subconscious — Semantic Memory

Kavramsal bilgi — vektör embedding ile semantik arama.
ChromaDB destekli uzun süreli anlamsal bellek.
"""
from __future__ import annotations

import json
from typing import Optional

import chromadb

from subconscious.core.types import MemoryRecord, MemoryType
from subconscious.core.config import settings


class SemanticMemory:
    """
    Anlamsal bellek — vektör embedding tabanlı.

    Genel bilgi, kavramlar, ilişkiler. ChromaDB ile semantik arama.
    Cognitive Graph ile entegre çalışır.
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self._persist_dir = persist_dir or str(settings.DATA_DIR / "semantic")
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="semantic_memory",
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, record: MemoryRecord):
        """Anlamsal bilgiyi kaydet (embedding otomatik üretilir)."""
        self._collection.upsert(
            ids=[record.memory_id],
            documents=[record.content],
            metadatas=[{
                "memory_type": record.memory_type.value if isinstance(record.memory_type, MemoryType) else record.memory_type,
                "importance": record.importance,
                "domain": record.domain,
                "tags": json.dumps(record.tags),
                "source": record.source,
                "timestamp": record.timestamp,
                "access_count": record.access_count,
            }],
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: Optional[float] = None,
        domain: Optional[str] = None,
    ) -> list[dict]:
        """
        Semantik arama — en yakın anıları bul.

        Returns:
            [{content, memory_id, similarity, metadata}, ...]
        """
        where = {}
        if domain:
            where["domain"] = domain

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, max(self._collection.count(), 1)),
                where=where if where else None,
            )
        except Exception:
            return []

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        output = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 0
            similarity = 1 - distance  # cosine distance → similarity

            if min_similarity and similarity < min_similarity:
                continue

            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            output.append({
                "memory_id": doc_id,
                "content": results["documents"][0][i],
                "similarity": round(similarity, 4),
                "metadata": meta,
            })

        return output

    def count(self) -> int:
        return self._collection.count()

    def delete(self, memory_id: str):
        try:
            self._collection.delete(ids=[memory_id])
        except Exception:
            pass

    def clear(self):
        """Tüm anlamsal belleği temizle ve yeniden oluştur."""
        self._client.delete_collection("semantic_memory")
        self._collection = self._client.get_or_create_collection(
            name="semantic_memory",
            metadata={"hnsw:space": "cosine"},
        )
