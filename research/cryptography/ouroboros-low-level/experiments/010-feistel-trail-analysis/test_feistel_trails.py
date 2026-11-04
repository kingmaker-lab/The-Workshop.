"""Tests for exhaustive EXP-010 Feistel prefix analysis."""
import unittest
import sys
from pathlib import Path

EXP008 = Path(__file__).resolve().parent.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))
from feistel16 import encrypt_block, expand_key
from feistel_trails import (
    BLOCK_MASK, DOMAIN, analyze_key, decrypt_prefix, encrypt_prefix, round_step,
)


class Exp010Tests(unittest.TestCase):
    def test_one_round_matches_exp008_round_order(self):
        key = 0x01234567
        keys = expand_key(key)
        for block in (0x0000, 0x0001, 0x1234, 0xBEEF, 0xFFFF):
            state = block
            for rk in keys:
                state = round_step(state, rk)
            self.assertEqual(state, encrypt_block(block, key))

    def test_prefix_round_trip(self):
        for key in (0, 0x01234567, 0xFFFFFFFF):
            keys = expand_key(key)
            for rounds in range(1, 9):
                for block in (0, 1, 0x1234, 0xBEEF, 0xFFFF):
                    cipher = encrypt_prefix(block, keys, rounds)
                    self.assertEqual(decrypt_prefix(cipher, keys, rounds), block)

    def test_prefix_outputs_are_permutations_for_all_round_counts(self):
        keys = expand_key(0x01234567)
        states = list(range(DOMAIN))
        for rk in keys:
            states = [round_step(state, rk) for state in states]
            self.assertEqual(len(set(states)), DOMAIN)

    def test_rejects_invalid_round_count(self):
        keys = expand_key(0)
        for bad in (0, 9, -1):
            with self.assertRaises(ValueError):
                encrypt_prefix(0, keys, bad)
            with self.assertRaises(ValueError):
                decrypt_prefix(0, keys, bad)

    def test_exhaustive_analysis_anchor_values(self):
        report = analyze_key(0x01234567)
        rounds = report["rounds"]
        self.assertEqual(len(rounds), 8)
        expected_dp = [1.0, 0.25, 0.0625, 0.03125, 0.0078125, 0.00390625, 35/32768, 22/32768]
        expected_corr = [1.0, 0.0625, 0.0625, 0.0625, 0.0234375, 856/65536, 856/65536, 736/65536]
        for index, row in enumerate(rounds):
            self.assertAlmostEqual(row["differential_single_bit"]["max_probability"], expected_dp[index])
            self.assertAlmostEqual(row["linear_basis_masks"]["max_abs_correlation"], expected_corr[index])
            self.assertEqual(row["differential_single_bit"]["total_pairs"], 16 * (DOMAIN // 2))
            self.assertEqual(row["linear_basis_masks"]["mask_pairs"], 256)
        self.assertEqual(rounds[-1]["differential_single_bit"]["max_count"], 22)

    def test_analysis_rejects_invalid_key(self):
        for key in (-1, 0x100000000, True):
            with self.assertRaises(ValueError):
                analyze_key(key)


if __name__ == "__main__":
    unittest.main()
