# EXP-00X ÍCARO | The Final Ascension
Research-only final synthetic evaluation for cycle one. PHOENIX is incorporated here; original experiments remain unchanged.
## Corrections
SOLARIS persistent smoke: 92.16% observer and 84.72% integrated CPU reduction vs HELIOS/PROMETHEUS; accuracy loss 3.97 pp vs FULL (target not met). Quantization-induced drift is a hypothesis, not isolated proof. ICARO removes integral threshold feedback entirely. Four cheap features determine confidence, a bounded max-heap chooses the lowest absolute margins subject to nested logical prefix quotas floor(i*(budget-4)/28), tie by earlier index. It maximizes feasible expansion count; optional exact cap matches the number of expansions actually used by a reference. No labels or expensive features used to select. Requires entire batch up front: logical prefix accounting is not physical execution ordering or online causality. All 32 features are resident and validated, so term counts are not FLOPs or acquisition costs. Complexity O(n log n), bounded n<=256. No guarantee of quality or superiority.
## Locked evaluation
Pilot seed 1299 separate from 30 final seeds 1301..1359 odd; 24 batches x64 rows (46,080 distinct test rows), fresh calibration 1000/seed, separate RNG namespace. Seven live strategies same input bytes; HELIOS/PROMETHEUS decode, validate, repack; SOLARIS full/fixed/reset/persistent and ICARO native; rotate order. Native candidate reuses SOLARIS safety and observation, no artificial pressure. Same-session comparisons only. Separate deterministic replay on actual ICARO announced budgets and fixed synthetic schedule [8,8,16,16,24,24,32,32] repeated three times. Compare reset/persistent/rank plus rank at exact reset and persistent term counts; no replay latency in live metrics. Replay matches logical budget, not necessarily compute overhead; exact-cost arms isolate selection better. Replay checks zero prefix overruns and aggregate equality of live rank. No policy feedback from labels or holdout. No tuning on final seeds. Safety fresh per live batch, 512 MiB and 80 C limits preserved; no sudo. Stop on failure. Tests use bounded offline fixtures only.
## Predeclared final criteria (live ICARO)
>=90% amortized observer CPU reduction vs HELIOS; >=50% amortized total CPU reduction vs PROMETHEUS; <=1 pp pooled accuracy loss vs native FULL; zero recorded logical prefix overrun; all 30 final seeds. Report separately static comparisons, paired per-seed losses, replay by budget, and failure of any criterion. 25% peak RSS reduction remains unverified (harness-wide peak only). If strict budgets make accuracy target infeasible, report negative result; no budget override. Final for this synthetic family, not evidence of generalization or production readiness. Real workloads, separate-process memory and energy, multiple devices/sessions remain future validation. Service time from resident binary input to result includes selection, validation, observer and Python wrapper, excludes data generation/serialization, sleep, queue/batch assembly and disk I/O. Report active throughput, not sustained application throughput. CLI independent after fixture generation; CLI timing excludes reads. Tests prepared, not yet executed.
## Run
```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off ../exp004-ascension/ascension.c -o ../exp004-ascension/libascension.so -lm
cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off icaro.c -o libicaro.so -lm
cc -std=c11 -O2 -Wall -Wextra -Werror -ffp-contract=off -DICARO_CLI icaro.c -o icaro_cli -lm
python3 -m unittest -v
python3 icaro.py --smoke --compiler-info "$(cc --version | head -n1); -O2 -ffp-contract=off" > icaro-smoke.json
python3 icaro.py --compiler-info "$(cc --version | head -n1); -O2 -ffp-contract=off" > icaro-final.json
# optional local standalone check, fresh filename
python3 icaro.py --fixture icaro-fixture.bin
./icaro_cli 64 icaro-fixture.bin > icaro-native.csv
```
Run final only after smoke and tests pass operationally; quality criterion may fail and must be recorded, not tuned away. No pressure flag.
