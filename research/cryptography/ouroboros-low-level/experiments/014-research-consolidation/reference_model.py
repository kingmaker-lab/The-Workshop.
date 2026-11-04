#!/usr/bin/env python3
"""Independent specification oracle for OUROBOROS EXP-008.

This module re-expresses the published EXP-008 specification and does not
import the canonical feistel16 implementation. It is a reference model for
differential conformance testing, not a second optimized implementation.
"""
from __future__ import annotations

SBOX4 = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD, 0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
P8 = (0, 4, 1, 5, 2, 6, 3, 7)
MASK8 = 0xFF
MASK16 = 0xFFFF
MASK32 = 0xFFFFFFFF
ROUNDS = 8


def _uint(value: int, bits: int, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if not 0 <= value < (1 << bits):
        raise ValueError(f"{name} must fit in {bits} bits")


def rotate_byte_left(value: int, amount: int) -> int:
    value &= MASK8
    amount %= 8
    if amount == 0:
        return value
    return ((value << amount) | (value >> (8 - amount))) & MASK8


def reference_substitute_byte(value: int) -> int:
    value &= MASK8
    high = SBOX4[(value >> 4) & 0x0F]
    low = SBOX4[value & 0x0F]
    return (high << 4) | low


def reference_permute_byte(value: int) -> int:
    value &= MASK8
    output = 0
    for destination in range(8):
        source = P8[destination]
        output |= ((value >> source) & 1) << destination
    return output


def reference_round_function(right: int, round_key: int) -> int:
    _uint(right, 8, "right")
    _uint(round_key, 8, "round_key")
    return reference_permute_byte(reference_substitute_byte(right ^ round_key))


def reference_expand_key(master_key: int) -> tuple[int, ...]:
    _uint(master_key, 32, "master_key")
    state = master_key
    output = []
    for round_index in range(ROUNDS):
        a = (state >> 24) & MASK8
        b = (state >> 16) & MASK8
        c = (state >> 8) & MASK8
        d = state & MASK8
        round_constant = (0x9D + (0x3D * round_index)) & MASK8
        total = (rotate_byte_left(a, 3) + b + rotate_byte_left(c, 1) + d + round_constant) & MASK8
        nonlinear = reference_permute_byte(reference_substitute_byte(total))
        output.append(nonlinear ^ d)
        state = ((state << 8) & MASK32) | nonlinear
    return tuple(output)


def reference_encrypt_with_round_keys(plaintext: int, round_keys: tuple[int, ...]) -> int:
    _uint(plaintext, 16, "plaintext")
    if not isinstance(round_keys, (tuple, list)) or len(round_keys) != ROUNDS:
        raise ValueError("round_keys must contain exactly eight bytes")
    for key in round_keys:
        _uint(key, 8, "round_key")
    left = (plaintext >> 8) & MASK8
    right = plaintext & MASK8
    for round_key in round_keys:
        old_left, old_right = left, right
        left = old_right
        right = old_left ^ reference_round_function(old_right, round_key)
    return ((left << 8) | right) & MASK16


def reference_encrypt(plaintext: int, master_key: int) -> int:
    _uint(master_key, 32, "master_key")
    return reference_encrypt_with_round_keys(plaintext, reference_expand_key(master_key))


def reference_decrypt_with_round_keys(ciphertext: int, round_keys: tuple[int, ...]) -> int:
    _uint(ciphertext, 16, "ciphertext")
    if not isinstance(round_keys, (tuple, list)) or len(round_keys) != ROUNDS:
        raise ValueError("round_keys must contain exactly eight bytes")
    for key in round_keys:
        _uint(key, 8, "round_key")
    left = (ciphertext >> 8) & MASK8
    right = ciphertext & MASK8
    for round_key in reversed(round_keys):
        old_left, old_right = left, right
        left = old_right ^ reference_round_function(old_left, round_key)
        right = old_left
    return ((left << 8) | right) & MASK16


def reference_decrypt(ciphertext: int, master_key: int) -> int:
    _uint(master_key, 32, "master_key")
    return reference_decrypt_with_round_keys(ciphertext, reference_expand_key(master_key))
