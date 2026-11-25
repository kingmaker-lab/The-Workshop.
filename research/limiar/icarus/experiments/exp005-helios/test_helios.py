import unittest
from helios import choose_budget,guard,percentile
class HeliosTests(unittest.TestCase):
    def obs(self,busy):
        return {"cpu_busy":busy,"mem_available_kib":2000000,"mem_total_kib":4000000,
                "memory_psi_avg10":0,"temperature_c":55}
    def test_budget(self):
        for busy,b in ((.1,32),(.3,24),(.5,16),(.8,8),(None,8)):
            self.assertEqual(choose_budget(self.obs(busy)),b)
    def test_memory(self):
        o=self.obs(.1);o["mem_available_kib"]=200000
        self.assertEqual(choose_budget(o),8)
        with self.assertRaises(RuntimeError):guard(o,False)
    def test_thermal(self):
        o=self.obs(.1);o["temperature_c"]=80
        with self.assertRaises(RuntimeError):guard(o,True)
        o["temperature_c"]=None
        with self.assertRaises(RuntimeError):guard(o,True)
        guard(o,False)
    def test_percentile(self):
        self.assertEqual(percentile(list(range(1,101)),.95),95)
if __name__=="__main__":unittest.main()
