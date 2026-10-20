"""Unit tests for EXP-007: reference implementations, SAC and BIC invariants."""
import csv
import hashlib
import tempfile
from pathlib import Path
import unittest

from sac_probe import analyze, engine, phi_coefficient, representative_inputs, rotl, save_files


class Experiment007Tests(unittest.TestCase):
    def test_sha_reference_vector(self):
        for name, bits in [('sha16', 16), ('sha32', 32)]:
            n, f = engine(name, 'ouroboros')
            self.assertEqual(n, bits)
            state = 0x1234 if bits == 16 else 0x12345678
            expected = hashlib.sha256(b'ouroboros' + state.to_bytes(bits//8, 'big')).digest()[:bits//8]
            self.assertEqual(f(state), int.from_bytes(expected, 'big'))

    def test_unique_unordered_pairs(self):
        for bit in range(8):
            x = list(representative_inputs(8, bit, 128, seed=1, exhaustive=True))
            self.assertEqual(len(set(x)), 128)
            self.assertTrue(all(not (v & (1 << bit)) for v in x))
            self.assertEqual(len(set(x + [v ^ (1 << bit) for v in x])), 256)

    def test_fixed_seed(self):
        x = list(representative_inputs(16, 1, 15, 42, False))
        self.assertEqual(x, list(representative_inputs(16, 1, 15, 42, False)))
        self.assertNotEqual(x, list(representative_inputs(16, 1, 15, 43, False)))

    def test_identity_control(self):
        summary, matrix, rows, bic = analyze('identity16', samples=64, bic_samples=32)
        self.assertEqual(summary['sac']['mean_changed_bits_per_pair'], 1.0)
        self.assertAlmostEqual(summary['sac']['mean_flip_probability'], 1/16)
        for i in range(16):
            for j in range(16):
                self.assertEqual(matrix[i][j], 1 if i == j else 0)
        self.assertEqual(summary['bic']['defined_phi_count'], 0)

    def test_known_toy_differential(self):
        summary, matrix, _, _ = analyze('toy_arx8', exhaustive=True, bic_samples=32)
        self.assertEqual(summary['samples_per_input_bit'], 128)
        for j in range(8):
            self.assertEqual(matrix[7][j], 1 if j in (4,6) else 0)

    def test_phi(self):
        self.assertIsNone(phi_coefficient(0, 5, 0, 10))
        self.assertAlmostEqual(phi_coefficient(5, 5, 5, 10), 1)
        self.assertAlmostEqual(phi_coefficient(5, 5, 0, 10), -1)
        self.assertAlmostEqual(phi_coefficient(5, 5, 2, 10), -0.2)

    def test_artifacts(self):
        summary, matrix, sac, bic = analyze('sha16',samples=16,bic_samples=8)
        self.assertEqual(len(matrix), 16)
        self.assertEqual(len(sac), 256)
        self.assertEqual(len(bic), 16*120)
        with tempfile.TemporaryDirectory() as d:
            save_files(Path(d), summary, matrix, sac, bic)
            for name in ['summary.json','sac.csv','sac_matrix.csv','bic.csv']:
                self.assertTrue((Path(d)/name).exists())
            with (Path(d)/'sac.csv').open() as f:
                self.assertEqual(len(list(csv.DictReader(f))),256)

    def test_unsupported_exhaustive_32(self):
        with self.assertRaises(ValueError):
            analyze('sha32', exhaustive=True)


if __name__ == '__main__':
    unittest.main()
