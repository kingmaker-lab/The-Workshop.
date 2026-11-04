#!/usr/bin/env python3
"""OUROBOROS EXP-011: multi-round differential characteristics and linear hulls.

Differential side:
  exact Markov-model propagation of DDT transitions for selected initial deltas;
  exact full-domain fixed-key observations for selected deltas, compared by TV distance.

Linear side:
  exact Walsh/LAT trail aggregation (linear hull) across Feistel prefixes;
  exact full-domain Walsh checks for the strongest predicted endpoints.

This is a research analysis of the EXP-008 toy 16-bit permutation, not production crypto.
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
HALF_DOMAIN = 1 << 8
DEFAULT_KEYS = (0x01234567, 0x00000000, 0xFFFFFFFF)
DIFFERENTIAL_STARTS = tuple((1 << bit) for bit in range(16)) + (
    0x0003, 0x0005, 0x0101, 0x0202, 0x8001, 0x8080,
)
OBSERVED_STARTS = (0x0001, 0x0100, 0x0101, 0x0003, 0x8000, 0x8080)
LINEAR_START_MASKS = (0x0100, 0x8000, 0x0101)


def parity(value: int) -> int:
    return value.bit_count() & 1


def feistel_round(block: int, round_key: int) -> int:
    left, right = (block >> 8) & 0xFF, block & 0xFF
    return ((right << 8) | (left ^ round_function(right, round_key))) & BLOCK_MASK


def build_round_tables() -> tuple[list[list[int]], list[list[int]]]:
    """Return DDT and Walsh LAT for G(x)=F(x,0), all 256x256 cells."""
    outputs = [round_function(x, 0) for x in range(256)]
    ddt = [[0] * 256 for _ in range(256)]
    for alpha in range(256):
        row = ddt[alpha]
        for x in range(256):
            row[outputs[x] ^ outputs[x ^ alpha]] += 1

    lat = [[0] * 256 for _ in range(256)]
    for beta in range(256):
        column = [1 if parity(beta & outputs[x]) == 0 else -1 for x in range(256)]
        stride = 1
        while stride < 256:
            for base in range(0, 256, 2 * stride):
                for offset in range(stride):
                    i, j = base + offset, base + offset + stride
                    u, v = column[i], column[j]
                    column[i], column[j] = u + v, u - v
            stride *= 2
        for alpha, value in enumerate(column):
            lat[alpha][beta] = value

    if any(sum(row) != 256 for row in ddt):
        raise AssertionError("DDT row sums must equal 256")
    return ddt, lat


def differential_model(start_delta: int, ddt: list[list[int]]) -> dict[str, Any]:
    """Propagate exact DDT transition counts as a Markov differential hull model.

    State delta is (dL << 8) | dR.
    One round transition for local F-output difference gamma:
      (dL,dR) -> (dR, dL XOR gamma)
    with transition weight DDT[dR,gamma]/256.
    """
    if not 0 < start_delta <= BLOCK_MASK:
        raise ValueError("start_delta must be a nonzero 16-bit value")

    hull = [0] * DOMAIN
    best = [0] * DOMAIN
    hull[start_delta] = best[start_delta] = 1
    parents: list[dict[int, tuple[int, int]]] = []
    rounds = []
    hulls_by_round: list[list[int]] = []

    for round_number in range(1, ROUNDS + 1):
        next_hull = [0] * DOMAIN
        next_best = [0] * DOMAIN
        parent: dict[int, tuple[int, int]] = {}

        for state, hull_numerator in enumerate(hull):
            if not hull_numerator:
                continue
            left_delta, right_delta = state >> 8, state & 0xFF
            for gamma, count in enumerate(ddt[right_delta]):
                if not count:
                    continue
                destination = (right_delta << 8) | (left_delta ^ gamma)
                next_hull[destination] += hull_numerator * count
                candidate = best[state] * count
                if candidate > next_best[destination]:
                    next_best[destination] = candidate
                    parent[destination] = (state, gamma)

        if sum(next_hull) != 256 * sum(hull):
            raise AssertionError("Differential Markov mass was not conserved")
        hull, best = next_hull, next_best
        hulls_by_round.append(hull.copy())
        parents.append(parent)

        denominator = 256 ** round_number
        ranked_hulls = sorted(
            ((value, endpoint) for endpoint, value in enumerate(hull) if value),
            reverse=True,
        )[:8]
        best_endpoint = max(range(DOMAIN), key=best.__getitem__)
        rounds.append({
            "rounds": round_number,
            "reachable_output_differences": sum(value != 0 for value in hull),
            "markov_mass": sum(hull) / denominator,
            "max_markov_hull_probability": max(hull) / denominator,
            "max_single_trail_probability": max(best) / denominator,
            "top_markov_hull_endpoints": [
                {"output_delta": f"0x{endpoint:04X}", "probability": value / denominator}
                for value, endpoint in ranked_hulls
            ],
            "best_trail_endpoint": f"0x{best_endpoint:04X}",
        })

    # Reconstruct the highest-probability individual trail after eight rounds.
    endpoint = max(range(DOMAIN), key=best.__getitem__)
    cursor = endpoint
    trail_reversed = []
    for round_index in range(ROUNDS - 1, -1, -1):
        previous, gamma = parents[round_index][cursor]
        trail_reversed.append({
            "round": round_index + 1,
            "input_state_difference": f"0x{previous:04X}",
            "round_function_input_difference": f"0x{previous & 0xFF:02X}",
            "round_function_output_difference": f"0x{gamma:02X}",
            "output_state_difference": f"0x{cursor:04X}",
            "local_ddt_count": ddt[previous & 0xFF][gamma],
        })
        cursor = previous
    trail = list(reversed(trail_reversed))
    return {
        "input_delta": f"0x{start_delta:04X}",
        "rounds": rounds,
        "_hulls_by_round": hulls_by_round,
        "best_eight_round_trail": {
            "output_delta": f"0x{endpoint:04X}",
            "probability": best[endpoint] / (256 ** ROUNDS),
            "steps": trail,
        },
        "_final_hull_numerators": hull,
    }


def _linear_transition_hull(
    start_mask: int,
    round_keys: tuple[int, ...],
    lat: list[list[int]],
) -> dict[str, Any]:
    """Sum signed products of all linear trails for a fixed key schedule.

    For state masks (a,b), one Feistel round maps to (b XOR alpha,a),
    weighted by LAT_F(alpha,a)/256. Fixed round-key translation contributes
    the exact sign (-1)^parity(alpha AND round_key).
    Integer numerators retain exact dyadic arithmetic.
    """
    if not 0 <= start_mask <= BLOCK_MASK:
        raise ValueError("start_mask must be a 16-bit unsigned integer")

    hull: dict[int, int] = {start_mask: 1}
    best_abs: dict[int, int] = {start_mask: 1}
    best_signed: dict[int, int] = {start_mask: 1}
    parents: list[dict[int, tuple[int, int, int]]] = []
    per_round = []
    hulls_by_round: list[dict[int, int]] = []

    nonzero_alpha_by_beta = [
        [alpha for alpha in range(256) if lat[alpha][beta]]
        for beta in range(256)
    ]

    for round_number, round_key in enumerate(round_keys, start=1):
        next_hull: dict[int, int] = {}
        next_best_abs: dict[int, int] = {}
        next_best_signed: dict[int, int] = {}
        parent: dict[int, tuple[int, int, int]] = {}

        for state, numerator in hull.items():
            a, b = state >> 8, state & 0xFF
            for alpha in nonzero_alpha_by_beta[a]:
                walsh = lat[alpha][a]
                signed_walsh = -walsh if parity(alpha & round_key) else walsh
                destination = ((b ^ alpha) << 8) | a
                next_hull[destination] = next_hull.get(destination, 0) + numerator * signed_walsh

                candidate_signed = best_signed[state] * signed_walsh
                candidate_abs = abs(candidate_signed)
                if candidate_abs > next_best_abs.get(destination, 0):
                    next_best_abs[destination] = candidate_abs
                    next_best_signed[destination] = candidate_signed
                    parent[destination] = (state, alpha, signed_walsh)

        hull, best_abs, best_signed = next_hull, next_best_abs, next_best_signed
        hulls_by_round.append(hull.copy())
        parents.append(parent)
        denominator = 256 ** round_number
        ranked = sorted(
            ((abs(value), state, value) for state, value in hull.items()),
            reverse=True,
        )[:8]
        best_endpoint = max(best_abs, key=best_abs.__getitem__)
        per_round.append({
            "rounds": round_number,
            "reachable_output_masks": len(hull),
            "max_abs_linear_hull_correlation": max(abs(x) for x in hull.values()) / denominator,
            "max_abs_single_trail_correlation": max(best_abs.values()) / denominator,
            "top_hull_endpoints": [
                {
                    "output_mask": f"0x{state:04X}",
                    "signed_correlation": value / denominator,
                    "absolute_correlation": absolute / denominator,
                }
                for absolute, state, value in ranked
            ],
            "best_single_trail_endpoint": f"0x{best_endpoint:04X}",
        })

    endpoint = max(best_abs, key=best_abs.__getitem__)
    cursor = endpoint
    trail_reversed = []
    for round_index in range(ROUNDS - 1, -1, -1):
        previous, alpha, signed_walsh = parents[round_index][cursor]
        beta = previous >> 8
        trail_reversed.append({
            "round": round_index + 1,
            "input_state_mask": f"0x{previous:04X}",
            "round_function_input_mask": f"0x{alpha:02X}",
            "round_function_output_mask": f"0x{beta:02X}",
            "output_state_mask": f"0x{cursor:04X}",
            "signed_round_walsh": signed_walsh,
        })
        cursor = previous

    return {
        "input_mask": f"0x{start_mask:04X}",
        "rounds": per_round,
        "_hulls_by_round": hulls_by_round,
        "best_eight_round_trail": {
            "output_mask": f"0x{endpoint:04X}",
            "signed_correlation": best_signed[endpoint] / (256 ** ROUNDS),
            "absolute_correlation": best_abs[endpoint] / (256 ** ROUNDS),
            "steps": list(reversed(trail_reversed)),
        },
        "_final_hull_numerators": hull,
    }


def _pack_bitplanes(values: list[int]) -> list[int]:
    planes = [bytearray(DOMAIN // 8) for _ in range(BLOCK_BITS)]
    for start in range(0, DOMAIN, 8):
        byte_index = start // 8
        for bit in range(BLOCK_BITS):
            packed = 0
            for offset in range(8):
                packed |= ((values[start + offset] >> bit) & 1) << offset
            planes[bit][byte_index] = packed
    return [int.from_bytes(bytes(plane), "little") for plane in planes]


def _mask_plane(mask: int, planes: list[int]) -> int:
    packed = 0
    for bit in range(BLOCK_BITS):
        if (mask >> bit) & 1:
            packed ^= planes[bit]
    return packed


def _exact_linear_walsh(
    outputs: list[int], input_mask: int, output_mask: int
) -> int:
    """Direct full-domain Walsh coefficient for a fixed input/output mask pair."""
    count = 0
    for x, y in enumerate(outputs):
        count += 1 if parity((x & input_mask) ^ (y & output_mask)) == 0 else -1
    return count


def _observed_differential_histogram(outputs: list[int], input_delta: int) -> Counter[int]:
    return Counter(outputs[x] ^ outputs[x ^ input_delta] for x in range(DOMAIN))


def run_campaign(
    keys: tuple[int, ...] = DEFAULT_KEYS,
    differential_starts: tuple[int, ...] = DIFFERENTIAL_STARTS,
    observed_starts: tuple[int, ...] = OBSERVED_STARTS,
    linear_starts: tuple[int, ...] = LINEAR_START_MASKS,
) -> dict[str, Any]:
    ddt, lat = build_round_tables()
    differential_models = {
        delta: differential_model(delta, ddt)
        for delta in differential_starts
    }

    key_reports = []
    observed_rows = []
    linear_rows = []
    linear_checks = []

    for master_key in keys:
        round_keys = expand_key(master_key)
        states = list(range(DOMAIN))
        output_snapshots = []
        for round_key in round_keys:
            states = [feistel_round(state, round_key) for state in states]
            output_snapshots.append(states.copy())

        key_report = {
            "master_key": f"0x{master_key:08X}",
            "round_keys": [f"0x{value:02X}" for value in round_keys],
            "observed_differentials": [],
            "linear_hulls": [],
        }

        for delta in observed_starts:
            model = differential_models[delta]
            model_rounds = model["rounds"]
            for round_index, outputs in enumerate(output_snapshots, start=1):
                histogram = _observed_differential_histogram(outputs, delta)
                denominator = 256 ** round_index
                predicted = model["_hulls_by_round"][round_index - 1]
                tv = 0.0
                for output_delta in range(DOMAIN):
                    actual_probability = histogram.get(output_delta, 0) / DOMAIN
                    model_probability = predicted[output_delta] / denominator
                    tv += abs(actual_probability - model_probability)
                tv *= 0.5
                max_count = max(histogram.values())
                top_actual = sorted(histogram.items(), key=lambda pair: (-pair[1], pair[0]))[:8]
                row = {
                    "master_key": f"0x{master_key:08X}",
                    "input_delta": f"0x{delta:04X}",
                    "rounds": round_index,
                    "pairs": DOMAIN,
                    "max_observed_probability": max_count / DOMAIN,
                    "max_observed_count": max_count,
                    "markov_hull_max_probability": max(predicted) / denominator,
                    "total_variation_distance": tv,
                    "top_observed_output_differences": [
                        {"output_delta": f"0x{out:04X}", "count": count, "probability": count / DOMAIN}
                        for out, count in top_actual
                    ],
                }
                observed_rows.append(row)
                key_report["observed_differentials"].append(row)

        for input_mask in linear_starts:
            result = _linear_transition_hull(input_mask, round_keys, lat)
            hull = result["_final_hull_numerators"]
            key_report["linear_hulls"].append({
                "input_mask": result["input_mask"],
                "rounds": result["rounds"],
                "best_eight_round_trail": result["best_eight_round_trail"],
            })

            # Independently verify the strongest predicted hull endpoints at every prefix.
            input_planes = _pack_bitplanes(list(range(DOMAIN)))
            input_plane = _mask_plane(input_mask, input_planes)
            output_planes_by_round = [_pack_bitplanes(outputs) for outputs in output_snapshots]
            for round_index, outputs in enumerate(output_snapshots, start=1):
                output_planes = output_planes_by_round[round_index - 1]
                # Verify all highest-magnitude hull endpoints from this prefix.
                endpoints = result["rounds"][round_index - 1]["top_hull_endpoints"]
                numerator_hull = None
                # Re-run the sparse hull for each prefix so the exact numerator is available.
                # The prefix hull recurrence is intentionally small for this 16-bit design.
                prefix_hull = result["_hulls_by_round"][round_index - 1]
                for endpoint_data in endpoints:
                    output_mask = int(endpoint_data["output_mask"], 16)
                    output_plane = _mask_plane(output_mask, output_planes)
                    walsh_exact = (DOMAIN - 2 * (input_plane ^ output_plane).bit_count())
                    hull_num = prefix_hull.get(output_mask, 0)
                    exact_match = hull_num * DOMAIN == walsh_exact * (256 ** round_index)
                    if not exact_match:
                        raise AssertionError(
                            f"Linear hull mismatch for key=0x{master_key:08X}, "
                            f"input=0x{input_mask:04X}, output=0x{output_mask:04X}, rounds={round_index}"
                        )
                    linear_checks.append({
                        "master_key": f"0x{master_key:08X}",
                        "input_mask": f"0x{input_mask:04X}",
                        "output_mask": f"0x{output_mask:04X}",
                        "rounds": round_index,
                        "exact_walsh": walsh_exact,
                        "hull_numerator": hull_num,
                        "exact_match": True,
                    })
            for round_data in result["rounds"]:
                linear_rows.append({
                    "master_key": f"0x{master_key:08X}",
                    "input_mask": result["input_mask"],
                    "rounds": round_data["rounds"],
                    "reachable_output_masks": round_data["reachable_output_masks"],
                    "max_abs_linear_hull_correlation": round_data["max_abs_linear_hull_correlation"],
                    "max_abs_single_trail_correlation": round_data["max_abs_single_trail_correlation"],
                    "best_single_trail_endpoint": round_data["best_single_trail_endpoint"],
                })

        key_reports.append(key_report)

    for delta, model in differential_models.items():
        # Preserve every exact Markov-hull distribution for direct observed comparison.
        model.pop("_hulls_by_round", None)
        model.pop("_final_hull_numerators", None)

    return {
        "experiment": "OUROBOROS-011",
        "design": "EXP-008 W16-K32-Feistel8-S4-P8-KS1",
        "keys": [f"0x{k:08X}" for k in keys],
        "method": {
            "differential_starts": [f"0x{x:04X}" for x in differential_starts],
            "observed_fixed_key_starts": [f"0x{x:04X}" for x in observed_starts],
            "linear_start_masks": [f"0x{x:04X}" for x in linear_starts],
            "differential_model": "exact DDT transition Markov hull propagation; not assumed equal to a fixed-key cipher DDT",
            "fixed_key_differential_check": "full 65,536-state enumeration for selected input differences and every 1..8-round prefix",
            "linear_hulls": "exact signed LAT trail summation with round-key translation signs",
            "linear_verification": "full-domain Walsh checks for the top eight predicted hull endpoints at each prefix",
        },
        "differential_model": {
            f"0x{delta:04X}": {
                "rounds": model["rounds"],
                "best_eight_round_trail": model["best_eight_round_trail"],
            }
            for delta, model in differential_models.items()
        },
        "fixed_key_observations": observed_rows,
        "linear_hull_metrics": linear_rows,
        "linear_exact_checks": {
            "checks": len(linear_checks),
            "all_match": all(row["exact_match"] for row in linear_checks),
            "records": linear_checks,
        },
        "key_details": key_reports,
        "scope": "Toy 16-bit Feistel only. Differential model probabilities are DDT Markov hull estimates; fixed-key probabilities are separately enumerated. Linear hulls are signed sums of trails. This is not a production-security claim.",
    }


def save_results(report: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    with (output / "observed_differentials.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "master_key", "input_delta", "rounds", "pairs", "max_observed_probability",
            "max_observed_count", "markov_hull_max_probability", "total_variation_distance",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["fixed_key_observations"])

    with (output / "linear_hulls.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "master_key", "input_mask", "rounds", "reachable_output_masks",
            "max_abs_linear_hull_correlation", "max_abs_single_trail_correlation",
            "best_single_trail_endpoint",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["linear_hull_metrics"])

    with (output / "linear_exact_checks.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["master_key", "input_mask", "output_mask", "rounds", "exact_walsh", "hull_numerator", "exact_match"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(report["linear_exact_checks"]["records"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--keys", nargs="*", type=lambda value: int(value, 0), default=list(DEFAULT_KEYS))
    args = parser.parse_args()
    report = run_campaign(tuple(args.keys))
    save_results(report, args.output)
    print(json.dumps({
        "experiment": report["experiment"],
        "keys": report["keys"],
        "differential_model_starts": len(report["differential_model"]),
        "fixed_key_observations": len(report["fixed_key_observations"]),
        "linear_hull_rows": len(report["linear_hull_metrics"]),
        "linear_exact_checks": report["linear_exact_checks"]["checks"],
        "linear_exact_all_match": report["linear_exact_checks"]["all_match"],
    }, indent=2))


if __name__ == "__main__":
    main()
