# OUROBOROS — EXP-011: Multi-round Differential Trails & Linear Hulls

**The Workshop / WolfPack Crypto Lab**  
**Branch:** `exp-011-multiround-trail-search`  
**Scope:** EXP-008 toy Feistel cipher, unchanged.

## 1. Research question

EXP-009 measured the complete DDT and Walsh LAT of the isolated round component. EXP-010 measured selected one-bit differences and basis-mask correlations of round prefixes. EXP-011 advances to multi-round propagation:

- search high-probability differential characteristics;
- aggregate DDT transition paths into a differential Markov-hull estimate;
- search high-correlation linear trails;
- aggregate signed trail correlations into linear hulls;
- compare differential Markov estimates with exact full-domain fixed-key observations;
- verify selected linear-hull coefficients against direct full-domain Walsh enumeration.

The cipher definition and its EXP-008 key schedule are not modified.

## 2. Differential characteristics versus differential hulls

For state difference ((\Delta L,\Delta R)), one Feistel round maps to:

[
(\Delta L,\Delta R) \longrightarrow (\Delta R,\Delta L\oplus\Delta F)
]

where (\Delta F) is an output difference of the 8-bit round function for input difference (\Delta R).

The local transition weight is:

[
p_r=\frac{DDT[\Delta R,\Delta F]}{256}
]

A **differential characteristic** is one particular sequence of intermediate differences. Its Markov-model probability is the product of its local transition probabilities.

A **differential Markov hull estimate** for a final output difference is the sum of the probabilities of all compatible characteristics reaching that output difference.

This DDT propagation is not silently treated as the exact differential distribution of a fixed-key, deterministic cipher. The internal value distribution conditioned on an accumulated difference need not remain uniform. Therefore EXP-011 separately enumerates the full 65,536-element plaintext domain for selected fixed-key input differences and compares the observed output-difference distribution with the Markov estimate using total variation distance.

## 3. Linear trails and linear hulls

For a local round-function approximation with input mask (\alpha) and output mask (\beta), the Walsh coefficient is:

[
W_F(\alpha,\beta)=\sum_{x\in\{0,1\}^{8}}(-1)^{\langle\alpha,x\rangle\oplus\langle\beta,F(x)\rangle}
]

For a fixed round subkey (K_r), the XOR input translation changes the sign by ( (-1)^{\langle\alpha,K_r\rangle} ), but not the magnitude.

For state masks ((a,b)), a compatible Feistel output mask is ((b\oplus\alpha,a)). The local signed correlation is the round-specific Walsh coefficient divided by 256.

A **linear trail** is one compatible sequence of intermediate masks. A **linear hull** is the signed sum of the products of all trail correlations connecting the same external input and output masks. These are distinct quantities: the largest individual trail is not necessarily the largest hull.

The implementation uses integer Walsh numerators and exact dyadic scaling to avoid floating-point accumulation during trail summation.

## 4. Experimental coverage

### Differential starting differences

- All 16 one-bit 16-bit differences.
- Six selected multi-bit differences: `0x0003`, `0x0005`, `0x0101`, `0x0202`, `0x8001`, `0x8080`.

The Markov transition model propagates each start through all eight round prefixes.

### Exact fixed-key differential observations

For each of three master keys (`0x01234567`, `0x00000000`, `0xFFFFFFFF`), six selected input differences are evaluated against every one of the 65,536 plaintext blocks for every prefix from one to eight rounds.

The result reports:
- maximum observed output-difference probability;
- maximum Markov-hull endpoint probability;
- total variation distance between the full observed distribution and the Markov estimate.

### Linear trail/hull search

Three external input masks (`0x0100`, `0x8000`, `0x0101`) are evaluated for the same three master keys and all eight prefixes.

The report distinguishes:
- maximum absolute single-trail correlation;
- maximum absolute signed linear-hull correlation;
- reachable external output masks;
- strongest predicted hull endpoints.

For the top eight predicted hull endpoints at each prefix, the implementation independently computes the full-domain Walsh coefficient over all 65,536 plaintexts and checks exact equality with the trail sum.

## 5. Reproduction

Python 3.9+; standard library only. Run from this directory:

~~~bash
python3 -m unittest -v
python3 trail_search.py --output results
~~~

To run another set of fixed keys:

~~~bash
python3 trail_search.py --keys 0x13579BDF 0x2468ACE0 --output results/custom
~~~

Outputs:
- `summary.json` — full methods, trail/hull results, fixed-key comparisons and exact linear checks.
- `observed_differentials.csv` — selected full-domain fixed-key differential observations and Markov-model distances.
- `linear_hulls.csv` — strongest trail and hull metrics per key/mask/round.
- `linear_exact_checks.csv` — direct Walsh checks against the signed trail sums.

## 6. Interpretation rules

- A high-probability characteristic is not the same as a high-probability final differential. Many characteristics can contribute to a hull.
- A large individual linear trail is not the same as a large linear hull. Signs can reinforce or cancel.
- DDT Markov propagation is an analytical model; fixed-key observed distributions are measured separately.
- The direct Walsh checks validate the linear-hull summation for the enumerated endpoints. They do not prove security.
- No full 16-bit DDT/LAT, key-recovery attack, side-channel analysis, or production suitability is claimed.

## 7. Explicit limits

The design is a 16-bit block / 32-bit key toy cipher. Results apply only to EXP-008's specified Feistel construction. They do not apply to the separate 64-bit Assembly state transition or to SHA-256. Do not use this construction to protect real information.

**Decision:** EXP-011 is a trail-search and hull-accounting experiment. Its main scientific output is the separation and comparison of Markov differential estimates, exact fixed-key differential observations, individual linear trails, and signed linear hulls.

**Build. Break. Understand. Rebuild.**
