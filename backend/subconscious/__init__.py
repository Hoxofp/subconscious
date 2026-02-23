"""
🧠 Subconscious — AI Cognitive Middleware

Model-agnostic cognitive middleware for AI systems.
Adds memory, associations, creativity, and background processing to any LLM.

Usage:
    from subconscious import Subconscious
    from subconscious.adapters import OllamaAdapter

    mind = Subconscious(adapter=OllamaAdapter("qwen2.5:7b"))
    result = mind.think("How can we improve this?")
"""

from subconscious.core.mind import Subconscious
from subconscious.core.types import (
    ThinkResult,
    Insight,
    CreativeSpark,
    MemoryRecord,
    ConceptNode,
    Association,
)

__version__ = "2.0.0-alpha.1"
__all__ = [
    "Subconscious",
    "ThinkResult",
    "Insight",
    "CreativeSpark",
    "MemoryRecord",
    "ConceptNode",
    "Association",
]
