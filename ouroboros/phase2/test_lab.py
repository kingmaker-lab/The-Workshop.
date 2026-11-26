import json
import unittest
from pathlib import Path

from .baseline import feistel16 as canonical
from .baseline import reference_model as oracle
from .lab import BITS, metrics, schedule, trace

VECTORS = json.loads((Path(__file__).parent / "baseline/known_answers.json").read_text())


class BaselineTests(unittest.TestCase):
    def test_frozen_vectors(self):
        for entry in VECTORS["master_keys"]:
            key = int(entry["key"], 16)
            self.assertEqual(canonical.expand_key(key), oracle.reference_expand_key(key))
            for pt, ct in entry["vectors"]:
                with self.subTest(key=entry["key"], plaintext=pt):
                    plain, cipher = int(pt, 16), int(ct, 16)
                    self.assertEqual(canonical.encrypt_block(plain, key), cipher)
                    self.assertEqual(oracle.reference_encrypt(plain, key), cipher)
                    self.assertEqual(canonical.decrypt_block(cipher, key), plain)
                    self.assertEqual(oracle.reference_decrypt(cipher, key), plain)

    def test_trace_endpoint(self):
        report = trace()
        self.assertEqual(len(report["states"]), 9)
        key = int(report["key"], 16)
        plain = int(report["states"][0], 16)
        self.assertEqual(int(report["states"][-1], 16), oracle.reference_encrypt(plain, key))

    def test_identity_control(self):
        points = range(65536)
        report = metrics(points, [0, *BITS])
        self.assertEqual(report["sac_flip_counts"][0], [17] + [0] * 15)
        self.assertEqual(report["differential_row_maxima"][0]["count"], 17)
        self.assertEqual(report["walsh_signed_numerators"][0][:2], [17, 13])

    def test_schedule_panel(self):
        report = schedule()
        self.assertEqual(report["samples"], 256)
        self.assertEqual(len(report["mean_changed_bits_by_input_bit"]), 32)
        self.assertTrue(all(0 < count < 64 for count in report["mean_changed_bits_by_input_bit"]))
