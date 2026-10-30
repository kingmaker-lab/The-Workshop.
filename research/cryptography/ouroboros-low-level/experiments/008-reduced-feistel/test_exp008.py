"Unit and exhaustive invariants for the EXP-008 reduced Feistel cipher."
import csv
import hashlib
import tempfile
from pathlib import Path
import unittest

from feistel16 import (
    BLOCK_MASK, SBOX4, decrypt_block, encrypt_block, expand_key,
    encrypt_with_round_keys, permute8, round_function, substitute8,
)


class Exp008Tests(unittest.TestCase):
    def test_sbox_is_permutation(self):
        self.assertEqual(set(SBOX4), set(range(16)))

    def test_substitution_and_permutation_are_bijective(self):
        self.assertEqual({substitute8(x) for x in range(256)}, set(range(256)))
        self.assertEqual({permute8(x) for x in range(256)}, set(range(256)))

    def test_key_schedule_has_eight_bytes(self):
        for key in (0, 1, 0x01234567, 0xFFFFFFFF):
            keys = expand_key(key)
            self.assertEqual(len(keys), 8)
            self.assertTrue(all(0 <= value <= 0xFF for value in keys))

    def test_distinct_selected_master_keys_expand_differently(self):
        self.assertNotEqual(expand_key(0x00000000), expand_key(0xFFFFFFFF))
        self.assertNotEqual(expand_key(0x00000000), expand_key(0x01234567))

    def test_preexpanded_schedule_matches_wrapper(self):
        key = 0x01234567
        schedule = expand_key(key)
        for block in (0, 1, 0x1234, 0xBEEF, 0xFFFF):
            self.assertEqual(encrypt_with_round_keys(block, schedule), encrypt_block(block, key))

    def test_known_answer_vectors(self):
        vectors = [
            (0x0000, 0x00000000, 0xEBEF),
            (0x0001, 0x00000000, 0xD1A6),
            (0x1234, 0x01234567, 0x561F),
            (0xBEEF, 0xFFFFFFFF, 0x2A94),
        ]
        for plaintext, key, expected in vectors:
            self.assertEqual(encrypt_block(plaintext, key), expected)

    def test_exhaustive_round_trip_for_representative_keys(self):
        for key in (0, 0x01234567, 0xFFFFFFFF):
            for block in range(BLOCK_MASK + 1):
                ciphertext = encrypt_block(block, key)
                self.assertEqual(decrypt_block(ciphertext, key), block)

    def test_exhaustive_permutation_for_zero_key(self):
        outputs = {encrypt_block(block, 0) for block in range(BLOCK_MASK + 1)}
        self.assertEqual(len(outputs), 1 << 16)

    def test_round_function_domain(self):
        for x in range(256):
            self.assertTrue(0 <= round_function(x, 0xA5) <= 0xFF)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            encrypt_block(0x10000, 0)
        with self.assertRaises(ValueError):
            encrypt_block(0, 0x100000000)
        with self.assertRaises(TypeError):
            encrypt_block(True, 0)


if __name__ == "__main__":
    unittest.main()
