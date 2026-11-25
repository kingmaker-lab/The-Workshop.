"""Bounded deterministic checks of existing implementations and mathematical claims."""
import ctypes as C
from fractions import Fraction as F
import itertools as it
import json
import math
import random
import resource
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath001-themis"))
import themis as t
a=t.a;m=t.m
BUDGETS=(8,16,24,32)
def feasible(s,n,b,cap):
    return len(s)<=cap and all(sum(j<i for j in s)<=i*(b-4)//28 for i in range(1,n+1))
def subsets(n):
    return [frozenset(s) for k in range(n+1) for s in it.combinations(range(n),k)]
def optimum(fs,p):
    # priority max, ties favor earlier index (lexicographic sorted tuple)
    return min(fs,key=lambda s:(-len(s),-sum(p[i] for i in s),tuple(sorted(s))))
def native():
    lib=C.CDLL(str(HERE/"libeuclid.so"))
    fn=lib.euclid_mask;fn.argtypes=[C.POINTER(C.c_double),C.c_size_t,C.c_int,C.c_int,C.POINTER(C.c_uint8)];fn.restype=C.c_int
    def mask(w,b,cap):
        n=len(w);out=(C.c_uint8*n)()
        rc=fn((C.c_double*n)(*w),n,b,cap,out)
        if rc:raise RuntimeError(f"native probe {rc}")
        return frozenset(i for i,v in enumerate(out) if v)
    return mask
def main():
    paths=a.b1.sensor_paths();a.safety_snapshot(paths)
    mask=native()
    counts={"enumerated_selector":0,"native_exact":0,"masked":0,"contraction":0,"native_large":0,"ht_exact":0,"ht_variance":0,"audit_feasibility":0}
    for n in range(1,9):
        a.safety_snapshot(paths);ss=subsets(n)
        for b in BUDGETS:
            for cap in range(n*(b-4)//28+1):
                fs=[s for s in ss if feasible(s,n,b,cap)]
                for w in ([0]*n,[i%3 for i in range(n)],list(reversed(range(n))),[random.Random(n*100+i).randrange(5) for i in range(n)]):
                    p=[-v for v in w];want=optimum(fs,p)
                    assert m.select(p,b,cap)==want
                    counts["enumerated_selector"]+=1
                    assert mask(w,b,cap)==want
                    counts["native_exact"]+=1
                    allowed=[i%2==0 for i in range(n)]
                    assert m.select(p,b,cap,allowed)==optimum([s for s in fs if all(allowed[i] for i in s)],p)
                    counts["masked"]+=1
                if b==16 and cap==n*12//28:
                    p=[(i*7)%5-2 for i in range(n)]
                    for audits in fs:
                        got=a.extend(p,set(audits))
                        assert got==optimum([s for s in fs if audits<=s],p)
                        counts["contraction"]+=1
    for n in (32,63,64,65,128,256):
        a.safety_snapshot(paths)
        for b in BUDGETS:
            w=[random.Random(n*100+i).randrange(11) for i in range(n)]
            k=n*(b-4)//28
            for cap in sorted({0,k//2,k}):
                assert mask(w,b,cap)==m.select([-v for v in w],b,cap)
                counts["native_large"]+=1
    # Exact expectations and variance, enumerate every possible one-draw outcome.
    for n in range(1,7):
        a.safety_snapshot(paths)
        for h in it.product((-1,0,1),repeat=n):
            d={i for i,v in enumerate(h) if v}
            if not d:continue
            # Include all nonzeros and optionally a zero in disagreement.
            for D in (d,d|{0}):
                pu=[F(1,n)]*n
                pt=[F(1,4*n)+(F(3,4*len(D)) if i in D else 0) for i in range(n)]
                assert sum(pt)==1
                var=[]
                for p in (pu,pt):
                    vals=[F(v)/q for v,q in zip(h,p)]
                    mean=sum(q*x for q,x in zip(p,vals))
                    assert mean==sum(h)
                    v=sum(q*(x-mean)**2 for q,x in zip(p,vals))
                    assert v==sum(F(x*x)/q for x,q in zip(h,p))-sum(h)**2
                    counts["ht_exact"]+=1;var.append(v)
                assert var[1]<=var[0];counts["ht_variance"]+=1
    for k,strata in ((2,((2,32),(32,64))),(4,((2,16),(16,32),(32,48),(48,64)))):
        for indices in it.product(*(range(lo,hi) for lo,hi in strata)):
            # All allowed audit combinations; prefix condition check at audit positions suffices.
            assert all(j+1<=(i+1)*12//28 for j,i in enumerate(indices))
            counts["audit_feasibility"]+=1
    # Compare actual estimator on nonzero synthetic draws.
    g=[0]*64;g[2]=1;g[32]=-1
    au={2:0.5,32:0.25}
    assert math.isclose(t.estimate(au,{2},{32},g),100/64*6)
    rev=subprocess.check_output(["git","rev-parse","HEAD"],cwd=HERE,text=True).strip()
    print(json.dumps({"experiment":"ATH-002-EUCLID-01","revision":rev,"checks":counts,"total":sum(counts.values()),"passed":True,"peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"scope":"bounded exhaustive and differential checks; not full formal verification"},indent=2))
if __name__=="__main__":
    if not __debug__:raise RuntimeError("assertions required; do not use -O")
    main()
