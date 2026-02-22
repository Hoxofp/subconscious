"""
microsubconscious — layer.py

SubconsciousLayer: AI'ın düşünce pipeline'ına takılan bilinçaltı katmanı.

Nasıl neural network bir AI'ın "düşünmesini" sağlıyorsa,
SubconsciousLayer de AI'ın "bilinçaltından düşünmesini" sağlar.

            Normal AI:  input → [LLM] → output
    Bilinçaltılı AI:    input → [SubconsciousLayer] → enriched → [LLM] → output
                                       ↑                              ↓
                                 Thought DAG                    auto-learn
                                 Resonance
                                 Associations
"""
from microsubconscious.engine import Thought
from microsubconscious.mind import Mind


class SubconsciousLayer:
    """
    AI'ın bilinçaltı katmanı.

    Her input'u Thought'lara çevirir, DAG üzerinde resonance çalıştırır,
    en ilgili çağrışımları bulur ve AI'ın bağlamını zenginleştirir.
    AI'ın çıktısından otomatik öğrenir.

    Usage:
        layer = SubconsciousLayer()

        # Her konuşmada:
        context = layer.process("Python'da parallelism")
        # → context["associations"] = en ilgili bağlantılar
        # → context["enriched_prompt"] = zenginleştirilmiş prompt

        response = llm.chat(context["enriched_prompt"])
        layer.absorb(response)  # Yanıttan öğren
    """

    def __init__(self, capacity=64):
        # Bilgi ağı — Thought'lar burada yaşar
        self._thoughts: dict[str, Thought] = {}
        self._capacity = capacity
        self._interaction_count = 0

    def process(self, text: str) -> dict:
        """
        Bilinçaltı işleme — input'u Thought DAG'dan geçir.

        1. Kelimeleri Thought'lara çevir
        2. Mevcut bilgi ağıyla ilişkilendir (>>)
        3. Resonance çalıştır — en ilgili kavramları bul
        4. Zenginleştirilmiş bağlam döndür

        Returns:
            {
                "associations": [(concept, relevance), ...],
                "enriched_prompt": "...",
                "thoughts_activated": int,
            }
        """
        self._interaction_count += 1
        words = self._tokenize(text)

        # 1. Her kelime için Thought oluştur veya mevcut olanı al
        current_thoughts = []
        for word in words:
            if word in self._thoughts:
                # Mevcut düşünce — aktivasyonunu güçlendir
                t = self._thoughts[word]
                t.activation = min(1.0, t.activation + 0.1)
            else:
                # Yeni düşünce
                t = Thought(word, activation=0.5)
                self._thoughts[word] = t
            current_thoughts.append(t)

        # 2. Ardışık kelimeleri ilişkilendir (DAG inşa)
        chain = current_thoughts[0] if current_thoughts else Thought("empty", 0.0)
        for t in current_thoughts[1:]:
            chain = chain >> t

        # 3. Mevcut bilgi ağıyla çapraz ilişkiler kur
        associations = []
        for word in words:
            for known_word, known_thought in self._thoughts.items():
                if known_word != word and known_word not in words:
                    # Cross-association: yeni kavram ↔ bilinen kavram
                    cross = self._thoughts[word] >> known_thought
                    cross.resonate()
                    if known_thought.relevance > 0.3:
                        associations.append((known_word, known_thought.relevance))

        # 4. Relevance'a göre sırala
        associations.sort(key=lambda x: x[1], reverse=True)
        top_associations = associations[:5]

        # 5. Zenginleştirilmiş prompt oluştur
        enriched = text
        if top_associations:
            related = ", ".join(f"{c}({r:.2f})" for c, r in top_associations)
            enriched = f"{text}\n[Bilinçaltı çağrışımlar: {related}]"

        # Bellek taşması kontrolü — düşük aktivasyonluları unut
        self._forget_if_needed()

        return {
            "associations": top_associations,
            "enriched_prompt": enriched,
            "thoughts_activated": len(current_thoughts),
            "total_thoughts": len(self._thoughts),
        }

    def absorb(self, text: str):
        """
        AI'ın çıktısından öğren — yeni kavramları ağa ekle
        ve mevcut kavramların aktivasyonunu güçlendir.
        """
        words = self._tokenize(text)
        for word in words:
            if word in self._thoughts:
                # Tekrar gördük — güçlendir (reinforcement)
                self._thoughts[word].activation = min(1.0, self._thoughts[word].activation + 0.05)
            else:
                # Yeni kavram — düşük aktivasyonla ekle
                self._thoughts[word] = Thought(word, activation=0.3)

    def _tokenize(self, text: str) -> list[str]:
        """Basit tokenizer — stop words filtreli."""
        stop = {"bir", "bu", "de", "da", "ve", "ile", "için", "the", "a", "an",
                "is", "are", "was", "to", "of", "in", "for", "on", "it", "and",
                "or", "but", "not", "at", "by", "from", "that", "this", "with"}
        words = []
        for w in text.lower().split():
            clean = "".join(c for c in w if c.isalnum())
            if clean and len(clean) > 2 and clean not in stop:
                words.append(clean)
        return words[:20]

    def _forget_if_needed(self):
        """Akıllı unutma — kapasiteyi aşarsa düşük aktivasyonluları sil."""
        if len(self._thoughts) > self._capacity:
            # Aktivasyona göre sırala, en düşükleri unut
            sorted_thoughts = sorted(
                self._thoughts.items(),
                key=lambda x: x[1].activation
            )
            n_forget = len(self._thoughts) - self._capacity
            for word, _ in sorted_thoughts[:n_forget]:
                del self._thoughts[word]

    @property
    def knowledge_size(self) -> int:
        return len(self._thoughts)

    def stats(self) -> dict:
        return {
            "thoughts": len(self._thoughts),
            "interactions": self._interaction_count,
            "top_concepts": sorted(
                [(w, t.activation) for w, t in self._thoughts.items()],
                key=lambda x: x[1], reverse=True
            )[:10],
        }

    def __repr__(self):
        return f"SubconsciousLayer(thoughts={len(self._thoughts)}, interactions={self._interaction_count})"
