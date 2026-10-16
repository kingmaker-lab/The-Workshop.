#!/usr/bin/env python3
"""Ouroboros EXP-005: seed-bit sensitivity of a truncated SHA-256 state map.

Reference model only. Not an implementation/audit of Ouroboros' C/ASM step.
Standard library, Python >= 3.9.
"""
import argparse
from collections import Counter
import hashlib
import json
import statistics
from pathlib import Path


def make_map(message: str, bits: int):
    if bits not in (16, 32):
        raise ValueError('Only 16 and 32 bits are supported')
    prefix = hashlib.sha256(message.encode('utf-8'))
    width = bits // 8
    seed = int.from_bytes(prefix.digest()[:width], 'big')

    def step(x: int) -> int:
        h = prefix.copy()
        h.update(x.to_bytes(width, 'big'))
        return int.from_bytes(h.digest()[:width], 'big')

    return step, seed


def orbit(step, seed: int, budget: int):
    """Enumerate states up to first repeat; return pre-period/cycle decomposition."""
    seen = {}
    path = []
    x = seed
    while x not in seen:
        if len(path) >= budget:
            raise RuntimeError(f'Orbit budget exhausted at {budget} unique states; raise --max-states')
        seen[x] = len(path)
        path.append(x)
        x = step(x)
    mu = seen[x]
    cycle = path[mu:]
    return {'mu': mu, 'lambda': len(cycle), 'entry': x, 'states': path,
            'cycle': cycle, 'cycle_id': min(cycle)}


def hamming_trace(step, original_seed, changed_seed, samples):
    x, y = original_seed, changed_seed
    series = []
    for _ in range(samples):
        series.append((x ^ y).bit_count())
        x, y = step(x), step(y)
    return series


def same_time_collision(a, b):
    """First synchronized collision t, or None (even when cycles are shared)."""
    if a['cycle_id'] != b['cycle_id']:
        return None
    t = max(a['mu'], b['mu'])
    x = a['states'][t] if t < len(a['states']) else a['cycle'][(t-a['mu']) % a['lambda']]
    y = b['states'][t] if t < len(b['states']) else b['cycle'][(t-b['mu']) % b['lambda']]
    if x != y:
        return None
    for i in range(t + 1):
        xa = a['states'][i] if i < len(a['states']) else a['cycle'][(i-a['mu']) % a['lambda']]
        xb = b['states'][i] if i < len(b['states']) else b['cycle'][(i-b['mu']) % b['lambda']]
        if xa == xb:
            return i
    raise AssertionError('Collision at t must exist')


def experiment(message='ouroboros', bits=16, samples=256, max_states=1000000):
    step, seed = make_map(message, bits)
    base = orbit(step, seed, max_states)
    traces, rows = [], []
    for bit in range(bits):
        changed = seed ^ (1 << bit)
        alt = orbit(step, changed, max_states)
        trace = hamming_trace(step, seed, changed, samples)
        joined = base['cycle_id'] == alt['cycle_id']
        sync_t = same_time_collision(base, alt)
        rows.append({
            'bit_flipped': bit,
            'changed_seed_hex': f'0x{changed:0{bits//4}X}',
            'mu': alt['mu'], 'lambda': alt['lambda'],
            'entry_hex': f'0x{alt["entry"]:0{bits//4}X}',
            'same_eventual_cycle': joined,
            'synchronous_collision_t': sync_t,
            'mean_hamming_t0_to_n_minus_1': round(statistics.mean(trace), 5),
            'mean_hamming_t1_to_n_minus_1': round(statistics.mean(trace[1:]), 5) if samples>1 else None,
            'hamming_at_t0': trace[0],
            'hamming_at_t1': trace[1] if len(trace)>1 else None,
            'hamming_at_t8': trace[8] if len(trace)>8 else None,
            'hamming_at_t32': trace[32] if len(trace)>32 else None
        })
        traces.append(trace)
    mean_curve = [round(statistics.mean(t[i] for t in traces), 5) for i in range(samples)]
    same_cycle = sum(r['same_eventual_cycle'] for r in rows)
    sync = sum(r['synchronous_collision_t'] is not None for r in rows)
    return {
        'model': 'first_k(SHA256(UTF8(message) || big_endian_k(x)))',
        'message': message, 'bits': bits, 'seed_hex': f'0x{seed:0{bits//4}X}',
        'samples_per_pair': samples,
        'baseline': {'mu': base['mu'], 'lambda': base['lambda'],
                     'entry_hex': f'0x{base["entry"]:0{bits//4}X}'},
        'summary': {
            'bit_flips_tested': bits,
            'same_eventual_cycle': same_cycle,
            'different_eventual_cycle': bits - same_cycle,
            'same_time_collisions': sync,
            'mean_hamming_t0': mean_curve[0],
            'mean_hamming_t1': mean_curve[1] if samples>1 else None,
            'mean_hamming_t8': mean_curve[8] if samples>8 else None,
            'mean_hamming_t32': mean_curve[32] if samples>32 else None,
            'mean_hamming_t1_onward_all': round(statistics.mean(v for trace in traces for v in trace[1:]), 5) if samples>1 else None,
            'unique_target_cycle_lengths': dict(sorted(Counter(r['lambda'] for r in rows).items()))
        },
        'mean_hamming_curve': mean_curve,
        'per_bit': rows,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bits', type=int, choices=[16,32], default=16)
    ap.add_argument('--message', default='ouroboros')
    ap.add_argument('--samples', type=int, default=256)
    ap.add_argument('--max-states', type=int, default=1000000)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    if args.samples < 2 or args.max_states < 1:
        ap.error('Samples must be >=2; max-states must be positive')
    result = experiment(args.message, args.bits, args.samples, args.max_states)
    contents = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(contents, encoding='utf-8')
        print('Saved:', args.output)
    print(json.dumps({'bits': args.bits, 'seed': result['seed_hex'],
                      'baseline': result['baseline'],
                      'summary': result['summary']}, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
