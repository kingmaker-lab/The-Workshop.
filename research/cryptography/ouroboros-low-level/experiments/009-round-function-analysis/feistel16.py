"""Standalone mirror of EXP-008's 8-bit round-function primitives.

The repository analyzer imports EXP-008's source directly. This small module is
included only to make the downloadable EXP-009 analysis bundle self-contained.
"""
SBOX4 = (0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,
         0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2)
P8 = (0, 4, 1, 5, 2, 6, 3, 7)

def substitute8(value: int) -> int:
    value &= 0xFF
    return (SBOX4[value >> 4] << 4) | SBOX4[value & 0x0F]

def permute8(value: int) -> int:
    value &= 0xFF
    out = 0
    for out_bit, in_bit in enumerate(P8):
        out |= ((value >> in_bit) & 1) << out_bit
    return out

def round_function(right: int, round_key: int) -> int:
    if not 0 <= right <= 0xFF or not 0 <= round_key <= 0xFF:
        raise ValueError("right and round_key must be 8-bit unsigned integers")
    return permute8(substitute8(right ^ round_key))
