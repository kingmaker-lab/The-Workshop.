import itertools
import unittest
from icaro import load,replay,ct,sol,batch
class IcaroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lib=load()
    def setUp(self):
        self.s=self.lib.icaro_replay_new((ct.c_double*4)(.5,1,2,12))
        self.assertTrue(self.s)
    def tearDown(self):self.lib.solar_free(self.s)
    def test_quantized_prefix(self):
        for n in (32,63,64,65,128,256):
            data=batch(1297,n,n)
            for b in (8,16,24,32):
                r=replay(self.lib,self.s,data,n,b,2)
                self.assertEqual(r["terms"],4*n+28*(n*(b-4)//28))
                self.assertEqual(r["over"],0)
    def test_matched_cost(self):
        n=64;data=batch(1297,0,n)
        for b in (8,16,24,32):
            for m in (0,1):
                old=replay(self.lib,self.s,data,n,b,m)
                r=replay(self.lib,self.s,data,n,b,3,(old["terms"]-4*n)//28)
                self.assertEqual(r["terms"],old["terms"])
                self.assertEqual(r["over"],0)
    def test_full_parity(self):
        data=batch(1297,0,64)
        a=replay(self.lib,self.s,data,64,32,0);b=replay(self.lib,self.s,data,64,32,2)
        self.assertEqual((a["correct"],a["terms"]),(b["correct"],b["terms"]))
    def test_rank_priority(self):
        # Only expansion flips the prediction; the minimum feasible margin
        # must be selected at exact cost 1 expansion. First row ineligible.
        rows=[([.01,0,0,0]+[-1.]*28,1),([.2,0,0,0]+[-1.]*28,1),
              ([.1,0,0,0]+[-1.]*28,0),([.3,0,0,0]+[-1.]*28,1)]
        r=replay(self.lib,self.s,sol.encode(rows),4,16,3,1)
        self.assertEqual((r["correct"],r["terms"],r["over"]),(4,44,0))
    def test_no_windup(self):
        data=batch(1297,2,64);a=replay(self.lib,self.s,data,64,16,2)
        for _ in range(24):self.assertEqual(replay(self.lib,self.s,data,64,16,2),a)
    def test_invalid_input(self):
        data=batch(1297,0,64)
        with self.assertRaises(RuntimeError):replay(self.lib,self.s,data[:-1],64,16,2)
        with self.assertRaises(RuntimeError):replay(self.lib,self.s,data,64,16,3,28)
        with self.assertRaises(RuntimeError):replay(self.lib,self.s,data,64,12,2)
        with self.assertRaises(RuntimeError):replay(self.lib,self.s,data[:-1]+b"\x02",64,16,2)
if __name__=="__main__":unittest.main()
