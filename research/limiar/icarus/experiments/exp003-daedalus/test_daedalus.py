import unittest
from daedalus import Controller, evaluate, calibrate, dataset, experiment, summarize, REGIMES, MODES
class DaedalusTests(unittest.TestCase):
    def test_prefix_cap(self):
        for budget in REGIMES.values():
            for adaptive in (False,True):
                c=Controller(budget,12.,adaptive)
                for i in range(300):
                    c.decide(0.)
                    self.assertLessEqual(c.actual,(i+1)*budget)
                    self.assertGreaterEqual(c.credit,0)
    def test_full_budget(self):
        c=Controller(32,0.,True)
        self.assertTrue(all(c.decide(100.)[0] for _ in range(10)))
    def test_variable_schedule(self):
        rows=dataset(999,400)
        t=calibrate(dataset(1000,100))
        schedule=[(k,100) for k in REGIMES]
        for m in ("adaptive","fixed_guarded"):
            r=evaluate(rows,schedule,m,t)
            self.assertEqual(len(r["segments"]),4)
            self.assertTrue(all(s["max_prefix_overrun_terms"]==0 for s in r["segments"]))
    def test_feedback(self):
        c=Controller(16,1.,True)
        c.decide(100.)
        self.assertGreater(c.threshold,1.)
    def test_experiment(self):
        r=experiment(11,100)
        self.assertEqual(set(r["scenarios"]["VARIABLE"]),set(MODES))
        self.assertEqual(summarize([r])["VARIABLE"]["adaptive"]["max_prefix_overrun_terms"],0)
if __name__=="__main__":
    unittest.main()
