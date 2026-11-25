import math
import unittest
from feather import classify,dataset,evaluate,calibrate,experiment,DIM,CHEAP
class FeatherTests(unittest.TestCase):
    def test_never_exit_matches_full(self):
        for x,y in dataset(11,100):
            self.assertEqual(classify(x,"full"),classify(x,"dynamic",math.inf))
    def test_always_exit_matches_lite(self):
        for x,y in dataset(11,100):
            self.assertEqual(classify(x,"lite"),classify(x,"dynamic",0))
    def test_cost_bounds(self):
        for x,y in dataset(29,100):
            self.assertIn(classify(x,"dynamic",1)[1],(CHEAP,DIM))
    def test_calibration_constraint(self):
        rows=dataset(42,100)
        t=calibrate(rows)
        self.assertGreaterEqual(evaluate(rows,"dynamic",t)["accuracy"],evaluate(rows,"full")["accuracy"]-.01)
    def test_experiment(self):
        r=experiment(11,100)
        self.assertTrue(0 <= r["term_reduction_fraction"] <= 1)
        self.assertEqual(len(r["models"]["full"]["cpu_samples_ns"]),3)
if __name__=="__main__":
    unittest.main()
