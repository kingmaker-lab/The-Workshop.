# OUROBOROS — EXP-013: Related-Key Dependency & Cross-Round Subkey Analysis

**The Workshop / WolfPack Crypto Lab**  
**Branch:** `exp-013-related-key-dependency-analysis`  
**Target:** canonical EXP-008 KS1 schedule; no cipher or key-schedule changes.

## 1. Hypothesis under investigation

EXP-012 raised a precise question: although every fixed-round internal KS1 state transition is bijective, does the emitted eight-byte round-key stream still exhibit measurable dependencies between bits/rounds, weak master-key bit influence, or systematic low-diffusion related-key patterns?

EXP-013 investigates that hypothesis at three distinct levels:
1. output-bit dependence across and within round-key bytes;
2. master-key-bit to emitted-round-key-bit influence;
3. dense related-key differences restricted to one master-key byte at a time.

A measured correlation or mutual-information value is an empirical statistic on the declared sample. It is not automatically a proof of a structural cryptographic weakness.

## 2. Frozen KS1 definition

This experiment imports `expand_key` directly from the sibling EXP-008 implementation. It does not rewrite or modify the constants, S-box, P8, rotations, modular additions or round order.

## 3. Campaign design

### Main deterministic sample

Default: 8,192 master keys, generated with a fixed seed. The all-zero and all-one keys are pinned into the sample.

### A. Cross-round emitted-bit dependence

For the 64 emitted round-key bits, enumerate all:

[
\binom{64}{2}=2016
]

unordered bit pairs. Record the 2×2 contingency table, Pearson correlation and empirical binary mutual information for every pair. Report cross-round and within-round results separately.

Pairwise mutual information is measured in bits. Its finite-sample estimate is positively biased in general, so it must be read with the sample count and not treated as a p-value. Pairwise independence also does not imply higher-order independence.

### B. Master-key-bit influence

For every one of the 32 master-key input bits, compare the schedule of each sampled key with the schedule under that key XOR the one-bit delta. Record the Hamming influence of every one of the 64 output bits, including its round position.

This produces an exact empirical 32×64 related-key influence matrix for the deterministic key sample.

### C. Dense single-byte related-key scan

For each of the four master-key byte positions, enumerate all 255 nonzero byte deltas. For each delta, compare the emitted 64-bit schedule over a separate deterministic sample of 1,024 master keys. This is 1,020 related-key deltas in total.

For every delta, record total output Hamming distance and the Hamming distance in each of the eight emitted round-key bytes. Rank low- and high-diffusion deltas and report min/max/mean.

This scan is exhaustive over the selected byte-delta family, but the master-key base values are sampled. It is not exhaustive over all 2^32 master keys or all 2^32 possible related-key deltas.

## 4. What would count as evidence?

Potential warning signals:
- a master-key input bit that has persistently low flip probability across many output bits/rounds;
- a specific byte delta that repeatedly changes very few emitted subkey bits;
- repeated cross-round output-bit correlations or mutual-information peaks that are reproducible under independent deterministic samples/seeds;
- pronounced differences between master-key byte positions.

A single extreme in one finite sample is only a lead. Follow-up should repeat the measurements using independent seeds/sample sizes and compare with an appropriate finite-sample baseline before calling it a systematic dependency.

A low Hamming-distance response is not itself a practical key-recovery attack. To claim an exploitable related-key weakness, an attacker model and an actual distinguishing or key-recovery result would be required.

## 5. Reproduction

Python 3.9+; standard library only:

~~~bash
python3 -m unittest -v
python3 dependency_analysis.py --samples 8192 --dense-samples 1024 --seed 0x0132026 --output results
~~~

For a second deterministic run:

~~~bash
python3 dependency_analysis.py --samples 16384 --dense-samples 2048 --seed 0xC0FFEE --output results/replicate
~~~

## 6. Outputs

- `summary.json` — complete reproducibility metadata and compact headline metrics.
- `summary_compact.json` — compact report without full 2,016- and 2,048-row internal matrices.
- `output_bit_dependencies.csv` — all 2,016 output bit-pair Pearson/MI records.
- `master_to_subkey_dependencies.csv` — all 2,048 master-bit/output-bit dependency records.
- `related_key_unit_deltas.csv` — 32 one-bit related-key profiles.
- `dense_byte_delta_scan.csv` — all 1,020 single-byte nonzero delta profiles.

## 7. Limits

- The 2^32 master-key domain is not exhaustively enumerated.
- Pairwise Pearson correlation and mutual information do not capture all higher-order dependencies.
- Empirical mutual information has finite-sample bias.
- The dense delta scan is exhaustive only over one-byte delta values and positions, evaluated on a deterministic key sample.
- No master-key recovery, practical related-key distinguisher, or full-domain equivalent-key classification is claimed.
- Results apply only to EXP-008 KS1 and the toy Feistel cipher. They do not apply to the separate 64-bit Assembly state transition or SHA-256.

**Decision:** EXP-013 is designed to either support or weaken the specific dependency/low-diffusion hypothesis raised by EXP-012. Any warning must reproduce before it is classified as structural.

**Build. Break. Understand. Rebuild.**
