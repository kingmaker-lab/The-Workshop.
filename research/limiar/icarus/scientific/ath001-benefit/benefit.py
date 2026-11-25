"""ATH-001 BENEFIT-01: exploratory offline selection study, stdlib only."""
import argparse
import bisect
import hashlib
import heapq
import json
import math
import platform
import random
import resource
import statistics
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
EXPS=HERE.parent.parent/"experiments"
sys.path.insert(0,str(EXPS/"exp002-feather"))
sys.path.insert(0,str(EXPS/"exp005-helios"))
import feather
from prometheus import sensor_paths,safety_snapshot
BUDGETS=(8,16,24,32)
SCENARIOS=("iid","heteroskedastic")
MODES=("full","lite","margin","benefit_margin","benefit_context","random","oracle")
EDGES=(.25,.5,1.,1.5,2.,3.,4.)
SEEDS=tuple(range(2101,2121,2))
N=64
BATCHES=24
CAL=2048

def data(seed,n,scenario):
    if scenario=="iid":
        return feather.dataset(seed,n)
    if scenario!="heteroskedastic":
        raise ValueError("unknown scenario")
    rng=random.Random(seed)
    rows=[]
    for _ in range(n):
        cheap=[rng.gauss(0,1) for _ in range(4)]
        # Same score model as FEATHER; expensive features' variance depends
        # on the observable sign of x[0]. No label leakage in selector.
        scale=2.0 if cheap[0]>=0 else .35
        x=cheap+[rng.gauss(0,scale) for _ in range(28)]
        y=int(sum(a*b for a,b in zip(x,feather.WEIGHTS))+rng.gauss(0,.35)>=0)
        rows.append((x,y))
    return rows

def observe_cheap(x):
    return (abs(sum(x[:4])),int(x[0]>=0))

def outcomes(x,y):
    score=sum(x[:4])
    full=score+sum(v*.15 for v in x[4:])
    a=int(int(score>=0)==y)
    b=int(int(full>=0)==y)
    return a,b,b-a

def bin_id(m):
    return bisect.bisect_right(EDGES,m)

def fit(rows):
    # Calibration only. Fixed bins and shrinkage; no tuning on test.
    pools=[[0,0] for _ in range(len(EDGES)+1)]
    groups=[[[0,0] for _ in range(2)] for _ in pools]
    for x,y in rows:
        m,c=observe_cheap(x);j=bin_id(m);g=outcomes(x,y)[2]
        pools[j][0]+=g;pools[j][1]+=1
        groups[j][c][0]+=g;groups[j][c][1]+=1
    pooled=[s/(n+16) for s,n in pools]
    contextual=[[(s+32*pooled[j])/(n+32) for s,n in row] for j,row in enumerate(groups)]
    return {"pooled":pooled,"contextual":contextual,"counts":[[v[1] for v in row] for row in groups]}

def select(priorities,budget):
    # Larger priority = better. Ties prefer smaller index.
    if budget not in BUDGETS or not priorities or len(priorities)>256:
        raise ValueError("invalid budget or batch")
    heap=[]
    for i,p in enumerate(priorities):
        if not math.isfinite(p):raise ValueError("nonfinite priority")
        heapq.heappush(heap,(p,-i))
        q=(i+1)*(budget-4)//28
        if len(heap)>q:heapq.heappop(heap)
    return {-i for p,i in heap}

def evaluate(selected,out,budget):
    n=len(out);terms=correct=helped=harmed=0;over=0
    for i,(lite,full,g) in enumerate(out):
        expand=i in selected
        terms+=32 if expand else 4
        correct+=full if expand else lite
        helped+=int(expand and g==1)
        harmed+=int(expand and g==-1)
        over=max(over,terms-(i+1)*budget)
    return {"correct":correct,"terms":terms,"expanded":len(selected),
            "helped":helped,"harmed":harmed,"over":over}

def experiment(seed,scenario,paths):
    scenario_id=SCENARIOS.index(scenario)
    namespace=710000000+seed*100000+scenario_id*10000
    safety_snapshot(paths)
    calibration=data(namespace,CAL,scenario)
    model=fit(calibration)
    del calibration
    events=[]
    for i in range(BATCHES):
        time.sleep(.05)
        safe=safety_snapshot(paths)
        rows=data(namespace+i+1,N,scenario)
        cheap=[observe_cheap(x) for x,y in rows]
        out=[outcomes(x,y) for x,y in rows]
        digest=hashlib.sha256()
        for x,y in rows:
            digest.update(struct.pack("<32dB",*x,y))
        rng=random.Random(namespace+5000+i)
        pri={"margin":[-m for m,c in cheap],
             "benefit_margin":[model["pooled"][bin_id(m)] for m,c in cheap],
             "benefit_context":[model["contextual"][bin_id(m)][c] for m,c in cheap],
             "random":[rng.random() for _ in cheap],
             "oracle":[g for a,b,g in out]}
        record={"batch":i,"sha256":digest.hexdigest(),
                "possible_corrections":sum(g==1 for a,b,g in out),
                "possible_harms":sum(g==-1 for a,b,g in out),
                "full":evaluate(set(range(N)),out,32),"lite":evaluate(set(),out,4),"regimes":{}}
        for b in BUDGETS:
            results={}
            for name,p in pri.items():
                results[name]=evaluate(select(p,b),out,b)
            expected=4*N+28*(N*(b-4)//28)
            if any(v["terms"]!=expected or v["over"] for v in results.values()):
                raise RuntimeError("matched quota invariant failed")
            if any(v["correct"]>results["oracle"]["correct"] for v in results.values()):
                raise RuntimeError("oracle invariant failed")
            if b==32 and any(v["correct"]!=record["full"]["correct"] for v in results.values()):
                raise RuntimeError("FULL parity failed")
            record["regimes"][str(b)]=results
        events.append(record)
    return {"seed":seed,"scenario":scenario,"calibration_seed":namespace,"model":model,"events":events}

def summarize(runs):
    result={}
    for scenario in SCENARIOS:
        rr=[r for r in runs if r["scenario"]==scenario]
        ev=[e for r in rr for e in r["events"]];total=N*len(ev)
        result[scenario]={"samples":total,"regimes":{}}
        full=sum(e["full"]["correct"] for e in ev)
        lite=sum(e["lite"]["correct"] for e in ev)
        for b in BUDGETS:
            arm={}
            for m in MODES:
                def get(e):return e[m] if m in ("full","lite") else e["regimes"][str(b)][m]
                vals=[get(e) for e in ev];correct=sum(v["correct"] for v in vals)
                arm[m]={"correct":correct,"accuracy":correct/total,"loss_pp_vs_full":100*(full-correct)/total,
                        "mean_terms":sum(v["terms"] for v in vals)/total,
                        "helped":sum(v["helped"] for v in vals),"harmed":sum(v["harmed"] for v in vals),
                        "net_gain_vs_lite":correct-lite,
                        "max_prefix_overrun":max(v["over"] for v in vals)}
            for m in ("benefit_margin","benefit_context","random","oracle"):
                differences=[100*sum(e["regimes"][str(b)][m]["correct"]-e["regimes"][str(b)]["margin"]["correct"] for e in r["events"])/(N*len(r["events"])) for r in rr]
                arm[m]["paired_gain_pp_vs_margin"]=statistics.mean(differences)
                arm[m]["seed_gain_pp"]=differences
                arm[m]["seed_gain_sd_pp"]=statistics.stdev(differences) if len(differences)>1 else None
            result[scenario]["regimes"][str(b)]=arm
        result[scenario]["possible_corrections"]=sum(e["possible_corrections"] for e in ev)
        result[scenario]["possible_harms"]=sum(e["possible_harms"] for e in ev)
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--smoke",action="store_true")
    a=p.parse_args()
    paths=sensor_paths();safety_snapshot(paths)
    runs=[]
    for seed in ((2099,) if a.smoke else SEEDS):
        for scenario in SCENARIOS:
            runs.append(experiment(seed,scenario,paths))
            print(f"ATH-001 seed={seed} scenario={scenario} complete",file=sys.stderr,flush=True)
    rev=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True,check=True).stdout.strip()
    print(json.dumps({"experiment":"ATH-001-BENEFIT-01","schema_version":1,"revision":rev,
        "exploratory":True,"smoke":a.smoke,"data":"synthetic","batch_size":N,
        "batches_per_seed":BATCHES,"calibration_samples":CAL,"margin_edges":EDGES,
        "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "runs":runs,"summary":summarize(runs)},indent=2,allow_nan=False))
if __name__=="__main__":main()
