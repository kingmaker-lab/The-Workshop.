# EXP-004 ASCENSION | research only
Question: reduce controller overhead without sacrificing budget tracking or quality. Targets per scenario: >=50% mean paired CPU reduction vs Python A1; <=1% mean absolute segment budget error; zero prefix overrun; <=0.5 percentage point mean additional accuracy loss. Targets are not results. Compare at achieved costs.

A1 calls original DAEDALUS evaluator per segment. A2 updates floating threshold every 16 decisions. A3 uses integer ticks (700 ticks/unit, 3 ticks per term error). A4 combines periodic integer feedback with full-budget fast path. C includes full, lite, guarded fixed, float feedback, integer feedback and periodic integer variants. Compare C A1 vs Python A1, and C native vs C A1, to distinguish language and algorithm effects; A4 vs A3 combines periodic update and fast path. Python 3.13 sum and C sequential addition need not be bitwise identical. Parity tests do not prove universal equivalence.

20 new seeds, independent calibration/holdout, distinct namespace from prior experiments. Same test rows across strategies/scenarios. Four static budgets and announced variable sequence 24,8,32,16; reset state between regimes. Five measured repeats after warmup, rotated order. CPU includes evaluation, wrapper and metrics; excludes generation, calibration, compilation and native input packing. Not an end-to-end comparison. No real hardware pressure or real data. Compiler required; no third-party Python packages. Record actual compiler flags, power, thermals and dirty-tree status. Do not use fast-math.

Run from this directory:
```sh
cc -std=c11 -O2 -Wall -Wextra -Werror -fPIC -shared -ffp-contract=off ascension.c -o libascension.so -lm
python3 -m unittest -v
python3 ascension.py --samples 1000 --compiler-info "$(cc --version | head -n1); -O2 -ffp-contract=off" > ascension-local.json
```
Status: implementation and tests prepared, local execution pending.
