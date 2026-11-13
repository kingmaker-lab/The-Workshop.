"""HEART_005: small, reproducible single-head causal self-attention.

Scaled dot-product attention with a strict lower-triangular mask, optional
sinusoidal positions, and deterministic *untrained* Q/K/V projections.
Educational forward pass only: not an LLM, Transformer or trained decoder.
No networking, model downloads, external libraries or persistence.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence

from .embeddings import TokenEmbeddings
from .tokenizer import BPETokenizer


@dataclass(frozen=True, slots=True)
class AttentionResult:
    token_ids: tuple[int, ...]
    weights: tuple[tuple[float, ...], ...]
    vectors: tuple[tuple[float, ...], ...]


class CausalAttention:
    """Deterministic, bounded, single-head Q/K/V attention with a causal mask."""

    def __init__(self, dimension: int = 8, seed: int = 17, max_tokens: int = 48):
        if type(dimension) is not int or not 2 <= dimension <= 64:
            raise ValueError("dimension must be an integer in [2, 64]")
        if type(seed) is not int:
            raise TypeError("seed must be an integer")
        if type(max_tokens) is not int or not 1 <= max_tokens <= 64:
            raise ValueError("max_tokens must be an integer in [1, 64]")
        self.dimension = dimension
        self.seed = seed
        self.max_tokens = max_tokens
        rng = random.Random(seed)
        scale = 1.0 / math.sqrt(dimension)
        def matrix() -> tuple[tuple[float, ...], ...]:
            return tuple(tuple(rng.uniform(-scale, scale) for _ in range(dimension))
                         for _ in range(dimension))
        self.query_weights = matrix()
        self.key_weights = matrix()
        self.value_weights = matrix()

    def _project(self, vector: Sequence[float], weights: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
        return tuple(sum(vector[k] * weights[k][j] for k in range(self.dimension))
                     for j in range(self.dimension))

    def _position(self, position: int) -> tuple[float, ...]:
        return tuple(
            math.sin(position / 10000 ** (2 * (d // 2) / self.dimension))
            if d % 2 == 0 else
            math.cos(position / 10000 ** (2 * (d // 2) / self.dimension))
            for d in range(self.dimension)
        )

    def forward(self, token_ids: Sequence[int], embeddings: TokenEmbeddings,
                *, add_positions: bool = True) -> AttentionResult:
        """Attend only to non-PAD tokens at positions <= the current query."""
        if not isinstance(embeddings, TokenEmbeddings):
            raise TypeError("embeddings must be a TokenEmbeddings instance")
        if embeddings.dimension != self.dimension:
            raise ValueError("embedding and attention dimensions must agree")
        if not isinstance(token_ids, (list, tuple)):
            raise TypeError("token_ids must be a list or tuple")
        if not 1 <= len(token_ids) <= self.max_tokens:
            raise ValueError("token_ids must be nonempty and within max_tokens")
        if type(add_positions) is not bool:
            raise TypeError("add_positions must be boolean")
        ids = tuple(token_ids)
        # lookup validates every ID and returns independent vectors
        vectors = embeddings.lookup(ids)
        for vector in vectors:
            if any(not math.isfinite(x) or abs(x) > 1_000_000 for x in vector):
                raise ValueError("embedding values must be finite and bounded")
        inputs = []
        for pos, vector in enumerate(vectors):
            encoding = self._position(pos) if add_positions else (0.0,) * self.dimension
            inputs.append(tuple(vector[d] + encoding[d] for d in range(self.dimension)))
        q = [self._project(vector, self.query_weights) for vector in inputs]
        k = [self._project(vector, self.key_weights) for vector in inputs]
        v = [self._project(vector, self.value_weights) for vector in inputs]
        zero = (0.0,) * self.dimension
        weights_rows: list[tuple[float, ...]] = []
        output_rows: list[tuple[float, ...]] = []
        scale = 1.0 / math.sqrt(self.dimension)
        for pos, token_id in enumerate(ids):
            if token_id == BPETokenizer.PAD_ID:
                weights_rows.append((0.0,) * len(ids))
                output_rows.append(zero)
                continue
            valid = [j for j in range(pos + 1) if ids[j] != BPETokenizer.PAD_ID]
            # Current token is valid, so the mask always allows at least one key.
            logits = [sum(a * b for a, b in zip(q[pos], k[j])) * scale for j in valid]
            maximum = max(logits)
            exps = [math.exp(score - maximum) for score in logits]
            denominator = sum(exps)
            row = [0.0] * len(ids)
            for j, numerator in zip(valid, exps):
                row[j] = numerator / denominator
            weights_rows.append(tuple(row))
            output_rows.append(tuple(
                sum(row[j] * v[j][d] for j in valid) for d in range(self.dimension)
            ))
        return AttentionResult(ids, tuple(weights_rows), tuple(output_rows))
