"""HEART_003: small educational, byte-level BPE tokenizer trained locally.

UTF-8 byte fallback preserves arbitrary Unicode without unknown tokens.
No network access, external tokenizer, or downloaded vocabulary required.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


class BPETokenizer:
    PAD_ID = 256
    BOS_ID = 257
    EOS_ID = 258
    BASE_VOCAB_SIZE = 259

    def __init__(self, merges: list[tuple[int, int]] | None = None):
        self.merges = list(merges or [])
        self._validate_merges()

    def _validate_merges(self) -> None:
        for offset, pair in enumerate(self.merges):
            if len(pair) != 2 or any(not isinstance(x, int) or x < 0 or x >= self.BASE_VOCAB_SIZE + offset for x in pair):
                raise ValueError("Invalid or out-of-order merge")

    @property
    def vocab_size(self) -> int:
        return self.BASE_VOCAB_SIZE + len(self.merges)

    def train(self, corpus: list[str], vocab_size: int = 512, min_frequency: int = 2) -> None:
        if vocab_size < self.BASE_VOCAB_SIZE:
            raise ValueError("vocab_size too small")
        if min_frequency < 2:
            raise ValueError("min_frequency must be >= 2")
        if not isinstance(corpus, list) or any(not isinstance(s, str) for s in corpus):
            raise TypeError("corpus must be a list of strings")
        words = [list(text.encode("utf-8")) for text in corpus if text]
        self.merges = []
        while self.vocab_size < vocab_size:
            counts = Counter(pair for row in words for pair in zip(row, row[1:]))
            candidates = [pair for pair, freq in counts.items() if freq >= min_frequency]
            if not candidates:
                break
            pair = min(candidates, key=lambda p: (-counts[p], p))
            new_id = self.vocab_size
            self.merges.append(pair)
            words = [self._merge_once(row, pair, new_id) for row in words]

    @staticmethod
    def _merge_once(tokens: list[int], pair: tuple[int, int], replacement: int) -> list[int]:
        result = []
        i = 0
        while i < len(tokens):
            if i + 1 < len(tokens) and (tokens[i], tokens[i + 1]) == pair:
                result.append(replacement)
                i += 2
            else:
                result.append(tokens[i])
                i += 1
        return result

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        tokens = list(text.encode("utf-8"))
        for offset, pair in enumerate(self.merges):
            tokens = self._merge_once(tokens, pair, self.BASE_VOCAB_SIZE + offset)
        return ([self.BOS_ID] + tokens + [self.EOS_ID]) if add_special_tokens else tokens

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
        for offset, (left, right) in enumerate(self.merges):
            vocab[self.BASE_VOCAB_SIZE + offset] = vocab[left] + vocab[right]
        output = bytearray()
        for token_id in token_ids:
            if token_id in (self.PAD_ID, self.BOS_ID, self.EOS_ID) and skip_special_tokens:
                continue
            if token_id not in vocab:
                raise ValueError(f"Unknown or unsupported token ID: {token_id}")
            output.extend(vocab[token_id])
        return output.decode("utf-8")

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps({"format": "heart-byte-bpe-v1", "merges": self.merges}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | Path) -> "BPETokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != "heart-byte-bpe-v1":
            raise ValueError("Unknown tokenizer format")
        return cls([tuple(pair) for pair in data["merges"]])
