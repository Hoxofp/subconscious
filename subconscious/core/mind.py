"""
Subconscious — Main Mind Class

Ana Subconscious sınıfı. Tüm katmanları birleştirir:
  Memory + Graph + Creative + Dream → unified API

Usage:
    from subconscious import Subconscious
    from subconscious.adapters import OllamaAdapter

    mind = Subconscious(adapter=OllamaAdapter("qwen2.5:7b"))
    result = mind.think("Bu sorunu nasıl çözeriz?")
    ideas = mind.imagine("veritabanı", "ekosistem")
"""
from __future__ import annotations

import re
import time
import logging
from typing import Optional

from subconscious.core.types import (
    ThinkResult,
    Insight,
    CreativeSpark,
    MemoryRecord,
    MemoryType,
    ConceptNode,
    Association,
    EdgeType,
    NodeType,
    DreamReport,
)
from subconscious.core.config import settings
from subconscious.memory.manager import MemoryManager
from subconscious.graph.cognitive import CognitiveGraph
from subconscious.creative.engine import CreativeEngine
from subconscious.processor.dream import DreamProcessor


logger = logging.getLogger("subconscious")


# ─── Turkish / English stop words ─────────────────────────────────────────────
STOP_WORDS = frozenset({
    # Türkçe temel
    "bir", "bu", "de", "da", "ve", "ile", "için", "gibi", "ama", "çok",
    "ne", "nasıl", "mi", "mu", "mı", "var", "yok", "daha", "en", "ben",
    "sen", "biz", "siz", "onlar", "olan", "olarak", "kadar", "sonra",
    "öyle", "böyle", "şey", "şu", "her", "bazı", "tüm", "hep", "hiç",
    "ise", "ki", "çünkü", "zaten", "ayrıca", "sadece", "yani", "hatta",
    "ancak", "fakat", "veya", "hem", "ya", "ise", "peki", "evet", "hayır",
    # Türkçe fiil ekleri / sık geçen fiil formları
    "olan", "olur", "olup", "olan", "eder", "eden", "etmek", "yapmak",
    "olan", "olması", "olarak", "olduğu", "olduğunu", "olmak", "olabilir",
    "yapılır", "yapılan", "edilir", "edilen", "kullanılır", "kullanılan",
    "sağlar", "sağlayan", "içerir", "içeren", "bulunur", "bulunan",
    # Türkçe sık geçen ama anlamsız kelimeler
    "üzerine", "üzerinde", "arasında", "arasındaki", "hakkında",
    "konuşalım", "konuşmak", "konuşurken", "konuştuğumuzda",
    "oluşumu", "gelişimi", "etkisini", "etkisi", "etkiler",
    "arasında", "bağlıdır", "yapısı", "sürecinde", "süreçtir",
    "nedenle", "yüzünden", "dolayı", "karşı", "tarafından",
    "örneğin", "mesela", "özellikle", "genellikle", "oldukça",
    "birçok", "birden", "fazla", "büyük", "küçük", "yeni", "eski",
    # İngilizce
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "it", "this", "that", "i",
    "you", "he", "she", "we", "they", "me", "my", "your", "his", "her",
    "not", "but", "or", "and", "if", "so", "no", "yes", "also", "just",
    "like", "how", "what", "when", "where", "which", "who", "about",
    "into", "through", "during", "before", "after", "above", "below",
    "between", "each", "other", "some", "such", "than", "too", "very",
    "use", "using", "used", "make", "made", "because", "while",
})


class Subconscious:
    """
    🧠 AI Subconscious — Düşünce Altyapısı

    Herhangi bir LLM'e takılabilen bilişsel middleware.
    Bilgi bağlama, yaratıcı düşünme ve arka plan işleme yeteneği ekler.

    Public API:
        mind.think(message)   → Bilinçaltı zenginleştirme ile düşün
        mind.learn(content)   → Bilgi öğren ve grafa entegre et
        mind.recall(query)    → Çok katmanlı bellek arama
        mind.imagine(a, b)    → Yaratıcı fikir üretimi
        mind.dream()          → Manuel rüya döngüsü
    """

    def __init__(
        self,
        adapter=None,
        data_dir: Optional[str] = None,
    ):
        """
        Args:
            adapter: LLM adapter (OllamaAdapter, OpenAIAdapter, vb.) veya None
            data_dir: Veri dizini (varsayılan: ./mind_data)
        """
        self.adapter = adapter
        data = data_dir or str(settings.DATA_DIR)

        # Core components
        self.memory = MemoryManager(data_dir=data)
        self.graph = CognitiveGraph(persist_path=f"{data}/cognitive_graph.json")
        self.creative = CreativeEngine(graph=self.graph, adapter=adapter)
        self.dream_processor = DreamProcessor(
            memory=self.memory,
            graph=self.graph,
            creative=self.creative,
        )

        # Conversation state
        self._conversation: list[dict[str, str]] = []

    # ─── Core API ─────────────────────────────────────────────────────────────

    def think(
        self,
        message: str,
        include_creative: bool = True,
        n_creative: int = 2,
    ) -> ThinkResult:
        """
        🧠 Ana düşünme fonksiyonu.

        1. Bellekten ilgili bilgileri çek
        2. Graf üzerinde çağrışım aktive et
        3. LLM ile zenginleştirilmiş yanıt üret
        4. Yeni bilgileri belleğe ve grafa kaydet
        5. Yaratıcı kıvılcımlar üret

        Args:
            message: Kullanıcı mesajı veya düşünülecek konu
            include_creative: Yaratıcı fikirler de üretilsin mi
            n_creative: Kaç yaratıcı fikir üretilsin

        Returns:
            ThinkResult — zenginleştirilmiş düşünce sonucu
        """
        # 1. Kavram çıkarma
        concepts = self._extract_concepts(message)

        # 2. Bellek arama
        recall_results = self.memory.recall(message, n_results=5)
        recalled = []
        for layer_items in recall_results.values():
            for item in layer_items:
                recalled.append(MemoryRecord(
                    content=item.get("content", str(item)),
                    memory_type=MemoryType.EPISODIC,
                    importance=item.get("importance", item.get("similarity", 0.5)),
                ))

        # 3. Çağrışım aktivasyonu
        activated_concepts: dict[str, float] = {}
        for concept in concepts:
            activated = self.graph.activate(concept, strength=0.8, depth=2)
            activated_concepts.update(activated)

        # 4. Kavramları grafa ekle ve bağla
        for concept in concepts:
            self.graph.add_concept(concept, node_type=NodeType.CONCEPT)
        if len(concepts) > 1:
            self.graph.connect_cooccurrence(concepts)

        # 5. LLM ile yanıt üret (adapter varsa)
        response = ""
        insights: list[Insight] = []

        if self.adapter:
            # Bağlam hazırla
            context = self._build_context(message, recall_results, activated_concepts)

            # System prompt
            system = (
                "Sen derin düşünce yeteneğine sahip bir bilinçaltı AI'sın. "
                "Kullanıcıya kısa, öz ve doğru yanıtlar ver. Gerçek bilgi sun, genel tekrardan kaçın. "
                "Farklı disiplinler arası bağlantılar kur (biyoloji↔bilgisayar, psikoloji↔matematik vb). "
                "Her yanıtında:"
                "1) Konunun özünü açıkla (kısa, net)"
                "2) Beklenmedik bir bağlantı kur (başka bir alandan)"
                "3) Somut bir örnek ver"
                "Asla genel, tekrarlayan, boş cümleler kurma. Her cümle bilgi taşımalı."
            )

            # Konuşma geçmişi
            messages = [{"role": "system", "content": system}]
            for msg in self._conversation[-6:]:
                messages.append(msg)
            messages.append({"role": "user", "content": context})

            response = self.adapter.chat(messages, temperature=0.7)

            # Yanıttan sezgiler çıkar
            insights = self._extract_insights(response, concepts)
        else:
            # LLM yokken sadece bilişsel operasyonlar
            response = self._build_summary(recall_results, activated_concepts, concepts)

        # 6. Konuşmayı kaydet
        self._conversation.append({"role": "user", "content": message})
        self._conversation.append({"role": "assistant", "content": response})

        # 7. Belleğe kaydet
        self.memory.remember(
            content=message,
            memory_type=MemoryType.EPISODIC,
            importance=0.5,
            source="user",
            tags=concepts[:5],
        )
        self.memory.remember(
            content=response[:500],
            memory_type=MemoryType.EPISODIC,
            importance=0.4,
            source="assistant",
        )

        # 8. Yaratıcı kıvılcımlar
        sparks = []
        if include_creative and len(self.graph._graph.nodes) >= 2:
            sparks = self.creative.spark(context=message, n=n_creative)

        # 9. Graf kaydet
        self.graph.save()

        return ThinkResult(
            response=response,
            associations=[
                Association(source=c, target=t, weight=w)
                for c in concepts[:3]
                for t, w in list(activated_concepts.items())[:5]
                if t != c.lower()
            ],
            insights=insights,
            creative_sparks=sparks,
            activated_concepts=activated_concepts,
            recalled_memories=recalled[:5],
        )

    def learn(
        self,
        content: str,
        domain: str = "",
        importance: float = 0.7,
        tags: list[str] | None = None,
    ) -> MemoryRecord:
        """
        📚 Bilgi öğren — bellek + grafa entegre et.

        Args:
            content: Öğrenilecek bilgi
            domain: Bilgi alanı ("programming", "science", "history", vb.)
            importance: Önem derecesi (0-1)
            tags: Etiketler
        """
        concepts = self._extract_concepts(content)

        # Belleğe kaydet (semantic + episodic)
        record = self.memory.remember(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            importance=importance,
            domain=domain,
            tags=tags or concepts[:5],
            source="learn",
        )

        # Kavramları grafa ekle
        for concept in concepts:
            self.graph.add_concept(
                concept,
                node_type=NodeType.CONCEPT,
                domain=domain,
                importance=importance * 0.8,
            )

        # Bağlantılar kur
        if len(concepts) > 1:
            self.graph.connect_cooccurrence(concepts, weight=0.4)

        self.graph.save()
        return record

    def recall(
        self,
        query: str,
        n_results: int = 10,
        domain: Optional[str] = None,
    ) -> list[dict]:
        """
        🔍 Çok katmanlı bellek arama.

        Tüm bellek katmanlarını (working, episodic, semantic, procedural) sorgular.
        """
        return self.memory.recall_flat(query, n_results=n_results)

    def imagine(
        self,
        concept_a: str = "",
        concept_b: str = "",
        n: int = 3,
    ) -> list[CreativeSpark]:
        """
        💡 Yaratıcı hayal gücü — farklı stratejilerle fikir üret.

        Args:
            concept_a: İlk kavram (opsiyonel)
            concept_b: İkinci kavram (opsiyonel)
            n: Kaç fikir üretilsin
        """
        if concept_a and concept_b:
            # Belirli iki kavram birleştir
            sparks = [
                self.creative.bisociate(concept_a, concept_b),
                self.creative.blend(concept_a, concept_b),
                self.creative.analogize(concept_a, concept_b),
            ]
            return sparks[:n]
        else:
            context = concept_a or concept_b or ""
            return self.creative.spark(context=context, n=n)

    def dream(self) -> DreamReport:
        """🌙 Manuel rüya döngüsü — arka plan keşif ve konsolidasyon."""
        return self.dream_processor.dream_once()

    def start_dreaming(self, interval: int = 300):
        """Arka plan rüya daemon'unu başlat."""
        self.dream_processor.start(interval=interval)

    def stop_dreaming(self):
        """Rüya daemon'unu durdur."""
        self.dream_processor.stop()

    # ─── Stats & Info ─────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Tüm sistem istatistikleri."""
        return {
            "memory": self.memory.get_stats(),
            "graph": self.graph.stats(),
            "dream": self.dream_processor.get_stats(),
            "adapter": self.adapter.model_name if self.adapter else "none",
            "conversation_length": len(self._conversation),
        }

    def reset(self):
        """Konuşma geçmişini sıfırla (bellek ve graf korunur)."""
        self._conversation.clear()
        self.memory.working.clear()

    # ─── Internal ─────────────────────────────────────────────────────────────

    def _extract_concepts(self, text: str) -> list[str]:
        """Metinden kavram çıkar (stopword filtreli + Türkçe ek temizleme)."""
        import re as _re
        # Turkish suffix patterns to strip
        _suffixes = [
            r'(ların|lerin|ları|leri|ında|inde|ınca|ince)$',
            r'(ıyla|iyle|ının|inin|ıdır|idir|ması|mesi)$',
            r'(arak|erek|ığını|iğini|ılır|ilir|ınır|inir)$',
            r'(deki|daki|teki|taki|sını|sini|ünü|unu)$',
            r'(abilir|ebilir|abilecek|ebilecek)$',
            r'(mekte|makta|mektedir|maktadır)$',
        ]
        words = _re.findall(r'\b\w{4,}\b', text.lower())
        cleaned = []
        for w in words:
            for pat in _suffixes:
                w = _re.sub(pat, '', w)
            if len(w) >= 4:
                cleaned.append(w)
        concepts = [w for w in cleaned if w not in STOP_WORDS and not w.isdigit()]
        # Deduplicate, keep order
        seen: set[str] = set()
        unique = []
        for c in concepts:
            if c not in seen:
                seen.add(c)
                unique.append(c)
        return unique[:15]

    def _build_context(
        self,
        message: str,
        recall_results: dict[str, list],
        activated: dict[str, float],
    ) -> str:
        """LLM için bağlam hazırla."""
        parts = [f"Kullanıcı mesajı: {message}\n"]

        # Bellek bağlamı
        all_memories = []
        for layer, items in recall_results.items():
            for item in items:
                content = item.get("content", str(item))
                all_memories.append(f"  [{layer}] {content[:150]}")
        if all_memories:
            parts.append("İlgili bellekler:\n" + "\n".join(all_memories[:5]))

        # Aktif kavramlar
        if activated:
            top_concepts = sorted(activated.items(), key=lambda x: x[1], reverse=True)[:8]
            concepts_text = ", ".join(f"{c} ({a:.2f})" for c, a in top_concepts)
            parts.append(f"\nAktif kavramlar: {concepts_text}")

        # Graftan komşu bilgiler
        for concept, activation in list(activated.items())[:3]:
            neighbors = self.graph.get_neighbors(concept, min_weight=0.3)
            if neighbors:
                neighbor_names = [n["target"] for n in neighbors[:5]]
                parts.append(f"    {concept} → {', '.join(neighbor_names)}")

        return "\n".join(parts)

    def _build_summary(
        self,
        recall_results: dict[str, list],
        activated: dict[str, float],
        concepts: list[str],
    ) -> str:
        """LLM olmadan özet yanıt oluştur."""
        parts = ["[Bilişsel analiz sonuçları]"]

        if concepts:
            parts.append(f"Çıkarılan kavramlar: {', '.join(concepts)}")

        if activated:
            top = sorted(activated.items(), key=lambda x: x[1], reverse=True)[:5]
            parts.append(f"Aktif ağ: {', '.join(f'{c}({a:.2f})' for c, a in top)}")

        total = sum(len(v) for v in recall_results.values())
        parts.append(f"Bellekten {total} ilgili kayıt bulundu.")

        return "\n".join(parts)

    def _extract_insights(self, response: str, concepts: list[str]) -> list[Insight]:
        """Yanıttan olası sezgiler çıkar."""
        insights = []
        # Basit heuristik: yanıtta "ilginç", "bağlantı", "belki" gibi kelimeler varsa
        markers = ["ilginç", "bağlantı", "belki", "aslında", "dikkat çekici", "interesting", "connection", "perhaps"]
        sentences = re.split(r"[.!?]\s+", response)
        for sent in sentences:
            if any(m in sent.lower() for m in markers):
                insights.append(Insight(
                    content=sent.strip(),
                    confidence=0.6,
                    source_concepts=concepts[:3],
                    insight_type="intuition",
                ))
        return insights[:3]


class SubconsciousMiddleware:
    """
    🔄 Kendi Kendine Gelişen AI Middleware

    Herhangi bir chat fonksiyonunu sarmalayıp otomatik olarak:
      1. Her mesajda bilinçaltı bağlam enjekte eder
      2. Her yanıtta otomatik öğrenir (learn)
      3. Arka planda sürekli dream cycle çalıştırır
      4. Zaman geçtikçe daha akıllı olur

    Usage:
        mind = Subconscious(adapter=OllamaAdapter("qwen2.5:7b"))
        middleware = SubconsciousMiddleware(mind)

        # Herhangi bir chat fonksiyonunu sar
        def my_chat(message: str) -> str:
            return ollama.chat(model="qwen2.5:7b", messages=[...])

        enhanced = middleware.wrap(my_chat)
        response = enhanced("Parallelism nasıl çözülür?")
        # → Bilinçaltı bağlam eklenmiş, yanıt sonrası öğrenilmiş
    """

    def __init__(self, mind: Subconscious, auto_dream: bool = True, dream_interval: int = 300):
        self.mind = mind
        self._interaction_count = 0

        if auto_dream:
            self.mind.start_dreaming(interval=dream_interval)

    def wrap(self, chat_fn):
        """
        Bir chat fonksiyonunu bilinçaltı ile sarmala.

        Args:
            chat_fn: (message: str) -> str şeklinde herhangi bir chat fonksiyonu

        Returns:
            Sarmalanmış fonksiyon — aynı imza, bilinçaltı eklendi
        """
        def enhanced(message: str) -> str:
            self._interaction_count += 1

            # 1. Bilinçaltı bağlam topla
            context = self._gather_context(message)

            # 2. Zenginleştirilmiş prompt oluştur
            enriched = self._enrich_prompt(message, context)

            # 3. Orijinal chat fonksiyonunu çağır
            response = chat_fn(enriched)

            # 4. Otomatik öğren — konuşmadan
            self._auto_learn(message, response)

            # 5. Periyodik dream tetikle (her 10 konuşmada bir)
            if self._interaction_count % 10 == 0:
                try:
                    self.mind.dream()
                except Exception:
                    pass

            return response

        return enhanced

    def _gather_context(self, message: str) -> dict:
        """Bilinçaltından ilgili bağlam topla."""
        concepts = self.mind._extract_concepts(message)

        # Bellek arama
        memories = self.mind.memory.recall(message, n_results=3)

        # Graf aktivasyonu
        activated = {}
        for concept in concepts[:5]:
            activated.update(self.mind.graph.activate(concept, strength=0.6, depth=2))

        return {
            "concepts": concepts,
            "memories": memories,
            "activated": activated,
        }

    def _enrich_prompt(self, message: str, context: dict) -> str:
        """Orijinal mesaja bilinçaltı bağlam ekle."""
        parts = [message]

        # İlgili bellekler
        all_mem = []
        for layer, items in context["memories"].items():
            for item in items:
                all_mem.append(item.get("content", str(item))[:100])
        if all_mem:
            parts.append(f"\n[Bilinçaltı bağlam: {'; '.join(all_mem[:3])}]")

        # Aktif kavramlar
        if context["activated"]:
            top = sorted(context["activated"].items(), key=lambda x: x[1], reverse=True)[:5]
            parts.append(f"[İlişkili kavramlar: {', '.join(c for c, _ in top)}]")

        return "\n".join(parts)

    def _auto_learn(self, message: str, response: str):
        """Her konuşmadan otomatik öğren."""
        # Kullanıcı mesajını öğren
        self.mind.learn(
            content=message,
            domain="conversation",
            importance=0.5,
        )

        # AI yanıtını öğren (daha düşük öncelik)
        if len(response) > 20:
            self.mind.learn(
                content=response[:300],
                domain="conversation",
                importance=0.3,
            )

    @property
    def interaction_count(self) -> int:
        return self._interaction_count

    def stats(self) -> dict:
        return {
            "interactions": self._interaction_count,
            **self.mind.stats(),
        }

