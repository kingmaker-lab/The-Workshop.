"""Tests for the independent EXP-014 specification oracle."""
import unittest
from conformance import KEYS, KNOWN_ANSWERS, run_exhaustive_conformance
from reference_model import reference_decrypt, reference_encrypt, reference_expand_key


class Exp014Tests(unittest.TestCase):
    def test_frozen_known_answer_vectors(self):
        for key, vectors in KNOWN_ANSWERS.items():
            for plaintext, expected in vectors.items():
                self.assertEqual(reference_encrypt(plaintext, key), expected)
                self.assertEqual(reference_decrypt(expected, key), plaintext)

    def test_round_key_schedule_anchors(self):
        self.assertEqual(reference_expand_key(0), (0xBD, 0x44, 0xB3, 0xC9, 0x88, 0x57, 0x48, 0xDE))
        self.assertEqual(reference_expand_key(0x01234567), (0xB3, 0xAB, 0x05, 0x10, 0x09, 0x94, 0x57, 0xBF))
        self.assertEqual(reference_expand_key(0xFFFFFFFF), (0x03, 0x93, 0xD8, 0xF4, 0xBF, 0xE2, 0x22, 0x52))

    def test_exhaustive_conformance_report(self):
        report = run_exhaustive_conformance()
        self.assertEqual(report["round_key_byte_comparisons"], 5 * 8)
        self.assertEqual(report["known_answer_vector_checks"], 25)
        self.assertEqual(report["full_domain_block_comparisons"], 5 * 65536)
        self.assertEqual(len(report["per_key"]), len(KEYS))
        self.assertTrue(all(row["canonical_mapping_is_permutation"] for row in report["per_key"]))


if __name__ == "__main__":
    unittest.main()
