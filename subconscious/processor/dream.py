"""
Subconscious — Background Dream Processor

Arka planda çalışan düşünce süreci:
  - Bellek konsolidasyonu (working → episodic → semantic)
  - Örüntü keşfi (pattern mining)
  - Akıllı unutma (importance-based forgetting)
  - Hipotez üretimi (yaratıcı keşif)
"""
from __future__ import annotations

import threading
import time
import logging
from typing import Optional, TYPE_CHECKING

from subconscious.core.types import DreamReport, MemoryType, MemoryRecord

if TYPE_CHECKING:
    from subconscious.memory.manager import MemoryManager
    from subconscious.graph.cognitive import CognitiveGraph
    from subconscious.creative.engine import CreativeEngine


logger = logging.getLogger("subconscious.dream")


class DreamProcessor:
    """
    🌙 Arka Plan Rüya İşlemcisi

    Periyodik olarak:
      1. Bellek konsolidasyonu
      2. Grafı optimize et
      3. Yeni bağlantılar keşfet
      4. Düşük önemli bilgileri unut
    """

    def __init__(
        self,
        memory: MemoryManager,
        graph: CognitiveGraph,
        creative: Optional[CreativeEngine] = None,
    ):
        self.memory = memory
        self.graph = graph
        self.creative = creative
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._dreams: list[DreamReport] = []
        self._interval = 300

    def dream_once(self) -> DreamReport:
        """Tek bir rüya döngüsü çalıştır."""
        start = time.time()
        report = DreamReport()

        # 1. Bellek konsolidasyonu
        report.memories_consolidated = self._consolidate()

        # 2. Aktivasyon sönümlemesi
        self.graph.decay_all()

        # 3. Graf kaydet
        self.graph.save()

        # 4. Akıllı unutma (pruning)
        report.memories_pruned = self._forget()

        # 5. Yeni bağlantı keşfi (random walk)
        report.new_connections = self._discover_connections()

        # 6. Hipotez üretimi (yaratıcılık motoru varsa)
        if self.creative:
            sparks = self.creative.spark(n=2)
            report.hypotheses_generated = [s.idea for s in sparks]

        # 7. Cluster tespiti
        clusters = self.graph.find_clusters()
        report.patterns_found = len(clusters)

        report.duration_seconds = time.time() - start
        report.dream_thoughts.append(
            f"Konsolide: {report.memories_consolidated}, "
            f"Budanan: {report.memories_pruned}, "
            f"Yeni bağlantı: {report.new_connections}, "
            f"Kümeler: {report.patterns_found}"
        )

        self._dreams.append(report)
        logger.info("Dream cycle completed in %.2fs", report.duration_seconds)
        return report

    def start(self, interval: int = 300):
        """Arka plan rüya daemon'unu başlat."""
        if self._running:
            return
        self._interval = interval
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Dream processor started (interval=%ds)", interval)

    def stop(self):
        """Rüya daemon'unu durdur."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Dream processor stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def history(self) -> list[DreamReport]:
        return list(self._dreams)

    def get_stats(self) -> dict:
        return {
            "running": self._running,
            "interval": self._interval,
            "total_dreams": len(self._dreams),
            "last_dream": self._dreams[-1].to_dict() if self._dreams else None,
        }

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _loop(self):
        while self._running:
            try:
                self.dream_once()
            except Exception as e:
                logger.error("Dream cycle error: %s", e)
            time.sleep(self._interval)

    def _consolidate(self) -> int:
        """Working memory taşanlarını episodic'e, önemlileri semantic'e taşı."""
        count = 0
        recent = self.memory.episodic.recall_recent(20)
        for record in recent:
            if record.importance >= 0.6:
                self.memory.semantic.store(record)
                count += 1
        return count

    def _forget(self) -> int:
        """Düşük önemli, az erişilen bellek kayıtlarını buda."""
        pruned = self.memory.episodic.prune(keep=500)
        return pruned

    def _discover_connections(self) -> int:
        """Random walk ile yeni bağlantılar keşfet."""
        new = 0
        for _ in range(3):
            path = self.graph.random_walk(steps=4, prefer_distant=True)
            if len(path) >= 2:
                # Yolun başı ve sonu arasında yeni bağlantı oluştur
                start, end = path[0], path[-1]
                if start != end:
                    from subconscious.core.types import EdgeType
                    self.graph.connect(
                        start, end,
                        edge_type=EdgeType.SEMANTIC,
                        weight=0.2,
                        confidence=0.3,
                    )
                    new += 1
        return new
