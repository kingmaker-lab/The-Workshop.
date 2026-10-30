import unittest
from round_analysis import analyze, round_core

class RoundAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.ddt, cls.lat = analyze()

    def test_round_core_is_permutation(self):
        self.assertEqual(len({round_core(x) for x in range(256)}),256)

    def test_ddt_row_sums(self):
        self.assertTrue(all(sum(row)==256 for row in self.ddt))

    def test_zero_difference_row(self):
        self.assertEqual(self.ddt[0][0],256)
        self.assertEqual(sum(self.ddt[0][1:]),0)

    def test_known_maxima(self):
        self.assertEqual(self.summary['ddt']['max_count_nonzero_input_difference'],64)
        self.assertEqual(self.summary['lat']['max_abs_walsh_nontrivial'],128)

    def test_nontrivial_lat_domain(self):
        self.assertEqual(self.summary['lat']['nontrivial_mask_pairs'],255*255)

    def test_round_key_invariance(self):
        checks=self.summary['fixed_round_key_invariance_checks']
        self.assertEqual(len(checks),3)
        self.assertTrue(all(v['ddt_counts_identical_by_input_translation'] and v['lat_absolute_walsh_identical_by_sign_factor'] for v in checks))

if __name__=='__main__':
    unittest.main()
