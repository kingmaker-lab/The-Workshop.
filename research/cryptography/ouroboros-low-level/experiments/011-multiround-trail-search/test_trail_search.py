"""Tests for OUROBOROS EXP-011 exact multi-round propagation."""
import sys
import unittest
from pathlib import Path
from collections import Counter

EXP008 = Path(__file__).resolve().parent.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))

from feistel16 import expand_key
from trail_search import (
    DOMAIN, build_round_tables, differential_model, feistel_round,
    _linear_transition_hull, _exact_linear_walsh,
)


class Exp011Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ddt, cls.lat = build_round_tables()

    def test_ddt_rows_conserve_domain(self):
        self.assertTrue(all(sum(row) == 256 for row in self.ddt))

    def test_differential_model_conserves_probability_mass(self):
        for delta in (0x0001, 0x0100, 0x0101, 0x0003):
            result = differential_model(delta, self.ddt)
            self.assertEqual(len(result["rounds"]), 8)
            self.assertAlmostEqual(result["rounds"][0]["max_markov_hull_probability"], 1.0)

    def test_one_round_differential_model_matches_direct_enumeration(self):
        delta = 0x0101
        result = differential_model(delta, self.ddt)
        expected = Counter()
        for x in range(DOMAIN):
            left, right = x >> 8, x & 0xFF
            dl, dr = delta >> 8, delta & 0xFF
            out = feistel_round(x, 0x5A)
            other = feistel_round(x ^ delta, 0x5A)
            expected[out ^ other] += 1
        model = result["_hulls_by_round"][0]
        for output_delta in range(DOMAIN):
            self.assertEqual(model[output_delta] * DOMAIN, expected[output_delta] * 256)

    def test_linear_hull_one_round_matches_direct_walsh(self):
        keys = expand_key(0x01234567)
        for input_mask in (0x0100, 0x0101, 0x8000):
            result = _linear_transition_hull(input_mask, keys[:1], self.lat)
            hull = result["_final_hull_numerators"]
            for output_mask in range(DOMAIN):
                exact = _exact_linear_walsh(
                    [feistel_round(x, keys[0]) for x in range(DOMAIN)],
                    input_mask,
                    output_mask,
                )
                self.assertEqual(hull.get(output_mask, 0) * DOMAIN, exact * 256)

    def test_linear_hull_sums_signed_trails(self):
        result = _linear_transition_hull(0x0101, expand_key(0xFFFFFFFF), self.lat)
        self.assertEqual(len(result["rounds"]), 8)
        self.assertTrue(all(row["reachable_output_masks"] >= 1 for row in result["rounds"]))


if __name__ == "__main__":
    unittest.main()
