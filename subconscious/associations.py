"""
Subconscious — Association Engine

Çağrışım motoru: kavramlar arası bağlantıları kurar, güçlendirir ve keşfeder.
Üç tip bağlantı:
  1. Semantic Similarity — embedding benzerliği
  2. Temporal Proximity — zamansal yakınlık
  3. Co-occurrence — birlikte geçme

Spreading Activation: bir kavram aktive olunca, ilişkili kavramlar da
ağırlıklarına göre aktive olur (dalga gibi yayılır).
"""
import json
import time
from dataclasses import dataclass, field
from typing import Optional

import networkx as nx

from config import settings
from subconscious.memory import MemoryManager, Memory


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Concept:
    """Bir kavram düğümü."""
    name: str
    activation: float = 0.0       # 0.0 → 1.0 aktiflik seviyesi
    base_importance: float = 0.5  # temel önem
    last_activated: float = field(default_factory=time.time)
    frequency: int = 1            # kaç kez karşılaşıldı

@dataclass
class Association:
    """İki kavram arası bağlantı."""
    source: str
    target: str
    weight: float = 0.5          # 0.0 → 1.0 bağlantı gücü
    association_type: str = "semantic"  # semantic | temporal | cooccurrence
    created_at: float = field(default_factory=time.time)
    reinforced_count: int = 1    # kaç kez güçlendirildi


# ─── Association Engine ──────────────────────────────────────────────────────

class AssociationEngine:
    """
    Çağrışım ağı motoru.

    Graf tabanlı çağrışım sistemi:
      - Düğümler = kavramlar
      - Kenarlar = çağrışım bağlantıları (ağırlıklı)
      - Spreading Activation = kavram yayılımı
    """

    def __init__(self, memory: Optional[MemoryManager] = None):
        self.graph = nx.DiGraph()
        self.memory = memory or MemoryManager()
        self._decay_rate = 0.1     # Aktivasyon azalma hızı
        self._spread_factor = 0.6  # Yayılım çarpanı
        self._reinforce_bonus = 0.1  # Güçlendirme bonusu

    # ─── Kavram Yönetimi ──────────────────────────────────────────────────

    def add_concept(self, name: str, importance: float = 0.5) -> Concept:
        """Yeni kavram ekle veya var olanı güçlendir."""
        name = name.lower().strip()
        if self.graph.has_node(name):
            data = self.graph.nodes[name]
            data["frequency"] += 1
            data["base_importance"] = min(1.0, data["base_importance"] + 0.05)
            return self._node_to_concept(name)
        else:
            concept = Concept(name=name, base_importance=importance)
            self.graph.add_node(
                name,
                activation=concept.activation,
                base_importance=concept.base_importance,
                last_activated=concept.last_activated,
                frequency=concept.frequency,
            )
            return concept

    def get_concept(self, name: str) -> Optional[Concept]:
        """Kavram getir."""
        name = name.lower().strip()
        if self.graph.has_node(name):
            return self._node_to_concept(name)
        return None

    # ─── Bağlantı Yönetimi ───────────────────────────────────────────────

    def connect(self, source: str, target: str,
                weight: float = 0.5,
                association_type: str = "semantic") -> Association:
        """
        İki kavram arasında bağlantı kur veya güçlendir.
        Çift yönlü (bidirectional) bağlantı oluşturur.
        """
        source = source.lower().strip()
        target = target.lower().strip()

        # Kavramları oluştur (yoksa)
        self.add_concept(source)
        self.add_concept(target)

        # Bağlantıyı oluştur veya güçlendir
        for s, t in [(source, target), (target, source)]:
            if self.graph.has_edge(s, t):
                edge = self.graph.edges[s, t]
                edge["weight"] = min(1.0, edge["weight"] + self._reinforce_bonus)
                edge["reinforced_count"] += 1
            else:
                self.graph.add_edge(
                    s, t,
                    weight=weight,
                    association_type=association_type,
                    created_at=time.time(),
                    reinforced_count=1,
                )

        return Association(
            source=source, target=target,
            weight=self.graph.edges[source, target]["weight"],
            association_type=association_type,
        )

    def connect_temporal(self, concepts: list[str], time_window: float = 60.0):
        """
        Aynı zaman diliminde geçen kavramları birbirine bağla (temporal proximity).
        concepts: aynı konuşmada geçen kavram listesi
        """
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                self.connect(c1, c2, weight=0.4, association_type="temporal")

    def connect_cooccurrence(self, concepts: list[str]):
        """
        Birlikte geçen kavramları bağla (co-occurrence).
        Aynı cümlede veya paragrafta geçen kavramlar.
        """
        for i, c1 in enumerate(concepts):
            for c2 in concepts[i + 1:]:
                self.connect(c1, c2, weight=0.6, association_type="cooccurrence")

    # ─── Spreading Activation ────────────────────────────────────────────

    def activate(self, concept_name: str, strength: float = 1.0,
                 depth: int = 3) -> dict[str, float]:
        """
        Spreading Activation — bir kavramı aktive et ve dalga gibi yay.

        Args:
            concept_name: Aktive edilecek kavram
            strength: Başlangıç aktivasyon gücü (0.0 → 1.0)
            depth: Kaç seviye derine yayılsın

        Returns:
            {kavram_adı: aktivasyon_seviyesi} dict'i
        """
        concept_name = concept_name.lower().strip()
        if not self.graph.has_node(concept_name):
            return {}

        # Tüm aktivasyonları sıfırla (decay uygula)
        self._decay_all()

        # BFS tarzı yayılım
        activated = {}
        queue = [(concept_name, strength)]
        visited = set()

        current_depth = 0
        next_level = []

        while queue and current_depth <= depth:
            for node, activation_strength in queue:
                if node in visited:
                    continue
                visited.add(node)

                # Aktivasyonu uygula
                new_activation = min(1.0, activation_strength)
                self.graph.nodes[node]["activation"] = new_activation
                self.graph.nodes[node]["last_activated"] = time.time()
                activated[node] = new_activation

                # Komşulara yay
                for neighbor in self.graph.successors(node):
                    if neighbor not in visited:
                        edge_weight = self.graph.edges[node, neighbor]["weight"]
                        spread_strength = activation_strength * edge_weight * self._spread_factor
                        if spread_strength > 0.05:  # Çok zayıf yayılımı kes
                            next_level.append((neighbor, spread_strength))

            queue = next_level
            next_level = []
            current_depth += 1

        return dict(sorted(activated.items(), key=lambda x: x[1], reverse=True))

    # ─── Sorgulama ────────────────────────────────────────────────────────

    def get_related(self, concept_name: str, limit: int = 10) -> list[dict]:
        """Bir kavramla ilişkili kavramları getir (ağırlığa göre sıralı)."""
        concept_name = concept_name.lower().strip()
        if not self.graph.has_node(concept_name):
            return []

        related = []
        for neighbor in self.graph.successors(concept_name):
            edge = self.graph.edges[concept_name, neighbor]
            related.append({
                "concept": neighbor,
                "weight": edge["weight"],
                "type": edge["association_type"],
                "reinforced": edge["reinforced_count"],
            })

        related.sort(key=lambda x: x["weight"], reverse=True)
        return related[:limit]

    def get_most_active(self, limit: int = 10) -> list[dict]:
        """En aktif kavramları getir."""
        nodes = []
        for name in self.graph.nodes:
            data = self.graph.nodes[name]
            nodes.append({
                "concept": name,
                "activation": data["activation"],
                "importance": data["base_importance"],
                "frequency": data["frequency"],
            })
        nodes.sort(key=lambda x: x["activation"], reverse=True)
        return nodes[:limit]

    def find_bridge_concepts(self, concept_a: str, concept_b: str) -> list[str]:
        """
        İki kavram arasındaki köprü kavramları bul.
        A ve B'yi bağlayan en kısa yoldaki ara kavramlar.
        """
        concept_a = concept_a.lower().strip()
        concept_b = concept_b.lower().strip()

        if not (self.graph.has_node(concept_a) and self.graph.has_node(concept_b)):
            return []

        try:
            path = nx.shortest_path(
                self.graph, concept_a, concept_b, weight="weight"
            )
            return path[1:-1]  # Başlangıç ve bitiş hariç ara kavramlar
        except nx.NetworkXNoPath:
            return []

    # ─── Bağlantı Keşfi ──────────────────────────────────────────────────

    def discover_hidden_connections(self, limit: int = 5) -> list[dict]:
        """
        Gizli bağlantıları keşfet — doğrudan bağlı olmayan ama
        dolaylı olarak güçlü ilişkisi olan kavram çiftlerini bul.
        """
        discoveries = []
        nodes = list(self.graph.nodes)

        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                if self.graph.has_edge(a, b):
                    continue  # Zaten bağlı
                try:
                    path_length = nx.shortest_path_length(
                        self.graph, a, b, weight="weight"
                    )
                    if 2 <= path_length <= 4:  # 2-4 adım arası
                        path = nx.shortest_path(self.graph, a, b, weight="weight")
                        # Yol üzerindeki ortalama ağırlık
                        avg_weight = sum(
                            self.graph.edges[path[j], path[j + 1]]["weight"]
                            for j in range(len(path) - 1)
                        ) / (len(path) - 1)

                        if avg_weight > 0.3:
                            discoveries.append({
                                "concept_a": a,
                                "concept_b": b,
                                "path": path,
                                "avg_weight": round(avg_weight, 3),
                                "distance": path_length,
                            })
                except nx.NetworkXNoPath:
                    continue

        discoveries.sort(key=lambda x: x["avg_weight"], reverse=True)
        return discoveries[:limit]

    # ─── İç Yardımcılar ──────────────────────────────────────────────────

    def _decay_all(self):
        """Tüm aktivasyonları zaman bazlı azalt."""
        now = time.time()
        for name in self.graph.nodes:
            data = self.graph.nodes[name]
            elapsed = now - data["last_activated"]
            decay = self._decay_rate * elapsed
            data["activation"] = max(0.0, data["activation"] - decay)

    def _node_to_concept(self, name: str) -> Concept:
        data = self.graph.nodes[name]
        return Concept(
            name=name,
            activation=data["activation"],
            base_importance=data["base_importance"],
            last_activated=data["last_activated"],
            frequency=data["frequency"],
        )

    # ─── İstatistikler ───────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "concepts": self.graph.number_of_nodes(),
            "associations": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 4) if self.graph.number_of_nodes() > 1 else 0,
            "components": nx.number_weakly_connected_components(self.graph),
        }

    def export_graph(self) -> dict:
        """Grafi JSON-serializable formata çevir."""
        nodes = []
        for name in self.graph.nodes:
            data = self.graph.nodes[name]
            nodes.append({"id": name, **data})

        edges = []
        for s, t in self.graph.edges:
            data = self.graph.edges[s, t]
            edges.append({"source": s, "target": t, **data})

        return {"nodes": nodes, "edges": edges}
