#!/usr/bin/env python3
"""EXP-008: educational 16-bit Feistel construction. Not for real-world use."""
from __future__ import annotations

BLOCK_BITS = 16
BLOCK_MASK = 0xFFFF
KEY_BITS = 32
KEY_MASK = 0xFFFFFFFF
ROUNDS = 8

# PRESENT 4-bit S-box, expressed with bit 0 as the least significant bit.
SBOX4 = (0xC, 0x5, 0x6, 0xB,
         0x9, 0x0, 0xA, 0xD,
         0x3, 0xE, 0xF, 0x8,
         0x4, 0x7, 0x1, 0x2)

# Output bit j receives input bit P8[j]. LSB-based indexing.
P8 = (0, 4, 1, 5, 2, 6, 3, 7)


def _check_uint(value: int, bits: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must fit in {bits} bits")


def rotl8(value: int, amount: int) -> int:
    value &= 0xFF
    amount %= 8
    if amount == 0:
        return value
    return ((value << amount) | (value >> (8 - amount))) & 0xFF


def substitute8(value: int) -> int:
    """Apply the 4-bit S-box independently to the high and low nibbles."""
    value &= 0xFF
    return (SBOX4[value >> 4] << 4) | SBOX4[value & 0x0F]


def permute8(value: int) -> int:
    """Apply the fixed bit permutation P8 using LSB-based bit numbering."""
    value &= 0xFF
    out = 0
    for out_bit, in_bit in enumerate(P8):
        out |= ((value >> in_bit) & 1) << out_bit
    return out


def round_function(right: int, round_key: int) -> int:
    """F(R, K_r) = P8(S4-parallel(R XOR K_r))."""
    _check_uint(right, 8, "right")
    _check_uint(round_key, 8, "round_key")
    return permute8(substitute8(right ^ round_key))


def expand_key(master_key: int) -> tuple[int, ...]:
    """Expand a 32-bit key into eight 8-bit round keys.

    Let Q_0 be the master key. For round r in [0, 7], read its bytes
    a,b,c,d from most-significant to least-significant and compute:
      RC_r = (0x9D + 0x3D*r) mod 256
      u_r  = (ROTL8(a,3) + b + ROTL8(c,1) + d + RC_r) mod 256
      t_r  = P8(S4-parallel(u_r))
      K_r  = t_r XOR d
      Q_{r+1} = (Q_r << 8 mod 2^32) OR t_r

    This simple nonlinear schedule is itself a research target, not a
    production-grade key schedule.
    """
    _check_uint(master_key, KEY_BITS, "master_key")
    state = master_key
    keys = []
    for r in range(ROUNDS):
        a = (state >> 24) & 0xFF
        b = (state >> 16) & 0xFF
        c = (state >> 8) & 0xFF
        d = state & 0xFF
        constant = (0x9D + 0x3D * r) & 0xFF
        mixed = (rotl8(a, 3) + b + rotl8(c, 1) + d + constant) & 0xFF
        nonlinear = permute8(substitute8(mixed))
        keys.append(nonlinear ^ d)
        state = ((state << 8) & KEY_MASK) | nonlinear
    return tuple(keys)


def encrypt_with_round_keys(plaintext: int, round_keys: tuple[int, ...]) -> int:
    """Encrypt using a pre-expanded key schedule (useful for bulk analysis)."""
    _check_uint(plaintext, BLOCK_BITS, "plaintext")
    if len(round_keys) != ROUNDS or any(not isinstance(k, int) or not 0 <= k <= 0xFF for k in round_keys):
        raise ValueError(f"round_keys must contain exactly {ROUNDS} bytes")
    left, right = (plaintext >> 8) & 0xFF, plaintext & 0xFF
    for round_key in round_keys:
        left, right = right, left ^ round_function(right, round_key)
    return ((left << 8) | right) & BLOCK_MASK


def encrypt_block(plaintext: int, master_key: int) -> int:
    """Encrypt one 16-bit block with eight Feistel rounds."""
    _check_uint(master_key, KEY_BITS, "master_key")
    return encrypt_with_round_keys(plaintext, expand_key(master_key))


def decrypt_block(ciphertext: int, master_key: int) -> int:
    """Invert encrypt_block by applying Feistel rounds in reverse order."""
    _check_uint(ciphertext, BLOCK_BITS, "ciphertext")
    round_keys = expand_key(master_key)
    left, right = (ciphertext >> 8) & 0xFF, ciphertext & 0xFF
    for round_key in reversed(round_keys):
        left, right = right ^ round_function(left, round_key), left
    return ((left << 8) | right) & BLOCK_MASK
