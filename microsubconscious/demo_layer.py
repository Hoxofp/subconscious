"""
🧠 microsubconscious — AI Bilinçaltı Demo

Bir AI'ın microsubconscious kullanarak nasıl bilinçaltından düşündüğünü gösterir.

Normal AI:       input → [LLM] → output
Bilinçaltılı AI: input → [SubconsciousLayer] → enriched → [LLM] → output
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from microsubconscious.layer import SubconsciousLayer

print("=" * 65)
print("🧠 microsubconscious — AI Bilinçaltı Katmanı Demo")
print("=" * 65)

# ─── Bilinçaltı katmanı oluştur ──────────────────────────────────
layer = SubconsciousLayer(capacity=128)
print(f"\n📦 SubconsciousLayer oluşturuldu: {layer}")

# ─── Simüle edilmiş konuşma ──────────────────────────────────────
conversations = [
    # 1. Konuşma — programlama hakkında
    ("Python'da parallelism GIL yüzünden zordur", 
     "Evet, multiprocessing veya asyncio kullanılabilir"),

    # 2. Konuşma — biyoloji hakkında
    ("Karınca kolonileri merkezi kontrol olmadan optimize yollar bulur",
     "Stigmergy — dolaylı iletişim ile kolektif zeka"),

    # 3. Konuşma — yazılım hakkında
    ("Mikroservis mimarisi dağıtık sistemler için idealdir",
     "Kubernetes ile orkestrasyon ve service mesh kullanılır"),

    # 4. Konuşma — şimdi bağlantı kurmayı dene!
    ("Yazılımda parallelism problemini doğadan ilham alarak çözebilir miyiz?",
     "Evet, swarm intelligence ve karınca algoritmaları bu konuda çok etkili"),
]

print("\n" + "─" * 65)
print("📡 Simüle edilen konuşmalar:")
print("─" * 65)

for i, (user_msg, ai_response) in enumerate(conversations, 1):
    print(f"\n🗣️  Konuşma {i}:")
    print(f"   User: {user_msg}")

    # Bilinçaltı işleme — input'u Thought DAG'dan geçir
    result = layer.process(user_msg)

    print(f"   🧠 Bilinçaltı:")
    print(f"      Aktive edilen: {result['thoughts_activated']} düşünce")
    print(f"      Toplam bilgi: {result['total_thoughts']} kavram")

    if result['associations']:
        print(f"      Çağrışımlar: {result['associations'][:3]}")
        print(f"      Zenginleştirilmiş: ...{result['enriched_prompt'][-80:]}")
    else:
        print(f"      (Henüz çağrışım yok — bilgi birikiyor)")

    # AI yanıtından öğren
    layer.absorb(ai_response)
    print(f"   AI: {ai_response}")

# ─── Final analiz ────────────────────────────────────────────────
print("\n" + "─" * 65)
print("📊 Bilinçaltı son durum:")
print("─" * 65)

stats = layer.stats()
print(f"   Toplam kavram: {stats['thoughts']}")
print(f"   Etkileşim sayısı: {stats['interactions']}")
print(f"\n   En güçlü kavramlar:")
for concept, activation in stats['top_concepts'][:10]:
    bar = "█" * int(activation * 20)
    print(f"      {concept:20s} {bar} ({activation:.2f})")

# ─── Kritik test: 4. konuşmada çağrışım var mı? ─────────────────
print("\n" + "─" * 65)
print("🔬 Kritik test: Konuşma 4'te bilinçaltı bağlantı kurabildi mi?")
print("─" * 65)

test = layer.process("yazılımda parallelism çözmek için doğadan ilham")
if test['associations']:
    print("   ✅ EVET! Bilinçaltı şu kavramları ilişkilendirdi:")
    for concept, relevance in test['associations']:
        print(f"      → {concept} (relevance: {relevance:.2f})")
    print("\n   → Tıpkı bir insanın bilinçaltının 'parallelism' duyunca")
    print("     otomatik olarak 'karınca kolonisi' ve 'stigmergy'yi")  
    print("     çağrıştırması gibi!")
else:
    print("   ❌ Henüz yeterli bağlantı kurulamadı (daha fazla konuşma gerekli)")

print("\n" + "=" * 65)
print("🧠 microsubconscious → AI'ın bilinçaltı katmanı olarak çalışıyor!")
print("=" * 65)

print("""
┌─────────────────────────────────────────────────────────┐
│                  Normal AI düşünce:                     │
│        input → [Neural Network] → output               │
│                                                         │
│              Bilinçaltılı AI düşünce:                   │
│        input → [SubconsciousLayer] → enriched input     │
│                       ↑                    ↓            │
│              Thought DAG            [Neural Network]    │
│              Resonance                     ↓            │
│              Associations             output            │
│                                          ↓              │
│                                   absorb(output)        │
│                                   → auto-learn          │
└─────────────────────────────────────────────────────────┘
""")
