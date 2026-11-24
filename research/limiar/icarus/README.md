# PROTOCOL ICARUS | LIM-I001
> Beyond Limits. Ad Solem.

Opened: 2026-11-24. Version: 0.1.0 (research only).

## Mission
Investigate whether adaptive computational strategies can reduce resource use without unacceptable loss of task quality on constrained commodity hardware.

Target reference environment: Intel Celeron N4020, 8 GB RAM, Debian Linux. Actual environment must be measured; no benchmark results are claimed at launch.

## Scientific charter
- Compare against strong static baselines, including smaller models.
- Predeclare hypotheses, metrics, budgets, splits and seeds before evaluation.
- Record negative results, uncertainty, source revision and environment.
- Separate training, calibration and held-out evaluation; do not tune on test data.
- Never bypass thermal protections, run as root, or exhaust system resources.
- No production or novelty claims without supporting evidence.

## Roadmap
| ID | Name | Scope |
|---|---|---|
| EXP-001 | WAX | Hardware and software baseline |
| EXP-002 | FEATHER | Confidence-based dynamic computation |
| EXP-003 | DAEDALUS | Resource-aware adaptive computation |
| EXP-004 | ASCENSION | Memory and execution optimization |
| EXP-005 | HELIOS | Controlled resource pressure |
| EXP-006 | SOLARIS | Integrated evaluation |

Candidate comparison: ICARUS-S (static), ICARUS-D (confidence-based), ICARUS-A (resource-aware).
Aspirational targets for later experiments: 50% lower mean CPU time, 25% lower peak memory, at most 1 percentage point accuracy loss. Not results; each must be evaluated separately under fair conditions.

## Experiments
See [WAX protocol](experiments/exp001-wax/README.md). No measurements have yet been recorded.

See [FEATHER protocol](experiments/exp002-feather/README.md): synthetic conditional computation; implementation and tests prepared, execution pending.

See [DAEDALUS protocol](experiments/exp003-daedalus/README.md): causal feedback and prefix feature-term budgets; implementation and tests prepared, execution pending.

See [ASCENSION protocol](experiments/exp004-ascension/README.md): Python/C overhead ablation; 20 seeds, implementation and tests prepared; execution pending.
