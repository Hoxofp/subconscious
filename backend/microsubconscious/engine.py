"""
microsubconscious — engine.py

A tiny subconscious engine. Implements spreading activation (forward pass)
and resonance (backward relevance propagation) over a dynamically built
association DAG. Analogous to micrograd's Value class.

~100 lines. Educational. Minimal. Elegant.
"""


class Thought:
    """
    The fundamental unit of subconscious processing.
    Like micrograd's Value wraps a scalar, Thought wraps an idea.

    micrograd analogy:
        Value.data     → Thought.data       (content)
        Value.grad     → Thought.relevance  (how relevant/important)
        Value._backward → Thought._resonate (backward propagation fn)
        Value + Value  → Thought >> Thought  (association)
        forward pass   → activation spread
        backprop       → resonance
    """

    def __init__(self, data, activation=0.0, _children=(), _op=''):
        self.data = data                    # content: string or any
        self.activation = activation        # how "active" this thought is [0,1]
        self.relevance = 0.0               # like grad — computed by resonate()
        self._prev = set(_children)
        self._op = _op                      # operation that produced this
        self._resonate = lambda: None       # backward fn

    def __rshift__(self, other):
        """
        Association operator: a >> b means 'a triggers b'.
        Like Value.__add__ builds the computational graph,
        >> builds the association graph.

        Activation propagates: child activation = avg(parent activations) * decay
        """
        out = Thought(
            data=f"({self.data} → {other.data})",
            activation=(self.activation + other.activation) / 2 * 0.9,
            _children=(self, other),
            _op='assoc'
        )

        def _resonate():
            self.relevance += 0.7 * out.relevance
            other.relevance += 0.7 * out.relevance
        out._resonate = _resonate

        return out

    def __add__(self, other):
        """
        Merge: combine two thoughts into one.
        Like Value.__add__ sums scalars, Thought.__add__ blends ideas.
        """
        other = other if isinstance(other, Thought) else Thought(other)
        out = Thought(
            data=f"({self.data} + {other.data})",
            activation=max(self.activation, other.activation),
            _children=(self, other),
            _op='merge'
        )

        def _resonate():
            self.relevance += out.relevance
            other.relevance += out.relevance
        out._resonate = _resonate

        return out

    def __mul__(self, other):
        """
        Amplify: strengthen a thought by a factor.
        Like Value.__mul__, but for cognitive amplification.
        """
        assert isinstance(other, (int, float))
        out = Thought(
            data=self.data,
            activation=min(1.0, self.activation * other),
            _children=(self,),
            _op='amplify'
        )

        def _resonate():
            self.relevance += other * out.relevance
        out._resonate = _resonate

        return out

    def __rmul__(self, other):
        return self * other

    def activate(self):
        """
        Activate this thought (like ReLU but for thoughts).
        Thresholds at 0.0 — only positive activations pass.
        """
        out = Thought(
            data=self.data,
            activation=max(0.0, self.activation),
            _children=(self,),
            _op='activate'
        )

        def _resonate():
            self.relevance += (self.activation > 0) * out.relevance
        out._resonate = _resonate

        return out

    def resonate(self):
        """
        Backward pass — propagate relevance through the association DAG.
        Like Value.backward() uses topological sort to propagate gradients,
        resonate() propagates relevance scores backward.

        "What thoughts were most important for reaching this conclusion?"
        """
        topo = []
        visited = set()

        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)
        self.relevance = 1.0
        for v in reversed(topo):
            v._resonate()

    def __repr__(self):
        return f"Thought(data={self.data}, act={self.activation:.4f}, rel={self.relevance:.4f})"
