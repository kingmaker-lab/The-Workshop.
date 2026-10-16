#!/usr/bin/env python3
"""OUROBOROS EXP-006: exhaustive basins of truncated SHA-256 state maps.

Reference model, NOT a validation of the independent C/Assembly Ouroboros engine.
Python 3.9+, standard library only. Every message is UTF-8 encoded.
Transition: f_m(x)=first16(SHA256(UTF8(m)||big_endian_2(x))).
"""
import argparse
from collections import deque, Counter
import csv
import hashlib
import json
from pathlib import Path

N = 1 << 16
DEFAULT_MESSAGES = ['ouroboros', 'OUROBOROS', 'Ouroboros', 'wolfpack', 'ares', 'the workshop', 'ouroboros!', '']

def transition_map(message):
    seed_hash = hashlib.sha256(message.encode('utf-8'))
    nxt = [0] * N
    for x in range(N):
        h = seed_hash.copy()
        h.update(x.to_bytes(2, 'big'))
        nxt[x] = int.from_bytes(h.digest()[:2], 'big')
    seed = int.from_bytes(seed_hash.digest()[:2], 'big')
    return nxt, seed

def analyze_functional_graph(nxt):
    """Decompose graph into disjoint cycles with directed in-trees."""
    n = len(nxt)
    if n == 0 or (n & (n - 1)) or not all(0 <= y < n for y in nxt):
        raise ValueError('Mapping must contain 2^k states, with valid target states')
    bits = n.bit_length() - 1
    indegree = [0] * n
    for target in nxt:
        indegree[target] += 1

    queue = deque(i for i, degree in enumerate(indegree) if degree == 0)
    peeled = []
    while queue:
        x = queue.popleft()
        peeled.append(x)
        y = nxt[x]
        indegree[y] -= 1
        if indegree[y] == 0:
            queue.append(y)

    basin_id = [-1] * n
    distance_to_cycle = [0] * n
    cycles = []
    for start in range(n):
        if indegree[start] == 0 or basin_id[start] != -1:
            continue
        members = []
        node = start
        while basin_id[node] == -1:
            basin_id[node] = len(cycles)
            members.append(node)
            node = nxt[node]
        assert node == start
        cycles.append(members)

    for x in reversed(peeled):
        y = nxt[x]
        basin_id[x] = basin_id[y]
        distance_to_cycle[x] = distance_to_cycle[y] + 1

    assert all(x >= 0 for x in basin_id)
    sizes = Counter(basin_id)
    assert sum(sizes.values()) == n
    members_on_cycles = sum(map(len, cycles))
    assert members_on_cycles == n - len(peeled)
    summary = {
        'states': n,
        'cycle_count': len(cycles),
        'cycle_lengths': sorted((len(c) for c in cycles), reverse=True),
        'fixed_points': [f'0x{c[0]:04X}' for c in cycles if len(c) == 1],
        'states_on_cycles': members_on_cycles,
        'largest_cycle': max(map(len, cycles)),
        'basin_sizes': sorted(sizes.values(), reverse=True),
        'largest_basin': max(sizes.values()),
        'largest_basin_percent': round(100 * max(sizes.values()) / n, 4),
        'mean_distance_to_cycle': round(sum(distance_to_cycle) / n, 4),
        'max_distance_to_cycle': max(distance_to_cycle),
        'single_bit_same_basin_percent': round(100 * sum(
            basin_id[x] == basin_id[x ^ (1 << bit)]
            for bit in range(bits)
            for x in range(n)
        ) / (bits * n), 4),
        'same_basin_independent_state_baseline_percent': round(100 * sum(
            size * size for size in sizes.values()
        ) / n**2, 4),
    }
    return summary, basin_id, distance_to_cycle

def baseline_orbit(nxt, seed, basin_id, distances, metrics):
    """Compute orbital entry and cycle length without enumerating visited nodes."""
    x = seed
    mu = distances[x]
    for _ in range(mu):
        x = nxt[x]
    first_on_cycle = x
    y, lam = nxt[x], 1
    while y != x:
        y = nxt[y]
        lam += 1
    assert lam in metrics['cycle_lengths']
    return {'seed_hex': f'0x{seed:04X}', 'mu': mu, 'lambda': lam,
            'cycle_entry_hex': f'0x{first_on_cycle:04X}',
            'basin_size': sum(1 for i in basin_id if i == basin_id[seed])}

def study(messages):
    records = []
    for message in messages:
        next_state, seed = transition_map(message)
        metrics, basin, distances = analyze_functional_graph(next_state)
        metrics['message'] = message
        metrics['initial_orbit'] = baseline_orbit(next_state, seed, basin, distances, metrics)
        records.append(metrics)
    return records

def write_outputs(records, destination):
    destination.mkdir(exist_ok=True, parents=True)
    (destination / 'results.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    cols = ['message', 'cycle_count', 'states_on_cycles', 'largest_cycle', 'largest_basin',
            'largest_basin_percent', 'mean_distance_to_cycle', 'max_distance_to_cycle',
            'single_bit_same_basin_percent', 'same_basin_independent_state_baseline_percent']
    with (destination / 'summary.csv').open('w', encoding='utf-8', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=cols)
        writer.writeheader()
        for row in records:
            writer.writerow({k: row[k] for k in cols})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--message', action='append', help='Message to test (repeatable). Omit to run all default messages.')
    parser.add_argument('--output', default='results', type=Path, help='Directory for results.json and summary.csv')
    args = parser.parse_args()
    result = study(DEFAULT_MESSAGES if args.message is None else args.message)
    write_outputs(result, args.output)
    for r in result:
        print(f"{r['message']!r:<17} cycles={r['cycle_count']:<2} fixed={len(r['fixed_points'])} "
              f"largest_cycle={r['largest_cycle']:<4} dominant_basin={r['largest_basin_percent']:>6.2f}% "
              f"bit_flip_same_basin={r['single_bit_same_basin_percent']:>6.2f}%")
    print('Files:', (args.output / 'results.json'), (args.output / 'summary.csv'))

if __name__ == '__main__':
    main()
