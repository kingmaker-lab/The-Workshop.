# OUROBOROS — EXP-009: Round Function Differential & Linear Analysis

**The Workshop / WolfPack Crypto Lab**  
**Status:** exhaustive component analysis implemented and reproduced. Research-only; no security claim for the full Feistel construction.

## 1. Research question

The EXP-008 cipher uses the round function

\[
F(R,K)=P8(S(R\oplus K)),
\]

where `R` and `K` are 8-bit values, `S` applies the EXP-008 PRESENT 4-bit S-box independently to both nibbles, and `P8` permutes the eight output bits. EXP-009 determines the complete differential distribution table (DDT) and linear approximation table (LAT) of this component.

This experiment does **not** model all eight Feistel rounds. It characterizes the nonlinear round component, which is a prerequisite for later trail analysis.

## 2. Method and definitions

For each input difference `alpha` and output difference `beta`:

\[
DDT[\alpha,\beta]=\#\{x\in\{0,1\}^8:G(x)\oplus G(x\oplus\alpha)=\beta\},
\]

where \(G(x)=P8(S(x))\). Every one of the 256 input differences and 256 output differences is enumerated. Each DDT row must sum to 256.

The Walsh-form LAT is

\[
W[a,b]=\sum_{x\in\{0,1\}^8}(-1)^{\langle a,x\rangle\oplus\langle b,G(x)\rangle}.
\]

The normalized correlation is \(W/256\), the absolute bias in counts is \(|W|/2\), and the probability of agreement for a signed approximation is \((1+W/256)/2\). The reported nontrivial maximum excludes zero input and output masks (`a != 0`, `b != 0`).

The LAT is computed using a fast Walsh–Hadamard transform. No sampling is used.

## 3. Why one representative round key is sufficient

For a fixed round key, \(F_K(x)=G(x\oplus K)\). XOR with a fixed key is a permutation of the input domain. Consequently:

- DDT counts are exactly invariant under a fixed round-key translation.
- LAT Walsh coefficients can change sign by a mask-dependent factor, but their absolute values are invariant.

The harness checks this identity computationally for round keys `0x00`, `0x5A` and `0xFF`. This does not analyze relations between different round keys or the EXP-008 key schedule.

## 4. Exact results

### Differential distribution

| Metric | Result |
|---|---:|
| Input differences enumerated | 256 |
| Output differences enumerated | 256 |
| Maximum count for nonzero input difference | 64 / 256 |
| Maximum differential probability | **0.25 (25%)** |
| Number of cells attaining that maximum | 48 |
| Nonzero DDT entry values observed | 4, 8, 16, 32, 64 |
| Minimum / maximum row sum | 256 / 256 |

Example: `DDT[0x01, 0x05] = 64`, so this particular input difference produces that output difference for one quarter of the inputs in the 8-bit domain.

### Linear approximation

| Metric | Result |
|---|---:|
| Nontrivial input/output mask pairs | 65,025 |
| Maximum absolute Walsh coefficient | **128** |
| Maximum absolute correlation | **0.5** |
| Absolute bias in counts | 64 / 256 |
| Number of cells attaining maximum absolute coefficient | 72 |

A coefficient with absolute correlation 0.5 corresponds to an agreement probability of 75% for one sign of the approximation (or 25% for the opposite sign). This is a strong linear relation in the round component. It is not, by itself, a key-recovery attack against the full eight-round cipher.

### Structural interpretation

The round substitution applies the same 4-bit S-box independently to two nibbles. It introduces no interaction between the nibbles. The bit permutation only reorders output coordinates; it does not remove the differential or linear extrema. The measured 8-bit table therefore retains strong component-level relations inherited from the parallel 4-bit construction.

The EXP-008 SAC result and this analysis are not contradictory. SAC asks for individual output-bit flip rates under selected input-bit flips. DDT and LAT expose multi-bit difference concentration and linear correlations that a near-0.5 SAC average can conceal.

## 5. Reproduction

Python 3.9+; standard library only. Run from this directory:

```bash
python3 -m unittest -v
python3 round_analysis.py --output results
```

`round_analysis.py` imports the exact `feistel16.py` implementation from the sibling EXP-008 directory; it does not duplicate the S-box or P8 definition.

Output files:

- `results/summary.json` — headline metrics and selected maximum entries.
- `results/ddt.csv` — complete 256 × 256 DDT.
- `results/lat_walsh.csv` — complete 256 × 256 Walsh LAT.

Tests verify permutation behavior, DDT row sums, the zero-difference row, known maxima, the nontrivial LAT domain, and round-key invariance.

## 6. Limits and conclusions

- Exact component tables are not a full-cipher differential or linear attack.
- No multi-round trail, hull, key ranking, or key-recovery experiment is claimed here.
- The EXP-008 block size is 16 bits and key size is 32 bits; exhaustive search is not a meaningful security barrier.
- No mode of operation, authentication, side-channel resistance, constant-time behavior, or production suitability is established.
- Results apply only to the specified EXP-008 round function and its fixed-key XOR input translation. They do not apply to the separate 64-bit `ouroboros_step` Assembly state transition or the SHA-256-truncated models in EXP-004–007.

**Decision:** component-level differential and linear weaknesses are measured and documented. Keep the construction in the research lab. Do not use it to protect real data.

## 7. Next experiment

EXP-010 should investigate how these component-level characteristics propagate through one to eight Feistel rounds: differential trails, linear trails/hulls, round-count comparisons, and fixed-key exhaustive verification. The full 16-bit block domain allows exhaustive characterization, but any result must remain explicitly scoped to this toy construction.

**Build. Break. Understand. Rebuild.**
