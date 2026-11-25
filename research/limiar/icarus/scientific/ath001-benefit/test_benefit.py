import itertools
import random
import unittest
from benefit import select,evaluate,fit,data,observe_cheap,outcomes,BUDGETS
class BenefitTest(unittest.TestCase):
    def test_exact_optimum(self):
        for n in range(1,9):
            p=[random.Random(i+n*100).randint(-2,2) for i in range(n)]
            for b in BUDGETS:
                k=n*(b-4)//28
                feasible=[s for s in itertools.combinations(range(n),k)
                    if all(sum(j<i for j in s)<=i*(b-4)//28 for i in range(1,n+1))]
                got=select(p,b)
                self.assertEqual(len(got),k)
                self.assertEqual(sum(p[i] for i in got),max(sum(p[i] for i in s) for s in feasible))
    def test_ties(self):
        self.assertEqual(select([0.]*8,16),{2,4,6})
    def test_calibration(self):
        m=fit(data(1,128,"iid"))
        self.assertEqual(sum(sum(r) for r in m["counts"]),128)
        self.assertEqual(len(m["pooled"]),8)
    def test_full_parity_and_cost(self):
        rows=data(9,64,"heteroskedastic")
        out=[outcomes(x,y) for x,y in rows]
        for b in BUDGETS:
            r=evaluate(select([-observe_cheap(x)[0] for x,y in rows],b),out,b)
            self.assertEqual(r["over"],0)
            self.assertEqual(r["terms"],256+28*(64*(b-4)//28))
            if b==32:self.assertEqual(r["correct"],sum(v[1] for v in out))
    def test_invalid(self):
        with self.assertRaises(ValueError):select([float("nan")],16)
        with self.assertRaises(ValueError):select([0.],12)
if __name__=="__main__":unittest.main()
