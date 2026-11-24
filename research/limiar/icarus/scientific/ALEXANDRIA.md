# ATH-001 ALEXANDRIA | initial scoping review
Date: 2026-11-24. Initial public abstract/metadata review, not a completed systematic review or full-text synthesis.
## Seed corpus and relation
- Trapeznikov & Saligrama (AISTATS 2013), Supervised Sequential Classification Under Budget Constraints, https://proceedings.mlr.press/v31/trapeznikov13a.html : sequential budgeted classification; compare causal stopping.
- Xu et al. (JMLR 2014), Classifier Cascades and Trees for Minimizing Feature Evaluation Cost, https://www.jmlr.org/beta/papers/v15/xu14a.html : separates evaluation and acquisition cost; measure feature extraction, not just terms.
- Huang et al. (ICLR 2018), Multi-Scale Dense Networks for Resource Efficient Image Classification, https://arxiv.org/abs/1703.09844 : explicitly budgeted batch classification and early exits; direct conceptual precedent for allocating more compute to hard examples.
- Laskaridis et al. (MobiCom 2020), SPINN, https://doi.org/10.1145/3372224.3419194 : dynamic progressive device/cloud inference; related resource-aware scheduling, distinct deployment.
- Improving DNN Inference Throughput Using Practical, Per-Input Compute Adaptation (SOSP 2024), https://doi.org/g826nf : practical early-exit serving; batch effects and strong throughput baselines.
- Fife & Oxley (2017), Laminar Matroids, https://doi.org/10.1016/j.ejc.2017.01.002 : nested prefix capacities form a special case of laminar constraints. Greedy optimization is established mathematics, not a new invention.
- Kalibera & Jones (2013), Rigorous Benchmarking in Reasonable Time, corrected version https://kar.kent.ac.uk/33611/ : hierarchical repetitions and rigorous timing.
- ACM artifact policy https://www.acm.org/publications/policies/artifact-review-and-badging-current : artifact documentation, availability and independent evaluation.
## Search plan
Databases: ACM DL, IEEE Xplore, DBLP, PMLR, OpenReview, arXiv. Search from inception through 2026-11-24; record exact search dates, queries, database, counts, deduplication and decisions. Terms: ("budgeted batch classification" OR "conditional computation" OR "early exit" OR "adaptive inference") AND ("resource aware" OR "budget" OR "edge" OR "runtime"); separate queries for prefix-constrained selection, laminar matroids, cost-sensitive feature acquisition and benchmarking. Backward and forward citation chaining. Include methods relevant to adaptive computation, resource-aware scheduling, budget guarantees or empirical methodology; retain preprints explicitly marked, prioritize peer-reviewed full text. Exclude unrelated work with reasons. Extract cost model, budget semantics, causal/batch lookahead, confidence measure, runtime signal, hardware, baseline, quality, uncertainty, data/code access. Second reviewer desirable; currently one research team. No exhaustive search/counts yet.
## Working gap (not novelty claim)
Characterize tradeoff of logical prefix constraints, native OS telemetry, confidence-based allocation and measurable break-even under equal native optimization. Need compare with simple global top-k, random feasible, causal threshold and fixed compute; external method comparisons where compatible. Literature may invalidate novelty.

## Wave 01 | 2026-11-24
[Search log](ALEXANDRIA-SEARCH-LOG.md) records 15 exploratory queries and prospective database screening. [Evidence matrix](ALEXANDRIA-MATRIX.md) records 15 distinct references (including methods, survey and artifact policy), abstract-level evidence and experimental requirements. ALERT, Apparate, EENet and ICML 2026 EEFP materially narrow the working gap. Full-text and systematic screening remain pending; no novelty conclusion. Cycle I code unchanged.

## BENEFIT-01 | Local exploratory pilot
[Protocol and execution instructions](ath001-benefit/README.md). Tests margin versus calibrated net gain at matched prefix quotas, with IID and deliberately heteroskedastic synthetic scenarios. Smoke and 10-seed exploratory run completed locally; HORIZON context gain vs margin -0.14974 pp IID and +1.36719 pp heteroskedastic, at exact matched terms. Source: uploaded ath001-pilot.json summary, revision 7beb45e2cb46. Raw files not archived yet. No runtime superiority or novelty claim. Full-text review remains open.

## BENEFIT-02 | METIS
[Protocol and run instructions](ath001-metis/README.md). Separate fit, gate and test partitions; five stable/shift conditions, calibration-selected fixed policy, variable-expansion risk heuristic and exact-cost controls. Pilot implementation and six unit tests prepared; local execution pending. No claim of drift detection, runtime speedup, or formal risk control.
