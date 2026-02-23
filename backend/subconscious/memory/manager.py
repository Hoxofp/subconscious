"""
Subconscious — Unified Memory Manager

4 katmanlı bellek sistemini koordine eder.
Working → Episodic → Semantic → Procedural akışını yönetir.
"""
from __future__ import annotations

from typing import Optional

from subconscious.core.types import MemoryRecord, MemoryType
from subconscious.core.config import settings
from subconscious.memory.working import WorkingMemory
from subconscious.memory.episodic import EpisodicMemory
from subconscious.memory.semantic import SemanticMemory
from subconscious.memory.procedural import ProceduralMemory


class MemoryManager:
    """
    4 katmanlı bellek sistemi koordinatörü.

    Bellek akışı:
      1. Input → Working Memory (7±2)
      2. Taşma → Episodic Memory (olaysal)
      3. Önemli bilgi → Semantic Memory (vektör)
      4. Başarılı pattern → Procedural Memory

    Recall: Tüm katmanları paralel sorgular, birleştirilmiş sonuç döner.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self.working = WorkingMemory(capacity=settings.WORKING_MEMORY_CAPACITY)
        self.episodic = EpisodicMemory(
            db_path=f"{data_dir}/episodic.db" if data_dir else None
        )
        self.semantic = SemanticMemory(
            persist_dir=f"{data_dir}/semantic" if data_dir else None
        )
        self.procedural = ProceduralMemory(
            db_path=f"{data_dir}/procedural.db" if data_dir else None
        )

    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        importance: float = 0.5,
        domain: str = "",
        tags: list[str] | None = None,
        source: str = "",
    ) -> MemoryRecord:
        """
        Yeni bilgiyi belleğe kaydet.

        Bilgi otomatik olarak doğru katmana yönlendirilir.
        """
        record = MemoryRecord(
            content=content,
            memory_type=memory_type,
            importance=importance,
            domain=domain,
            tags=tags or [],
            source=source,
        )

        # Working memory'ye ekle
        overflow = self.working.push({
            "content": content,
            "role": source if source in ("user", "assistant") else "system",
            "memory_id": record.memory_id,
        })

        # Taşan öğeyi episodic'e konsolide et
        if overflow:
            overflow_record = MemoryRecord(
                content=overflow.get("content", ""),
                memory_type=MemoryType.EPISODIC,
                importance=0.4,
                source="working_overflow",
            )
            self.episodic.store(overflow_record)

        # Katmana göre kaydet
        if memory_type == MemoryType.EPISODIC:
            self.episodic.store(record)
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic.store(record)
        elif memory_type == MemoryType.PROCEDURAL:
            self.procedural.store(record)
        else:
            # Default: hem episodic hem semantic
            self.episodic.store(record)

        # Önemli bilgileri semantic'e de kaydet (çapraz referans)
        if importance >= 0.6:
            self.semantic.store(record)

        return record

    def recall(
        self,
        query: str,
        n_results: int = 5,
        domain: Optional[str] = None,
    ) -> dict[str, list]:
        """
        Çok katmanlı bellek arama.

        Tüm katmanları sorgular, birleştirilmiş sonuç döndürür.

        Returns:
            {
                "working": [...],
                "episodic": [...],
                "semantic": [...],
                "procedural": [...],
            }
        """
        results: dict[str, list] = {
            "working": [],
            "episodic": [],
            "semantic": [],
            "procedural": [],
        }

        # 1. Working Memory — birebir arama
        for item in self.working.get_context():
            content = item.get("content", "")
            if query.lower() in content.lower():
                results["working"].append(item)

        # 2. Episodic — metin arama
        if domain:
            results["episodic"] = [
                r.to_dict() for r in self.episodic.recall_by_domain(domain, n_results)
            ]
        else:
            results["episodic"] = [
                r.to_dict() for r in self.episodic.search_content(query, n_results)
            ]

        # 3. Semantic — vektör benzerlik arama
        results["semantic"] = self.semantic.search(
            query, n_results=n_results, domain=domain
        )

        # 4. Procedural — pattern arama
        results["procedural"] = [
            r.to_dict() for r in self.procedural.search_content(query, n_results)
        ]

        return results

    def recall_flat(self, query: str, n_results: int = 10) -> list[dict]:
        """Tüm katmanları düz bir liste olarak döndür (importance'a göre sıralı)."""
        all_results = self.recall(query, n_results=n_results)
        flat = []
        for layer, items in all_results.items():
            for item in items:
                item["_layer"] = layer
                flat.append(item)
        # Sort by importance/similarity
        flat.sort(
            key=lambda x: x.get("importance", x.get("similarity", 0)),
            reverse=True,
        )
        return flat[:n_results]

    def get_stats(self) -> dict:
        """Bellek istatistikleri."""
        return {
            "working": {
                "size": self.working.size,
                "capacity": self.working.capacity,
                "usage": f"{self.working.size}/{self.working.capacity}",
            },
            "episodic": {"count": self.episodic.count()},
            "semantic": {"count": self.semantic.count()},
            "procedural": {"count": self.procedural.count()},
            "total": (
                self.working.size
                + self.episodic.count()
                + self.semantic.count()
                + self.procedural.count()
            ),
        }

    def clear_all(self):
        """Tüm belleği temizle."""
        self.working.clear()
        self.episodic.clear()
        self.semantic.clear()
        self.procedural.clear()
