# ICARUS OMEGA — The Final Ascension
Terminal study, [design](../OMEGA-FINAL-PROTOCOL.md). One finite calibration, five measurement blocks, one terminal verdict. No successor optimization in this research cycle. Linux little-endian x86_64. The only Python dependency is stdlib and existing local safety helpers for preparation and analysis. Native inference is a standalone C executable with libm/libc, no interpreter. Binary input consists of a magic header, per-recording subject/trial/window-count/activity metadata and channel-major float64 windows. Model contains 248 doubles. No raw CSV is read by the native executable. The recorded end-to-end native elapsed time includes file reading, guards, warmup and CSV output; not live acquisition or Python CSV preparation.

## Download
Official [MotionSense](https://github.com/mmalekzadeh/motion-sense/blob/master/data/A_DeviceMotion_data.zip). Extract under ~/datasets/motionsense; use the folder directly containing dws_1/, ups_3/ etc. Requires 360 CSVs (24 participants x 15 trials). Preserve archive hash; 128-sample nonoverlapping windows, incomplete final windows discarded. The original CSVs are never committed. Leave sufficient disk for binary fixtures and logs.

## Build and smoke, before freezing
```sh
nice -n 10 cc -std=c11 -O2 -Wall -Wextra -Werror -ffp-contract=off omega.c -o omega -lm
nice -n 10 cc -std=c11 -O2 -Wall -Wextra -Werror -ffp-contract=off -fPIC -shared omega.c -o libomega.so -lm
python3 -m py_compile omega.py
nice -n 10 python3 omega.py smoke --data "$HOME/datasets/motionsense/A_DeviceMotion_data" --work .omega-smoke
```
Smoke validates fused statistics vs two-pass on synthetic and development windows, fits a development model and checks native predictions and masks on two short development recordings. Stop on error; no final data used. Freeze requires matching smoke binary/revision.

## Freeze and prepare
```sh
nice -n 10 python3 omega.py freeze --data "$HOME/datasets/motionsense/A_DeviceMotion_data" --work .omega-final
nice -n 10 python3 omega.py prepare-test --data "$HOME/datasets/motionsense/A_DeviceMotion_data" --work .omega-final
```
Freeze records 360 source file hashes (including held-out bytes without computing outcomes), dataset split, fit and learned table, all 12 calibration choices and selected candidate, binary and protocol identities. Only after successful freeze may prepare-test parse held-out recordings. Do not pull or recompile after freeze. Preserve freeze.json and test.json. The selection criterion is macro-subject loss and geometric CPU ratio, not the held-out outcome. Source order within recording retained; label order dws,ups,wlk,jog,sit,std.

## Five separate measurement blocks
```sh
nice -n 10 python3 omega.py run --work .omega-final --session 1
# Later, under stable thermal conditions, separately:
nice -n 10 python3 omega.py run --work .omega-final --session 2
nice -n 10 python3 omega.py run --work .omega-final --session 3
nice -n 10 python3 omega.py run --work .omega-final --session 4
nice -n 10 python3 omega.py run --work .omega-final --session 5
python3 omega.py analyze --work .omega-final
```
The same held-out windows are repeated for timing, not independent additional quality samples. Session 5 includes the bounded stress replay (1/16/64/256, max 15s per arm checked before each batch). Memory uses separate native process VmHWM (KiB), same input/output contract and allocation. Primary paired CPU timing excludes reading, output printing, safety, preparation. Safety checks before native batches and during Python preparation; 256 MiB/80 C; unknown native temperature readings are not proof of thermal safety, no continuous monitoring. If a session stops, preserve partial CSV; at most one explicit --resume for that session after checking conditions. Completed stages retained; an incomplete stage is restarted once with first partial preserved. No rerunning a completed session. If evidence is incomplete/invalid and cannot be safely completed, use `python3 omega.py close-incomplete --work .omega-final` to record INCONCLUSIVE, do not extend the study. No result-dependent retuning. Final analyzer enforces hash, parity, exact coverage, quota and five nonoverlapping chronological sessions; approximate t upper bounds per protocol; no power guarantee. No automatic claim of external hardware replication. Stress grid uses bounded replay and cannot certify maximum physical load.

## Output
.omega-final/freeze.json, test.json, s01..s05/session.json and omega-final.json; preserve corresponding native CSVs and raw input archive locally. The analyzer checks output against CSVs. Do not upload raw sensor records or demographic information. Test code, compilation and full execution on user hardware pending as of publication.
