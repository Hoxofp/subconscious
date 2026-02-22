"""
Subconscious — Working Memory

Miller's Law tabanlı aktif bağlam yönetimi (7±2 öğe).
Şu anki konuşmanın kısa süreli hafızası.
"""
from __future__ import annotations

from collections import deque
from typing import Any


class WorkingMemory:
    """
    Aktif çalışma belleği — sınırlı kapasiteli bağlam havuzu.

    Miller's Law: İnsan kısa süreli belleğinde 7±2 öğe tutar.
    Bu modül aynı prensibi uygular.
    """

    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self._items: deque[dict[str, Any]] = deque(maxlen=capacity)

    def push(self, item: dict[str, Any]) -> dict[str, Any] | None:
        """
        Yeni öğe ekle. Kapasite aşılırsa en eski öğe döndürülür (consolidation için).

        Returns:
            Taşan öğe veya None
        """
        overflow = None
        if len(self._items) >= self.capacity:
            overflow = self._items[0]  # En eski öğe taşacak
        self._items.append(item)
        return overflow

    def get_context(self) -> list[dict[str, Any]]:
        """Tüm aktif bağlamı döndür."""
        return list(self._items)

    def get_recent(self, n: int = 3) -> list[dict[str, Any]]:
        """Son n öğeyi döndür."""
        items = list(self._items)
        return items[-n:] if len(items) >= n else items

    def search(self, key: str, value: Any) -> list[dict[str, Any]]:
        """Belirli bir anahtar-değer çiftine göre ara."""
        return [item for item in self._items if item.get(key) == value]

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def is_full(self) -> bool:
        return len(self._items) >= self.capacity

    def clear(self):
        self._items.clear()

    def to_text(self) -> str:
        """Bağlamı metin formatına çevir (LLM için)."""
        if not self._items:
            return ""
        parts = []
        for item in self._items:
            role = item.get("role", "")
            content = item.get("content", str(item))
            if role:
                parts.append(f"{role}: {content[:300]}")
            else:
                parts.append(content[:300])
        return "\n".join(parts)
