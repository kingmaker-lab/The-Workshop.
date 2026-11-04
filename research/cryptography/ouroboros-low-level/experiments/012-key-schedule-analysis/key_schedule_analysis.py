#!/usr/bin/env python3
"""OUROBOROS EXP-012: deterministic analysis of the EXP-008 KS1 key schedule.

The experiment reuses the canonical EXP-008 implementation. It measures
single-bit related-key propagation, selected multi-bit deltas, round-key
byte statistics, output-bit balance/correlation and sampled schedule collisions.

The 32-bit master-key space is NOT exhaustively enumerated.
Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP008 = HERE.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))
from feistel16 import KEY_BITS, KEY_MASK, ROUNDS, expand_key, permute8, rotl8, substitute8

DEFAULT_SAMPLE_COUNT = 8192
DEFAULT_SEED = 0x012_3456
MULTI_BIT_DELTAS = (
    0x00000003, 0x00000005, 0x0000000F, 0x000000FF,
    0x01010101, 0x0F0F0F0F, 0x33333333, 0x55555555,
    0x80000001, 0xFFFFFFFF,
)


def round_constant(round_index: int) -> int:
    if isinstance(round_index, bool) or not isinstance(round_index, int):
        raise TypeError("round_index must be an integer")
    if not 0 <= round_index < ROUNDS:
        raise ValueError("round_index must be in 0..7")
    return (0x9D + 0x3D * round_index) & 0xFF


def ks1_transition(state: int, round_index: int) -> tuple[int, int]:
    """Return (next_state, round_key) for one exact KS1 step."""
    if isinstance(state, bool) or not isinstance(state, int) or not 0 <= state <= KEY_MASK:
        raise ValueError("state must be an unsigned 32-bit integer")
    rc = round_constant(round_index)
    a = (state >> 24) & 0xFF
    b = (state >> 16) & 0xFF
    c = (state >> 8) & 0xFF
    d = state & 0xFF
    mixed = (rotl8(a, 3) + b + rotl8(c, 1) + d + rc) & 0xFF
    t = permute8(substitute8(mixed))
    key_byte = t ^ d
    next_state = ((state << 8) & KEY_MASK) | t
    return next_state, key_byte


def expand_key_reference(master_key: int) -> tuple[int, ...]:
    """Independent transcription used only as a differential cross-check."""
    if isinstance(master_key, bool) or not isinstance(master_key, int):
        raise TypeError("master_key must be an integer")
    if not 0 <= master_key <= KEY_MASK:
        raise ValueError("master_key must fit in 32 bits")
    state = master_key
    result = []
    for round_index in range(ROUNDS):
        state, key_byte = ks1_transition(state, round_index)
        result.append(key_byte)
    return tuple(result)


def schedule_stream(master_key: int) -> int:
    stream = 0
    for index, value in enumerate(expand_key(master_key)):
        stream |= value << (8 * index)
    return stream


def deterministic_keys(sample_count: int, seed: int) -> list[int]:
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 2:
        raise ValueError("sample_count must be an integer >= 2")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = random.Random(seed)
    keys = [rng.getrandbits(KEY_BITS) for _ in range(sample_count)]
    # Ensure the canonical corner cases are always part of the measured set.
    keys[0] = 0x00000000
    keys[1] = 0xFFFFFFFF
    return keys


def _bit(value: int, index: int) -> int:
    return (value >> index) & 1


def _pearson_from_packed(plane_a: int, plane_b: int, count: int,
                         ones_a: int, ones_b: int) -> float:
    if ones_a in (0, count) or ones_b in (0, count):
        return 0.0
    both = (plane_a & plane_b).bit_count()
    p_a = ones_a / count
    p_b = ones_b / count
    covariance = both / count - p_a * p_b
    variance = p_a * (1.0 - p_a) * p_b * (1.0 - p_b)
    return covariance / math.sqrt(variance)


def _output_bitplanes(streams: list[int]) -> list[int]:
    planes = [0] * (ROUNDS * 8)
    for sample_index, stream in enumerate(streams):
        bit = 1 << sample_index
        for output_bit in range(ROUNDS * 8):
            if (stream >> output_bit) & 1:
                planes[output_bit] |= bit
    return planes


def analyze(sample_count: int = DEFAULT_SAMPLE_COUNT, seed: int = DEFAULT_SEED) -> dict[str, Any]:
    keys = deterministic_keys(sample_count, seed)
    baseline_schedules = [expand_key(key) for key in keys]
    reference_checks = all(
        expand_key(key) == expand_key_reference(key)
        for key in (0, 1, 0x01234567, 0x89ABCDEF, KEY_MASK)
    )
    if not reference_checks:
        raise AssertionError("Independent KS1 transcription differs from EXP-008")

    streams = [
        sum(round_key << (8 * round_index) for round_index, round_key in enumerate(schedule))
        for schedule in baseline_schedules
    ]
    distinct_streams = len(set(streams))
    stream_counts = Counter(streams)
    duplicate_stream_groups = sum(1 for count in stream_counts.values() if count > 1)

    # Exact SAC-style related-key influence matrix over the deterministic key sample.
    avalanche_counts = [[0] * (ROUNDS * 8) for _ in range(KEY_BITS)]
    related_rows = []
    all_deltas = tuple(1 << bit for bit in range(KEY_BITS)) + MULTI_BIT_DELTAS
    for delta in all_deltas:
        hamming_distances = []
        per_round_hamming = [0] * ROUNDS
        for master_key, baseline_stream in zip(keys, streams):
            changed_stream = schedule_stream(master_key ^ delta)
            difference = baseline_stream ^ changed_stream
            distance = difference.bit_count()
            hamming_distances.append(distance)
            for round_index in range(ROUNDS):
                per_round_hamming[round_index] += (
                    (difference >> (8 * round_index)) & 0xFF
                ).bit_count()
            if delta & (delta - 1) == 0:
                input_bit = delta.bit_length() - 1
                remaining = difference
                while remaining:
                    lsb = remaining & -remaining
                    output_bit = lsb.bit_length() - 1
                    avalanche_counts[input_bit][output_bit] += 1
                    remaining ^= lsb

        related_rows.append({
            "master_key_delta": f"0x{delta:08X}",
            "input_hamming_weight": delta.bit_count(),
            "sample_count": sample_count,
            "mean_output_stream_hamming": statistics.mean(hamming_distances),
            "mean_output_stream_hamming_fraction": statistics.mean(hamming_distances) / 64,
            "min_output_stream_hamming": min(hamming_distances),
            "max_output_stream_hamming": max(hamming_distances),
            "mean_round_key_hamming": [
                value / sample_count for value in per_round_hamming
            ],
        })

    avalanche_matrix = []
    for input_bit in range(KEY_BITS):
        for output_bit in range(ROUNDS * 8):
            flips = avalanche_counts[input_bit][output_bit]
            avalanche_matrix.append({
                "master_key_bit": input_bit,
                "round_index": output_bit // 8,
                "round_key_output_bit": output_bit % 8,
                "output_stream_bit": output_bit,
                "flip_count": flips,
                "flip_probability": flips / sample_count,
            })

    byte_rows = []
    for round_index in range(ROUNDS):
        values = [schedule[round_index] for schedule in baseline_schedules]
        counts = Counter(values)
        probabilities = [count / sample_count for count in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probabilities)
        bit_ones = [sum(_bit(value, bit) for value in values) for bit in range(8)]
        byte_rows.append({
            "round_index": round_index,
            "round_constant": f"0x{round_constant(round_index):02X}",
            "distinct_round_key_bytes": len(counts),
            "empirical_byte_entropy_bits": entropy,
            "max_byte_frequency": max(counts.values()),
            "max_byte_probability": max(counts.values()) / sample_count,
            "output_bit_one_fractions": [value / sample_count for value in bit_ones],
            "max_output_bit_bias": max(abs(value / sample_count - 0.5) for value in bit_ones),
        })

    planes = _output_bitplanes(streams)
    ones = [plane.bit_count() for plane in planes]
    bit_correlations = []
    for first in range(ROUNDS * 8):
        for second in range(first + 1, ROUNDS * 8):
            corr = _pearson_from_packed(
                planes[first], planes[second], sample_count, ones[first], ones[second]
            )
            bit_correlations.append({
                "first_stream_bit": first,
                "second_stream_bit": second,
                "pearson_correlation": corr,
                "absolute_correlation": abs(corr),
            })

    per_round_correlations = []
    for round_index in range(ROUNDS):
        selected = [
            row for row in bit_correlations
            if row["first_stream_bit"] // 8 == round_index
            and row["second_stream_bit"] // 8 == round_index
        ]
        per_round_correlations.append({
            "round_index": round_index,
            "max_abs_within_round_key_bit_correlation": max(
                (row["absolute_correlation"] for row in selected), default=0.0
            ),
            "mean_abs_within_round_key_bit_correlation": statistics.mean(
                (row["absolute_correlation"] for row in selected)
            ) if selected else 0.0,
        })

    return {
        "experiment": "OUROBOROS-012",
        "target": "EXP-008 KS1 32-bit master key -> eight 8-bit round keys",
        "method": {
            "sample_count": sample_count,
            "seed": seed,
            "sampling": "deterministic pseudorandom sample with 0x00000000 and 0xFFFFFFFF pinned",
            "master_key_space_size": 1 << KEY_BITS,
            "master_key_space_exhaustively_enumerated": False,
            "single_bit_related_key_deltas": KEY_BITS,
            "additional_multi_bit_deltas": [f"0x{x:08X}" for x in MULTI_BIT_DELTAS],
            "output_stream_bits": ROUNDS * 8,
            "reference_implementation_cross_checks": 5,
        },
        "round_constants": [f"0x{round_constant(r):02X}" for r in range(ROUNDS)],
        "round_constants_all_distinct": len({round_constant(r) for r in range(ROUNDS)}) == ROUNDS,
        "independent_reference_implementation_matches": reference_checks,
        "schedule_stream_sample": {
            "distinct_streams": distinct_streams,
            "duplicate_stream_groups": duplicate_stream_groups,
            "sample_collision_observed": distinct_streams != sample_count,
            "interpretation": "No collision in a finite sample is not proof that the 32->64-bit schedule mapping is injective.",
        },
        "round_key_byte_statistics": byte_rows,
        "related_key_deltas": related_rows,
        "avalanche_matrix": avalanche_matrix,
        "round_key_bit_correlations": per_round_correlations,
        "output_stream_bit_correlations": {
            "pair_count": len(bit_correlations),
            "max_abs_pearson": max(row["absolute_correlation"] for row in bit_correlations),
            "mean_abs_pearson": statistics.mean(row["absolute_correlation"] for row in bit_correlations),
        },
        "limits": [
            "The 2^32 master-key space was not exhaustively enumerated.",
            "Empirical byte entropy and correlations describe only the stated deterministic sample.",
            "No collision in the sample does not prove injectivity or absence of equivalent master keys.",
            "Related-key avalanche statistics are diagnostic measurements, not a cryptographic security proof.",
            "Results apply only to the EXP-008 KS1 schedule, not to SHA-256 or the separate 64-bit assembly state transition.",
        ],
    }


def save_results(report: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with (output / "avalanche_matrix.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["master_key_bit", "round_index", "round_key_output_bit", "output_stream_bit", "flip_count", "flip_probability"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["avalanche_matrix"])

    with (output / "related_key_deltas.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key_delta", "input_hamming_weight", "sample_count",
            "mean_output_stream_hamming", "mean_output_stream_hamming_fraction",
            "min_output_stream_hamming", "max_output_stream_hamming",
        ] + [f"round_{r}_mean_hamming" for r in range(ROUNDS)]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["related_key_deltas"]:
            writer.writerow({
                **{key: value for key, value in row.items() if key != "mean_round_key_hamming"},
                **{f"round_{r}_mean_hamming": value for r, value in enumerate(row["mean_round_key_hamming"])},
            })

    with (output / "round_key_statistics.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "round_index", "round_constant", "distinct_round_key_bytes",
            "empirical_byte_entropy_bits", "max_byte_frequency", "max_byte_probability",
            "max_output_bit_bias",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["round_key_byte_statistics"]:
            writer.writerow({key: value for key, value in row.items() if key != "output_bit_one_fractions"})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLE_COUNT)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    report = analyze(args.samples, args.seed)
    save_results(report, args.output)
    print(json.dumps({
        "experiment": report["experiment"],
        "sample_count": report["method"]["sample_count"],
        "distinct_schedule_streams": report["schedule_stream_sample"]["distinct_streams"],
        "round_constants": report["round_constants"],
        "round_constants_all_distinct": report["round_constants_all_distinct"],
        "reference_matches": report["independent_reference_implementation_matches"],
        "output_stream_max_abs_bit_correlation": report["output_stream_bit_correlations"]["max_abs_pearson"],
    }, indent=2))


if __name__ == "__main__":
    main()
