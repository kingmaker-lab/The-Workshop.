"""Tests for OUROBOROS EXP-011 exact multi-round propagation."""
import sys
import unittest
import csv
import json
import tempfile
from pathlib import Path
from collections import Counter

EXP008 = Path(__file__).resolve().parent.parent / "008-reduced-feistel"
sys.path.insert(0, str(EXP008))

from feistel16 import expand_key
from trail_search import (
    DOMAIN, build_round_tables, differential_model, feistel_round,
    _linear_transition_hull, _exact_linear_walsh, save_results,
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
            self.assertAlmostEqual(result["rounds"][0]["markov_mass"], 1.0)

    def test_one_round_differential_model_matches_direct_enumeration(self):
        delta = 0x0101
        result = differential_model(delta, self.ddt, retain_hulls=True)
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
            outputs = [feistel_round(x, keys[0]) for x in range(DOMAIN)]
            candidates = {0, 1, 0x0100, 0x1234, 0xFFFF}
            candidates.update(int(row["output_mask"], 16) for row in result["rounds"][0]["top_hull_endpoints"])
            for output_mask in candidates:
                exact = _exact_linear_walsh(outputs, input_mask, output_mask)
                self.assertEqual(hull.get(output_mask, 0) * DOMAIN, exact * 256)

    def test_save_results_serializes_ranked_observed_differences(self):
        report = {
            "fixed_key_observations": [{
                "master_key": "0x01234567",
                "input_delta": "0x0001",
                "rounds": 8,
                "pairs": DOMAIN,
                "max_observed_probability": 0.01,
                "max_observed_count": 655,
                "markov_hull_max_probability": 0.02,
                "total_variation_distance": 0.1,
                "top_observed_output_differences": [
                    {"output_delta": "0x0003", "count": 655, "probability": 0.01}
                ],
            }],
            "linear_hull_metrics": [],
            "linear_exact_checks": {"records": []},
        }
        with tempfile.TemporaryDirectory() as tmp:
            save_results(report, Path(tmp))
            csv_path = Path(tmp) / "observed_differentials.csv"
            with csv_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            parsed = json.loads(rows[0]["top_observed_output_differences"])
            self.assertEqual(parsed[0]["output_delta"], "0x0003")

    def test_linear_hull_sums_signed_trails(self):
        result = _linear_transition_hull(0x0101, expand_key(0xFFFFFFFF), self.lat)
        self.assertEqual(len(result["rounds"]), 8)
        self.assertTrue(all(row["reachable_output_masks"] >= 1 for row in result["rounds"]))


if __name__ == "__main__":
    unittest.main()
