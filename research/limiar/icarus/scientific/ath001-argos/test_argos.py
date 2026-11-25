import itertools
import random
import unittest
from unittest.mock import patch
import argos as a
class ArgosTests(unittest.TestCase):
    def test_local_memory_floor(self):
        with patch.object(a,"memory",return_value={"MemAvailable":256*1024}), patch.object(a,"cached_temperature",return_value=65.):
            self.assertEqual(a.safety_snapshot(())["mem_available_kib"],256*1024)
        for value in (None,256*1024-1):
            with patch.object(a,"memory",return_value={"MemAvailable":value}):
                with self.assertRaises(RuntimeError):a.safety_snapshot(())
    def test_thermal_guard(self):
        with patch.object(a,"memory",return_value={"MemAvailable":400*1024}):
            for value,paths in ((80.,()),(None,("known",))):
                with patch.object(a,"cached_temperature",return_value=value):
                    with self.assertRaises(RuntimeError):a.safety_snapshot(paths)
    def test_quota_and_audits(self):
        for seed in range(30):
            r=random.Random(seed);s=a.audit_indices(r)
            got=a.extend([r.random() for _ in range(a.N)],s)
            self.assertTrue(s<=got);self.assertEqual(len(got),a.K)
            self.assertTrue(all(sum(j<i for j in got)<=i*(a.B-4)//28 for i in range(1,a.N+1)))
    def test_contraction_exhaustive(self):
        p=[0.,1.,4.,3.,2.,6.,5.,7.]
        for audit in ({2},{4},{6},{2,6}):
            got=a.extend(p,audit)
            fs=[set(s) for s in itertools.combinations(range(len(p)),3) if audit<=set(s) and all(sum(j<i for j in s)<=i*(a.B-4)//28 for i in range(1,len(p)+1))]
            self.assertEqual(sum(p[i] for i in got),max(sum(p[i] for i in s) for s in fs))
    def test_no_feedback(self):
        self.assertEqual(a.policy([],None,"benefit_context"),("benefit_context",None))
    def test_delay(self):
        pending=[(t+a.DELAY,t) for t in range(10)]
        self.assertEqual([t for due,t in pending if due<=3],[])
        self.assertEqual([t for due,t in pending if due<=4],[0])
    def test_stable_cheap_distribution(self):
        x=a.stream(17,"abrupt",0);y=a.stream(17,"abrupt",30)
        self.assertEqual([v[:4] for v,_ in x],[v[:4] for v,_ in y])
        self.assertNotEqual([v[4:] for v,_ in x],[v[4:] for v,_ in y])
    def test_schedule(self):
        self.assertEqual(a.mixture("gradual",16),0)
        self.assertEqual(a.mixture("gradual",28),.5)
        self.assertEqual(a.mixture("gradual",40),1)
        self.assertEqual([a.mixture("recurring",t) for t in (0,16,32,48)],[0,1,0,1])
if __name__=="__main__":unittest.main()
