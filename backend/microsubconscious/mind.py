"""
microsubconscious — mind.py

A tiny neural-network-like library for building minds.
Like micrograd's nn.py builds networks from Value objects,
mind.py builds minds from Thought objects.

~50 lines. Neuron → Memory, Layer → Association, MLP → Mind.
"""
import random
from microsubconscious.engine import Thought


class Module:
    """Base class, like nn.Module in micrograd."""

    def zero_relevance(self):
        for p in self.parameters():
            p.relevance = 0.0

    def parameters(self):
        return []


class Memory(Module):
    """
    A single memory — like a Neuron.

    A Neuron computes: out = activation(sum(wi * xi) + b)
    A Memory computes: out = activate(sum(wi * xi) + bias)

    Where wi = connection weights, xi = input thoughts.
    """

    def __init__(self, nin):
        self.w = [Thought(f'w{i}', activation=random.uniform(-1, 1)) for i in range(nin)]
        self.b = Thought('bias', activation=0.0)

    def __call__(self, x):
        # sum(wi * xi) + b — exactly like a Neuron
        # xi can be float (first layer) or Thought (hidden layers)
        act = self.b.activation
        for wi, xi in zip(self.w, x):
            xi_val = xi.activation if isinstance(xi, Thought) else xi
            act += wi.activation * xi_val
        out = Thought(data='memory', activation=act, _children=tuple(self.w) + (self.b,))
        return out.activate()

    def parameters(self):
        return self.w + [self.b]


class Association(Module):
    """
    A group of memories — like a Layer.
    Each memory independently processes the same input.
    """

    def __init__(self, nin, nout):
        self.memories = [Memory(nin) for _ in range(nout)]

    def __call__(self, x):
        out = [m(x) for m in self.memories]
        return out[0] if len(out) == 1 else out

    def parameters(self):
        return [p for m in self.memories for p in m.parameters()]


class Mind(Module):
    """
    A complete mind — like an MLP.

    Mind([3, 4, 4, 1]) creates:
      3 inputs → 4 memories → 4 memories → 1 output
    Just like MLP([3, 4, 4, 1]) in micrograd.
    """

    def __init__(self, layers):
        self.layers = [Association(layers[i], layers[i+1]) for i in range(len(layers)-1)]

    def __call__(self, x):
        for layer in self.layers:
            x = layer(x)
        return x

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]

    def think(self, inputs):
        """Forward pass — like MLP.__call__."""
        return self(inputs)

    def learn(self, rate=0.01):
        """
        Update — like SGD step.
        Adjusts memory weights by their relevance (gradient).
        """
        for p in self.parameters():
            p.activation -= rate * p.relevance
