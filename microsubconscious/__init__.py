"""
microsubconscious

A tiny subconscious engine (with a thought! :)).
Implements spreading activation and resonance over a dynamically built
association DAG, and a small cognitive library on top of it.

Inspired by Karpathy's micrograd.
"""
from microsubconscious.engine import Thought
from microsubconscious.mind import Memory, Association, Mind
from microsubconscious.layer import SubconsciousLayer
