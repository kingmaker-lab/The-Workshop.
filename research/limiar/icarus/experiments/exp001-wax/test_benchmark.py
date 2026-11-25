import unittest
from benchmark import integer_work, buffer_work, measure

class WaxTests(unittest.TestCase):
    def test_integer_known(self):
        self.assertEqual(integer_work(1), 1015568748)
    def test_buffer_known(self):
        self.assertEqual(buffer_work(10), 900)
    def test_measure(self):
        r = measure(buffer_work, 8, 3)
        self.assertEqual(r["checksum"], 720)
        self.assertEqual(len(r["samples"]), 3)
        self.assertTrue(all(s["wall_ns"] >= 0 and s["cpu_ns"] >= 0 for s in r["samples"]))

if __name__ == "__main__":
    unittest.main()
