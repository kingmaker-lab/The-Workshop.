# ICARUS OMEGA | Terminal evidence record
25 November 2026. Research only. Experimental cycle closed: **PARTIAL ASCENSION**. [Original terminal design](OMEGA-FINAL-PROTOCOL.md) | [Frozen engine](ath005-omega/README.md).

## Frozen identity and evidence
Revision `11fe6a3286f35749caf37d5fe6664d2f5bf6e1ca`; Linux 6.12.117+deb13-amd64 x86_64, Python 3.13.5 for preparation/analysis. SHA-256:
- Executable (reported): 8c175b8757d8e6d05f78a7b66182fd50289455937c121ae947bffc8cf8f3c3dd
- Library (reported): d69712ab00d897c37ec7147bdadba371cae31d95a271f5044994c31c33fdf7f8
- Protocol (reported): 3881652f0d68eaee87bedb9aacd7be470f3626dd67b067b6b24f196f11400635
- freeze.json: 4d82a662f865e687afaad6d3c14f6acdcf67821a33c8a35dce7bf26f401c8b05
- test.json: 1415c2317310ab396a904bd0a9acbc135dbb633b9541f215d15143f30732f7c4
- test.bin (reported): 00cfebddc26a86c98c9f8810d0ce2fc3b2bd1bfc5acbd1ab120f5e0287127f53
- omega-final.json: 88f6dd94c80c4dac121ba7e9297fd078502a10a57288141ee51296f18d96bdda
- session-01.json: 7a8a93ba6319cea0b512f210cfcdc951eca114faa4b9b53a77e1d66da6baa31e
- session-02.json: e2873ca27b6d22b90539185e021f65491b97c1dac46e30279c9da0e1f4df7e17
- session-03.json: 1be72b0c745b99f305de643f49e26fa862d24fa52351e624e19f354cf5241d98
- session-04.json: 400482964000e8de353d4acdf6ef4cd3e7b249f989848bc71f324a799ddc0f31
- session-05.json: ad2e922b0c7a5947e2036f562859276a50deac0762fab54c1a0b0ccd6487ee4b

Eight submitted JSONs reviewed; all five session hashes match the terminal report. Recomputed primary CPU ratios, subject losses, coverage, selection masks and cross-session prediction parity. Original binaries, raw sensor bytes and native CSVs not independently verified; hashes of these are reported, not independently established. JSONs and raw recordings are not redistributed here. No new experiments.

## Study and finite calibration
MotionSense: 24 participants, 360 source files, 128-sample nonoverlapping windows within recordings. Fit 8 subjects / 3,554 windows; benefit fit 4 / 1,849; tune 4 / 1,811; held-out test 8 / 3,640. Six channels; 12 cheap features (means and variances), 18 optional lag features; standardized centroid scores; cheap dynamic/static gate, expanded all-class prediction. Shared native feature kernel for FULL and OMEGA. No forced expansion fill; expand only when estimated signed gain exceeds threshold and prefix count allows it. Tuning grid (macro accuracy %, loss pp, subject geometric CPU ratio):

| Maximum quota | Threshold | Macro | Loss | CPU ratio |
|---:|---:|---:|---:|---:|
|25%|0|75.4729|8.1013|0.464045|
|25%|0.02|75.9207|7.6535|0.419752|
|25%|0.05|75.9207|7.6535|0.419679|
|25%|0.10|76.1576|7.4166|0.403556|
|50%|0|78.4048|5.1694|0.595374|
|50%|0.02|79.1472|4.4270|0.494148|
|50%|0.05|79.1472|4.4270|0.493212|
|50%|0.10|78.6538|4.9203|0.428271|
|75%|0|81.0410|2.5332|0.714734|
|75%|0.02|82.1134|1.4608|0.531507|
|75%|0.05|82.1134|1.4608|0.534981|
|75%|0.10|79.6165|3.9577|0.437054|

No setting met both tuning goals. Prespecified fallback selected q=3 (75% cap), threshold 0.10, highest macro accuracy among CPU-feasible settings; no post-test retuning.

## Primary results
133 batches per session; 5 sessions, 7 paired timed repeats, 4 arms = 18,620 primary timed calls. Same 3,640 held-out windows each session, not 18,200 independent quality observations. Separate standalone memory runs and stress replay are secondary. 3,564 recorded stress batch measurements; memory-run timing records not included in this audit total.

| Arm | Correct | Pooled accuracy % | Subject macro accuracy % | Expansions |
|---|---:|---:|---:|---:|
| FULL |2687|73.818681|73.969536|3640|
| OMEGA |2580|70.879121|71.040243|575|
| LITE |2386|65.549451|65.851803|0|
| STATIC |2611|71.730769|71.904842|2685|

OMEGA avoids 84.2033% of expansions and 50.5220% of feature calculations vs FULL (12 + 18 per expansion, not instruction counts). Recovers 194 correct vs LITE; loses 31 vs STATIC while avoiding 2,110 expansions. Zero logical prefix violations. Group recovery and benefit selection not independent causal ablations.

| Session | CPU ratio | FULL VmHWM KiB | OMEGA VmHWM KiB | FULL elapsed s | OMEGA elapsed s |
|---|---:|---:|---:|---:|---:|
|1|0.4418225871|2056|2044|1.558478|1.440580|
|2|0.4405154987|2108|2060|1.597474|1.654135|
|3|0.4435080874|2060|2032|1.382987|1.585289|
|4|0.4428137924|2032|2044|1.366985|1.635082|
|5|0.4428999609|2056|2060|2.131154|1.851746|

| Criterion | Estimate | Approximate one-sided 95% upper bound | Prespecified target | Outcome |
|---|---:|---:|---:|---|
| CPU ratio |0.4423107416|0.4434304968|<=0.5|Met |
| Macro quality loss pp |2.9292926717|4.6774897503|<=1|Not established |
| Peak RSS ratio |0.9930758833|1.0042317549|<=0.75|Not established |
| Native parity |passed|engineering check|yes|Met |
| Logical prefix overrun |0|engineering check|0|Met |

CPU reduction 55.768926%, lower bound 55.656950%; speedup 2.26085x in kernel CPU only. Quality losses across eight subjects (sorted by numerical ID) 2.916667, 2.916667, 1.282051, 7.709251, 0, 1.091703, 5.854801, 1.663202 pp. Pooled loss 2.93956 pp differs from macro loss. Peak RSS reduction 0.692412%; native elapsed geometric ratio 1.02660145 (2.6601% slower, descriptive). Kernel timing excludes input parsing, guard and output printing; native elapsed includes binary input, warmups, guards and CSV output, not sensor acquisition or Python preparation. No demonstrated end-to-end speedup or energy reduction.

## Bounded replay, session 5
Common completed prefix; active throughput is rows divided by summed kernel wall time, not sustained acquisition throughput.

| Max batch | Common rows | CPU saving % | FULL active rows/s | OMEGA active rows/s | OMEGA expansions | FULL/Omega p95 wall µs |
|---:|---:|---:|---:|---:|---:|---:|
|1|1164|40.79|193252|285753|0|5.591 / 18.113|
|16|3640|54.36|301796|636607|559|53.536 / 42.920|
|64|3640|54.94|293597|651744|575|209.178 / 115.844|
|256|3640|53.98|299679|380615|575|249.897 / 100.289|

Batch 1 both arms stopped at cap (FULL 1322, OMEGA 1164 rows); quota cannot permit any expansion in a one-row batch. Remaining sizes completed. No artificial pressure or physical saturation claim. The batch 256 label is a maximum, not an assertion that recordings supplied 256 windows per batch.

## Limitations and close
Single reference machine; 8 quality clusters and 5 timing blocks, approximate t bounds under representative independent block assumptions; inter-session gaps only 4.74–25.16 seconds, independence not certified, no formal power calculation. Duplicate source hash across two recordings of the same held-out participant and activity (sit_5/sit_13, subject 1), not cross-split leakage; kept unchanged. Absolute classifier accuracy modest; no cross-dataset raw accuracy comparison as proof of improvement. Sensor collection and preprocessing not timed. No independent hardware replication, no peer review, no universal speedup claim. The primary conjunction failed; CPU criterion and native checks passed. No OMEGA-02 or further outcome-driven optimization. ATH-006 THEMIS independent replication and ATH-007 ACADEMIA archival/review remain separate activities. Publication of the summary does not certify a complete immutable raw archive.
