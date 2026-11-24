# EXP-003 DAEDALUS | v0.1
Research only; implementation prepared, execution pending.

## Hypothesis
Causal feedback can keep feature-term spending near changing budgets while preserving quality better than equally guarded fixed thresholds. Hard prefix caps are guaranteed by a separate credit gate, not by the feedback loop. No CPU deadline or energy guarantee is implied.

## Design
Reuse FEATHER synthetic fixed classifier; independent RNG namespace, ten seeds. Calibration only selects best accuracy among thresholds with mean terms <= target. Held-out test never tunes the thresholds. Compare full, lite, per-regime fixed threshold, guarded fixed threshold, and guarded adaptive threshold. Both guarded variants start each announced regime with zero credit and its calibrated threshold; adaptive changes the threshold after each decision using observed cost, not labels. Unspent credit can accumulate inside a regime, not across boundaries. Thus all guarded prefixes satisfy spent <= count*budget. The variable schedule is announced at regime boundaries (75%,25%,100%,50%); this is not autonomous detection of hardware pressure. Static baselines may exceed budgets. The 100% adaptive and guarded variants always expand. At lower budgets the gate can force a lite decision.

## Metrics and acceptance
Mean absolute relative budget error across segments <=5% for adaptive, plus zero positive prefix overrun; record fraction of segments within 5% and all per-seed values. Compare accuracy at achieved costs against guarded fixed, not just full. No superiority is assumed. CPU is exploratory, three rotated measured repetitions after warmups, data generation excluded. Segment CPU values are first repetition; whole-scenario median is used in summary. Same held-out rows reused across scenarios for paired comparison. Regime resets mean this tests adaptation within an announced regime, not retention of controller state across transitions. Synthetic favorable distribution, fixed feature acquisition, no model fitting, no physical telemetry yet. Margin is not calibrated probability.

## Run
From this directory:
```sh
python3 -m unittest -v
python3 daedalus.py --samples 1000 > daedalus-local.json
```
Record hardware, thermal/power context and working tree cleanliness separately. No dependencies beyond Python standard library. WAX and FEATHER remain unchanged.
