"""HEART_004: bounded, deterministic, local skip-gram token embeddings.

Research primitive only. A learned token vector is not proof of semantic
understanding, and this module does not implement an LLM or network requests.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence

from .tokenizer import BPETokenizer


class TokenEmbeddings:
    """Small trainable input and context tables with negative sampling."""

    def __init__(self, vocab_size: int, dimension: int = 16, seed: int = 7):
        if type(vocab_size) is not int or not 259 <= vocab_size <= 4096:
            raise ValueError("vocab_size must be in [259, 4096]")
        if type(dimension) is not int or not 2 <= dimension <= 128:
            raise ValueError("dimension must be in [2, 128]")
        if type(seed) is not int:
            raise TypeError("seed must be an integer")
        self.vocab_size, self.dimension, self.seed = vocab_size, dimension, seed
        rng = random.Random(seed)
        scale = .5 / dimension
        self.input_weights = [[rng.uniform(-scale, scale) for _ in range(dimension)]
                              for _ in range(vocab_size)]
        self.context_weights = [[rng.uniform(-scale, scale) for _ in range(dimension)]
                                for _ in range(vocab_size)]
        self.input_weights[BPETokenizer.PAD_ID] = [0.0] * dimension

    def _validate(self, token_id: int) -> None:
        if type(token_id) is not int or not 0 <= token_id < self.vocab_size:
            raise ValueError("invalid token ID for embedding vocabulary")

    def lookup(self, ids: Sequence[int]) -> list[list[float]]:
        for token_id in ids:
            self._validate(token_id)
        return [self.input_weights[token_id].copy() for token_id in ids]

    def mean_pool(self, ids: Sequence[int]) -> list[float]:
        for token_id in ids:
            self._validate(token_id)
        usable = [token_id for token_id in ids if token_id not in (256, 257, 258)]
        if not usable:
            raise ValueError("cannot pool empty or special-only tokens")
        return [sum(self.input_weights[token_id][dim] for token_id in usable) / len(usable)
                for dim in range(self.dimension)]

    @staticmethod
    def cosine(left: Sequence[float], right: Sequence[float]) -> float:
        if not left or len(left) != len(right):
            raise ValueError("vectors must have equal nonzero dimensions")
        if any(not math.isfinite(value) for value in (*left, *right)):
            raise ValueError("vectors must be finite")
        denominator = math.sqrt(sum(x*x for x in left)*sum(x*x for x in right))
        if denominator == 0:
            return 0.0
        return max(-1.0, min(1.0, sum(a*b for a,b in zip(left,right))/denominator))

    @staticmethod
    def _sigmoid(x: float) -> float:
        if x >= 0:
            return 1.0/(1.0+math.exp(-x))
        t = math.exp(x)
        return t/(1.0+t)

    @staticmethod
    def _softplus(x: float) -> float:
        return max(0.0,x) + math.log1p(math.exp(-abs(x)))

    def _step(self, center: int, target: int, label: int, rate: float) -> float:
        inp, ctx = self.input_weights[center], self.context_weights[target]
        dot = sum(a*b for a,b in zip(inp,ctx))
        derivative = self._sigmoid(dot)-label
        for d in range(self.dimension):
            a,b = inp[d],ctx[d]
            inp[d] -= rate*derivative*b
            ctx[d] -= rate*derivative*a
        return self._softplus(-dot if label else dot)

    def fit(self, sequences: Sequence[Sequence[int]], *, epochs: int = 5,
            window: int = 2, negatives: int = 2, learning_rate: float = .05) -> list[float]:
        if type(epochs) is not int or not 1 <= epochs <= 30:
            raise ValueError("epochs must be in [1, 30]")
        if type(window) is not int or not 1 <= window <= 5:
            raise ValueError("window must be in [1, 5]")
        if type(negatives) is not int or not 0 <= negatives <= 10:
            raise ValueError("negatives must be in [0, 10]")
        if type(learning_rate) not in (float, int) or not math.isfinite(learning_rate) or not 0 < learning_rate <= 1:
            raise ValueError("learning_rate must be finite in (0, 1]")
        if not isinstance(sequences, (list, tuple)) or len(sequences) > 1000:
            raise ValueError("training corpus must be a bounded list")
        pairs = []
        token_count = 0
        for row in sequences:
            if not isinstance(row, (list, tuple)) or len(row) > 2000:
                raise ValueError("each row must be at most 2000 tokens")
            for token_id in row:
                self._validate(token_id)
            row = [i for i in row if i not in (256,257,258)]
            token_count += len(row)
            if token_count > 15000:
                raise ValueError("training corpus exceeds 15000 tokens")
            for position, center in enumerate(row):
                for neighbor in range(max(0,position-window),min(len(row),position+window+1)):
                    if neighbor != position:
                        pairs.append((center,row[neighbor]))
                        if len(pairs) > 60000:
                            raise ValueError("training pair budget exceeded")
        if not pairs:
            raise ValueError("at least one training context pair is required")
        if len(pairs) * epochs * (negatives + 1) * self.dimension > 2_000_000:
            raise ValueError("training exceeds the compute budget")
        observed = sorted({token_id for pair in pairs for token_id in pair})
        candidates = {target: [x for x in observed if x != target] for target in observed}
        if negatives and len(observed) < 2:
            raise ValueError("negative sampling needs distinct tokens")
        rng = random.Random(self.seed + 104729)
        history = []
        for _ in range(epochs):
            loss, steps = 0.0, 0
            for center, target in pairs:
                loss += self._step(center,target,1,learning_rate)
                steps += 1
                for _ in range(negatives):
                    negative = rng.choice(candidates[target])
                    loss += self._step(center,negative,0,learning_rate)
                    steps += 1
            history.append(loss/steps)
        return history
