# 🧠 Subconscious

**Model-agnostic cognitive middleware for AI.**

A Python library that adds **memory**, **knowledge graphs**, **creative thinking**, and **background processing** to any Large Language Model. Think of it as a "thinking substrate" — a subconscious that runs beneath any AI.

## Quick Start

```python
from subconscious import Subconscious
from subconscious.adapters import OllamaAdapter

# Initialize with any LLM (or None for pure cognitive mode)
mind = Subconscious(adapter=OllamaAdapter("qwen2.5:7b"))

# Learn knowledge
mind.learn("Python GIL prevents true parallelism", domain="programming")
mind.learn("Ant colonies find optimal paths without central control", domain="biology")

# Think — LLM response enriched by memory + graph + associations
result = mind.think("How to solve the parallelism problem?")
print(result.response)            # LLM-enriched answer
print(result.activated_concepts)  # Related concepts from knowledge graph
print(result.creative_sparks)     # Novel ideas from creative engine

# Imagine — cross-domain creative sparks
sparks = mind.imagine("ant colony", "microservices")
for s in sparks:
    print(f"[{s.strategy.value}] {s.idea}")

# Dream — background consolidation & discovery
report = mind.dream()
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           🧠 Subconscious API               │
│   think()  learn()  recall()  imagine()     │
├─────────┬─────────┬──────────┬──────────────┤
│ 📦 Memory│ 🕸 Graph │ 🎨 Creative│ 🌙 Dream    │
│ Working  │ Multi-  │ Bisociat. │ Consolidate │
│ Episodic │ type    │ Blending  │ Discover    │
│ Semantic │ Spread  │ Analogy   │ Forget      │
│ Procedur.│ Walk    │ Lateral   │ Hypothesize │
├─────────┴─────────┴──────────┴──────────────┤
│              🔌 LLM Adapters                │
│      Ollama  ·  OpenAI  ·  Anthropic        │
└─────────────────────────────────────────────┘
```

## Features

- **4-Layer Memory**: Working (7±2) → Episodic (SQLite) → Semantic (ChromaDB) → Procedural (reinforcement)
- **Cognitive Graph**: Multi-type nodes & edges, spreading activation, random walk discovery
- **Creative Engine**: Bisociation, conceptual blending, analogical reasoning, lateral thinking
- **Dream Processor**: Background memory consolidation, pattern mining, smart forgetting
- **Model Agnostic**: Works with Ollama, OpenAI, Anthropic — or without any LLM

## Install

```bash
pip install -e .                    # Core
pip install -e ".[ollama]"          # + Ollama support
pip install -e ".[openai]"          # + OpenAI support
pip install -e ".[dev]"             # + dev tools
```

## License

MIT
