# EXP-005 HELIOS | research only
Hypothesis: Linux-observed resource signals can select a useful batch budget under bounded local contention. No scenario label enters the policy. Compare full and lite static native references, A3/native with fixed 16 terms, and A3/native with telemetry-driven 8/16/24/32 terms. Report accuracy, achieved terms and budget, prefix overruns, batch CPU/wall and p50/p95/p99. Observe budget changes and recovery across the ECLIPSE midpoint; no superiority or deadline guarantee assumed. Require zero prefix overruns in guarded modes; compare accuracy/latency tradeoffs at observed loads and report negative results.

20 new seeds, independent calibration and test namespace. 12 batches of 128 default per seed per scenario. Same rows across scenarios/strategies; rotated ordering. C kernel resets at every batch, so guarantee is per-batch and no controller-state continuity claimed. Telemetry reads aggregate allowed-CPU tick deltas, available memory, PSI avg10, optional frequency and CPU temperature; missing CPU/memory selects 8 terms. Missing PSI/frequency are null. Policy is a predeclared heuristic, not a learned estimator. CPU usage includes other processes and benchmark itself. Pressure is not a guaranteed utilization level; record worker_alive and observed telemetry, do not treat labels as realized load. 32 MiB allocation is mild, not evidence of actual memory contention. No memory exhaustion, sudo, affinity changes or thermal-control changes. One nice+10 worker, bounded duty and 4-second lifetime, cleaned up in finally. Pressure opt-in requires readable CPU temperature, abort at >=80 C or available RAM <512 MiB; sensor sampling is not a guarantee against overheating, keep normal cooling and stop with Ctrl-C on abnormal behavior. No pressure if sensors unavailable; quiet reference still possible. ECLIPSE stops worker after batch six. Worker can exit earlier, report this. No real workloads yet.

Latency includes packing and evaluation for resident feature rows; excludes generation, calibration and queueing. Policy-inclusive timing adds shared observer cost to each adaptive measurement (sum of components, not contiguous end-to-end request latency). Baselines do not pay observer cost. Report both raw batch wall and policy-inclusive wall. No true end-to-end application latency claim. Percentiles pooled across batches/seeds, not independent samples. No unit-test results yet.

Run from this directory:
```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off ../exp004-ascension/ascension.c -o ../exp004-ascension/libascension.so -lm
python3 -m unittest -v
python3 helios.py --seeds 1 > helios-quiet-smoke.json
python3 helios.py --pressure > helios-local.json
```
If pressure cannot run safely, use python3 helios.py > helios-local.json for quiet only. Keep machine attended. Record compiler version and flags, hardware and power context separately. No external packages. Results pending.

## HELIOS v0.2
See [PROMETHEUS](PROMETHEUS.md) for passive contention and observer overhead ablation. The original HELIOS remains unchanged. Smoke measurement is preliminary; v0.2 execution pending.
