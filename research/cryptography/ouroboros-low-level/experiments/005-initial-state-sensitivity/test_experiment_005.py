import unittest
import hashlib
from ouroboros_sensitivity import experiment, make_map, orbit, hamming_trace, same_time_collision

class TestOuroborosExperiment005(unittest.TestCase):
    def test_reference_vectors(self):
        for bits, seed in [(16, 0x93DB), (32, 0x93DBF636)]:
            step, actual_seed = make_map('ouroboros', bits)
            self.assertEqual(actual_seed, seed)
            expected = hashlib.sha256(b'ouroboros' + seed.to_bytes(bits//8, 'big')).digest()[:bits//8]
            self.assertEqual(step(seed), int.from_bytes(expected, 'big'))

    def test_exp004_regression(self):
        for bits, expected in [(16, (55,31,0xE977)), (32,(115659,19959,0xA8A73F96))]:
            step, seed = make_map('ouroboros', bits)
            result = orbit(step, seed, 1000000)
            self.assertEqual((result['mu'],result['lambda'],result['entry']), expected)

    def test_same_cycle_different_phase(self):
        step = lambda x: 1-x
        a, b = orbit(step, 0, 10), orbit(step, 1, 10)
        self.assertEqual(a['cycle_id'],b['cycle_id'])
        self.assertIsNone(same_time_collision(a, b))

    def test_same_time_merge(self):
        step = lambda x: {0:2,1:2,2:3,3:3}[x]
        self.assertEqual(same_time_collision(orbit(step,0,10),orbit(step,1,10)),1)

    def test_hamming_trace(self):
        self.assertEqual(hamming_trace(lambda x:(x+1)%4,0,1,3), [1,2,1])

    def test_all_flips_16(self):
        result = experiment(bits=16, samples=64)
        summary = result['summary']
        self.assertEqual(summary['same_eventual_cycle'],4)
        self.assertEqual(summary['different_eventual_cycle'],12)
        self.assertEqual(summary['same_time_collisions'],0)
        self.assertEqual(summary['unique_target_cycle_lengths'], {7:8,31:4,155:4})

if __name__ == '__main__':
    unittest.main()
