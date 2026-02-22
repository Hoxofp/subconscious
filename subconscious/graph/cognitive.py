"""
Subconscious — Cognitive Graph v2

Çok boyutlu, çok-tipli bilgi grafiği.
Her düğüm bir kavram/varlık/olay, her kenar bir ilişki tipi.
Spreading activation + random walk + cluster yeteneği.
"""
from __future__ import annotations

import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional

import networkx as nx

from subconscious.core.types import (
    ConceptNode,
    Association,
    NodeType,
    EdgeType,
)
from subconscious.core.config import settings


class CognitiveGraph:
    """
    🧠 Bilişsel Ağ — çok tipli düğüm ve kenarlarla bilgi organizasyonu.

    Özellikler:
        - Çoklu düğüm tipleri (concept, entity, event, pattern, hypothesis)
        - Çoklu kenar tipleri (semantic, causal, analogical, metaphorical, vb.)
        - Spreading activation (yayılma aktivasyonu)
        - Random walk (yaratıcı keşif)
        - Cluster tespiti (topluluk keşfi)
        - Persistence (JSON kayıt/yükleme)
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._graph = nx.MultiDiGraph()
        self._persist_path = persist_path or str(settings.DATA_DIR / "cognitive_graph.json")
        self._load()

    # ─── Node Operations ──────────────────────────────────────────────────────

    def add_concept(
        self,
        name: str,
        node_type: NodeType = NodeType.CONCEPT,
        domain: str = "",
        importance: float = 0.5,
        metadata: dict | None = None,
    ) -> ConceptNode:
        """Kavram ekle veya güncelle."""
        node_id = name.lower().strip()

        if self._graph.has_node(node_id):
            # Güncelle: frequency artır, activation yenile
            data = self._graph.nodes[node_id]
            data["frequency"] = data.get("frequency", 1) + 1
            data["last_activated"] = time.time()
            if importance > data.get("importance", 0.5):
                data["importance"] = importance
            if domain and not data.get("domain"):
                data["domain"] = domain
        else:
            # Yeni ekle
            self._graph.add_node(
                node_id,
                name=name,
                node_type=node_type.value,
                domain=domain,
                importance=importance,
                frequency=1,
                activation=0.0,
                created_at=time.time(),
                last_activated=time.time(),
                metadata=metadata or {},
            )

        return self._node_to_concept(node_id)

    def get_concept(self, name: str) -> Optional[ConceptNode]:
        """Kavramı getir."""
        node_id = name.lower().strip()
        if not self._graph.has_node(node_id):
            return None
        return self._node_to_concept(node_id)

    def remove_concept(self, name: str):
        """Kavramı ve bağlı kenarlarını sil."""
        node_id = name.lower().strip()
        if self._graph.has_node(node_id):
            self._graph.remove_node(node_id)

    # ─── Edge Operations ──────────────────────────────────────────────────────

    def connect(
        self,
        source: str,
        target: str,
        edge_type: EdgeType = EdgeType.SEMANTIC,
        weight: float = 0.5,
        confidence: float = 1.0,
        metadata: dict | None = None,
    ) -> Association:
        """İki kavram arası bağlantı kur."""
        src = source.lower().strip()
        tgt = target.lower().strip()

        # Düğümler yoksa oluştur
        if not self._graph.has_node(src):
            self.add_concept(source)
        if not self._graph.has_node(tgt):
            self.add_concept(target)

        # Aynı tip bağlantı var mı?
        existing_key = self._find_edge(src, tgt, edge_type)
        if existing_key is not None:
            # Güçlendir
            data = self._graph.edges[src, tgt, existing_key]
            data["weight"] = min(1.0, data.get("weight", 0.5) + 0.05)
            data["reinforced_count"] = data.get("reinforced_count", 1) + 1
        else:
            # Yeni kenar
            self._graph.add_edge(
                src, tgt,
                edge_type=edge_type.value,
                weight=weight,
                confidence=confidence,
                reinforced_count=1,
                created_at=time.time(),
                metadata=metadata or {},
            )

        return Association(
            source=source,
            target=target,
            edge_type=edge_type,
            weight=weight,
            confidence=confidence,
        )

    def connect_cooccurrence(self, concepts: list[str], weight: float = 0.3):
        """Birlikte geçen kavramlar arası bağlantı kur."""
        for i, a in enumerate(concepts):
            for b in concepts[i + 1:]:
                if a.lower().strip() != b.lower().strip():
                    self.connect(a, b, EdgeType.COOCCURRENCE, weight=weight)

    def get_neighbors(
        self,
        name: str,
        edge_types: list[EdgeType] | None = None,
        min_weight: float = 0.0,
    ) -> list[dict]:
        """Bir kavramın komşularını kenar tiplerine göre getir."""
        node_id = name.lower().strip()
        if not self._graph.has_node(node_id):
            return []

        neighbors = []
        for _, target, key, data in self._graph.out_edges(node_id, keys=True, data=True):
            if edge_types and EdgeType(data["edge_type"]) not in edge_types:
                continue
            if data.get("weight", 0) < min_weight:
                continue
            neighbors.append({
                "target": target,
                "edge_type": data["edge_type"],
                "weight": data.get("weight", 0.5),
                "target_data": dict(self._graph.nodes.get(target, {})),
            })

        # Gelen kenarlar da (indegree)
        for source, _, key, data in self._graph.in_edges(node_id, keys=True, data=True):
            if edge_types and EdgeType(data["edge_type"]) not in edge_types:
                continue
            if data.get("weight", 0) < min_weight:
                continue
            neighbors.append({
                "target": source,
                "edge_type": data["edge_type"],
                "weight": data.get("weight", 0.5),
                "target_data": dict(self._graph.nodes.get(source, {})),
            })

        return neighbors

    # ─── Spreading Activation ─────────────────────────────────────────────────

    def activate(
        self,
        name: str,
        strength: float = 1.0,
        depth: int = 2,
        decay: float | None = None,
    ) -> dict[str, float]:
        """
        Yayılma aktivasyonu — bir kavramdan başlayarak ilişkili kavramları aktive et.

        Returns:
            {kavram_adı: aktivasyon_seviyesi, ...}
        """
        decay = decay or settings.ACTIVATION_DECAY
        spread = settings.SPREAD_FACTOR
        node_id = name.lower().strip()

        if not self._graph.has_node(node_id):
            return {}

        activated: dict[str, float] = {}
        queue: list[tuple[str, float, int]] = [(node_id, strength, 0)]
        visited: set[str] = set()

        while queue:
            current, current_strength, current_depth = queue.pop(0)
            if current in visited or current_depth > depth:
                continue
            visited.add(current)

            # Aktivasyonu güncelle
            old_activation = self._graph.nodes[current].get("activation", 0)
            new_activation = min(1.0, old_activation + current_strength)
            self._graph.nodes[current]["activation"] = new_activation
            self._graph.nodes[current]["last_activated"] = time.time()
            activated[current] = new_activation

            # Komşulara yay
            if current_depth < depth:
                for _, neighbor, data in self._graph.out_edges(current, data=True):
                    if neighbor not in visited:
                        edge_weight = data.get("weight", 0.5)
                        propagated = current_strength * spread * edge_weight
                        if propagated > 0.01:
                            queue.append((neighbor, propagated, current_depth + 1))

                for neighbor, _, data in self._graph.in_edges(current, data=True):
                    if neighbor not in visited:
                        edge_weight = data.get("weight", 0.5)
                        propagated = current_strength * spread * edge_weight * 0.7
                        if propagated > 0.01:
                            queue.append((neighbor, propagated, current_depth + 1))

        return activated

    def decay_all(self, rate: float | None = None):
        """Tüm aktivasyonları azalt (zaman geçişi simülasyonu)."""
        rate = rate or settings.ACTIVATION_DECAY
        for node_id in self._graph.nodes:
            current = self._graph.nodes[node_id].get("activation", 0)
            self._graph.nodes[node_id]["activation"] = max(0.0, current - rate)

    # ─── Random Walk (Yaratıcı Keşif) ────────────────────────────────────────

    def random_walk(
        self,
        start: str | None = None,
        steps: int = 5,
        prefer_distant: bool = True,
    ) -> list[str]:
        """
        Graf üzerinde rastgele yürüyüş — uzak bağlantı keşfi.

        Args:
            start: Başlangıç kavramı (None = rastgele)
            steps: Adım sayısı
            prefer_distant: True ise az kullanılan kenarlara yönel

        Returns:
            [kavram1, kavram2, ...] — yürüyüş yolu
        """
        nodes = list(self._graph.nodes)
        if not nodes:
            return []

        if start:
            current = start.lower().strip()
            if current not in self._graph:
                current = random.choice(nodes)
        else:
            current = random.choice(nodes)

        path = [current]
        for _ in range(steps):
            edges = list(self._graph.out_edges(current, data=True))
            edges += [(t, s, d) for s, t, d in self._graph.in_edges(current, data=True)]

            if not edges:
                # Çıkmaz — rastgele sıçrama
                current = random.choice(nodes)
                path.append(current)
                continue

            if prefer_distant:
                # Ağırlığı düşük (uzak) kenarları tercih et
                weights = [1.0 / max(d.get("weight", 0.5), 0.01) for _, _, d in edges]
            else:
                weights = [d.get("weight", 0.5) for _, _, d in edges]

            total = sum(weights)
            if total == 0:
                current = random.choice(nodes)
            else:
                probs = [w / total for w in weights]
                idx = random.choices(range(len(edges)), weights=probs, k=1)[0]
                _, next_node, _ = edges[idx]
                if isinstance(next_node, tuple):
                    next_node = next_node[0] if next_node else current
                current = next_node

            path.append(current)

        return path

    # ─── Discovery ────────────────────────────────────────────────────────────

    def find_distant_pairs(self, limit: int = 5) -> list[tuple[str, str, float]]:
        """
        Grafta var olan ama uzak (düşük ağırlıklı) kavram çiftlerini bul.
        Yaratıcılık motoru bunları bisociation'a besler.
        """
        simple = self._graph.to_undirected()
        if simple.number_of_nodes() < 2:
            return []

        pairs = []
        nodes = list(simple.nodes)
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                try:
                    length = nx.shortest_path_length(simple, a, b)
                    if length >= 3:  # En az 3 adım uzak
                        pairs.append((a, b, float(length)))
                except nx.NetworkXNoPath:
                    pairs.append((a, b, float("inf")))

        pairs.sort(key=lambda x: x[2], reverse=True)
        return pairs[:limit]

    def find_clusters(self) -> list[set[str]]:
        """Topluluk keşfi — birbiriyle yoğun bağlı kavram gruplarını bul."""
        simple = self._graph.to_undirected()
        if simple.number_of_nodes() == 0:
            return []
        try:
            from networkx.algorithms.community import greedy_modularity_communities
            communities = greedy_modularity_communities(simple)
            return [set(c) for c in communities]
        except Exception:
            components = list(nx.connected_components(simple))
            return [set(c) for c in components]

    def get_most_active(self, limit: int = 10) -> list[ConceptNode]:
        """En aktif kavramları döndür."""
        nodes = []
        for node_id in self._graph.nodes:
            nodes.append(self._node_to_concept(node_id))
        nodes.sort(key=lambda n: n.activation, reverse=True)
        return nodes[:limit]

    def get_most_connected(self, limit: int = 10) -> list[tuple[str, int]]:
        """En çok bağlantıya sahip kavramları döndür."""
        degree_list = [(n, self._graph.degree(n)) for n in self._graph.nodes]
        degree_list.sort(key=lambda x: x[1], reverse=True)
        return degree_list[:limit]

    # ─── Stats & Export ───────────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "nodes": self._graph.number_of_nodes(),
            "edges": self._graph.number_of_edges(),
            "density": nx.density(self._graph) if self._graph.number_of_nodes() > 1 else 0,
            "clusters": len(self.find_clusters()),
        }

    def export_graph(self) -> dict:
        """JSON-serializable graf verisi (dashboard + frontend için)."""
        nodes = []
        for node_id in self._graph.nodes:
            data = dict(self._graph.nodes[node_id])
            data.pop("metadata", None)
            nodes.append({"id": node_id, **data})

        edges = []
        for src, tgt, data in self._graph.edges(data=True):
            edge = dict(data)
            edge.pop("metadata", None)
            edges.append({"source": src, "target": tgt, **edge})

        return {"nodes": nodes, "edges": edges}

    # ─── Persistence ──────────────────────────────────────────────────────────

    def save(self):
        """Grafı JSON olarak kaydet."""
        data = nx.node_link_data(self._graph, edges="edges")
        path = Path(self._persist_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        """Grafı dosyadan yükle (varsa)."""
        path = Path(self._persist_path)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._graph = nx.node_link_graph(data, directed=True, multigraph=True, edges="edges")
            except Exception:
                self._graph = nx.MultiDiGraph()

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _find_edge(self, src: str, tgt: str, edge_type: EdgeType) -> int | None:
        """Aynı tip kenarı bul."""
        if not self._graph.has_node(src) or not self._graph.has_node(tgt):
            return None
        edges = self._graph.get_edge_data(src, tgt)
        if not edges:
            return None
        for key, data in edges.items():
            if data.get("edge_type") == edge_type.value:
                return key
        return None

    def _node_to_concept(self, node_id: str) -> ConceptNode:
        data = self._graph.nodes[node_id]
        return ConceptNode(
            name=data.get("name", node_id),
            node_type=NodeType(data.get("node_type", "concept")),
            activation=data.get("activation", 0.0),
            importance=data.get("importance", 0.5),
            frequency=data.get("frequency", 1),
            domain=data.get("domain", ""),
            created_at=data.get("created_at", 0),
            last_activated=data.get("last_activated", 0),
        )
