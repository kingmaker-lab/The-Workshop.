import unittest
from ascension import load_native,pack,run,dataset,calibrate,REGIMES,MODES
class AscensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lib=load_native("libascension.so")
        cls.rows=dataset(999,400)
        cls.thresholds=calibrate(dataset(1000,400))
    def test_guarded_prefix(self):
        for name in REGIMES:
            seg=[(name,self.rows,pack(self.rows))]
            for m in MODES:
                if m.endswith(("full","lite")): continue
                self.assertEqual(run(m,seg,self.thresholds,self.lib)["segments"][0]["max_prefix_overrun_terms"],0)
    def test_static_parity(self):
        seg=[("LIBERTAS",self.rows,pack(self.rows))]
        for py,c in (("py_full","c_full"),("py_lite","c_lite")):
            a,b=(run(m,seg,self.thresholds,self.lib) for m in (py,c))
            self.assertEqual(a["accuracy"],b["accuracy"])
            self.assertEqual(a["mean_terms"],b["mean_terms"])
    def test_integer_parity(self):
        for name in REGIMES:
            seg=[(name,self.rows,pack(self.rows))]
            for py,c in (("A3","c_A3"),("A4","c_native")):
                a,b=(run(m,seg,self.thresholds,self.lib) for m in (py,c))
                self.assertEqual(a["segments"],b["segments"])
    def test_fast_path(self):
        seg=[("LIBERTAS",self.rows,pack(self.rows))]
        a,b=(run(m,seg,self.thresholds,self.lib) for m in ("A1","A4"))
        self.assertEqual(a["segments"],b["segments"])
    def test_variable(self):
        seg=[(k,self.rows[i*100:(i+1)*100],pack(self.rows[i*100:(i+1)*100])) for i,k in enumerate(REGIMES)]
        for m in ("A1","A2","A3","A4","c_native"):
            r=run(m,seg,self.thresholds,self.lib)
            self.assertEqual(len(r["segments"]),4)
            self.assertTrue(all(s["max_prefix_overrun_terms"]==0 for s in r["segments"]))
if __name__=="__main__": unittest.main()
