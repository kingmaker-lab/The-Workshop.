# OUROBOROS — EXP-008: Reduced Feistel Cipher

**The Workshop / WolfPack Crypto Lab**  
**Status:** experimental design implemented; exhaustive single-bit characterization completed for three fixed master keys. **Not suitable for protecting real data.**

## 1. Research question

Can we define a small, fully specified reversible block transformation and create a reproducible baseline for structural, differential, and linear cryptanalysis?

EXP-008 introduces an independent educational cipher. It does **not** reuse the 64-bit ouroboros_step Assembly state transition, and it does **not** treat the SHA-256-truncated functions from EXP-004–007 as a cipher.

## 2. Fixed specification

| Parameter | Definition |
| --- | --- |
| Construction | Feistel network |
| Block size | 16 bits |
| Master-key size | 32 bits |
| Number of rounds | 8 |
| Halves | 8 bits each |
| Nonlinear layer | PRESENT 4-bit S-box, applied in parallel to two nibbles |
| Diffusion layer | Fixed 8-bit bit permutation P8 |
| Arithmetic | 8-bit addition in key schedule; XOR in round function and Feistel combiner |
| Byte/word convention | Block halves and key bytes are read most-significant first |
| Implementation | Python 3.9+, standard library only |

S-box:
~~~text
S4 = [C, 5, 6, B, 9, 0, A, D, 3, E, F, 8, 4, 7, 1, 2]
~~~

Bit positions in P8 are numbered from the least-significant bit. Output bit j receives input bit P8[j]:
~~~text
P8 = [0, 4, 1, 5, 2, 6, 3, 7]
~~~

## 3. Round function and Feistel transform

For an 8-bit right half R and 8-bit round key K_r:

F(R,K_r) = P8(S(R XOR K_r)).

S applies S4 independently to the high and low nibbles. For each of eight rounds:

L_(r+1) = R_r  
R_(r+1) = L_r XOR F(R_r,K_r).

The plaintext is split as L_0 = plaintext >> 8 and R_0 = plaintext & 0xFF; output is serialized as (L_8 << 8) | R_8.

Decryption runs the Feistel relation with round keys in reverse order:

R_r = L_(r+1)  
L_r = R_(r+1) XOR F(L_(r+1),K_r).

A Feistel round is invertible for any well-defined F when its round key and order are known. This proves the permutation property of this construction; it does **not** prove cryptographic strength.

## 4. Candidate key schedule KS1

Let Q_0 be the 32-bit master-key state. For each round r = 0,...,7, read bytes a,b,c,d from most-significant to least-significant and calculate:

~~~text
RC_r = (0x9D + 0x3D*r) mod 256
u_r  = (ROTL8(a,3) + b + ROTL8(c,1) + d + RC_r) mod 256
t_r  = P8(S(u_r))
K_r  = t_r XOR d
Q_(r+1) = ((Q_r << 8) mod 2^32) OR t_r
~~~

All four master-key bytes participate in the first update. KS1 is a deliberately small candidate schedule and remains a cryptanalysis target. No claim is made that it has adequate key diffusion, resists related-key attacks, or is injective over master keys.

### Rejected preliminary schedule

An earlier draft used XOR mixing of adjacent key bytes. It produced the same eight round keys for master keys 0x00000000 and 0xFFFFFFFF. That candidate was rejected. The issue is retained as part of the experiment record; KS1 replaces it. The regression suite checks that these two selected keys do not collapse to the same schedule, but this single check is not a proof of schedule quality.

## 5. Implementation and tests

- feistel16.py: S-box, P8, KS1, round function, encryption and decryption.
- probe.py: exhaustive single-bit SAC and differential-distribution probe.
- test_exp008.py: unit tests, fixed known-answer vectors, full-domain round trips and permutation check.

Run from this directory:

~~~bash
python3 -m unittest -v
python3 probe.py --key 0x01234567 --output results/my-key
python3 probe.py --key 0x00000000 --output results/zero-key
python3 probe.py --key 0xFFFFFFFF --output results/all-ones-key
~~~

The test suite checks the S-box and P8 as permutations, schedule width, selected schedule separation, fixed vectors, input validation, and encryption/decryption over every one of the 65,536 blocks for three representative keys. It also verifies that the complete encryption mapping is a permutation for the zero master key.

## 6. Exhaustive single-bit method

For every input bit i, the probe evaluates all 2^15 = 32,768 distinct unordered pairs {x, x XOR 2^i}. The representative is selected with bit i equal to zero. Thus, each key produces:

- 16 rows in the single-bit differential distribution, each with 32,768 pairs;
- a complete 16 × 16 empirical SAC matrix for that fixed key;
- 524,288 plaintext-pair comparisons in total;
- the most frequent output differences for each single-bit input difference.

This is exhaustive over the chosen **single-bit input differences**. It is not the complete 65,536 × 65,536 DDT over every possible nonzero input difference.

## 7. Results — three fixed keys

| Master key | Mean SAC | Mean absolute deviation from 0.5 | Maximum cell deviation | Mean changed output bits | Largest single-bit differential count |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0x01234567 | 0.499809 | 0.002298 | 0.008667 | 7.99694 / 16 | 22 / 32,768 |
| 0x00000000 | 0.499912 | 0.002270 | 0.009033 | 7.99860 / 16 | 23 / 32,768 |
| 0xFFFFFFFF | 0.500172 | 0.002291 | 0.007446 | 8.00275 / 16 | 16 / 32,768 |

All values are computed by exhaustive enumeration of the single-bit input pairs for each listed key.

### Interpretation

The measured SAC averages are close to 0.5, and the mean number of changed output bits is close to 8. This is evidence of diffusion for the tested keys and the tested one-bit perturbations only. It is not evidence of independence, resistance to differential or linear attacks, or security of any mode of operation.

The largest differential counts vary by key. The next analysis must examine the structure of the round function and key schedule, not merely compare the mean SAC values.

## 8. Explicit limits

- A 16-bit block and 32-bit key are intentionally tiny. The full block space has only 65,536 values, and the master-key space is trivially enumerable by modern hardware.
- This is a one-block permutation only. No mode of operation, nonce/IV discipline, padding, authentication, replay defense, or key-management protocol is specified.
- There is no formal proof, independent cryptographic review, side-channel analysis, constant-time claim, or production hardening.
- SAC and selected differential rows do not replace differential, linear, algebraic, related-key, integral, boomerang, or implementation analysis.
- Results are not transferable to ouroboros_step (the distinct 64-bit C/Assembly state transition) or to SHA-256.

**Decision:** research-only toy cipher. Never use it to encrypt real data, passwords, credentials, or communications.

## 9. Next research steps

1. Compute the full round-function DDT (all 256 input differences) and linear approximation table for F.
2. Enumerate differential trails across 1–8 Feistel rounds and compare observed hull probabilities against round-level predictions.
3. Characterize KS1 separately: Hamming-distance distribution between round-key sequences, weak/equivalent keys, and related-key behavior.
4. Build a known-plaintext exhaustive key-search baseline to demonstrate the 32-bit key-space limitation and validate the harness.
5. Evaluate bit independence and higher-order dependencies; pre-register statistical procedures before interpreting sample-based results.
6. Only after the baseline is understood, test alternative S-boxes, permutations, schedules, and round counts as separate variants.

**Build. Break. Understand. Rebuild.**
