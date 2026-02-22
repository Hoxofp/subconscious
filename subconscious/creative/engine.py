"""
Subconscious — Creative Engine

İnsan yaratıcılığını simüle eden 4 strateji:
  1. Bisociation (Koestler) — iki uzak çerçeveyi birleştir
  2. Conceptual Blending (Fauconnier & Turner) — kavramsal karışım
  3. Analogical Reasoning (Structure Mapping) — analoji ile transfer
  4. Lateral Thinking (de Bono) — rastgele sıçrama ile yeni bakış açısı
"""
from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

from subconscious.core.types import CreativeSpark, CreativityStrategy, EdgeType

if TYPE_CHECKING:
    from subconscious.graph.cognitive import CognitiveGraph
    from subconscious.adapters.base import LLMAdapter


class CreativeEngine:
    """
    🎨 Yaratıcılık Motoru

    Cognitive Graph'taki uzak kavramları birleştirerek yeni fikirler üretir.
    LLM adapter varsa, fikirleri doğal dilde zenginleştirir.
    LLM olmadan da çalışır (sadece graf tabanlı basit çıktılar).
    """

    def __init__(self, graph: CognitiveGraph, adapter: Optional[LLMAdapter] = None):
        self._graph = graph
        self._adapter = adapter

    def spark(
        self,
        context: str = "",
        strategy: Optional[CreativityStrategy] = None,
        n: int = 1,
    ) -> list[CreativeSpark]:
        """
        Yaratıcı kıvılcım üret.

        Args:
            context: Mevcut bağlam veya konu
            strategy: Belirli bir strateji seç (None = otomatik)
            n: Kaç fikir üretilsin

        Returns:
            [CreativeSpark, ...]
        """
        if strategy:
            strategies = [strategy] * n
        else:
            strategies = random.choices(
                list(CreativityStrategy), k=n
            )

        sparks = []
        for strat in strategies:
            if strat == CreativityStrategy.BISOCIATION:
                spark = self._bisociate(context)
            elif strat == CreativityStrategy.BLENDING:
                spark = self._blend(context)
            elif strat == CreativityStrategy.ANALOGY:
                spark = self._analogize(context)
            elif strat == CreativityStrategy.LATERAL:
                spark = self._lateral_jump(context)
            else:
                spark = self._lateral_jump(context)

            if spark:
                sparks.append(spark)

        return sparks

    def bisociate(self, concept_a: str, concept_b: str) -> CreativeSpark:
        """İki belirli kavramı birleştir (Koestler Bisociation)."""
        return self._bisociate_pair(concept_a, concept_b)

    def blend(self, space_a: str, space_b: str) -> CreativeSpark:
        """İki kavramsal uzayı karıştır."""
        return self._blend_pair(space_a, space_b)

    def analogize(self, source: str, target: str) -> CreativeSpark:
        """Kaynak alan → hedef alan analojisi."""
        return self._analogize_pair(source, target)

    def lateral_jump(self, topic: str) -> CreativeSpark:
        """Konudan rastgele uzak bir kavrama sıçra."""
        return self._lateral_jump(topic)

    # ─── Internal Strategies ──────────────────────────────────────────────────

    def _bisociate(self, context: str) -> Optional[CreativeSpark]:
        """Graftan iki uzak kavram seç ve bisociation yap."""
        distant = self._graph.find_distant_pairs(limit=5)
        if not distant:
            # Graf yeterince zengin değil — rastgele iki kavram seç
            nodes = list(self._graph._graph.nodes)
            if len(nodes) < 2:
                return self._create_spark_without_graph(context, CreativityStrategy.BISOCIATION)
            pair = random.sample(nodes, 2)
            return self._bisociate_pair(pair[0], pair[1])

        # En uzak çifti seç (biraz rastgelelik ekle)
        pair = random.choice(distant[:3])
        return self._bisociate_pair(pair[0], pair[1])

    def _bisociate_pair(self, a: str, b: str) -> CreativeSpark:
        """İki kavram arası bisociation."""
        if self._adapter:
            prompt = (
                f"İki farklı kavram arasında yaratıcı bir bağlantı kur:\n"
                f"Kavram A: {a}\n"
                f"Kavram B: {b}\n\n"
                f"Bu iki kavramın beklenmedik bir ortak noktasını bul ve "
                f"bu bağlantıdan yola çıkarak özgün bir fikir üret. "
                f"Kısa ve öz yaz (1-2 cümle)."
            )
            idea = self._adapter.generate(prompt, temperature=0.9)
        else:
            idea = f"[{a}] ve [{b}] arasında keşfedilmemiş bir bağlantı olabilir."

        return CreativeSpark(
            idea=idea,
            strategy=CreativityStrategy.BISOCIATION,
            source_a=a,
            source_b=b,
            novelty=0.8,
        )

    def _blend(self, context: str) -> Optional[CreativeSpark]:
        """Bağlamla ilgili iki kavramı blend et."""
        concepts = self._extract_related_pair(context)
        if not concepts:
            return self._create_spark_without_graph(context, CreativityStrategy.BLENDING)
        return self._blend_pair(concepts[0], concepts[1])

    def _blend_pair(self, a: str, b: str) -> CreativeSpark:
        """Kavramsal karışım."""
        if self._adapter:
            prompt = (
                f"Kavramsal karışım (Conceptual Blending):\n"
                f"Uzay A: {a}\n"
                f"Uzay B: {b}\n\n"
                f"Bu iki kavramsal uzayı birleştirerek yeni bir 'blend' oluştur. "
                f"Her ikisinden yapısal özellikler alarak tamamen yeni bir kavram üret. "
                f"Kısa ve öz yaz (1-2 cümle)."
            )
            idea = self._adapter.generate(prompt, temperature=0.85)
        else:
            idea = f"[{a}] + [{b}] karışımı → yeni bir kavram potansiyeli."

        return CreativeSpark(
            idea=idea,
            strategy=CreativityStrategy.BLENDING,
            source_a=a,
            source_b=b,
            novelty=0.7,
        )

    def _analogize(self, context: str) -> Optional[CreativeSpark]:
        """Bağlamla ilgili analoji üret."""
        concepts = self._extract_related_pair(context)
        if not concepts:
            return self._create_spark_without_graph(context, CreativityStrategy.ANALOGY)
        return self._analogize_pair(concepts[0], concepts[1])

    def _analogize_pair(self, source: str, target: str) -> CreativeSpark:
        """Yapısal analoji."""
        if self._adapter:
            prompt = (
                f"Analojik akıl yürütme:\n"
                f"Kaynak alan: {source}\n"
                f"Hedef alan: {target}\n\n"
                f"Kaynak alanındaki yapısal ilişkileri hedef alana transfer et. "
                f"'{source}' nasıl çalışıyorsa, '{target}' da benzer şekilde düşünülebilir. "
                f"Kısa ve öz yaz (1-2 cümle)."
            )
            idea = self._adapter.generate(prompt, temperature=0.8)
        else:
            idea = f"{source} : X = {target} : ? → yapısal transfer potansiyeli."

        return CreativeSpark(
            idea=idea,
            strategy=CreativityStrategy.ANALOGY,
            source_a=source,
            source_b=target,
            novelty=0.65,
        )

    def _lateral_jump(self, context: str) -> CreativeSpark:
        """Yanal düşünme — rastgele kavram enjeksiyonu."""
        nodes = list(self._graph._graph.nodes)
        if not nodes:
            return self._create_spark_without_graph(context, CreativityStrategy.LATERAL)

        # Rastgele yürüyüşle uzak bir kavrama sıçra
        path = self._graph.random_walk(steps=4, prefer_distant=True)
        distant = path[-1] if path else random.choice(nodes)

        if self._adapter:
            prompt = (
                f"Yanal düşünme (Lateral Thinking):\n"
                f"Mevcut konu: {context or 'genel'}\n"
                f"Rastgele enjekte edilen kavram: {distant}\n\n"
                f"Bu iki tamamen ilgisiz şey arasında zorlanarak bir bağlantı kur. "
                f"Mevcut konuya '{distant}' perspektifinden bak. "
                f"Kısa ve öz yaz (1-2 cümle)."
            )
            idea = self._adapter.generate(prompt, temperature=0.95)
        else:
            idea = f"Ya [{context or 'konuya'}] [{distant}] perspektifinden baksaydık?"

        return CreativeSpark(
            idea=idea,
            strategy=CreativityStrategy.LATERAL,
            source_a=context,
            source_b=distant,
            novelty=0.9,
        )

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _extract_related_pair(self, context: str) -> list[str] | None:
        """Bağlamla ilgili iki kavram bul."""
        nodes = list(self._graph._graph.nodes)
        if len(nodes) < 2:
            return None

        # Bağlamda geçen kavramları bul
        matches = [n for n in nodes if n in context.lower()]
        if len(matches) >= 2:
            return matches[:2]

        # Yoksa en aktif iki kavramı seç
        active = self._graph.get_most_active(5)
        if len(active) >= 2:
            return [active[0].name, active[1].name]

        return random.sample(nodes, min(2, len(nodes))) if len(nodes) >= 2 else None

    def _create_spark_without_graph(
        self, context: str, strategy: CreativityStrategy
    ) -> CreativeSpark:
        """Graf yetersizken LLM ile doğrudan yaratıcı fikir üret."""
        if self._adapter:
            prompt = (
                f"Yaratıcı düşünme — strateji: {strategy.value}\n"
                f"Konu: {context or 'genel'}\n\n"
                f"Bu konuyla ilgili özgün ve beklenmedik bir fikir üret. "
                f"Sıra dışı düşün, farklı alanlardan ilham al. "
                f"Kısa ve öz yaz (1-2 cümle)."
            )
            idea = self._adapter.generate(prompt, temperature=0.9)
        else:
            idea = f"[{context or 'konu'}] hakkında henüz yeterli bağlantı yok, daha fazla bilgi gerekli."

        return CreativeSpark(
            idea=idea,
            strategy=strategy,
            source_a=context,
            novelty=0.5,
        )
