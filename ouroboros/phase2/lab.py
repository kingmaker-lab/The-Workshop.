"""Pilotos offline para a permutação sintética EXP-008."""
import argparse
import json
import platform
import random
from array import array
from collections import Counter
from functools import reduce
from operator import xor
from statistics import median
from time import perf_counter

from .baseline.feistel16 import encrypt_with_round_keys, expand_key, rotl8, round_function
from .baseline.reference_model import reference_expand_key

SIZE = 1 << 16
KEY = 0x01234567
SEED = 20261126
BITS = tuple(1 << bit for bit in range(16))


def trace():
    left, right = 0x12, 0x34
    states = [f"{left:02x}{right:02x}"]
    keys = expand_key(KEY)
    for subkey in keys:
        left, right = right, left ^ round_function(right, subkey)
        states.append(f"{left:02x}{right:02x}")
    return {"key": f"{KEY:08x}", "subkeys": list(keys), "states": states}


def metrics(table, points):
    """Ordered pairs for DDT; Walsh numerator = agreements minus disagreements."""
    sac, differential, linear = [], [], []
    for bit in BITS:
        histogram = Counter(table[x] ^ table[x ^ bit] for x in points)
        sac.append([sum(n for delta, n in histogram.items() if delta & b) for b in BITS])
        delta, count = max(histogram.items(), key=lambda item: (item[1], -item[0]))
        differential.append({"input_difference": bit, "output_difference": delta, "count": count})
        linear.append([
            sum(1 - 2 * ((bool(x & bit)) ^ (bool(table[x] & out))) for x in points)
            for out in BITS
        ])
    return {"sac_flip_counts": sac, "differential_row_maxima": differential,
            "walsh_signed_numerators": linear}


def panel(exact):
    keys = expand_key(KEY)
    permutation = array("H", range(SIZE))
    random.Random(SEED).shuffle(permutation)
    points = range(SIZE) if exact else random.Random(SEED + 1).sample(range(SIZE), 4096)
    tables = {
        "feistel8": array("H", (encrypt_with_round_keys(x, keys) for x in range(SIZE))),
        "identity": range(SIZE),
        "random_permutation": permutation,
    }
    return {"key": f"{KEY:08x}", "seed_control": SEED, "seed_sample": SEED + 1,
            "denominator": len(points), "bit_order": "LSB first",
            "results": {name: metrics(table, points) for name, table in tables.items()}}


def schedule():
    rng = random.Random(SEED)
    samples = rng.sample(range(1 << 32), 256)
    distances = [0] * 32
    for key in samples:
        subkeys = expand_key(key)
        if subkeys != reference_expand_key(key):
            raise AssertionError(f"KS1 differs from oracle for {key:08x}")
        state = key.to_bytes(4, "big")
        for index in range(8):
            a, b, c, d = state
            mixed = (rotl8(a, 3) + b + rotl8(c, 1) + d + 0x9D + 0x3D * index) & 255
            state = state[1:] + bytes([round_function(mixed, 0)])
        if reduce(xor, subkeys, key & 255) != state[-1]:
            raise AssertionError(f"KS1 invariant failed for {key:08x}")
        for bit in range(32):
            changed = expand_key(key ^ (1 << bit))
            distances[bit] += sum((a ^ b).bit_count() for a, b in zip(subkeys, changed))
    return {"seed": SEED, "samples": len(samples), "output_bits": 64,
            "mean_changed_bits_by_input_bit": [n / len(samples) for n in distances]}


def benchmark():
    count, repeats = 4096, 5
    keys = expand_key(KEY)
    timings = {"expand_key": [], "encrypt_preexpanded": []}
    for _ in range(repeats):
        start = perf_counter()
        for key in range(count):
            expand_key(key)
        timings["expand_key"].append((perf_counter() - start) * 1e9 / count)
        start = perf_counter()
        for block in range(count):
            encrypt_with_round_keys(block, keys)
        timings["encrypt_preexpanded"].append((perf_counter() - start) * 1e9 / count)
    return {"python": platform.python_version(), "platform": platform.platform(),
            "operations_per_repeat": count, "repeats": repeats,
            "median_ns_per_operation": {name: median(values) for name, values in timings.items()},
            "ns_per_operation_by_repeat": timings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("trace")
    commands.add_parser("schedule")
    commands.add_parser("benchmark")
    commands.add_parser("panel").add_argument("--exact", action="store_true")
    args = parser.parse_args()
    handlers = {"trace": trace, "schedule": schedule, "benchmark": benchmark,
                "panel": lambda: panel(args.exact)}
    print(json.dumps(handlers[args.command](), indent=2))


if __name__ == "__main__":
    main()
