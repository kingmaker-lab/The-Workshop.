#!/usr/bin/env python3
"""Ouroboros EXP-004: SHA-256 truncation as a finite-state mapping (educational)."""
import argparse
from collections import Counter, deque
import hashlib
import json
import math

def make_oracle(message, bits):
    nbytes = bits // 8
    template = hashlib.sha256(message.encode("utf-8"))
    def step(x):
        h = template.copy()
        h.update(x.to_bytes(nbytes, "big"))
        return int.from_bytes(h.digest()[:nbytes], "big")
    seed = int.from_bytes(template.digest()[:nbytes], "big")
    return step, seed

class Meter:
    def __init__(self, step, maximum):
        self.step, self.maximum, self.calls = step, maximum, 0
    def __call__(self, state):
        if self.calls >= self.maximum:
            raise RuntimeError("Evaluation budget exceeded")
        self.calls += 1
        return self.step(state)

def floyd(step, seed, maximum):
    f = Meter(step, maximum)
    slow, fast = f(seed), f(f(seed))
    while slow != fast:
        slow, fast = f(slow), f(f(fast))
    mu, slow = 0, seed
    while slow != fast:
        slow, fast = f(slow), f(fast)
        mu += 1
    entry, lam = slow, 1
    fast = f(slow)
    while fast != slow:
        fast = f(fast)
        lam += 1
    return {"mu": mu, "lambda": lam, "entry": entry, "calls": f.calls}

def brent(step, seed, maximum):
    f = Meter(step, maximum)
    power, lam, slow, fast = 1, 1, seed, f(seed)
    while slow != fast:
        if power == lam:
            slow, power, lam = fast, power * 2, 0
        fast = f(fast)
        lam += 1
    slow = fast = seed
    for _ in range(lam):
        fast = f(fast)
    mu = 0
    while slow != fast:
        slow, fast = f(slow), f(fast)
        mu += 1
    return {"mu": mu, "lambda": lam, "entry": slow, "calls": f.calls}

def full_graph_16(step):
    n = 65536
    nxt = [step(i) for i in range(n)]
    indegree = [0] * n
    for y in nxt:
        indegree[y] += 1
    q = deque(i for i, d in enumerate(indegree) if d == 0)
    peel = []
    while q:
        x = q.popleft()
        peel.append(x)
        y = nxt[x]
        indegree[y] -= 1
        if indegree[y] == 0:
            q.append(y)
    component = [-1] * n
    distance = [0] * n
    cycles = []
    for start in range(n):
        if indegree[start] == 0 or component[start] != -1:
            continue
        x = start
        members = []
        while component[x] == -1:
            component[x] = len(cycles)
            members.append(x)
            x = nxt[x]
        cycles.append(members)
    for x in reversed(peel):
        component[x] = component[nxt[x]]
        distance[x] = 1 + distance[nxt[x]]
    return {
        "cycle_lengths": sorted((len(c) for c in cycles), reverse=True),
        "fixed_points": [hex(x) for x in range(n) if nxt[x] == x],
        "states_on_cycles": sum(map(len, cycles)),
        "largest_basin": max(Counter(component).values()),
        "max_preperiod": max(distance),
        "mean_preperiod": sum(distance) / n
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bits", choices=[16, 32], type=int, default=16)
    p.add_argument("--message", default="ouroboros")
    p.add_argument("--seed", type=lambda x: int(x, 0))
    p.add_argument("--max-evals", type=int, default=5000000)
    p.add_argument("--full-graph", action="store_true")
    args = p.parse_args()
    if args.full_graph and args.bits != 16:
        p.error("--full-graph is available only for 16-bit states")
    step, default_seed = make_oracle(args.message, args.bits)
    seed = default_seed if args.seed is None else args.seed
    if not 0 <= seed < 2**args.bits:
        p.error("seed out of range")
    result = {
        "bits": args.bits, "message": args.message, "seed": hex(seed),
        "floyd": floyd(step, seed, args.max_evals),
        "brent": brent(step, seed, args.max_evals)
    }
    assert all(result["floyd"][key] == result["brent"][key]
               for key in ("mu", "lambda", "entry"))
    if args.full_graph:
        result["graph"] = full_graph_16(step)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
