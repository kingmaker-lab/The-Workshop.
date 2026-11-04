#!/usr/bin/env python3
"""OUROBOROS EXP-013: cross-round subkey dependency and related-key patterns.

Uses the canonical EXP-008 KS1 schedule. All master-key sampling is deterministic
and explicitly bounded. No exhaustive 2^32 master-key enumeration is claimed.
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
from feistel16 import KEY_MASK, ROUNDS, expand_key

DEFAULT_SEED = 0x013_2026
DEFAULT_MAIN_SAMPLES = 8192
DEFAULT_DENSE_SAMPLES = 1024
OUTPUT_BITS = ROUNDS * 8


def validate_sample_count(value: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 2:
        raise ValueError(f"{name} must be an integer >= 2")


def sample_keys(count: int, seed: int) -> list[int]:
    validate_sample_count(count, "count")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = random.Random(seed)
    result = [rng.getrandbits(32) for _ in range(count)]
    result[0] = 0
    result[1] = KEY_MASK
    return result


def schedule_stream(master_key: int) -> int:
    result = 0
    for round_index, byte in enumerate(expand_key(master_key)):
        result |= byte << (8 * round_index)
    return result


def output_bitplanes(streams: list[int]) -> list[int]:
    planes = [0] * OUTPUT_BITS
    for sample_index, stream in enumerate(streams):
        sample_mask = 1 << sample_index
        remaining = stream
        while remaining:
            low = remaining & -remaining
            bit_index = low.bit_length() - 1
            planes[bit_index] |= sample_mask
            remaining ^= low
    return planes


def joint_metrics(plane_a: int, plane_b: int, count: int) -> dict[str, float | int]:
    ones_a = plane_a.bit_count()
    ones_b = plane_b.bit_count()
    both = (plane_a & plane_b).bit_count()
    n11 = both
    n10 = ones_a - both
    n01 = ones_b - both
    n00 = count - n11 - n10 - n01

    p_a = ones_a / count
    p_b = ones_b / count
    if p_a in (0.0, 1.0) or p_b in (0.0, 1.0):
        pearson = 0.0
    else:
        covariance = n11 / count - p_a * p_b
        pearson = covariance / math.sqrt(p_a * (1 - p_a) * p_b * (1 - p_b))

    cells = (n00, n01, n10, n11)
    row_marginals = (n00 + n01, n10 + n11)
    col_marginals = (n00 + n10, n01 + n11)
    mutual_information = 0.0
    for index, cell in enumerate(cells):
        if not cell:
            continue
        row = index // 2
        col = index % 2
        expected = (row_marginals[row] * col_marginals[col]) / count
        mutual_information += (cell / count) * math.log2(cell / expected)

    return {
        "n00": n00, "n01": n01, "n10": n10, "n11": n11,
        "pearson": pearson,
        "mutual_information_bits": mutual_information,
        "bias_a": abs(p_a - 0.5),
        "bias_b": abs(p_b - 0.5),
    }


def bit_pair_analysis(streams: list[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    planes = output_bitplanes(streams)
    rows = []
    for first in range(OUTPUT_BITS):
        for second in range(first + 1, OUTPUT_BITS):
            metric = joint_metrics(planes[first], planes[second], len(streams))
            rows.append({
                "first_round": first // 8,
                "first_bit": first % 8,
                "first_stream_bit": first,
                "second_round": second // 8,
                "second_bit": second % 8,
                "second_stream_bit": second,
                **metric,
            })
    cross_round = [row for row in rows if row["first_round"] != row["second_round"]]
    within_round = [row for row in rows if row["first_round"] == row["second_round"]]
    ordered_by_mi = sorted(rows, key=lambda row: (-row["mutual_information_bits"], -abs(row["pearson"])))
    ordered_by_corr = sorted(rows, key=lambda row: -abs(row["pearson"]))
    summary = {
        "sample_count": len(streams),
        "output_bit_pairs": len(rows),
        "cross_round_pairs": len(cross_round),
        "within_round_pairs": len(within_round),
        "max_abs_pearson_all_pairs": max(abs(row["pearson"]) for row in rows),
        "mean_abs_pearson_all_pairs": statistics.mean(abs(row["pearson"]) for row in rows),
        "max_mutual_information_all_pairs_bits": max(row["mutual_information_bits"] for row in rows),
        "mean_mutual_information_all_pairs_bits": statistics.mean(row["mutual_information_bits"] for row in rows),
        "max_abs_pearson_cross_round": max(abs(row["pearson"]) for row in cross_round),
        "mean_abs_pearson_cross_round": statistics.mean(abs(row["pearson"]) for row in cross_round),
        "max_mutual_information_cross_round_bits": max(row["mutual_information_bits"] for row in cross_round),
        "mean_mutual_information_cross_round_bits": statistics.mean(row["mutual_information_bits"] for row in cross_round),
        "top_20_mutual_information_pairs": ordered_by_mi[:20],
        "top_20_absolute_correlation_pairs": ordered_by_corr[:20],
    }
    return rows, summary


def input_output_bit_dependencies(keys: list[int], streams: list[int]) -> list[dict[str, Any]]:
    n = len(keys)
    key_planes = [0] * 32
    for index, key in enumerate(keys):
        mask = 1 << index
        remaining = key
        while remaining:
            low = remaining & -remaining
            key_planes[low.bit_length() - 1] |= mask
            remaining ^= low
    output_planes = output_bitplanes(streams)
    rows = []
    for input_bit in range(32):
        for output_bit in range(OUTPUT_BITS):
            metric = joint_metrics(key_planes[input_bit], output_planes[output_bit], n)
            rows.append({
                "master_key_bit": input_bit,
                "round_index": output_bit // 8,
                "round_key_bit": output_bit % 8,
                "output_stream_bit": output_bit,
                **metric,
            })
    return rows


def related_key_unit_deltas(keys: list[int], base_streams: list[int]) -> list[dict[str, Any]]:
    n = len(keys)
    rows = []
    for input_bit in range(32):
        delta = 1 << input_bit
        total = [0] * ROUNDS
        minimum = [65] * ROUNDS
        maximum = [0] * ROUNDS
        whole_distances = []
        for key, baseline in zip(keys, base_streams):
            changed = schedule_stream(key ^ delta)
            diff = baseline ^ changed
            whole_distances.append(diff.bit_count())
            for round_index in range(ROUNDS):
                distance = ((diff >> (8 * round_index)) & 0xFF).bit_count()
                total[round_index] += distance
                minimum[round_index] = min(minimum[round_index], distance)
                maximum[round_index] = max(maximum[round_index], distance)
        rows.append({
            "input_bit": input_bit,
            "master_key_delta": f"0x{delta:08X}",
            "input_weight": 1,
            "sample_count": n,
            "mean_total_output_hamming": statistics.mean(whole_distances),
            "mean_total_output_fraction": statistics.mean(whole_distances) / 64,
            "min_total_output_hamming": min(whole_distances),
            "max_total_output_hamming": max(whole_distances),
            "mean_hamming_per_round": [value / n for value in total],
            "min_hamming_per_round": minimum,
            "max_hamming_per_round": maximum,
        })
    return rows


def dense_byte_delta_scan(keys: list[int]) -> list[dict[str, Any]]:
    """Test all 255 nonzero byte deltas at each master-key byte position."""
    n = len(keys)
    base = [schedule_stream(key) for key in keys]
    rows = []
    for byte_position in range(4):
        for delta_byte in range(1, 256):
            delta = delta_byte << (8 * byte_position)
            total_hamming = []
            per_round_total = [0] * ROUNDS
            per_round_min = [65] * ROUNDS
            per_round_max = [0] * ROUNDS
            for key, original in zip(keys, base):
                changed = schedule_stream(key ^ delta)
                diff = original ^ changed
                total_hamming.append(diff.bit_count())
                for round_index in range(ROUNDS):
                    distance = ((diff >> (8 * round_index)) & 0xFF).bit_count()
                    per_round_total[round_index] += distance
                    per_round_min[round_index] = min(per_round_min[round_index], distance)
                    per_round_max[round_index] = max(per_round_max[round_index], distance)
            mean_total = statistics.mean(total_hamming)
            rows.append({
                "master_key_byte_position": byte_position,
                "byte_delta": delta_byte,
                "master_key_delta": f"0x{delta:08X}",
                "delta_weight": delta_byte.bit_count(),
                "sample_count": n,
                "mean_total_output_hamming": mean_total,
                "mean_total_output_fraction": mean_total / 64,
                "min_total_output_hamming": min(total_hamming),
                "max_total_output_hamming": max(total_hamming),
                "mean_hamming_per_round": [value / n for value in per_round_total],
                "min_hamming_per_round": per_round_min,
                "max_hamming_per_round": per_round_max,
            })
    return rows


def summarize_dense_scan(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall = [row["mean_total_output_hamming"] for row in rows]
    by_position = []
    for pos in range(4):
        selected = [row for row in rows if row["master_key_byte_position"] == pos]
        ordered_low = sorted(selected, key=lambda row: (row["mean_total_output_hamming"], row["byte_delta"]))
        ordered_high = sorted(selected, key=lambda row: (-row["mean_total_output_hamming"], row["byte_delta"]))
        by_position.append({
            "master_key_byte_position": pos,
            "deltas_tested": len(selected),
            "mean_of_delta_mean_hamming": statistics.mean(row["mean_total_output_hamming"] for row in selected),
            "minimum_delta_mean_hamming": ordered_low[0]["mean_total_output_hamming"],
            "minimum_delta": ordered_low[0]["master_key_delta"],
            "maximum_delta_mean_hamming": ordered_high[0]["mean_total_output_hamming"],
            "maximum_delta": ordered_high[0]["master_key_delta"],
        })
    low = sorted(rows, key=lambda row: (row["mean_total_output_hamming"], row["master_key_delta"]))[:20]
    high = sorted(rows, key=lambda row: (-row["mean_total_output_hamming"], row["master_key_delta"]))[:20]
    return {
        "deltas_tested": len(rows),
        "byte_positions_tested": 4,
        "sample_count_per_delta": rows[0]["sample_count"] if rows else 0,
        "overall_mean_of_delta_mean_hamming": statistics.mean(overall),
        "overall_minimum_delta_mean_hamming": min(overall),
        "overall_maximum_delta_mean_hamming": max(overall),
        "by_byte_position": by_position,
        "lowest_20_deltas": low,
        "highest_20_deltas": high,
    }


def analyze(main_samples: int = DEFAULT_MAIN_SAMPLES,
            dense_samples: int = DEFAULT_DENSE_SAMPLES,
            seed: int = DEFAULT_SEED) -> dict[str, Any]:
    validate_sample_count(main_samples, "main_samples")
    validate_sample_count(dense_samples, "dense_samples")
    main_keys = sample_keys(main_samples, seed)
    main_streams = [schedule_stream(key) for key in main_keys]
    pair_rows, pair_summary = bit_pair_analysis(main_streams)
    io_rows = input_output_bit_dependencies(main_keys, main_streams)
    unit_rows = related_key_unit_deltas(main_keys, main_streams)

    dense_keys = sample_keys(dense_samples, seed ^ 0x5A5A5A5A)
    dense_rows = dense_byte_delta_scan(dense_keys)
    dense_summary = summarize_dense_scan(dense_rows)

    per_round_io = []
    for round_index in range(ROUNDS):
        selected = [row for row in io_rows if row["round_index"] == round_index]
        ordered = sorted(selected, key=lambda row: (row["flip_probability"], row["master_key_bit"], row["round_key_bit"]))
        per_round_io.append({
            "round_index": round_index,
            "mean_flip_probability": statistics.mean(row["flip_probability"] for row in selected),
            "min_flip_probability": min(row["flip_probability"] for row in selected),
            "max_flip_probability": max(row["flip_probability"] for row in selected),
            "max_abs_input_output_pearson": max(abs(row["pearson"]) for row in selected),
            "max_input_output_mutual_information_bits": max(row["mutual_information_bits"] for row in selected),
            "lowest_10_influences": ordered[:10],
        })

    return {
        "experiment": "OUROBOROS-013",
        "target": "EXP-008 KS1 master-key to 64-bit round-key stream",
        "method": {
            "main_sample_count": main_samples,
            "dense_delta_sample_count": dense_samples,
            "seed": seed,
            "sample_generation": "deterministic pseudorandom; zero and all-one master keys pinned",
            "master_key_space_size": 1 << 32,
            "master_key_space_exhaustively_enumerated": False,
            "output_stream_bits": OUTPUT_BITS,
            "output_bit_pair_count": OUTPUT_BITS * (OUTPUT_BITS - 1) // 2,
            "cross_round_output_bit_pair_count": sum(8 * 8 for first in range(ROUNDS) for second in range(first + 1, ROUNDS)),
            "unit_related_key_deltas": 32,
            "dense_byte_delta_scan": "all 255 nonzero byte deltas at each of four master-key byte positions",
            "dense_byte_delta_count": 4 * 255,
            "mutual_information": "empirical pairwise MI for binary output bits; estimates pairwise dependence only and has finite-sample bias",
        },
        "cross_round_and_output_bit_dependencies": pair_summary,
        "master_key_to_round_key_bit_dependencies": {
            "matrix_dimensions": [32, 64],
            "rows": io_rows,
            "per_round_summary": per_round_io,
        },
        "unit_related_key_deltas": unit_rows,
        "dense_byte_delta_scan": {
            "summary": dense_summary,
            "rows": dense_rows,
        },
        "interpretation_limits": [
            "No exhaustive enumeration of all 2^32 master keys was performed.",
            "Empirical Pearson correlation and mutual information do not prove independence or dependence outside the stated deterministic sample.",
            "Finite-sample mutual information has positive estimation bias; compare against sample size and use as a diagnostic, not a p-value.",
            "A low Hamming-distance response for a related-key delta is a diffusion warning, not by itself a practical key-recovery attack.",
            "The 64-bit emitted schedule stream is a deterministic 32-to-64-bit mapping; this sample does not prove injectivity or rule out equivalent master keys.",
            "Results apply only to EXP-008 KS1 and the toy cipher, not to the separate 64-bit Assembly state transition or SHA-256.",
        ],
    }


def save_results(report: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with (output / "output_bit_dependencies.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "first_round", "first_bit", "first_stream_bit", "second_round", "second_bit",
            "second_stream_bit", "pearson", "mutual_information_bits", "n00", "n01", "n10", "n11",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["_pair_rows"])

    with (output / "master_to_subkey_dependencies.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key_bit", "round_index", "round_key_bit", "output_stream_bit",
            "pearson", "mutual_information_bits", "flip_probability", "n00", "n01", "n10", "n11",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["_io_rows"])

    with (output / "related_key_unit_deltas.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "input_bit", "master_key_delta", "input_weight", "sample_count",
            "mean_total_output_hamming", "mean_total_output_fraction",
            "min_total_output_hamming", "max_total_output_hamming",
        ] + [f"round_{r}_mean_hamming" for r in range(ROUNDS)]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["unit_related_key_deltas"]:
            writer.writerow({
                **{key: value for key, value in row.items() if key not in (
                    "mean_hamming_per_round", "min_hamming_per_round", "max_hamming_per_round"
                )},
                **{f"round_{r}_mean_hamming": value for r, value in enumerate(row["mean_hamming_per_round"])},
            })

    with (output / "dense_byte_delta_scan.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key_byte_position", "byte_delta", "master_key_delta", "delta_weight",
            "sample_count", "mean_total_output_hamming", "mean_total_output_fraction",
            "min_total_output_hamming", "max_total_output_hamming",
        ] + [f"round_{r}_mean_hamming" for r in range(ROUNDS)]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in report["dense_byte_delta_scan"]["rows"]:
            writer.writerow({
                **{key: value for key, value in row.items() if key not in (
                    "mean_hamming_per_round", "min_hamming_per_round", "max_hamming_per_round"
                )},
                **{f"round_{r}_mean_hamming": value for r, value in enumerate(row["mean_hamming_per_round"])},
            })

    # Remove large internal matrices from the compact summary file after CSV export.
    compact = dict(report)
    compact.pop("_pair_rows", None)
    compact.pop("_io_rows", None)
    (output / "summary_compact.json").write_text(json.dumps(compact, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=DEFAULT_MAIN_SAMPLES)
    parser.add_argument("--dense-samples", type=int, default=DEFAULT_DENSE_SAMPLES)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    report = analyze(args.samples, args.dense_samples, args.seed)
    save_results(report, args.output)
    print(json.dumps({
        "experiment": report["experiment"],
        "main_sample_count": args.samples,
        "dense_delta_sample_count": args.dense_samples,
        "output_bit_pairs": report["cross_round_and_output_bit_dependencies"]["output_bit_pairs"],
        "max_abs_cross_round_pearson": report["cross_round_and_output_bit_dependencies"]["max_abs_pearson_cross_round"],
        "max_cross_round_mutual_information_bits": report["cross_round_and_output_bit_dependencies"]["max_mutual_information_cross_round_bits"],
        "dense_delta_count": report["dense_byte_delta_scan"]["summary"]["deltas_tested"],
        "lowest_delta_mean_hamming": report["dense_byte_delta_scan"]["summary"]["overall_minimum_delta_mean_hamming"],
        "highest_delta_mean_hamming": report["dense_byte_delta_scan"]["summary"]["overall_maximum_delta_mean_hamming"],
    }, indent=2))


if __name__ == "__main__":
    main()
