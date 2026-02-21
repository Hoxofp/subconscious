"""
Subconscious — Emotional Tagging

Duygusal etiketleme sistemi:
  - Her anıya duygusal ağırlık ve etiket atar
  - Duygusal ağırlık zamanla azalır (decay)
  - Güçlü duygulu anılar daha kolay hatırlanır
  - Konuşmanın duygusal tonunu analiz eder
"""
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

from config import settings


# ─── Duygu Modelleri ──────────────────────────────────────────────────────────

class EmotionCategory(Enum):
    """Temel duygu kategorileri (Plutchik'in duygu çarkından esinlenerek)."""
    JOY = "sevinç"
    TRUST = "güven"
    FEAR = "korku"
    SURPRISE = "şaşkınlık"
    SADNESS = "üzüntü"
    DISGUST = "tiksinme"
    ANGER = "öfke"
    ANTICIPATION = "beklenti"
    CURIOSITY = "merak"
    EXCITEMENT = "heyecan"
    ANXIETY = "kaygı"
    CALM = "sakinlik"
    NEUTRAL = "nötr"


@dataclass
class EmotionalTag:
    """Bir anı veya kavrama atanan duygusal etiket."""
    primary_emotion: EmotionCategory = EmotionCategory.NEUTRAL
    intensity: float = 0.5        # 0.0 → 1.0 duygu yoğunluğu
    valence: float = 0.0          # -1.0 (negatif) → +1.0 (pozitif)
    arousal: float = 0.5          # 0.0 (sakin) → 1.0 (uyarılmış)
    timestamp: float = field(default_factory=time.time)
    context: str = ""             # hangi bağlamda oluştu

    @property
    def current_intensity(self) -> float:
        """Zamanla azalan gerçek yoğunluk."""
        elapsed = time.time() - self.timestamp
        hours_elapsed = elapsed / 3600.0
        decay = settings.EMOTIONAL_WEIGHT_DECAY ** hours_elapsed
        return self.intensity * decay

    @property
    def memory_priority(self) -> float:
        """
        Bellek öncelik skoru: güçlü duygulu anılar daha kolay hatırlanır.
        Negatif duygular biraz daha güçlü (negativity bias — insan psikolojisi).
        """
        negativity_boost = 1.2 if self.valence < 0 else 1.0
        return self.current_intensity * self.arousal * negativity_boost

    def to_dict(self) -> dict:
        return {
            "primary_emotion": self.primary_emotion.value,
            "intensity": round(self.intensity, 3),
            "current_intensity": round(self.current_intensity, 3),
            "valence": round(self.valence, 3),
            "arousal": round(self.arousal, 3),
            "memory_priority": round(self.memory_priority, 3),
            "context": self.context,
        }


# ─── Duygu Sözlüğü (Keyword-based) ──────────────────────────────────────────

EMOTION_KEYWORDS: dict[EmotionCategory, dict] = {
    EmotionCategory.JOY: {
        "keywords": ["mutlu", "harika", "süper", "mükemmel", "güzel", "sevindim",
                      "happy", "great", "awesome", "wonderful", "love", "amazing"],
        "valence": 0.8, "arousal": 0.7,
    },
    EmotionCategory.EXCITEMENT: {
        "keywords": ["heyecanlı", "inanılmaz", "vay", "müthiş", "excited",
                      "incredible", "wow", "fantastic", "thrilling"],
        "valence": 0.9, "arousal": 0.9,
    },
    EmotionCategory.CURIOSITY: {
        "keywords": ["merak", "nasıl", "neden", "acaba", "ilginç", "curious",
                      "wonder", "how", "why", "interesting", "fascinating"],
        "valence": 0.3, "arousal": 0.6,
    },
    EmotionCategory.TRUST: {
        "keywords": ["güveniyorum", "emin", "doğru", "trust", "sure", "confident",
                      "reliable", "safe"],
        "valence": 0.5, "arousal": 0.3,
    },
    EmotionCategory.FEAR: {
        "keywords": ["korkuyorum", "tehlikeli", "endişe", "risk", "afraid",
                      "dangerous", "scary", "worried", "fear"],
        "valence": -0.8, "arousal": 0.8,
    },
    EmotionCategory.ANXIETY: {
        "keywords": ["kaygı", "stres", "gergin", "tedirgin", "anxious",
                      "stressed", "nervous", "tense", "uneasy"],
        "valence": -0.6, "arousal": 0.7,
    },
    EmotionCategory.SADNESS: {
        "keywords": ["üzgün", "kötü", "maalesef", "yazık", "sad", "unfortunate",
                      "sorry", "disappointed", "depressed", "unhappy"],
        "valence": -0.7, "arousal": 0.3,
    },
    EmotionCategory.ANGER: {
        "keywords": ["kızgın", "sinir", "saçma", "berbat", "angry", "furious",
                      "annoyed", "frustrated", "ridiculous", "terrible"],
        "valence": -0.8, "arousal": 0.9,
    },
    EmotionCategory.SURPRISE: {
        "keywords": ["şaşırdım", "beklemiyordum", "ciddi mi", "surprise",
                      "unexpected", "shocked", "really", "seriously"],
        "valence": 0.1, "arousal": 0.8,
    },
    EmotionCategory.CALM: {
        "keywords": ["sakin", "rahat", "huzur", "stressiz", "calm", "relaxed",
                      "peaceful", "serene", "tranquil"],
        "valence": 0.4, "arousal": 0.2,
    },
}


# ─── Emotional Tagger ────────────────────────────────────────────────────────

class EmotionalTagger:
    """
    Duygusal etiketleme motoru.

    Hybrid approach:
      1. Keyword-based hızlı analiz (her zaman çalışır)
      2. LLM-based derin analiz (bilinçaltı analizinden gelir)
    """

    def __init__(self):
        self.emotional_history: list[EmotionalTag] = []
        self._max_history = 100

    def analyze(self, text: str, context: str = "") -> EmotionalTag:
        """
        Metin üzerinden duygusal analiz yap.
        Keyword-based hızlı analiz.
        """
        text_lower = text.lower()
        scores: dict[EmotionCategory, float] = {}

        for emotion, config in EMOTION_KEYWORDS.items():
            keyword_matches = sum(1 for kw in config["keywords"] if kw in text_lower)
            if keyword_matches > 0:
                # Daha çok keyword = daha güçlü duygu
                scores[emotion] = min(1.0, keyword_matches * 0.3)

        if not scores:
            tag = EmotionalTag(
                primary_emotion=EmotionCategory.NEUTRAL,
                intensity=0.3,
                valence=0.0,
                arousal=0.3,
                context=context,
            )
        else:
            # En güçlü duyguyu seç
            primary = max(scores, key=scores.get)
            config = EMOTION_KEYWORDS[primary]

            tag = EmotionalTag(
                primary_emotion=primary,
                intensity=scores[primary],
                valence=config["valence"],
                arousal=config["arousal"],
                context=context,
            )

        self._add_to_history(tag)
        return tag

    def analyze_with_llm_result(self, llm_emotional_tone: str,
                                 context: str = "") -> EmotionalTag:
        """
        LLM bilinçaltı analizinden gelen duygusal tonu EmotionalTag'e çevir.
        """
        tone_lower = llm_emotional_tone.lower()

        # LLM tonunu EmotionCategory'ye eşle
        for emotion, config in EMOTION_KEYWORDS.items():
            for kw in config["keywords"]:
                if kw in tone_lower:
                    tag = EmotionalTag(
                        primary_emotion=emotion,
                        intensity=0.7,  # LLM analizi keyword'den daha güvenilir
                        valence=config["valence"],
                        arousal=config["arousal"],
                        context=context,
                    )
                    self._add_to_history(tag)
                    return tag

        # Eşleşme bulunamazsa nötr
        tag = EmotionalTag(
            primary_emotion=EmotionCategory.NEUTRAL,
            intensity=0.3,
            valence=0.0,
            arousal=0.3,
            context=context,
        )
        self._add_to_history(tag)
        return tag

    def get_emotional_trend(self, last_n: int = 10) -> dict:
        """
        Son N konuşmanın duygusal trendini analiz et.
        Duygusal yön (iyiye mi kötüye mi gidiyor?) ve baskın duygu.
        """
        recent = self.emotional_history[-last_n:]
        if not recent:
            return {
                "dominant_emotion": EmotionCategory.NEUTRAL.value,
                "avg_valence": 0.0,
                "avg_arousal": 0.5,
                "trend": "stable",
                "emotion_counts": {},
            }

        # Duygu sayıları
        emotion_counts = {}
        for tag in recent:
            name = tag.primary_emotion.value
            emotion_counts[name] = emotion_counts.get(name, 0) + 1

        # Ortalama değerler
        avg_valence = sum(t.valence for t in recent) / len(recent)
        avg_arousal = sum(t.arousal for t in recent) / len(recent)

        # Trend hesapla
        if len(recent) >= 3:
            first_half = recent[:len(recent) // 2]
            second_half = recent[len(recent) // 2:]
            first_avg = sum(t.valence for t in first_half) / len(first_half)
            second_avg = sum(t.valence for t in second_half) / len(second_half)
            diff = second_avg - first_avg
            if diff > 0.15:
                trend = "improving"
            elif diff < -0.15:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Baskın duygu
        dominant = max(emotion_counts, key=emotion_counts.get)

        return {
            "dominant_emotion": dominant,
            "avg_valence": round(avg_valence, 3),
            "avg_arousal": round(avg_arousal, 3),
            "trend": trend,
            "emotion_counts": emotion_counts,
        }

    def calculate_memory_weight(self, text: str) -> float:
        """
        Bir metin için bellek ağırlığı hesapla.
        Güçlü duygulu içerikler daha yüksek ağırlık alır.
        """
        tag = self.analyze(text)
        # Pop the auto-added tag (we just want the weight, not to track this)
        if self.emotional_history:
            self.emotional_history.pop()
        return tag.memory_priority

    def _add_to_history(self, tag: EmotionalTag):
        """Duygusal geçmişe ekle (kapasite kontrolü ile)."""
        self.emotional_history.append(tag)
        if len(self.emotional_history) > self._max_history:
            self.emotional_history = self.emotional_history[-self._max_history:]
