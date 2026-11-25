"""Bounded Linux/Python baseline. Research only."""
import argparse
import json
import os
import platform
import resource
import statistics
import time

def integer_work(n):
    x = 1
    for i in range(n):
        x = (1664525 * (x ^ i) + 1013904223) & 0xffffffff
    return x

def buffer_work(n):
    return sum(bytearray(b"\x5a") * n)

def measure(fn, n, repeats):
    expected = fn(n)
    samples = []
    for _ in range(repeats):
        w, c = time.perf_counter_ns(), time.process_time_ns()
        result = fn(n)
        cpu, wall = time.process_time_ns() - c, time.perf_counter_ns() - w
        if result != expected:
            raise RuntimeError("Non-deterministic result")
        samples.append({"wall_ns": wall, "cpu_ns": cpu})
    return {"checksum": expected, "samples": samples,
            "median_wall_ns": statistics.median(s["wall_ns"] for s in samples),
            "median_cpu_ns": statistics.median(s["cpu_ns"] for s in samples)}

def environment():
    cpu = None
    with open("/proc/cpuinfo", encoding="utf-8") as f:
        for line in f:
            if line.startswith("model name"):
                cpu = line.split(":", 1)[1].strip()
                break
    with open("/proc/meminfo", encoding="utf-8") as f:
        ram = next((int(s.split()[1]) for s in f if s.startswith("MemTotal:")), None)
    return {"cpu_model": cpu, "logical_cpus_available": len(os.sched_getaffinity(0)),
            "ram_total_kib": ram, "kernel": platform.release(),
            "python": platform.python_version(), "machine": platform.machine()}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repeats", type=int, default=7)
    p.add_argument("--iterations", type=int, default=250000)
    p.add_argument("--buffer-bytes", type=int, default=1048576)
    p.add_argument("--revision", default=None, help="Git commit SHA; record before publication")
    a = p.parse_args()
    if not (1 <= a.repeats <= 20 and 1 <= a.iterations <= 1000000 and
            1 <= a.buffer_bytes <= 8388608):
        p.error("Parameters outside safe bounds")
    if a.revision is not None and (len(a.revision) != 40 or
            any(c not in "0123456789abcdef" for c in a.revision.lower())):
        p.error("Revision must be a 40-character Git SHA")
    out = {"experiment": "EXP-001-WAX", "schema_version": 1,
           "revision": a.revision, "environment": environment(),
           "parameters": {"repeats": a.repeats, "iterations": a.iterations,
                          "buffer_bytes": a.buffer_bytes},
           "integer": measure(integer_work, a.iterations, a.repeats),
           "buffer": measure(buffer_work, a.buffer_bytes, a.repeats)}
    out["process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
