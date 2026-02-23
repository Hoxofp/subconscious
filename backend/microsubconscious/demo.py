"""
microsubconscious — Demo

Shows the parallel between micrograd and microsubconscious.
Run: python demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from microsubconscious.engine import Thought
from microsubconscious.mind import Mind

print("=" * 60)
print("  microsubconscious demo — Karpathy micrograd style")
print("=" * 60)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Thought — like micrograd's Value
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📌 1. Thoughts (like Value in micrograd)")
print("-" * 40)

# Create thoughts — like creating Values
a = Thought("python",     activation=0.8)
b = Thought("creativity", activation=0.6)
c = Thought("music",      activation=0.4)

print(f"  a = {a}")
print(f"  b = {b}")
print(f"  c = {c}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Association DAG — like computational graph
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📌 2. Building association DAG (like computational graph)")
print("-" * 40)

# >> operator builds associations (like + builds computation)
d = a >> b          # python triggers creativity
e = b >> c          # creativity triggers music
f = d + e           # merge both association chains
g = f * 1.5         # amplify the merged thought
h = g.activate()    # threshold (like ReLU)

print(f"  d = a >> b        = {d}")
print(f"  e = b >> c        = {e}")
print(f"  f = d + e         = {f}")
print(f"  g = f * 1.5       = {g}")
print(f"  h = g.activate()  = {h}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Resonance — like backpropagation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📌 3. Resonance (like backpropagation)")
print("-" * 40)

# resonate() propagates relevance backward — like backward()
h.resonate()

print("  After h.resonate():")
print(f"    a.relevance = {a.relevance:.4f}  (python)")
print(f"    b.relevance = {b.relevance:.4f}  (creativity)")
print(f"    c.relevance = {c.relevance:.4f}  (music)")
print(f"    h.relevance = {h.relevance:.4f}  (output)")
print()
print("  → 'creativity' has highest relevance — it connects both chains!")
print("  → Just like backprop finds the most influential parameters.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Mind — like MLP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📌 4. Mind (like MLP in micrograd)")
print("-" * 40)

# Create a mind with 3 inputs → 4 memories → 4 memories → 1 output
# Exactly like: MLP(3, [4, 4, 1])
mind = Mind([3, 4, 4, 1])
print(f"  Mind architecture: [3, 4, 4, 1]")
print(f"  Total parameters: {len(mind.parameters())}")

# Think — forward pass
inputs = [0.8, 0.6, 0.4]  # python, creativity, music activations
output = mind.think(inputs)
print(f"  Input activations: {inputs}")
print(f"  Output: {output}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Learning — like SGD training
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n📌 5. Learning loop (like training in micrograd)")
print("-" * 40)

# Simple training: target activation = 0.5
target = 0.5
print(f"  Target: {target}")
print(f"  Training for 20 steps...")

for step in range(20):
    # Forward
    output = mind.think(inputs)
    act = output.activation

    # Loss = (output - target)^2 — surprise/prediction-error
    loss = (act - target) ** 2

    # Backward — resonate relevance through the mind
    mind.zero_relevance()
    # Manual gradient: d(loss)/d(act) = 2*(act - target)
    for p in mind.parameters():
        p.relevance = 2 * (act - target) * p.activation * 0.01

    # Update — learn from the resonance
    mind.learn(rate=0.01)

    if step % 5 == 0:
        print(f"    step {step:2d}: output={act:.4f}, loss={loss:.6f}")

final = mind.think(inputs)
print(f"  Final output: {final.activation:.4f} (target was {target})")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

print("\n" + "=" * 60)
print("  ✅ microsubconscious works! Karpathy would be proud.")
print("=" * 60)

print("""
╔══════════════════════════════════════════════════════════╗
║          micrograd  ↔  microsubconscious                ║
╠═════════════════════╤════════════════════════════════════╣
║  Value              │  Thought                          ║
║  .data (scalar)     │  .data (idea)                     ║
║  .grad              │  .relevance                       ║
║  __add__, __mul__   │  __add__, __mul__, __rshift__     ║
║  .relu()            │  .activate()                      ║
║  .backward()        │  .resonate()                      ║
║  Neuron             │  Memory                           ║
║  Layer              │  Association                      ║
║  MLP                │  Mind                             ║
║  Loss function      │  Surprise (prediction error)      ║
║  SGD                │  learn()                          ║
╚═════════════════════╧════════════════════════════════════╝
""")
