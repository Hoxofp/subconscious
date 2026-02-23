"""
Subconscious — Ollama Adapter

Ollama LLM provider adapter. Yerel model çalıştırma.
"""
from __future__ import annotations

from typing import Iterator

try:
    import ollama as _ollama
except ImportError:
    _ollama = None  # type: ignore


class OllamaAdapter:
    """
    Ollama LLM adapter.

    Yerel Ollama sunucusu üzerinden model çalıştırır.
    CUDA/Metal otomatik algılanır.

    Usage:
        adapter = OllamaAdapter("qwen2.5:7b")
        response = adapter.generate("Merhaba!")
    """

    def __init__(self, model: str = "llama3.1:8b", base_url: str = ""):
        if _ollama is None:
            raise ImportError(
                "Ollama adapter requires 'ollama' package. "
                "Install with: pip install subconscious[ollama]"
            )
        self._model = model
        if base_url:
            self._client = _ollama.Client(host=base_url)
        else:
            self._client = _ollama.Client()

    @property
    def model_name(self) -> str:
        return self._model

    def generate(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature, max_tokens=max_tokens)

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        response = self._client.chat(
            model=self._model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        return response["message"]["content"]

    def embed(self, text: str) -> list[float]:
        response = self._client.embed(model=self._model, input=text)
        # Ollama embed returns {"embeddings": [[...]]}
        embeddings = response.get("embeddings", [[]])
        if embeddings and len(embeddings) > 0:
            return embeddings[0]
        return []

    def stream(
        self,
        prompt: str,
        system: str = "",
        temperature: float = 0.7,
    ) -> Iterator[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = self._client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature},
            stream=True,
        )
        for chunk in stream:
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
