import itertools
import random
import unittest
import metis as m

class MetisTests(unittest.TestCase):
    def test_exact_and_masked_optimum(self):
        for n in range(1,9):
            p=[random.Random(17*n+i).randint(-3,3) for i in range(n)]
            for b in m.BUDGETS:
                for k in range(n*(b-4)//28+1):
                    for mask in ([True]*n,[i%2==0 for i in range(n)]):
                        feasible=[s for count in range(k+1) for s in itertools.combinations(range(n),count)
                            if all(mask[j] for j in s) and all(sum(j<i for j in s)<=i*(b-4)//28 for i in range(1,n+1))]
                        got=m.select(p,b,k,mask)
                        self.assertEqual((len(got),sum(p[i] for i in got)),max((len(s),sum(p[i] for i in s)) for s in feasible))
    def test_ties_and_cap(self):
        self.assertEqual(m.select([0.]*8,16),{2,4,6})
        self.assertEqual(m.select([0.]*8,16,1),{2})
        self.assertEqual(m.select([1.]*8,16,allowed=[False]*8),set())
    def test_gate_fallback(self):
        rows=[([0.]*32,1) for _ in range(64)]
        model=m.fit(rows)
        self.assertTrue(all(v["policy"]=="margin" for v in m.gate(model,[rows]*4).values()))
    def test_reversal_cheap_inputs(self):
        a=m.data(77,64,"heteroskedastic");b=m.data(77,64,"reversed")
        self.assertEqual([x[:4] for x,y in a],[x[:4] for x,y in b])
        self.assertNotEqual([x[4:] for x,y in a],[x[4:] for x,y in b])
    def test_batch_invariants(self):
        model=m.fit(m.data(44,128,"heteroskedastic"))
        gates={b:{"policy":"benefit_context"} for b in m.BUDGETS}
        v=m.test_batch(m.data(45,64,"reversed"),model,gates,random.Random(46))
        for b in m.BUDGETS:
            a=v["regimes"][str(b)]
            self.assertTrue(all(r["over"]==0 for r in a.values()))
            self.assertEqual(a["risk_context"]["terms"],a["margin_matched"]["terms"])
            self.assertEqual(a["risk_context"]["terms"],a["oracle_matched"]["terms"])
    def test_invalid(self):
        with self.assertRaises(ValueError):m.select([float("nan")],16)
        with self.assertRaises(ValueError):m.select([1.],16,1)
if __name__=="__main__":unittest.main()
