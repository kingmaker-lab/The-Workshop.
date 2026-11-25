# EXP-001 WAX | Baseline v0.1
Status: protocol and measurement harness prepared; execution pending.

## Question
What reproducible baseline performance does the reference machine exhibit for fixed integer and sequential-buffer workloads? This initial harness is not a CPU hardware benchmark or evidence of adaptive gains.

## Protocol
Linux, Python 3 standard library only. Run on AC power with ordinary cooling, no sudo, no artificial load, no competing benchmarks. Record Python version, kernel, CPU model, available logical CPUs, RAM, workload parameters, and commit SHA. Observe thermal conditions separately if supported. Stop if the machine becomes unusually hot or unstable. Do not modify clocks or thermal controls.

From repository root:
```sh
python3 -m unittest discover -s research/limiar/icarus/experiments/exp001-wax -p 'test_*.py'
python3 research/limiar/icarus/experiments/exp001-wax/benchmark.py > wax-local.json
```
Use the same parameters for all runs. Default: one warmup per workload, seven measured repetitions, fixed integer iteration count and buffer size. Record per-run wall and process CPU time, median, and process high-water RSS (Linux KiB, cumulative, not workload-specific). The buffer workload includes allocation and summation; it is not a DRAM bandwidth measurement. Integer workload measures Python interpreter plus arithmetic, not theoretical CPU throughput.

Repeat on three independent sessions when feasible. Record power and thermal context externally. Do not infer causality from these baseline measurements alone. Record checksums to detect accidental workload changes. Publish anonymized results only; no hostname, usernames, serial numbers, network identifiers or raw machine logs.

## Acceptance
Harness runs without privileges or third-party dependencies; deterministic checksums; raw samples retained; JSON parses; actual environment and revision recorded. No minimum speed threshold. Later adaptive experiments require equal task/data splits, comparable resources, static baselines, and uncertainty reporting.

## Results
Pending; no fabricated or placeholder performance values.
