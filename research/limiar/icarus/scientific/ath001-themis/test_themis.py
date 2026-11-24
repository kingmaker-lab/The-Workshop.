import json
import random
import tempfile
import unittest
from pathlib import Path
import themis as t
class Tests(unittest.TestCase):
    def test_audits_feasible(self):
        for k in (2,4):
            for targeted in (False,True):
                for seed in range(32):
                    au=t.sample(random.Random(seed),{2,15,32,63},k,targeted)
                    got=t.a.extend([float(i) for i in range(64)],set(au))
                    self.assertEqual(len(au),k);self.assertEqual(len(got),27)
                    self.assertTrue(set(au)<=got)
                    self.assertTrue(all(0<p<=1 for p in au.values()))
                    self.assertTrue(all(sum(j<i for j in got)<=i*12//28 for i in range(1,65)))
    def test_ht_single_contribution(self):
        # Exact expectation under targeted and uniform mixture.
        d={2,3}
        for targeted in (True,False):
            total=0.
            for i in range(2,32):
                p=(.25/30+.75/2*(i in d)) if targeted else 1/30
                total+=p*t.estimate({i:p},{2},{3},[1]*64 if i==2 else [-1]*64)
            self.assertAlmostEqual(total,200/64)
    def test_inconclusive_retains(self):
        j=t.Judge("benefit_context")
        j.history.extend([0.]*16)
        self.assertEqual(j.observe(20),"benefit_context")
    def test_switch_both_ways(self):
        j=t.Judge("benefit_context")
        j.history.extend([-2.]*16);self.assertEqual(j.observe(20),"margin")
        j.history.extend([2.]*16);self.assertEqual(j.observe(40),"benefit_context")
    def test_delay(self):
        j=t.Judge("margin");j.pending.append((4,2.,2))
        j.observe(3);self.assertEqual(j.delivered,0)
        j.observe(4);self.assertEqual(j.delivered,2)
    def test_no_feedback(self):
        j=t.Judge("benefit_context")
        for i in range(64):self.assertEqual(j.observe(i),"benefit_context")
    def test_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"run.json";run={"seed":1,"scenario":"x","events":[{"batch":i} for i in range(64)]}
            t.save(p,run);self.assertEqual(t.load(p,1,"x"),run)
            obj=json.loads(p.read_text());obj["run"]["seed"]=2;p.write_text(json.dumps(obj))
            with self.assertRaises(RuntimeError):t.load(p,1,"x")
if __name__=="__main__":unittest.main()
