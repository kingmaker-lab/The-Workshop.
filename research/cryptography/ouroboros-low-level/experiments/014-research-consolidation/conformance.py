#!/usr/bin/env python3
"""Exhaustive cross-check of the canonical EXP-008 implementation vs oracle."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[4]
EXP008 = REPO_ROOT / "research/cryptography/ouroboros-low-level/experiments/008-reduced-feistel"
sys.path.insert(0, str(EXP008))

from feistel16 import BLOCK_MASK, ROUNDS, decrypt_block, encrypt_with_round_keys, expand_key
from reference_model import (
    reference_decrypt, reference_encrypt, reference_encrypt_with_round_keys,
    reference_expand_key,
)

_KAT_DATA = json.loads((HERE / "known_answers.json").read_text(encoding="utf-8"))
KEYS = tuple(int(entry["key"], 16) for entry in _KAT_DATA["master_keys"])
KNOWN_ANSWERS = {
    int(entry["key"], 16): {
        int(plaintext, 16): int(ciphertext, 16)
        for plaintext, ciphertext in entry["vectors"]
    }
    for entry in _KAT_DATA["master_keys"]
}


def run_exhaustive_conformance() -> dict[str, Any]:
    vector_checks = 0
    schedule_byte_checks = 0
    total_blocks = 0
    per_key = []

    for master_key in KEYS:
        canonical_keys = expand_key(master_key)
        oracle_keys = reference_expand_key(master_key)
        if canonical_keys != oracle_keys:
            raise AssertionError(f"round-key schedule mismatch for 0x{master_key:08X}")
        schedule_byte_checks += ROUNDS

        for plaintext, expected in KNOWN_ANSWERS[master_key].items():
            canonical = encrypt_with_round_keys(plaintext, canonical_keys)
            oracle = reference_encrypt(plaintext, master_key)
            if canonical != expected or oracle != expected:
                raise AssertionError(
                    f"KAT mismatch key=0x{master_key:08X}, P=0x{plaintext:04X}: "
                    f"canonical=0x{canonical:04X}, oracle=0x{oracle:04X}, expected=0x{expected:04X}"
                )
            if decrypt_block(expected, master_key) != plaintext:
                raise AssertionError(f"canonical decrypt KAT mismatch for key=0x{master_key:08X}")
            vector_checks += 1

        seen = bytearray(1 << 13)
        round_trip_checks = 0
        for plaintext in range(BLOCK_MASK + 1):
            canonical = encrypt_with_round_keys(plaintext, canonical_keys)
            oracle = reference_encrypt_with_round_keys(plaintext, oracle_keys)
            if canonical != oracle:
                raise AssertionError(
                    f"oracle mismatch key=0x{master_key:08X}, P=0x{plaintext:04X}"
                )
            index, bit = canonical >> 3, 1 << (canonical & 7)
            if seen[index] & bit:
                raise AssertionError(
                    f"duplicate ciphertext key=0x{master_key:08X}, C=0x{canonical:04X}"
                )
            seen[index] |= bit
            if reference_decrypt(oracle, master_key) != plaintext:
                raise AssertionError(
                    f"reference inverse mismatch key=0x{master_key:08X}, P=0x{plaintext:04X}"
                )
            round_trip_checks += 1

        if sum(byte.bit_count() for byte in seen) != (1 << 16):
            raise AssertionError(f"permutation coverage incomplete for 0x{master_key:08X}")
        total_blocks += round_trip_checks
        per_key.append({
            "master_key": f"0x{master_key:08X}",
            "schedule_match": True,
            "known_answer_vectors": len(KNOWN_ANSWERS[master_key]),
            "full_domain_blocks_compared": round_trip_checks,
            "reference_round_trip_checks": round_trip_checks,
            "canonical_mapping_is_permutation": True,
        })

    return {
        "experiment": "OUROBOROS-014",
        "target": "EXP-008 W16-K32-Feistel8-S4-P8-KS1",
        "method": "Independent specification oracle vs canonical EXP-008 Python implementation",
        "master_keys": [f"0x{x:08X}" for x in KEYS],
        "round_key_byte_comparisons": schedule_byte_checks,
        "known_answer_vector_checks": vector_checks,
        "full_domain_block_comparisons": total_blocks,
        "expected_permutation_checks": len(KEYS),
        "per_key": per_key,
        "scope": "Exhaustive 16-bit block-domain conformance for five selected fixed keys. Not exhaustive over the 32-bit master-key space and not a cryptographic security proof.",
    }


def main() -> None:
    report = run_exhaustive_conformance()
    output = HERE / "results"
    output.mkdir(parents=True, exist_ok=True)
    (output / "conformance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved {output / 'conformance.json'}")


if __name__ == "__main__":
    main()
