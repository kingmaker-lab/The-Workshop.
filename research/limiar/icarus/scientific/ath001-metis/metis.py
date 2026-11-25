"""ATH-001 BENEFIT-02 METIS: prospective exploratory study, no runtime claim."""
import argparse
import hashlib
import heapq
import json
import math
import platform
import random
import resource
import statistics as st
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath001-benefit"))
import benefit as b1

N=64
FIT_N=2048
GATE_BATCHES=32
TEST_BATCHES=24
BUDGETS=b1.BUDGETS
SEEDS=tuple(range(2201,2221,2))
SCENARIOS={
    "iid_stable":("iid","iid"),
    "context_stable":("heteroskedastic","heteroskedastic"),
    "context_disappears":("heteroskedastic","iid"),
    "context_reverses":("heteroskedastic","reversed"),
    "context_emerges":("iid","heteroskedastic"),
}
FIXED=("margin","benefit_margin","benefit_context","metis","random","oracle")
VARIABLE=("risk_context","margin_matched","context_matched","oracle_matched","oracle_variable")
MIN_GAIN=.02
MAX_HARM=.10
GATE_PP=.25

def data(seed,n,scenario):
    if scenario!="reversed":
        return b1.data(seed,n,scenario)
    rng=random.Random(seed)
    rows=[]
    for _ in range(n):
        cheap=[rng.gauss(0,1) for _ in range(4)]
        scale=.35 if cheap[0]>=0 else 2.
        x=cheap+[rng.gauss(0,scale) for _ in range(28)]
        y=int(sum(a*w for a,w in zip(x,b1.feather.WEIGHTS))+rng.gauss(0,.35)>=0)
        rows.append((x,y))
    return rows

def fit(rows):
    model=b1.fit(rows)
    pooled=[[0,0] for _ in b1.EDGES+(0.,)]
    groups=[[[0,0],[0,0]] for _ in pooled]
    for x,y in rows:
        m,c=b1.observe_cheap(x);j=b1.bin_id(m)
        h=int(b1.outcomes(x,y)[2]==-1)
        pooled[j][0]+=h;pooled[j][1]+=1
        groups[j][c][0]+=h;groups[j][c][1]+=1
    # Smoothed estimated harmful-expansion probability, not a risk bound.
    p=[(h+1)/(n+16) for h,n in pooled]
    model["harm"]=[[(h+32*p[j])/(n+32) for h,n in row] for j,row in enumerate(groups)]
    return model

def priorities(features,model):
    cheap=[b1.observe_cheap(x) for x in features]
    return {
        "margin":[-m for m,c in cheap],
        "benefit_margin":[model["pooled"][b1.bin_id(m)] for m,c in cheap],
        "benefit_context":[model["contextual"][b1.bin_id(m)][c] for m,c in cheap],
        "harm":[model["harm"][b1.bin_id(m)][c] for m,c in cheap],
    }

def select(p,b,cap=None,allowed=None):
    if b not in BUDGETS or not 1<=len(p)<=256 or any(not math.isfinite(v) for v in p):
        raise ValueError("invalid priorities/budget")
    maxcap=len(p)*(b-4)//28
    if cap is None:cap=maxcap
    if not isinstance(cap,int) or not 0<=cap<=maxcap:raise ValueError("invalid cap")
    if allowed is not None and len(allowed)!=len(p):raise ValueError("invalid mask")
    heap=[]
    for i,v in enumerate(p):
        if allowed is None or allowed[i]:
            heapq.heappush(heap,(v,-i))
        quota=min(cap,(i+1)*(b-4)//28)
        if len(heap)>quota:heapq.heappop(heap)
    return {-i for _,i in heap}

def gate(model,batches):
    # Fit is already frozen. Gate uses only the separate validation split.
    # Two halves must show positive gain and pooled mean >=0.25 pp.
    deltas={b:[] for b in BUDGETS}
    for rows in batches:
        p=priorities([x[:4] for x,y in rows],model)
        out=[b1.outcomes(x,y) for x,y in rows]
        for b in BUDGETS:
            c=b1.evaluate(select(p["benefit_context"],b),out,b)["correct"]
            m=b1.evaluate(select(p["margin"],b),out,b)["correct"]
            deltas[b].append(100*(c-m)/len(rows))
    ans={}
    for b,d in deltas.items():
        mid=len(d)//2
        halves=[st.mean(d[:mid]),st.mean(d[mid:])]
        mean=st.mean(d)
        ans[b]={"policy":"benefit_context" if mean>=GATE_PP and min(halves)>0 else "margin",
                "mean_gain_pp":mean,"halves_pp":halves,"batch_gain_pp":d}
    return ans

def test_batch(rows,model,decisions,rng):
    n=len(rows)
    p=priorities([x[:4] for x,y in rows],model)
    p["random"]=[rng.random() for _ in rows]
    # All deployable selections are computed before accessing held-out labels.
    selected={}
    for b in BUDGETS:
        a={m:select(p[m],b) for m in ("margin","benefit_margin","benefit_context","random")}
        a["metis"]=a[decisions[b]["policy"]]
        allowed=[g>=MIN_GAIN and h<=MAX_HARM for g,h in zip(p["benefit_context"],p["harm"])]
        a["risk_context"]=select(p["benefit_context"],b,allowed=allowed)
        k=len(a["risk_context"])
        a["margin_matched"]=select(p["margin"],b,cap=k)
        a["context_matched"]=select(p["benefit_context"],b,cap=k)
        selected[b]=a
    out=[b1.outcomes(x,y) for x,y in rows]
    gains=[g for _,_,g in out]
    full=b1.evaluate(set(range(n)),out,32)
    lite=b1.evaluate(set(),out,4)
    digest=hashlib.sha256()
    for x,y in rows:digest.update(struct.pack("<32dB",*x,y))
    result={"sha256":digest.hexdigest(),"full":full,"lite":lite,"regimes":{}}
    for b,a in selected.items():
        a["oracle"]=select(gains,b)
        a["oracle_matched"]=select(gains,b,cap=len(a["risk_context"]))
        a["oracle_variable"]=select(gains,b,allowed=[g>0 for g in gains])
        v={m:b1.evaluate(s,out,b) for m,s in a.items()}
        k=n*(b-4)//28
        if any(v[m]["expanded"]!=k for m in FIXED):raise RuntimeError("fixed quota")
        if any(v[m]["expanded"]!=v["risk_context"]["expanded"] for m in ("margin_matched","context_matched","oracle_matched")):raise RuntimeError("matched quota")
        if any(r["over"] or r["terms"]!=4*n+28*r["expanded"] or r["correct"]!=lite["correct"]+r["helped"]-r["harmed"] for r in v.values()):raise RuntimeError("budget/correctness invariant")
        if any(v[m]["correct"]>v["oracle"]["correct"] for m in FIXED):raise RuntimeError("fixed oracle invariant")
        if any(v[m]["correct"]>v["oracle_matched"]["correct"] for m in ("risk_context","margin_matched","context_matched")):raise RuntimeError("matched oracle invariant")
        if any(r["correct"]>v["oracle_variable"]["correct"] for r in v.values()):raise RuntimeError("variable oracle invariant")
        if b==32 and any(v[m]["correct"]!=full["correct"] for m in FIXED):raise RuntimeError("full parity")
        result["regimes"][str(b)]=v
    return result

def experiment(seed,scenario,paths):
    src,dst=SCENARIOS[scenario]
    root=810000000+seed*100000+list(SCENARIOS).index(scenario)*10000
    b1.safety_snapshot(paths)
    model=fit(data(root,FIT_N,src))
    def validation():
        for i in range(GATE_BATCHES):
            b1.safety_snapshot(paths)
            yield data(root+1+i,N,src)
    decisions=gate(model,validation())
    events=[]
    for i in range(TEST_BATCHES):
        time.sleep(.05)
        b1.safety_snapshot(paths)
        rows=data(root+100+i,N,dst)
        event=test_batch(rows,model,decisions,random.Random(root+1000+i))
        events.append({"batch":i,**event})
    return {"seed":seed,"scenario":scenario,"source":src,"target":dst,
            "fit_seed":root,"gate_seeds":[root+1+i for i in range(GATE_BATCHES)],
            "test_seeds":[root+100+i for i in range(TEST_BATCHES)],
            "model":model,"gate":decisions,"events":events}

def summarize(runs):
    result={}
    for scenario in SCENARIOS:
        rr=[r for r in runs if r["scenario"]==scenario]
        ev=[e for r in rr for e in r["events"]];total=N*len(ev)
        full=sum(e["full"]["correct"] for e in ev)
        lite=sum(e["lite"]["correct"] for e in ev)
        summary={"samples":total,"full_accuracy":full/total,"lite_accuracy":lite/total,"regimes":{}}
        for b in BUDGETS:
            key=str(b)
            arm={}
            for m in FIXED+VARIABLE:
                vals=[e["regimes"][key][m] for e in ev]
                c=sum(v["correct"] for v in vals)
                # All fixed arms versus original margin; risk vs matched margin additionally.
                ref="margin_matched" if m in VARIABLE[:-1] else "margin"
                deltas=[100*sum(e["regimes"][key][m]["correct"]-e["regimes"][key][ref]["correct"] for e in r["events"])/(N*len(r["events"])) for r in rr]
                arm[m]={"correct":c,"accuracy":c/total,"loss_pp_vs_full":100*(full-c)/total,
                        "mean_terms":sum(v["terms"] for v in vals)/total,
                        "expanded":sum(v["expanded"] for v in vals),
                        "helped":sum(v["helped"] for v in vals),"harmed":sum(v["harmed"] for v in vals),
                        "max_prefix_overrun":max(v["over"] for v in vals),
                        "paired_reference":ref,"paired_gain_pp":st.mean(deltas),
                        "seed_gain_pp":deltas,"seed_gain_sd_pp":st.stdev(deltas) if len(deltas)>1 else None}
            summary["regimes"][key]={"context_gate_count":sum(r["gate"][b]["policy"]=="benefit_context" for r in rr),"arms":arm}
        result[scenario]=summary
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("--smoke",action="store_true");a=p.parse_args()
    paths=b1.sensor_paths();b1.safety_snapshot(paths)
    runs=[]
    for seed in ((2199,) if a.smoke else SEEDS):
        for scenario in SCENARIOS:
            runs.append(experiment(seed,scenario,paths))
            print(f"METIS seed={seed} scenario={scenario} complete",file=sys.stderr,flush=True)
    rev=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True,check=True).stdout.strip()
    dirty=subprocess.run(["git","status","--porcelain","--untracked-files=no"],cwd=HERE,capture_output=True,text=True,check=True).stdout.strip()
    print(json.dumps({"experiment":"ATH-001-BENEFIT-02-METIS","schema_version":1,"revision":rev,
        "tracked_tree_dirty":bool(dirty),"exploratory":True,"smoke":a.smoke,"data":"synthetic",
        "batch_size":N,"fit_n":FIT_N,"gate_batches":GATE_BATCHES,"test_batches":TEST_BATCHES,
        "gate_min_pp":GATE_PP,"risk_min_gain":MIN_GAIN,"risk_max_estimated_harm":MAX_HARM,
        "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "runs":runs,"summary":summarize(runs)},indent=2,allow_nan=False))
if __name__=="__main__":main()
