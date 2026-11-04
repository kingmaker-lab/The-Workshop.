#!/usr/bin/env python3
"""EXP-010: exhaustive single-bit differential and basis-mask linear analysis.

Analyzes every one-bit input difference and every weight-one input/output
linear-mask pair for each Feistel prefix from 1 through 8 rounds.

This is NOT a full 16-bit DDT or LAT, and is not a security proof.
Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EXP008 = HERE.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))
from feistel16 import BLOCK_BITS, BLOCK_MASK, ROUNDS, expand_key, round_function

DOMAIN = 1 << BLOCK_BITS
PAIR_COUNT = DOMAIN // 2
DEFAULT_KEYS = (0x01234567, 0x00000000, 0xFFFFFFFF)


def round_step(block: int, round_key: int) -> int:
    left, right = (block >> 8) & 0xFF, block & 0xFF
    return ((right << 8) | (left ^ round_function(right, round_key))) & BLOCK_MASK


def encrypt_prefix(block: int, round_keys: tuple[int, ...], rounds: int) -> int:
    if not 1 <= rounds <= ROUNDS:
        raise ValueError(f"rounds must be in 1..{ROUNDS}")
    state = block
    for round_key in round_keys[:rounds]:
        state = round_step(state, round_key)
    return state


def decrypt_prefix(block: int, round_keys: tuple[int, ...], rounds: int) -> int:
    if not 1 <= rounds <= ROUNDS:
        raise ValueError(f"rounds must be in 1..{ROUNDS}")
    left, right = (block >> 8) & 0xFF, block & 0xFF
    for round_key in reversed(round_keys[:rounds]):
        left, right = right ^ round_function(left, round_key), left
    return ((left << 8) | right) & BLOCK_MASK


def _representative(rep: int, input_bit: int) -> int:
    lower = (1 << input_bit) - 1
    return (rep & lower) | ((rep >> input_bit) << (input_bit + 1))


def _input_bitsets() -> list[int]:
    packed = []
    for bit in range(BLOCK_BITS):
        data = bytearray(DOMAIN // 8)
        for start in range(0, DOMAIN, 8):
            value = 0
            for offset in range(8):
                value |= (((start + offset) >> bit) & 1) << offset
            data[start // 8] = value
        packed.append(int.from_bytes(data, "little"))
    return packed


INPUT_BITSETS = _input_bitsets()


def _output_bitsets(outputs: list[int]) -> list[int]:
    planes = [bytearray(DOMAIN // 8) for _ in range(BLOCK_BITS)]
    for start in range(0, DOMAIN, 8):
        group = outputs[start:start + 8]
        byte_index = start // 8
        for bit in range(BLOCK_BITS):
            value = 0
            for offset, block in enumerate(group):
                value |= ((block >> bit) & 1) << offset
            planes[bit][byte_index] = value
    return [int.from_bytes(bytes(plane), "little") for plane in planes]


def _differential_row(outputs: list[int], input_bit: int) -> dict[str, Any]:
    histogram: Counter[int] = Counter()
    delta = 1 << input_bit
    for rep in range(PAIR_COUNT):
        x = _representative(rep, input_bit)
        histogram[outputs[x] ^ outputs[x ^ delta]] += 1
    maximum = max(histogram.values())
    winners = sorted(value for value, count in histogram.items() if count == maximum)
    return {
        "input_bit": input_bit,
        "input_delta": f"0x{delta:04X}",
        "pairs": PAIR_COUNT,
        "max_count": maximum,
        "max_probability": maximum / PAIR_COUNT,
        "distinct_output_differences": len(histogram),
        "max_output_differences": [f"0x{x:04X}" for x in winners[:16]],
    }


def _basis_lat(outputs: list[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    out_bits = _output_bitsets(outputs)
    cells = []
    for input_bit, input_plane in enumerate(INPUT_BITSETS):
        for output_bit, output_plane in enumerate(out_bits):
            mismatches = (input_plane ^ output_plane).bit_count()
            walsh = DOMAIN - 2 * mismatches
            cells.append({
                "input_bit": input_bit,
                "output_bit": output_bit,
                "input_mask": f"0x{1 << input_bit:04X}",
                "output_mask": f"0x{1 << output_bit:04X}",
                "walsh": walsh,
                "correlation": walsh / DOMAIN,
                "bias": walsh / (2 * DOMAIN),
            })
    max_abs = max(abs(cell["walsh"]) for cell in cells)
    max_cells = [cell for cell in cells if abs(cell["walsh"]) == max_abs]
    summary = {
        "mask_pairs": len(cells),
        "max_abs_walsh": max_abs,
        "max_abs_correlation": max_abs / DOMAIN,
        "max_abs_bias": max_abs / (2 * DOMAIN),
        "max_cells_count": len(max_cells),
        "mean_abs_correlation": statistics.mean(abs(c["correlation"]) for c in cells),
        "max_cells": max_cells[:32],
    }
    return cells, summary


def analyze_key(master_key: int) -> dict[str, Any]:
    if isinstance(master_key, bool) or not isinstance(master_key, int) or not 0 <= master_key <= 0xFFFFFFFF:
        raise ValueError("master_key must be an unsigned 32-bit integer")
    round_keys = expand_key(master_key)
    states = list(range(DOMAIN))
    round_results = []

    for round_number, round_key in enumerate(round_keys, start=1):
        states = [round_step(state, round_key) for state in states]
        differential_rows = [_differential_row(states, bit) for bit in range(BLOCK_BITS)]
        lat_cells, lat_summary = _basis_lat(states)
        round_results.append({
            "rounds": round_number,
            "round_key": f"0x{round_key:02X}",
            "differential_single_bit": {
                "input_pairs_per_delta": PAIR_COUNT,
                "total_pairs": PAIR_COUNT * BLOCK_BITS,
                "max_count": max(row["max_count"] for row in differential_rows),
                "max_probability": max(row["max_probability"] for row in differential_rows),
                "mean_row_max_probability": statistics.mean(row["max_probability"] for row in differential_rows),
                "min_distinct_output_differences": min(row["distinct_output_differences"] for row in differential_rows),
                "max_distinct_output_differences": max(row["distinct_output_differences"] for row in differential_rows),
                "input_delta_rows": differential_rows,
            },
            "linear_basis_masks": lat_summary,
            "linear_cells": lat_cells,
        })

    return {
        "master_key": f"0x{master_key:08X}",
        "round_keys": [f"0x{x:02X}" for x in round_keys],
        "rounds": round_results,
    }


def analyze(keys: tuple[int, ...] = DEFAULT_KEYS) -> dict[str, Any]:
    reports = [analyze_key(key) for key in keys]
    headline = []
    for report in reports:
        for round_report in report["rounds"]:
            headline.append({
                "master_key": report["master_key"],
                "rounds": round_report["rounds"],
                "max_single_bit_differential_probability": round_report["differential_single_bit"]["max_probability"],
                "mean_row_max_differential_probability": round_report["differential_single_bit"]["mean_row_max_probability"],
                "max_basis_mask_correlation": round_report["linear_basis_masks"]["max_abs_correlation"],
                "mean_abs_basis_mask_correlation": round_report["linear_basis_masks"]["mean_abs_correlation"],
            })
    return {
        "experiment": "OUROBOROS-010",
        "design": "EXP-008 W16-K32-Feistel8-S4-P8-KS1",
        "method": {
            "round_prefixes": list(range(1, ROUNDS + 1)),
            "master_keys": [f"0x{k:08X}" for k in keys],
            "domain_states_per_prefix": DOMAIN,
            "single_bit_input_differences": BLOCK_BITS,
            "unordered_pairs_per_single_bit_difference": PAIR_COUNT,
            "differential_pair_comparisons_per_key_per_prefix": PAIR_COUNT * BLOCK_BITS,
            "linear_analysis": "exact 16x16 basis-mask slice: all weight-one input masks against all weight-one output masks",
            "linear_mask_pairs_per_key_per_prefix": BLOCK_BITS * BLOCK_BITS,
            "sampling": "none; exact enumeration",
        },
        "headline": headline,
        "keys": reports,
        "scope": "Not a full 16-bit DDT or LAT. Exact only for one-bit input differences and weight-one linear masks over the specified toy Feistel prefixes. Not a security proof.",
    }


def save_results(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "round_metrics.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key", "rounds", "max_single_bit_differential_probability",
            "mean_row_max_differential_probability", "max_basis_mask_correlation",
            "mean_abs_basis_mask_correlation",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["headline"])

    with (output_dir / "single_bit_ddt.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key", "rounds", "input_bit", "input_delta", "pairs",
            "max_count", "max_probability", "distinct_output_differences",
            "max_output_differences",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key_report in report["keys"]:
            for round_report in key_report["rounds"]:
                for row in round_report["differential_single_bit"]["input_delta_rows"]:
                    writer.writerow({
                        "master_key": key_report["master_key"],
                        "rounds": round_report["rounds"],
                        **row,
                        "max_output_differences": ";".join(row["max_output_differences"]),
                    })

    with (output_dir / "basis_lat.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "master_key", "rounds", "input_bit", "output_bit",
            "input_mask", "output_mask", "walsh", "correlation", "bias",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for key_report in report["keys"]:
            for round_report in key_report["rounds"]:
                for cell in round_report["linear_cells"]:
                    writer.writerow({
                        "master_key": key_report["master_key"],
                        "rounds": round_report["rounds"],
                        **cell,
                    })


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--keys", nargs="*", type=lambda value: int(value, 0),
                        default=list(DEFAULT_KEYS), help="32-bit master keys; default: three reference keys")
    args = parser.parse_args()
    try:
        report = analyze(tuple(args.keys))
    except ValueError as error:
        parser.error(str(error))
    save_results(args.output, report)
    for row in report["headline"]:
        print(
            f'{row["master_key"]} r={row["rounds"]}: '
            f'DPmax={row["max_single_bit_differential_probability"]:.8f} '
            f'Corr1,max={row["max_basis_mask_correlation"]:.8f}'
        )
    print(f"Saved results to {args.output.resolve()}")


if __name__ == "__main__":
    main()
