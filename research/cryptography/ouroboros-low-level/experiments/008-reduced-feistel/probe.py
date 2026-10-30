#!/usr/bin/env python3
"""Exhaustive single-bit SAC/DDT probe for the EXP-008 toy Feistel cipher.

This is a characterization harness for a 16-bit educational permutation, not a
security test suite or proof. Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from feistel16 import BLOCK_BITS, encrypt_with_round_keys, expand_key


def analyze_key(master_key: int) -> tuple[dict, list[list[float]], list[dict], list[dict]]:
    """Enumerate all 2^15 unordered pairs for each of 16 single-bit deltas."""
    n_pairs = 1 << (BLOCK_BITS - 1)
    round_keys = expand_key(master_key)
    encrypt = lambda block: encrypt_with_round_keys(block, round_keys)
    matrix = [[0.0] * BLOCK_BITS for _ in range(BLOCK_BITS)]
    sac_rows: list[dict] = []
    differential_rows: list[dict] = []
    total_changed = 0

    for input_bit in range(BLOCK_BITS):
        counts = [0] * BLOCK_BITS
        histogram: dict[int, int] = {}
        mask = 1 << input_bit
        for representative in range(n_pairs):
            plaintext = ((representative & ((1 << input_bit) - 1)) |
                         ((representative >> input_bit) << (input_bit + 1)))
            delta = encrypt(plaintext) ^ encrypt(plaintext ^ mask)
            histogram[delta] = histogram.get(delta, 0) + 1
            total_changed += delta.bit_count()
            for output_bit in range(BLOCK_BITS):
                counts[output_bit] += (delta >> output_bit) & 1

        for output_bit, count in enumerate(counts):
            probability = count / n_pairs
            matrix[input_bit][output_bit] = probability
            sac_rows.append({
                "input_bit": input_bit,
                "output_bit": output_bit,
                "changed_count": count,
                "pairs": n_pairs,
                "flip_probability": probability,
                "abs_deviation_from_half": abs(probability - 0.5),
            })

        for output_delta, count in histogram.items():
            differential_rows.append({
                "input_delta": mask,
                "output_delta": output_delta,
                "count": count,
                "pairs": n_pairs,
                "probability": count / n_pairs,
            })

    probabilities = [row["flip_probability"] for row in sac_rows]
    deviations = [abs(p - 0.5) for p in probabilities]
    mean_changed = total_changed / (BLOCK_BITS * n_pairs)
    top_differentials = []
    for input_bit in range(BLOCK_BITS):
        candidates = [row for row in differential_rows if row["input_delta"] == (1 << input_bit)]
        top_differentials.extend(sorted(candidates, key=lambda row: (-row["count"], row["output_delta"]))[:5])

    summary = {
        "experiment": "OUROBOROS-008",
        "design": "W16-K32-Feistel8-S4-P8-KS1",
        "phase": "exhaustive single-bit characterization",
        "master_key": f"0x{master_key:08X}",
        "round_keys": [f"0x{k:02X}" for k in round_keys],
        "block_bits": BLOCK_BITS,
        "key_bits": 32,
        "rounds": 8,
        "pairs_per_input_bit": n_pairs,
        "total_pairs": BLOCK_BITS * n_pairs,
        "sac": {
            "mean_flip_probability": sum(probabilities) / len(probabilities),
            "mean_abs_deviation_from_half": sum(deviations) / len(deviations),
            "max_abs_deviation_from_half": max(deviations),
            "min_flip_probability": min(probabilities),
            "max_flip_probability": max(probabilities),
            "mean_changed_bits_per_pair": mean_changed,
            "ideal_reference_changed_bits": BLOCK_BITS / 2,
        },
        "single_bit_differentials": {
            "max_count": max(row["count"] for row in differential_rows),
            "max_probability": max(row["probability"] for row in differential_rows),
            "distinct_output_deltas_total": len(differential_rows),
            "top_5_per_input_bit": top_differentials,
        },
        "scope": "Exhaustive characterization of the specified toy 16-bit block permutation only. Not production cryptography.",
    }
    return summary, matrix, sac_rows, differential_rows


def save_results(folder: Path, summary: dict, matrix: list[list[float]],
                 sac_rows: list[dict], differential_rows: list[dict]) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (folder / "sac_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["input_bit"] + [f"output_{i}" for i in range(BLOCK_BITS)])
        for i, row in enumerate(matrix):
            writer.writerow([i] + row)
    with (folder / "sac.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sac_rows[0]))
        writer.writeheader()
        writer.writerows(sac_rows)
    with (folder / "ddt_single_bit.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(differential_rows[0]))
        writer.writeheader()
        writer.writerows(sorted(differential_rows, key=lambda row: (row["input_delta"], row["output_delta"])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key", type=lambda value: int(value, 0), default=0x01234567,
                        help="32-bit master key in decimal or 0x-prefixed hexadecimal")
    parser.add_argument("--output", type=Path, default=Path("results/default-key"))
    args = parser.parse_args()
    if not 0 <= args.key <= 0xFFFFFFFF:
        parser.error("--key must fit in 32 bits")
    summary, matrix, sac_rows, differential_rows = analyze_key(args.key)
    save_results(args.output, summary, matrix, sac_rows, differential_rows)
    print(json.dumps(summary, indent=2))
    print(f"Saved: {args.output.resolve()}")


if __name__ == "__main__":
    main()
