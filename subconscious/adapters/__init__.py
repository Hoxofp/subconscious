"""
Subconscious — LLM Adapters

Model-agnostic adapter pattern. Her LLM provider bir adapter implemente eder.
"""
from subconscious.adapters.base import LLMAdapter
from subconscious.adapters.ollama import OllamaAdapter

__all__ = ["LLMAdapter", "OllamaAdapter"]
