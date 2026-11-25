# ATHENA | Evidence ledger — exploratory cycle closure

Updated 2026-11-25. Research only; ICARUS Cycle I remains frozen at 37e848d2886c6cd9937951139cec6d1e991008f5. This ledger consolidates previously analyzed local uploads and versioned protocols, not a new independent replication. Raw JSON files are not archived in this revision. Reported zero overruns are logical prefix counts, not physical deadlines.

## ALEXANDRIA — four selector pilots

| Pilot / local result | Revision | Unique test rows | Selector evaluations | Main observation |
|---|---|---:|---:|---|
| BENEFIT-01 / ath001-pilot.json | 7beb45e2cb4643f44babb24998f1e722f6a4cc45 | 30,720 | 9,600 | Context vs margin at HORIZON: -0.150 pp IID, +1.367 pp heteroskedastic. |
| METIS / metis-pilot.json | 123cdcf63835aa215b06a2cc65f5c4abe00661de | 76,800 | 52,800 | +1.504 pp stable context; -2.969 pp reversed context, matched terms. |
| ARGOS / argos-pilot.json | 62b57b1fcae3ef3c2bffbc054579d6fbdf412dca | 286,720 | 31,360 | Abrupt post-shift: +641 correct / 25,600 rows vs AUDIT-METIS (+2.504 pp); stable context -0.715 pp. |
| THEMIS / themis-pilot.json | 4652c70de4330cec0a8c7154c71997a3eae3fa41 | 286,720 | 44,800 | TARGET2 stable context +0.842 pp vs ARGOS4, no switches vs 47; slower post-shift recovery. |

Totals: 680,960 pilot test rows, 138,560 selector evaluations, zero reported logical prefix violations. Counts exclude calibration and smoke; selector evaluations are not independent observations. All four are synthetic exploratory studies. See [ALEXANDRIA](ALEXANDRIA.md). In THEMIS, targeted2 used 8,960 audits, 6,820 in disagreement (76.12%), vs ARGOS4 17,920 audits, 3,804 in disagreement (21.23%). RMSE of the per-batch plain-policy contrast estimate: 5.739 vs 7.383 pp. This is not measured CPU saving or a formal sequential risk guarantee. No feedback does not identify arbitrary conditional shifts. No universal selector superiority.

## EUCLID — mathematical checks

Local euclid-local.json, revision 1fae7461142a33d48388c499011447dc7e7e9fa9: 66,218 bounded checks passed, including 488 native comparisons and 58,304 feasible audit combinations. Peak RSS 19,144 KiB. Theoretical results and hypotheses in [PROOFS.md](ath002-euclid/PROOFS.md). Neither bounded checks nor proof drafts constitute independent review or whole-program formal verification.

## ARCHIMEDES — native resident aggregation

| Pilot | Revision | Timed calls | Grid cells | Unique test rows |
|---|---|---:|---:|---:|
| ARCHIMEDES-01 | dc787f73fd228b6e26a5ad2f41018a16f81d60de | 10,080 | 80 | 7,200 |
| LEVER (s01) | b63dbd07a063057e036c077eaaa6775f060e0dd0 | 12,960 | 108 | 1,920 latent |

ARCHIMEDES-01 sources arch-smoke.json, arch-pilot.json; reported binary SHA256 c8b7c67f0b675855162e8eb4a1c0f2955c36a43a918f01f423f933b7f397f843. Nine HORIZON cells attained median CPU reduction >=50% and observed loss <=1 pp; N256/W64: 60.80% reduction, 0.391 pp loss, 742 vs 745 correct of 768. HORIZON aggregate crossing between W1 and W4. GLOBAL-TOP-K recorded violations in 173/240 seed-cells, RANK zero.

LEVER sources lever-smoke.json, lever-s01.json; reported binary SHA256 6797fa8f325e9a29a7049b4d045e5bac20329b0dc1e38fe3b8f8f62e33ef9e47. Three seeds, two sizes, nine work levels, three budgets, two distributions. 108 groups, 324 seed-cells, 9,720 resident-kernel timed calls and 3,240 diagnostic calls. Latent samples reused across W; 17,280 raw fixture rows are not independent quality samples. The smoke has 288 timed calls and is separate. At IID HORIZON N256/W16 CAUSAL observed 69.05% CPU reduction (median of paired seed-level median ratios), 0.78125 pp loss, 768 rows, no reported overrun. This candidate was selected after viewing pilot results. RANK N256/W64: 57.22% CPU reduction, within the descriptive quality target. At IID HORIZON aggregate over N64/N256, RANK crossing between W1 and W2; CAUSAL faster on median at all nine W. In adverse HORIZON, RANK loss 8.854 pp and CAUSAL loss 4.688 pp, versus FULL. No adverse configuration met both descriptive goals. At LIBERTAS, FAST ratio 1.0030 vs FULL; RANK ratio 1.1248; same reported checksums and correct counts. FAST bypasses heap at full budget only. LEVER peak RSS 26,132 KiB for current invocation, not per-strategy RSS.

Both engineering pilots use resident synthetic raw inputs and a genuine aggregation kernel in C; timing excludes fixture generation, external acquisition, Python orchestration, live observation, and I/O. Medians across three seeds from one identified pilot session are descriptive, not independent hardware replications. No energy or memory-reduction claim. Raw files and independent replication pending. [ARCHIMEDES](ARCHIMEDES.md) | [LEVER protocol](ath003-lever/README.md).

## GAUSS — prospective synthetic confirmation

Local gauss-confirmation.json and five session files at revision eaf3152b7ae048979d433729910920d55435b5f1; protocol SHA256 42a40f46baf1ee7450ef0d822fe93c78b484eb365d67f04523030e7fe605c897; native binary SHA256 6797fa8f325e9a29a7049b4d045e5bac20329b0dc1e38fe3b8f8f62e33ef9e47. Five blocks, 120 fresh seeds, 30,720 test rows, 491,520 calibration rows and 3,360 timed calls. FULL 29,160 correct; CAUSAL 28,907; RANK 28,980; STATIC 27,761. Primary CAUSAL vs FULL: loss 0.8235677083 pp, one-sided approximate 95% upper bound 0.9445638633 pp; geometric CPU ratio 0.3885853062, upper bound 0.4078031562. Both primary criteria and strong 50% reduction criterion met, zero reported logical prefix violations. Conditional to IID synthetic resident N256/W16/HORIZON, five block means, approximate t assumptions, one device and temporal proximity. Not independent hardware replication, full pipeline timing or memory reduction. Prior analysis checked all source hashes and aggregates; raw archive pending. [Locked protocol](ath004-gauss/PROTOCOL.md).

## Status

Exploratory selector and engineering pilots closed. GAUSS conditional synthetic confirmation completed; [ATLAS-01 MOTION](ath005-atlas/README.md) real-signal pilot prepared, local execution pending; ATH-006 THEMIS (independent replication, distinct from BENEFIT-04), ACADEMIA (archival and manuscript review) remain pending. Systematic/full-text literature review and independent mathematical review remain open. No production readiness or universal speedup claim. Candidate CAUSAL IID HORIZON N256/W16 met the predeclared synthetic confirmation criteria; RANK and FAST remain relevant comparators. No additional experiments executed for publication.
