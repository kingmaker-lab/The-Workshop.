# Cycle I evidence ledger
Source: user-provided icaro-final.json, revision 37e848d2886c6cd9937951139cec6d1e991008f5, pilot=false, tracked_tree_dirty=false, 30 seeds, 24 batches/seed, 64 samples/batch, 46,080 synthetic rows; GCC 14.2.0 -O2 -ffp-contract=off, Debian Linux x86_64. Values below transcribed from summary, not a new full raw-data audit. Raw JSON not archived in this commit.
| Metric | Value |
|---|---:|
| HELIOS amortized CPU ns | 3991156.140277778 |
| PROMETHEUS amortized CPU ns | 1718572.0027777778 |
| FULL amortized CPU ns | 226356.3986111111 |
| ICARO amortized CPU ns | 248724.39444444445 |
| HELIOS observer amortized CPU ns | 2725432.783333333 |
| ICARO observer amortized CPU ns | 204623.7888888889 |
| ICARO accuracy | 0.9353081597222223 |
| FULL accuracy | 0.9481987847222222 |
| ICARO mean terms | 14.993402777777778 |
| FULL mean terms | 32 |
| ICARO max recorded logical prefix overrun | 0 |
| ICARO loss vs FULL pp | 1.2890625 |
| observer reduction vs HELIOS | 92.49206254% |
| CPU reduction vs PROMETHEUS | 85.52726368% |
| exact-cost replay persistent accuracy | 0.9145182291666667 |
| rank at persistent cost accuracy | 0.9351345486111111 |
| matched mean terms | 14.809288194444445 |
Criterion: 4/5 met, quality failed. ICARO CPU is higher than FULL (about 9.88%); terms are not time or energy. Exact-cost replay advantage = 950 more correct predictions over 46,080 rows; not independent physical repetitions. Peak RSS 28940 KiB entire harness. No per-mode memory or energy result. No new standalone ICARO CLI result available here; SOLARIS CLI previously demonstrated. Preserve original data and negative findings. Raw archive and SHA256 verification pending.
