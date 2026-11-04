# OUROBOROS — EXP-010: Multi-round Feistel Differential & Linear Propagation

**The Workshop / WolfPack Crypto Lab**  
**Status:** exact enumeration implemented for single-bit input differences and weight-one linear-mask pairs across 1–8 Feistel rounds, using three fixed master keys. Research-only.

## 1. Research question

EXP-009 found strong component-level differential and linear relations in the EXP-008 round function. EXP-010 asks how selected relations propagate through the actual Feistel composition as the round count grows.

The target is the exact EXP-008 construction:
- 16-bit block, split into two 8-bit halves;
- 32-bit master key and the existing KS1 schedule;
- Feistel update L(r+1) = R(r), R(r+1) = L(r) XOR F(R(r), K(r));
- the same S-box, P8 and round function from EXP-008.

No changes are made to the cipher definition.

## 2. Exact analysis scope

This is intentionally **not** a complete DDT or LAT of a 16-bit permutation.

### Differential slice

For each round prefix r = 1,...,8, each of the 16 one-bit input differences Δ(i) = 2^i, and each of the three fixed master keys, enumerate all 2^15 = 32,768 unordered plaintext pairs {x, x XOR Δ(i)}.

For every input difference, record:
- maximum output-difference count and probability;
- number of distinct output differences observed;
- output differences attaining the row maximum.

Per key and round prefix this is 16 × 32,768 = 524,288 pair comparisons.

### Linear basis-mask slice

For each prefix, calculate the exact Walsh coefficient for all 256 pairs of weight-one input and output masks:

W(i,j) = sum over x in {0,1}^16 of (-1)^(x_i XOR E_r(x)_j).

The reported correlation is W(i,j) / 65,536, and the bias is W(i,j) / (2 × 65,536).

The analyzer packs truth tables into Python integers and uses exact population counts. No random sampling or floating-point estimation is involved. This is a 16 × 16 basis-mask slice, not the complete 65,536 × 65,536 LAT.

## 3. Reproducibility and keys

Three reference master keys are analyzed:
- 0x01234567
- 0x00000000
- 0xFFFFFFFF

The implementation imports the canonical EXP-008 feistel16.py from the sibling experiment directory. It does not duplicate the S-box, P8 or KS1. Each prefix uses the first r subkeys of the same eight-round schedule.

## 4. Results

### Maximum differential probability among one-bit input differences

| Prefix rounds | 0x01234567 | 0x00000000 | 0xFFFFFFFF |
|---:|---:|---:|---:|
| 1 | 1.000000 | 1.000000 | 1.000000 |
| 2 | 0.250000 | 0.250000 | 0.250000 |
| 3 | 0.062500 | 0.062500 | 0.062500 |
| 4 | 0.031250 | 0.031250 | 0.031250 |
| 5 | 0.007812 | 0.007812 | 0.007812 |
| 6 | 0.003906 | 0.003906 | 0.003906 |
| 7 | 0.001068 | 0.002380 | 0.001404 |
| 8 | 0.000671 | 0.000702 | 0.000488 |

These are maxima **only over the 16 one-bit input-difference rows**. They are not global maximum differential probabilities over all nonzero 16-bit input differences.

The probability 1.0 at one round is expected from the Feistel wiring: a one-bit difference in the left input half is copied directly into the right output half. It is a structural property of a one-round prefix, not a discovered break of the full eight-round construction.

### Maximum absolute correlation among weight-one mask pairs

| Prefix rounds | 0x01234567 | 0x00000000 | 0xFFFFFFFF |
|---:|---:|---:|---:|
| 1 | 1.000000 | 1.000000 | 1.000000 |
| 2 | 0.062500 | 0.062500 | 0.062500 |
| 3 | 0.062500 | 0.062500 | 0.062500 |
| 4 | 0.062500 | 0.062500 | 0.062500 |
| 5 | 0.023438 | 0.015625 | 0.023438 |
| 6 | 0.013062 | 0.011353 | 0.009277 |
| 7 | 0.013062 | 0.011658 | 0.010376 |
| 8 | 0.011230 | 0.011658 | 0.012939 |

These maxima cover only the 16 × 16 weight-one mask slice. A larger-mask linear approximation may have a higher correlation; this experiment does not claim otherwise.

## 5. Interpretation

1. The one-round extremes are explained by Feistel's direct half swap and copy paths.
2. For the tested one-bit input differences, the maximum differential probability falls sharply as rounds are added. By round 8, the maximum in this restricted slice ranges from 16/32,768 to 23/32,768 for the three keys.
3. The maximum basis-mask correlation also falls sharply after the first round, but it is not monotonic at every round and differs by key in later prefixes.
4. Similar early-round values across keys do not prove key-schedule quality. Only three selected keys were tested.
5. These observations do not establish security. Differential trails can use multi-bit input differences, and linear approximations can use masks with Hamming weight greater than one. Hull effects, related-key behavior and key recovery remain untested.

## 6. Reproduce

Python 3.9+; standard library only. Run from this directory:

~~~bash
python3 -m unittest -v
python3 feistel_trails.py --output results
~~~

To examine another fixed set of keys:

~~~bash
python3 feistel_trails.py --keys 0x13579BDF 0x2468ACE0 --output results/custom
~~~

Outputs:
- summary.json — all round-prefix results and three key schedules;
- round_metrics.csv — headline metrics by key and round;
- single_bit_ddt.csv — all 16 one-bit input-difference row summaries per key and round;
- basis_lat.csv — all 256 basis-mask Walsh coefficients per key and round.

Tests verify the exact EXP-008 round order, prefix reversibility, full-domain permutation behavior for each prefix, bounds checking, and anchor measurements from exhaustive analysis.

## 7. Limits

- The block and key sizes are toy-sized: 16 and 32 bits.
- Only one-bit input differences are included in the differential slice.
- Only weight-one input and output masks are included in the linear slice.
- No full DDT/LAT, multi-round trail search, hull calculation, key ranking, or key-recovery attack is claimed.
- No mode of operation, authentication, side-channel resistance, constant-time behavior, or production suitability is established.
- These results apply to EXP-008's Feistel permutation only. They do not apply to the separate 64-bit Assembly state transition or to SHA-256.

**Decision:** the EXP-009 component weaknesses attenuate substantially in the measured restricted slices as the Feistel rounds accumulate, but this is insufficient to declare the toy cipher secure.

**Build. Break. Understand. Rebuild.**
