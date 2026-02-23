"""
🧠 Subconscious v2.0 — Demo

Kütüphanenin tüm yeteneklerini gösteren interaktif demo.
Ollama ile çalışır; Ollama yoksa LLM'siz modda devam eder.
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from subconscious import Subconscious

print("=" * 65)
print("🧠 Subconscious v2.0 — Full Demo")
print("=" * 65)

# ─── 1. Initialize ────────────────────────────────────────────────
print("\n📦 1. Initializing...")
try:
    from subconscious.adapters import OllamaAdapter
    adapter = OllamaAdapter("qwen2.5-coder:7b-instruct-q4_K_M")
    mind = Subconscious(adapter=adapter)
    print(f"   ✅ Adapter: Ollama ({adapter.model_name})")
except Exception as e:
    print(f"   ⚠️  Ollama unavailable ({e}), running in pure cognitive mode")
    mind = Subconscious()

print(f"   ✅ Mind initialized — stats: {mind.stats()}")

# ─── 2. Learn ─────────────────────────────────────────────────────
print("\n📚 2. Learning knowledge...")
knowledge = [
    ("Python GIL (Global Interpreter Lock) gerçek CPU paralelliğini engeller", "programming"),
    ("Beyin nöronları paralel çalışır, her saniye milyarlarca sinyal iletimi olur", "neuroscience"),
    ("Karınca kolonileri merkezi kontrol olmadan optimize yollar bulur", "biology"),
    ("Kuantum süperpozisyon: bir parçacık aynı anda birden fazla durumda olabilir", "physics"),
    ("Mikroservis mimarisi bağımsız dağıtılabilir servislerden oluşur", "software"),
    ("İnsan sezgisi — bilinçaltı örüntü tanıma mekanizmasıdır", "psychology"),
]
for content, domain in knowledge:
    mind.learn(content, domain=domain, importance=0.8)
    print(f"   📝 [{domain}] {content[:60]}...")

print(f"   ✅ {len(knowledge)} bilgi öğrenildi")
print(f"   📊 Graph: {mind.stats()['graph']}")
print(f"   📊 Memory: {mind.stats()['memory']}")

# ─── 3. Think ─────────────────────────────────────────────────────
print("\n🧠 3. Thinking (bilinçaltı zenginleştirme)...")
result = mind.think(
    "Yazılım mimarisinde paralellik problemini nasıl çözeriz?",
    include_creative=True,
    n_creative=2,
)
print(f"   📝 Response:\n   {result.response[:300]}")
print(f"   🔗 Activated concepts: {list(result.activated_concepts.keys())[:8]}")
print(f"   💡 Insights: {len(result.insights)}")
for i, insight in enumerate(result.insights[:3]):
    print(f"      {i+1}. {insight.content[:100]}")
print(f"   ✨ Creative sparks: {len(result.creative_sparks)}")
for spark in result.creative_sparks:
    print(f"      [{spark.strategy.value}] {spark.idea[:100]}")

# ─── 4. Recall ────────────────────────────────────────────────────
print("\n🔍 4. Multi-layer recall...")
memories = mind.recall("paralel işlem")
print(f"   Found {len(memories)} relevant items:")
for m in memories[:5]:
    layer = m.get("_layer", "?")
    content = m.get("content", str(m))[:80]
    print(f"   [{layer:10}] {content}")

# ─── 5. Imagine ───────────────────────────────────────────────────
print("\n💡 5. Imagination (creative engine)...")
sparks = mind.imagine("karınca kolonisi", "yazılım mimarisi", n=3)
print(f"   Generated {len(sparks)} creative sparks:")
for i, spark in enumerate(sparks):
    print(f"   {i+1}. [{spark.strategy.value}]")
    print(f"      {spark.idea[:120]}")
    print(f"      novelty={spark.novelty:.1f}")

# ─── 6. Dream ─────────────────────────────────────────────────────
print("\n🌙 6. Dream cycle (background processing)...")
report = mind.dream()
print(f"   Consolidated: {report.memories_consolidated}")
print(f"   Pruned: {report.memories_pruned}")
print(f"   New connections: {report.new_connections}")
print(f"   Patterns found: {report.patterns_found}")
if report.hypotheses_generated:
    print(f"   Hypotheses:")
    for h in report.hypotheses_generated[:2]:
        print(f"      • {h[:100]}")

# ─── 7. Final Stats ──────────────────────────────────────────────
print("\n📊 7. Final system state:")
stats = mind.stats()
print(f"   Graph: {stats['graph']['nodes']} nodes, {stats['graph']['edges']} edges")
print(f"   Memory: {stats['memory']['total']} total records")
print(f"   Adapter: {stats['adapter']}")

print("\n" + "=" * 65)
print("🎉 Demo complete! Subconscious v2.0 is operational.")
print("=" * 65)
