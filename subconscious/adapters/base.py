"""
Subconscious — LLM Adapter Protocol

Tüm LLM adapter'larının uyması gereken interface.
"""
from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable


@runtime_checkable
class LLMAdapter(Protocol):
    """
    Model-agnostic LLM adapter interface.

    Her LLM provider (Ollama, OpenAI, Anthropic, vb.) bu protocol'ü
    implemente ederek subconscious kütüphanesine entegre olabilir.
    """

    @property
    def model_name(self) -> str:
        """Kullanılan model adı."""
        ...

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Tek seferlik metin üretimi.

        Args:
            prompt: Kullanıcı/input prompt
            system: System prompt
            temperature: Yaratıcılık seviyesi (0-1)
            max_tokens: Maksimum token sayısı

        Returns:
            Üretilen metin
        """
        ...

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Multi-turn sohbet.

        Args:
            messages: [{"role": "system|user|assistant", "content": "..."}]
            temperature: Yaratıcılık seviyesi
            max_tokens: Maks token

        Returns:
            Assistant yanıtı
        """
        ...

    def embed(self, text: str) -> list[float]:
        """
        Metin embedding üret.

        Args:
            text: Embed edilecek metin

        Returns:
            Embedding vektörü
        """
        ...

    def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """
        Streaming metin üretimi.

        Args:
            prompt: Input prompt
            system: System prompt
            temperature: Yaratıcılık

        Yields:
            Metin parçaları (chunks)
        """
        ...
