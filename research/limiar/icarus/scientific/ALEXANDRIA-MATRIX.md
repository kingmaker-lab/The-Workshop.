# ATH-001 | Evidence matrix v0.2
Date 2026-11-24. Abstract/metadata evidence, not exhaustive systematic review. NR = not established by inspected evidence, not absence in paper. Published venue and preprint link may differ. No numeric cross-paper rankings.
| ID | Work | Mechanism / budget | Relevance to ICARUS | Evidence / URL |
|---|---|---|---|---|
| A01 | Trapeznikov & Saligrama, AISTATS 2013 | sequential classification with acquisition costs | causal baseline | abstract, https://proceedings.mlr.press/v31/trapeznikov13a.html |
| A02 | Xu et al., JMLR 2014 | classifier cascade/tree; feature extraction and evaluation costs | avoid claiming savings from precomputed features | abstract, https://jmlr.org/beta/papers/v15/xu14a.html |
| A03 | Huang et al., ICLR 2018, MSDNet | anytime and batch allocation under a fixed computational budget | direct precedent for uneven allocation across examples; hard prefix quota NR | abstract/preprint metadata, https://arxiv.org/abs/1703.09844 |
| A04 | Wan et al., USENIX ATC 2020, ALERT | joint model and system configuration under accuracy/latency/energy constraints | direct precedent for resource-aware adaptation; CPU/GPU real applications | publisher abstract, https://www.usenix.org/conference/atc20/presentation/wan |
| A05 | Laskaridis et al., MobiCom 2020, SPINN | runtime early-exit and device/cloud splitting | dynamic environment and service requirements | preprint abstract, https://arxiv.org/abs/2008.06402 |
| A06 | Matsubara et al., ACM Computing Surveys, 55(5), DOI 10.1145/3527155 | survey of split computing and early exit | taxonomy and citation chaining | abstract/metadata, https://arxiv.org/abs/2103.04505 |
| A07 | Ilhan et al., WACV 2024, EENet | learned exit policy for pretrained multi-exit models | learned allocation comparator | abstract/venue metadata, https://arxiv.org/abs/2301.07099 |
| A08 | Dai et al., SOSP 2024, Apparate | feedback from exits for runtime adaptation; latency/throughput tradeoff | measure batching overhead and accuracy constraints | abstract, https://arxiv.org/abs/2312.05385 |
| A09 | Padmanabha Iyer et al., SOSP 2024 | per-input adaptive DNN execution; batch size/resource utilization | native/static performance comparison and batch effects | institutional abstract, https://collaborate.princeton.edu/en/publications/improving-dnn-inference-throughput-using-practical-per-input-comp/ |
| A10 | Fast yet Safe: Early-Exiting with Risk Control, NeurIPS 2024 | risk-controlled exit decisions | quality-aware rather than resource-only policy | proceedings abstract/metadata, https://proceedings.neurips.cc/paper_files/paper/2024/hash/ea5a63f7ddb82e58623693fd1f4933f7-Abstract-Conference.html |
| A11 | Beyond Greedy Exits, NeurIPS 2025 | early-exit risk control and reliability | follow-up quality-control reading | proceedings abstract, https://papers.nips.cc/paper_files/paper/2025/hash/f92ad7a76bb102afab768fd4e675c073-Abstract-Conference.html |
| A12 | Kubaty et al., ICML 2026, Rethinking Calibration for Early-Exit Neural Networks | EEFP accounts for correctness and further compute cost; calibration alone insufficient | measure actual incremental benefit, not just cheap margin | PMLR abstract and citation, https://proceedings.mlr.press/v306/kubaty26a.html |
| A13 | Fife & Oxley, 2017, Laminar Matroids | mathematical model for nested capacities | known combinatorial structure, not novel heap/greedy theorem | publication metadata, https://repository.lsu.edu/mathematics_pubs/1189/ |
| A14 | Kalibera & Jones, ISMM 2013 | hierarchical benchmark repetitions | robust timing and uncertainty | institutional abstract, https://kar.kent.ac.uk/33611/ |
| A15 | ACM artifact review policy | artifact availability and evaluation | reproducibility goals, not an awarded badge | retained seed reference, https://www.acm.org/publications/policies/artifact-review-and-badging-current |
## Interpretation and decisions
A03 and A04 invalidate broad claims that batch confidence allocation or resource-aware inference are new. A08/A09 address runtime tradeoffs; A10/A12 challenge resource-only and confidence-only decisions. A13 gives mathematical precedent. What remains to test is specific combination of nested logical quotas, native observation and incremental workload economics on constrained CPUs. Absence of identical design in this selected corpus is not evidence of novelty.
## ARCHIMEDES / ATLAS action requirements
1. FULL and static smaller native baselines, same compiler, representation and timing. Include actual feature acquisition avoided (A01/A02).
2. Global top-k at identical expansion count (no prefix constraint; report violations), causal threshold and feasible random exact-count controls (A03). Distinguish advantage from future information.
3. Resource-blind and resource-aware policy ablation with matched schedule; real telemetry vs scripted budgets; no claim of ALERT replication (A04/A05).
4. Measure batch assembly, copies, selection, observation, actual processing, latency/throughput (A08/A09).
5. Define benefit g_i = 1[full correct] - 1[cheap correct] in {-1,0,1}; labels available for evaluation/calibration only. Compare margin ranking against learned expected net gain using independent calibration and a diagnostic label oracle (not deployable), at same feasible count. Include adverse cases where expansion harms prediction. Evaluate rank utility, quality/cost curves and noninferiority on untouched test; no claim of implementing EEFP (A07/A10/A11/A12).
6. Distinguish hard logical prefix constraints from elapsed CPU, wall time, energy or OS quotas; compare relaxed global quota; validate EUCLID theorem and code (A13).
7. Repeat independent sessions and devices; record invalid runs and confidence intervals (A14). Archive raw data and reproducibility manifest (A15).
## Full-text queue
Priority: MSDNet, ALERT, EENet, Apparate, Practical Per-Input Compute Adaptation, Fast yet Safe, EEFP, Laminar Matroids, Kalibera/Jones. ACM DOI redirects returned 403 on direct open; institutional abstracts available for the SOSP papers. No full-text claims or quantitative extraction in this pass.
