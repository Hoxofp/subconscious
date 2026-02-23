"""
Subconscious — Core Type Definitions

Tüm modüllerin paylaştığı veri modelleri.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ─── Enums ────────────────────────────────────────────────────────────────────

class NodeType(str, Enum):
    """Cognitive Graph düğüm tipleri."""
    CONCEPT = "concept"       # Soyut kavram: "demokrasi", "rekürsiyon"
    ENTITY = "entity"         # Somut varlık: "Python", "Einstein"
    EVENT = "event"           # Olay/deneyim: "2024 projesi"
    PATTERN = "pattern"       # Tekrarlayan örüntü: "her zaman timeout"
    HYPOTHESIS = "hypothesis" # Üretilen fikir: "belki X+Y çalışır"


class EdgeType(str, Enum):
    """Cognitive Graph kenar tipleri."""
    SEMANTIC = "semantic"         # Anlamsal benzerlik
    CAUSAL = "causal"             # Neden-sonuç
    TEMPORAL = "temporal"         # Zamansal yakınlık
    ANALOGICAL = "analogical"     # Yapısal benzerlik (A:B :: C:D)
    METAPHORICAL = "metaphorical" # Metaforik eşleme
    CONTRADICTS = "contradicts"   # Çelişki/karşıtlık
    ENABLES = "enables"           # X, Y'yi mümkün kılar
    PART_OF = "part_of"           # Parça-bütün
    COOCCURRENCE = "cooccurrence" # Birlikte geçen


class MemoryType(str, Enum):
    """Bellek katman tipleri."""
    WORKING = "working"       # Aktif bağlam
    EPISODIC = "episodic"     # Olaysal bellek
    SEMANTIC = "semantic"     # Anlamsal bellek
    PROCEDURAL = "procedural" # İşlemsel bellek


class CreativityStrategy(str, Enum):
    """Yaratıcılık stratejileri."""
    BISOCIATION = "bisociation"     # İki uzak kavramı birleştir
    BLENDING = "blending"           # Kavramsal karışım
    ANALOGY = "analogy"             # Analojik akıl yürütme
    LATERAL = "lateral"             # Yanal düşünme / rastgele sıçrama


# ─── Core Data Models ─────────────────────────────────────────────────────────

@dataclass
class ConceptNode:
    """Cognitive Graph düğümü."""
    name: str
    node_type: NodeType = NodeType.CONCEPT
    activation: float = 0.0
    importance: float = 0.5
    frequency: int = 1
    domain: str = ""                    # Bilgi alanı: "programming", "science"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_activated: float = field(default_factory=time.time)

    @property
    def id(self) -> str:
        return self.name.lower().strip()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "id": self.id,
            "node_type": self.node_type.value,
            "activation": self.activation,
            "importance": self.importance,
            "frequency": self.frequency,
            "domain": self.domain,
            "created_at": self.created_at,
            "last_activated": self.last_activated,
        }


@dataclass
class Association:
    """Cognitive Graph kenarı — iki kavram arası ilişki."""
    source: str
    target: str
    edge_type: EdgeType = EdgeType.SEMANTIC
    weight: float = 0.5
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    reinforced_count: int = 1

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "confidence": self.confidence,
            "reinforced_count": self.reinforced_count,
        }


@dataclass
class MemoryRecord:
    """Tek bir bellek kaydı — tüm katmanlar için ortak."""
    content: str
    memory_type: MemoryType = MemoryType.EPISODIC
    importance: float = 0.5
    domain: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""
    memory_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    embedding: Optional[list[float]] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "importance": self.importance,
            "domain": self.domain,
            "tags": self.tags,
            "source": self.source,
            "timestamp": self.timestamp,
            "access_count": self.access_count,
        }


@dataclass
class Insight:
    """Bilinçaltı sezgi — düşünme sürecinde keşfedilen bağlantı."""
    content: str
    confidence: float = 0.5
    source_concepts: list[str] = field(default_factory=list)
    insight_type: str = "association"  # association, pattern, intuition
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "confidence": self.confidence,
            "source_concepts": self.source_concepts,
            "insight_type": self.insight_type,
        }


@dataclass
class CreativeSpark:
    """Yaratıcılık motorundan çıkan bir fikir."""
    idea: str
    strategy: CreativityStrategy
    source_a: str = ""       # İlk kaynak kavram
    source_b: str = ""       # İkinci kaynak kavram
    novelty: float = 0.5     # Ne kadar "yeni" (0=banal, 1=çığır açan)
    relevance: float = 0.5   # Bağlama uygunluk
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "idea": self.idea,
            "strategy": self.strategy.value,
            "source_a": self.source_a,
            "source_b": self.source_b,
            "novelty": self.novelty,
            "relevance": self.relevance,
        }


@dataclass
class ThinkResult:
    """mind.think() çıktısı — zenginleştirilmiş düşünce sonucu."""
    response: str
    associations: list[Association] = field(default_factory=list)
    insights: list[Insight] = field(default_factory=list)
    creative_sparks: list[CreativeSpark] = field(default_factory=list)
    activated_concepts: dict[str, float] = field(default_factory=dict)
    recalled_memories: list[MemoryRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "response": self.response,
            "associations": [a.to_dict() for a in self.associations],
            "insights": [i.to_dict() for i in self.insights],
            "creative_sparks": [c.to_dict() for c in self.creative_sparks],
            "activated_concepts": self.activated_concepts,
            "recalled_memories": [m.to_dict() for m in self.recalled_memories],
        }


@dataclass
class DreamReport:
    """Arka plan rüya işlemcisinin raporu."""
    new_connections: int = 0
    patterns_found: int = 0
    memories_consolidated: int = 0
    memories_pruned: int = 0
    hypotheses_generated: list[str] = field(default_factory=list)
    dream_thoughts: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "new_connections": self.new_connections,
            "patterns_found": self.patterns_found,
            "memories_consolidated": self.memories_consolidated,
            "memories_pruned": self.memories_pruned,
            "hypotheses_generated": self.hypotheses_generated,
            "dream_thoughts": self.dream_thoughts,
            "duration_seconds": self.duration_seconds,
        }
