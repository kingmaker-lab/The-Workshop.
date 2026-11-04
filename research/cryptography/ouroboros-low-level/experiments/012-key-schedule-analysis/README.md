# OUROBOROS — EXP-012: KS1 Key Schedule Analysis

**The Workshop / WolfPack Crypto Lab**  
**Branch:** `exp-012-key-schedule-analysis`  
**Target:** the canonical 32-bit to eight-byte KS1 schedule in EXP-008.  
**Status:** deterministic analysis; not an exhaustive enumeration of the 32-bit master-key space.

## 1. Scope and frozen target

EXP-012 investigates the key schedule exactly as specified in the sibling EXP-008 `feistel16.py`. No constants, rotations, S-boxes, permutations, or round counts are changed.

For round (r\in\{0,\ldots,7\}), state bytes (a,b,c,d) are read most-significant to least-significant:

[
RC_r=(0x9D+0x3D\cdot r)\bmod 256
]

[
u_r=(ROTL_8(a,3)+b+ROTL_8(c,1)+d+RC_r)\bmod 256
]

[
t_r=P8(S(u_r)),\qquad K_r=t_r\oplus d
]

[
Q_{r+1}=((Q_r\ll 8)\bmod 2^{32})\;\mathrm{OR}\;t_r
]

The emitted key stream is eight bytes (64 bits) derived from a 32-bit master key.

## 2. Structural property: fixed-context bijection

For fixed (b,c,d) and fixed round constant:

1. (a\mapsto ROTL_8(a,3)) is a permutation of the 256 byte values.
2. Adding a fixed byte modulo 256 is a permutation.
3. The parallel PRESENT nibble S-box is a permutation because the 4-bit S-box is bijective.
4. (P8) is a bit permutation and therefore bijective.
5. XOR with fixed (d) is also bijective.

Thus, for fixed (b,c,d), both (a\mapsto t_r) and (a\mapsto K_r) are permutations of the byte domain. The internal state update ((a,b,c,d)\mapsto(b,c,d,t_r)) is therefore bijective for each fixed round index.

This proof concerns the internal 32-bit state transition. It does **not** prove that the emitted 64-bit round-key stream uniquely identifies the original 32-bit master key, nor does it establish cryptographic security.

The tests verify the fixed-context property computationally for representative contexts and every round constant. The analyzer also implements the exact inverse transition: undo P8, invert the parallel S-box, subtract the fixed modular addends, and apply ROTL8 by five (the inverse of ROTL8 by three). Round-trip tests check representative 32-bit states across all eight round constants.

## 3. Measurement campaign

Default deterministic sample: 8,192 master keys generated with Python's seeded PRNG. The all-zero and all-one keys are pinned into the sample. The complete (2^{32}) master-key space is not enumerated.

The campaign measures:

- 32 single-bit related-key differences against the 64-bit emitted round-key stream;
- 10 additional multi-bit key differences;
- a (32\times64) related-key avalanche influence matrix;
- per-round byte frequencies, distinct values, empirical byte entropy and bit balance;
- pairwise Pearson correlations among the 64 emitted key-stream bits;
- duplicate complete 8-byte schedules in the finite sample;
- a separate source-to-source cross-check against the canonical EXP-008 `expand_key`.

All measurements are deterministic for a fixed sample count and seed. Entropy, balance, correlations and collision counts are empirical sample statistics, not proofs about all (2^{32}) keys.

## 4. Outputs

- `results/summary.json` — campaign settings, structural findings and metric summaries.
- `results/avalanche_matrix.csv` — input master-key bit to output round-key bit flip frequencies.
- `results/related_key_deltas.csv` — Hamming-distance results for unit and selected multi-bit deltas.
- `results/round_key_statistics.csv` — per-round byte distribution and balance metrics.

## 5. Reproduction

Python 3.9+; standard library only.

~~~bash
python3 -m unittest -v
python3 key_schedule_analysis.py --samples 8192 --seed 0x0123456 --output results
~~~

Use a different deterministic sample size or seed:

~~~bash
python3 key_schedule_analysis.py --samples 16384 --seed 0xC0FFEE --output results/extended
~~~

## 6. Interpretation rules and limits

- The KS1 master-key domain has (2^{32}) values. This experiment does not claim exhaustive coverage.
- A lack of duplicate schedules in a finite sample is not proof of injectivity or absence of equivalent keys.
- A high average avalanche score is not sufficient to establish a secure key schedule.
- Per-byte sample entropy near eight bits does not prove uniformity over all master keys.
- Pairwise output-bit correlation is only one diagnostic and does not capture every higher-order dependency.
- No related-key attack, master-key recovery, weak-key classification over the full domain, or production-security claim is made.
- Results apply only to EXP-008 KS1 and the 16-bit toy Feistel construction. They do not apply to SHA-256 or the separate 64-bit assembly state transition.

**Decision:** EXP-012 separates a provable structural property of the internal state update from empirical observations about the emitted subkey stream. The next research step may test higher-order and broader related-key patterns without changing the defined schedule.

**Build. Break. Understand. Rebuild.**
