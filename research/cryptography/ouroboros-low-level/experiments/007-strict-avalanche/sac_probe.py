#!/usr/bin/env python3
"""Ouroboros EXP-007: Strict Avalanche Criterion (SAC) and bit-change dependence.

Experimental tests of finite functions only. This is NOT a security certification.
Python 3.9+, standard library only. Input and output width always match.
"""
import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path


def rotl(x: int, amount: int, width: int) -> int:
    mask = (1 << width) - 1
    amount %= width
    return ((x << amount) | (x >> (width - amount))) & mask if amount else x & mask


def engine(name: str, message: str):
    if name.startswith('sha'):
        bits = int(name[3:])
        if bits not in (16, 32):
            raise ValueError('Supported SHA variants: sha16, sha32')
        template = hashlib.sha256(message.encode('utf-8'))
        width = bits // 8
        def function(x):
            h = template.copy()
            h.update(x.to_bytes(width, 'big'))
            return int.from_bytes(h.digest()[:width], 'big')
        return bits, function
    if name in ('identity16', 'identity32'):
        bits = int(name[8:])
        return bits, lambda x: x
    if name == 'toy_arx8':
        bits = 8
        def function(x):
            return rotl((x + 0x2a) & 255, 7, 8) ^ rotl(x, 5, 8)
        return bits, function
    raise ValueError('Unknown engine')


def representative_inputs(bits, input_bit, samples, seed, exhaustive):
    """One representative per unordered pair {x, x xor 2^j} (j-th bit = 0)."""
    half = 1 << (bits - 1)
    if exhaustive:
        if bits > 16:
            raise ValueError('Exhaustive test is limited to <= 16 bits')
        values = range(half)
    else:
        if not 1 <= samples <= half:
            raise ValueError(f'samples must be from 1 to {half} for {bits}-bit engine')
        rng = random.Random(seed + (input_bit + 1) * 0x9E3779B97F4A7C15)
        values = rng.sample(range(half), samples)
    low_mask = (1 << input_bit) - 1
    for v in values:
        yield (v & low_mask) | ((v >> input_bit) << (input_bit + 1))


def phi_coefficient(a, b, joint, n):
    """Pearson phi of binary flip indicators, or None if a margin is constant."""
    variance = a * (n - a) * b * (n - b)
    if variance == 0:
        return None
    return (n * joint - a * b) / math.sqrt(variance)


def analyze(name='sha16', message='ouroboros', samples=4096, bic_samples=256,
            seed=20261020, exhaustive=False):
    bits, function = engine(name, message)
    per_bit_samples = 1 << (bits - 1) if exhaustive else samples
    if per_bit_samples < 2:
        raise ValueError('At least 2 pairs per input bit required')
    if bic_samples < 2:
        raise ValueError('bic-samples must be >= 2')
    bic_n = min(per_bit_samples, bic_samples)
    matrix = [[0.0] * bits for _ in range(bits)]
    sac_rows = []
    bic_rows = []
    total_changed = 0
    for i in range(bits):
        counts = [0] * bits
        b_counts = [0] * bits
        joint = [[0] * bits for _ in range(bits)]
        n = 0
        for x in representative_inputs(bits, i, samples, seed, exhaustive):
            n += 1
            difference = function(x) ^ function(x ^ (1 << i))
            total_changed += difference.bit_count()
            for j in range(bits):
                changed = (difference >> j) & 1
                counts[j] += changed
            if n <= bic_n:
                flipped = [j for j in range(bits) if (difference >> j) & 1]
                for j in flipped:
                    b_counts[j] += 1
                for ind, j in enumerate(flipped):
                    for k in flipped[ind + 1:]:
                        joint[j][k] += 1
        assert n == per_bit_samples
        for j in range(bits):
            p = counts[j] / n
            matrix[i][j] = p
            sac_rows.append({'input_bit': i, 'output_bit': j,
                             'changed_count': counts[j], 'pairs': n,
                             'flip_probability': p, 'abs_deviation_from_half': abs(p - 0.5)})
        for j in range(bits):
            for k in range(j + 1, bits):
                phi = phi_coefficient(b_counts[j], b_counts[k], joint[j][k], bic_n)
                bic_rows.append({'input_bit': i, 'output_bit_a': j,
                                 'output_bit_b': k, 'pairs': bic_n,
                                 'both_changed': joint[j][k],
                                 'phi': phi})
    probabilities = [r['flip_probability'] for r in sac_rows]
    phis = [r['phi'] for r in bic_rows if r['phi'] is not None]
    summary = {
        'experiment': 'OUROBOROS-007', 'phase': 'exploratory',
        'engine': name, 'message': message, 'input_bits': bits,
        'output_bits': bits, 'seed': seed,
        'sampling': 'exhaustive distinct input pairs' if exhaustive else 'uniform distinct input pairs per input bit',
        'samples_per_input_bit': per_bit_samples, 'bic_samples_per_input_bit': bic_n,
        'sac': {
            'mean_flip_probability': sum(probabilities) / len(probabilities),
            'mean_abs_deviation_from_half': sum(abs(p - 0.5) for p in probabilities) / len(probabilities),
            'max_abs_deviation_from_half': max(abs(p - 0.5) for p in probabilities),
            'min_flip_probability': min(probabilities),
            'max_flip_probability': max(probabilities),
            'mean_changed_bits_per_pair': total_changed / (bits * per_bit_samples),
            'expected_changed_bits_ideal_model': bits / 2,
        },
        'bic': {
            'pairs_evaluated_per_input_bit': bic_n,
            'defined_phi_count': len(phis),
            'undefined_phi_count': len(bic_rows) - len(phis),
            'mean_abs_phi': sum(map(abs, phis)) / len(phis) if phis else None,
            'max_abs_phi': max(map(abs, phis)) if phis else None,
            'warning': 'Correlation of flip indicators; not a cryptographic security proof.'
        },
        'scope': 'This experiment analyzes finite, specified functions; not the native C/Assembly Ouroboros binary.'
    }
    return summary, matrix, sac_rows, bic_rows


def save_files(folder, summary, matrix, sac_rows, bic_rows):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    for name, fields, rows in [
        ('sac.csv', ['input_bit', 'output_bit', 'changed_count', 'pairs', 'flip_probability', 'abs_deviation_from_half'], sac_rows),
        ('bic.csv', ['input_bit', 'output_bit_a', 'output_bit_b', 'pairs', 'both_changed', 'phi'], bic_rows),
    ]:
        with (folder / name).open('w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with (folder / 'sac_matrix.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['input_bit'] + [f'output_{j}' for j in range(len(matrix))])
        for i, row in enumerate(matrix):
            writer.writerow([i] + row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', choices=['sha16','sha32','identity16','identity32','toy_arx8'], default='sha16')
    parser.add_argument('--message', default='ouroboros')
    parser.add_argument('--samples', type=int, default=4096)
    parser.add_argument('--bic-samples', type=int, default=256)
    parser.add_argument('--seed', type=int, default=20261020)
    parser.add_argument('--exhaustive', action='store_true', help='Exhaustive distinct input pairs, 8/16 bits only')
    parser.add_argument('--output', type=Path, default=Path('results'))
    args = parser.parse_args()
    try:
        summary, matrix, sac, bic = analyze(args.engine, args.message, args.samples,
                                            args.bic_samples, args.seed, args.exhaustive)
    except ValueError as error:
        parser.error(str(error))
    save_files(args.output, summary, matrix, sac, bic)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print('Saved:', args.output.resolve())


if __name__ == '__main__':
    main()
