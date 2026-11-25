import unittest
from unittest.mock import patch
from prometheus import BudgetPolicy,target_budget,safety_snapshot,FastObserver
class PrometheusTests(unittest.TestCase):
    def test_caps(self):
        o={"cpu_busy":.8,"mem_available_kib":650000,"mem_total_kib":3834768,"memory_psi_avg10":0}
        self.assertEqual(target_budget(o),8)
        o["cpu_busy"]=.1
        self.assertEqual(target_budget(o),16)
        o["memory_psi_avg10"]=6
        self.assertEqual(target_budget(o),8)
    def test_hysteresis(self):
        p=BudgetPolicy()
        self.assertEqual(p.update(32,True),8)
        self.assertEqual(p.update(32,False),8)
        self.assertEqual(p.update(32,True),16)
        self.assertEqual(p.update(8,False),8)
    def test_guard(self):
        with patch("prometheus.memory",return_value={"MemAvailable":450000,"MemTotal":3834768}),patch("prometheus.cached_temperature",return_value=70):
            with self.assertRaises(RuntimeError):safety_snapshot(())
    def test_temperature_guard(self):
        with patch("prometheus.memory",return_value={"MemAvailable":800000,"MemTotal":3834768}),patch("prometheus.cached_temperature",return_value=80):
            with self.assertRaises(RuntimeError):safety_snapshot(())
    def test_missing_known_sensor(self):
        with patch("prometheus.memory",return_value={"MemAvailable":800000,"MemTotal":3834768}),patch("prometheus.cached_temperature",return_value=None):
            with self.assertRaises(RuntimeError):safety_snapshot(("known",))
if __name__=="__main__":unittest.main()
