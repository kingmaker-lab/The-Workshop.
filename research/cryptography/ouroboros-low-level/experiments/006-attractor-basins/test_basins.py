"""Regression tests for the Ouroboros EXP-006 reference model."""
import hashlib
import unittest
from basins import analyze_functional_graph, transition_map, baseline_orbit, study

class FunctionalGraphTests(unittest.TestCase):
    def test_known_tiny_functional_graph(self):
        nxt = [1, 2, 1, 3]
        metrics, basin, distances = analyze_functional_graph(nxt)
        self.assertEqual(metrics['cycle_count'], 2)
        self.assertEqual(metrics['cycle_lengths'], [2, 1])
        self.assertEqual(metrics['basin_sizes'], [3, 1])
        self.assertEqual(distances, [1, 0, 0, 0])
        self.assertEqual(basin[0], basin[1])
        self.assertNotEqual(basin[0], basin[3])
        self.assertEqual(metrics['states_on_cycles'], 3)

    def test_hash_reference_and_seed(self):
        nxt, seed = transition_map('ouroboros')
        self.assertEqual(seed, 0x93DB)
        for x in (0, 1, seed, 0xFFFF):
            expected = hashlib.sha256(b'ouroboros' + x.to_bytes(2, 'big')).digest()
            self.assertEqual(nxt[x], int.from_bytes(expected[:2], 'big'))

    def test_exp004_regression(self):
        nxt, seed = transition_map('ouroboros')
        metrics, basin, dist = analyze_functional_graph(nxt)
        self.assertEqual(metrics['cycle_lengths'], [155, 31, 18, 7, 4, 1])
        self.assertEqual(metrics['basin_sizes'], [40691, 15629, 8251, 928, 35, 2])
        self.assertEqual(metrics['fixed_points'], ['0x9A18'])
        self.assertEqual(baseline_orbit(nxt, seed, basin, dist, metrics), {
            'seed_hex': '0x93DB', 'mu': 55, 'lambda': 31,
            'cycle_entry_hex': '0xE977', 'basin_size': 8251})
        self.assertEqual(sum(basin[seed] == basin[seed ^ (1 << bit)] for bit in range(16)), 4)

    def test_other_message_reference(self):
        results = study(['wolfpack', 'ares'])
        self.assertEqual((results[0]['cycle_count'], results[0]['largest_basin']), (3, 64623))
        self.assertEqual((results[1]['cycle_count'], results[1]['largest_basin']), (8, 28932))
        for r in results:
            self.assertEqual(sum(r['basin_sizes']), 65536)
            self.assertEqual(len(r['fixed_points']), r['cycle_lengths'].count(1))
            self.assertLessEqual(r['mean_distance_to_cycle'], r['max_distance_to_cycle'])

    def test_stability_across_calls(self):
        a, b = study(['ouroboros', 'ouroboros'])
        self.assertEqual(a, b)

if __name__ == '__main__':
    unittest.main(verbosity=2)
