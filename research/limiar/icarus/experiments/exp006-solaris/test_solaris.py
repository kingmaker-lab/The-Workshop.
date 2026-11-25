import unittest
from solaris import load,encode,decode,dataset,step,ct
class SolarisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.lib=load()
    def test_binary_roundtrip(self):
        rows=dataset(77,32)
        self.assertEqual([(tuple(x),y) for x,y in rows],decode(encode(rows),32))
    def test_caps(self):
        for busy,b in ((.9,8),(.5,16),(.3,24),(.1,32)):
            self.assertEqual(self.lib.solar_target(busy,1000000,3800000,0),b)
        self.assertEqual(self.lib.solar_target(.9,650000,3800000,0),8)
    def test_invalid_init(self):
        self.assertFalse(self.lib.solar_new((ct.c_double*4)(-1,0,0,0)))
    def test_native(self):
        s=self.lib.solar_new((ct.c_double*4)(1,1,1,1))
        if not s:self.skipTest("environment safety preflight failed")
        try:
            rows=dataset(89,64);data=encode(rows)
            r=step(self.lib,s,data,64,0)
            self.assertEqual(r["terms"],2048)
            for _ in range(4):
                r=step(self.lib,s,data,64,3)
                self.assertEqual(r["over"],0)
                self.assertLessEqual(r["terms"],64*r["budget"])
            with self.assertRaises(RuntimeError):step(self.lib,s,data[:-1],64,3)
        finally:self.lib.solar_free(s)
if __name__=="__main__":unittest.main()
