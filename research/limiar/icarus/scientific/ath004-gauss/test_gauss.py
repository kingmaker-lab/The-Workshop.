import math
import unittest
import gauss as g
class Checks(unittest.TestCase):
    def test_seeds(self):
        a=[s for i in range(1,6) for s in g.seeds(i)]
        self.assertEqual(len(a),120);self.assertEqual(len(set(a)),120)
        self.assertNotIn(2999,a)
    def test_bound_constant(self):
        self.assertAlmostEqual(g.upper([.5]*5),.5)
    def test_bound_variation(self):
        self.assertAlmostEqual(g.upper([1,2,3,4,5]),3+g.T95/math.sqrt(2))
    def test_log_ratio(self):
        self.assertAlmostEqual(math.exp(g.upper([math.log(.4)]*5)),.4)
    def test_incomplete(self):
        with self.assertRaises(ValueError):g.upper([0]*4)
if __name__=="__main__":unittest.main()
