"""ARGOS: offline simulation of causal delayed audit feedback, stdlib only."""
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
sys.path.insert(0,str(HERE.parent/"ath001-metis"))
import metis as m
b1=m.b1
N=64
B=16
K=N*(B-4)//28
AUDITS=4
BATCHES=64
DELAY=4
WINDOW=8
SEEDS=tuple(range(2301,2321,2))
SCENARIOS=("stable_iid","stable_context","abrupt","gradual","recurring","no_feedback","emergence")
MODES=("margin","context","metis","audit_margin","audit_metis","argos","argos_refit")
def source(s):return "iid" if s in ("stable_iid","emergence") else "heteroskedastic"
def mixture(s,t):
    # probability of reversed context; source is context except IID arms.
    if s=="gradual":return min(1.,max(0.,(t-16)/24))
    if s=="recurring":return float(16<=t<32 or t>=48)
    return float(s in ("abrupt","no_feedback") and t>=24)
def stream(seed,s,t):
    if s=="stable_iid" or (s=="emergence" and t<24):return m.data(seed,N,"iid")
    p=mixture(s,t)
    rng=random.Random(seed);rows=[]
    for _ in range(N):
        cheap=[rng.gauss(0,1) for _ in range(4)]
        rev=rng.random()<p
        scale=2. if (cheap[0]>=0)!=rev else .35
        x=cheap+[rng.gauss(0,scale) for _ in range(28)]
        y=int(sum(a*w for a,w in zip(x,b1.feather.WEIGHTS))+rng.gauss(0,.35)>=0)
        rows.append((x,y))
    return rows

def audit_indices(rng):
    # Uniform within 4 strata; first 2 positions have zero inclusion probability
    # but cannot be expanded by ANY feasible selector at B=16.
    return {rng.randrange(lo,hi) for lo,hi in ((2,16),(16,32),(32,48),(48,64))}
def extend(p,a):
    # Contract fixed audit set: residual nested quotas tightened by suffix min.
    n=len(p);q=[(i+1)*(B-4)//28 for i in range(n)]
    count=0;res=[]
    for i in range(n):
        count+=i in a;res.append(q[i]-count)
    if min(res)<0:raise ValueError("infeasible audits")
    for i in range(n-2,-1,-1):res[i]=min(res[i],res[i+1])
    heap=[]
    for i,v in enumerate(p):
        if i not in a:heapq.heappush(heap,(v,-i))
        while len(heap)>res[i]:heapq.heappop(heap)
    return a|{-i for _,i in heap}
def contrast(record,model):
    # Horvitz-Thompson estimate of plain-policy accuracy difference per batch.
    # Candidate model must be independent of these validation labels.
    p=m.priorities(record["cheap"],model)
    c=m.select(p["benefit_context"],B);v=m.select(p["margin"],B)
    return 100/N*sum((int(i in c)-int(i in v))*g*(14 if i<16 else 16)
                     for i,x,y,g in record["audits"])
def policy(history,model,initial):
    if len(history)<WINDOW:return initial,None
    d=st.mean(contrast(r,model) for r in history[-WINDOW:])
    # Deliberately simple point-estimate monitor, not a sequential risk bound.
    return ("benefit_context" if d>=.25 else "margin"),d
def refit_policy(history,original,initial):
    # Older 16 delivered batches train; disjoint newer 8 validate. No future labels.
    if len(history)<24:return original,*policy(history,original,initial),False
    train=history[-24:-8];valid=history[-8:]
    model=m.fit([(x,y) for r in train for i,x,y,g in r["audits"]])
    choice,d=policy(valid,model,"margin")
    return model,choice,d,True
def experiment(seed,s,paths):
    root=910000000+seed*100000+SCENARIOS.index(s)*10000
    src=source(s)
    b1.safety_snapshot(paths)
    model=m.fit(m.data(root,2048,src))
    def validation():
        for i in range(32):
            b1.safety_snapshot(paths)
            yield m.data(root+1+i,N,src)
    initial=m.gate(model,validation())[B]["policy"]
    pending=[];history=[];events=[]
    refmodel=model;refchoice=initial;refscore=None;refitted=False
    for t in range(BATCHES):
        time.sleep(.05);b1.safety_snapshot(paths)
        delivered=[r for due,r in pending if due<=t]
        history.extend(delivered);pending=[(due,r) for due,r in pending if due>t]
        choice,score=policy(history,model,initial)
        if delivered and (not refitted or len(history)%8==0):
            refmodel,refchoice,refscore,refitted=refit_policy(history,model,initial)
        rows=stream(root+100+t,s,t)
        cheap=[x[:4] for x,y in rows]
        p=m.priorities(cheap,model);rp=m.priorities(cheap,refmodel)
        a=audit_indices(random.Random(root+1000+t))
        selected={"margin":m.select(p["margin"],B),
                  "context":m.select(p["benefit_context"],B),
                  "metis":m.select(p[initial],B),
                  "audit_margin":extend(p["margin"],a),
                  "audit_metis":extend(p[initial],a),
                  "argos":extend(p[choice],a),
                  "argos_refit":extend(rp[refchoice],a)}
        # Only now evaluate offline outcomes and construct delayed audited feedback.
        out=[b1.outcomes(x,y) for x,y in rows]
        full=b1.evaluate(set(range(N)),out,32);lite=b1.evaluate(set(),out,4)
        values={k:b1.evaluate(v,out,B) for k,v in selected.items()}
        for name,v in values.items():
            if v["over"] or v["expanded"]!=K or v["terms"]!=4*N+28*K:raise RuntimeError("quota")
            if name.startswith("audit_") or name.startswith("argos"):
                if not a<=selected[name]:raise RuntimeError("audit lost")
        r={"cheap":cheap,"audits":[(i,rows[i][0],rows[i][1],out[i][2]) for i in sorted(a)]}
        if s!="no_feedback":pending.append((t+DELAY,r))
        digest=hashlib.sha256()
        for x,y in rows:digest.update(struct.pack("<32dB",*x,y))
        # Store evaluation-only metadata; never passed to the controller.
        events.append({"batch":t,"sha256":digest.hexdigest(),"reverse_probability":mixture(s,t),
                       "feedback_delivered":len(delivered)*AUDITS,"feedback_total":len(history)*AUDITS,
                       "audit_indices":sorted(a),"audit_gains":[out[i][2] for i in sorted(a)],
                       "argos_policy":choice,"argos_score_pp":score,"refit_policy":refchoice,
                       "refit_score_pp":refscore,"refitted":refitted,"full":full,"lite":lite,"arms":values,
                       "audit_extra_expansions_vs_plain_metis":len(a-selected["metis"])})
    return {"seed":seed,"scenario":s,"initial_policy":initial,"fit_seed":root,"events":events}

def summarize(runs):
    result={}
    for s in SCENARIOS:
        rr=[r for r in runs if r["scenario"]==s]
        ev=[e for r in rr for e in r["events"]]
        phases={}
        for label,lo,hi in (("all",0,64),("pre",0,16),("mid",24,40),("late",48,64)):
            es=[e for e in ev if lo<=e["batch"]<hi];n=N*len(es)
            full=sum(e["full"]["correct"] for e in es)
            arms={}
            for name in MODES:
                v=[e["arms"][name] for e in es];c=sum(x["correct"] for x in v)
                ds=[100*sum(e["arms"][name]["correct"]-e["arms"]["metis"]["correct"] for e in r["events"] if lo<=e["batch"]<hi)/(N*(hi-lo)) for r in rr]
                arms[name]={"correct":c,"accuracy":c/n,"loss_pp_vs_full":100*(full-c)/n,
                            "mean_terms":sum(x["terms"] for x in v)/n,
                            "max_prefix_overrun":max(x["over"] for x in v),
                            "gain_pp_vs_metis":st.mean(ds),"seed_gain_pp":ds,
                            "seed_gain_sd_pp":st.stdev(ds) if len(ds)>1 else None,
                            "helped":sum(x["helped"] for x in v),"harmed":sum(x["harmed"] for x in v)}
            phases[label]={"samples":n,"full_accuracy":full/n,"arms":arms,
                           "argos_context_batches":sum(e["argos_policy"]=="benefit_context" for e in es),
                           "refit_context_batches":sum(e["refit_policy"]=="benefit_context" for e in es)}
        recovery=[]
        if s in ("abrupt","no_feedback","recurring"):
            onset=16 if s=="recurring" else 24
            end=32 if s=="recurring" else 64
            for r in rr:
                # First margin decision after onset; not necessarily sustained recovery.
                recovery.append(next((e["batch"]-onset for e in r["events"] if onset<=e["batch"]<end and e["argos_policy"]=="margin"),None))
        result[s]={"phases":phases,"initial_context_count":sum(r["initial_policy"]=="benefit_context" for r in rr),
                   "first_margin_delay_batches":recovery,
                   "audit_extra_expansions_vs_plain_metis":sum(e["audit_extra_expansions_vs_plain_metis"] for e in ev)}
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument("--smoke",action="store_true");a=p.parse_args()
    paths=b1.sensor_paths();b1.safety_snapshot(paths);runs=[]
    for seed in ((2299,) if a.smoke else SEEDS):
        for s in SCENARIOS:
            runs.append(experiment(seed,s,paths))
            print(f"ARGOS seed={seed} scenario={s} complete",file=sys.stderr,flush=True)
    def git(*args):return subprocess.run(["git",*args],cwd=HERE,capture_output=True,text=True,check=True).stdout.strip()
    print(json.dumps({"experiment":"ATH-001-BENEFIT-03-ARGOS","schema_version":1,"revision":git("rev-parse","HEAD"),
        "tracked_tree_dirty":bool(git("status","--porcelain","--untracked-files=no")),"exploratory":True,"smoke":a.smoke,
        "data":"synthetic","batch_size":N,"batches":BATCHES,"budget":B,"audits_per_batch":AUDITS,
        "feedback_delay_batches":DELAY,"monitor_window_batches":WINDOW,"fit_n":2048,"gate_batches":32,
        "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
        "process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"runs":runs,"summary":summarize(runs)},indent=2,allow_nan=False))
if __name__=="__main__":main()
