"""THEMIS: low-memory exploratory delayed-audit policy simulation."""
import argparse
from collections import deque
import fcntl
import hashlib
import json
import math
import os
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
sys.path.insert(0,str(HERE.parent/"ath001-argos"))
import argos as a
m=a.m
b1=a.b1
N,B,K=a.N,a.B,a.K
SCENARIOS=a.SCENARIOS
SEEDS=tuple(range(2401,2421,2))
MODES=("margin","metis","audit_metis4","argos4","audit_metis2","themis_uniform2","themis_target2","themis_adaptive","audit_metis_adaptive","audit_metis_target2")
WINDOW=16
DELAY=4
EPS=.25
MIX=.25
MIN_NONZERO=4
def git(*args):
    return subprocess.run(["git",*args],cwd=HERE,capture_output=True,text=True,check=True).stdout.strip()
def sample(rng,diff,k,target):
    strata=((2,32),(32,64)) if k==2 else ((2,16),(16,32),(32,48),(48,64))
    result={}
    for lo,hi in strata:
        d=[i for i in range(lo,hi) if i in diff]
        exploit=target and bool(d)
        i=rng.choice(d) if exploit and rng.random()>=MIX else rng.randrange(lo,hi)
        prob=(MIX/(hi-lo)+(1-MIX)/len(d)*(i in diff)) if exploit else 1/(hi-lo)
        result[i]=prob
    return result
def estimate(audits,context,margin,gains):
    return 100/N*sum((int(i in context)-int(i in margin))*gains[i]/p for i,p in audits.items())
class Judge:
    def __init__(self,initial,old=False):
        self.initial=initial;self.choice=initial;self.old=old
        self.history=deque(maxlen=8 if old else WINDOW)
        self.pending=deque()
        self.mean=None;self.se=None;self.nonzero=0;self.delivered=0
    def observe(self,t):
        while self.pending and self.pending[0][0]<=t:
            _,value,count=self.pending.popleft()
            self.history.append(value);self.delivered+=count
        self.nonzero=sum(x!=0 for x in self.history)
        if len(self.history)<self.history.maxlen:return self.choice
        self.mean=st.mean(self.history)
        self.se=st.stdev(self.history)/math.sqrt(len(self.history))
        if self.old:
            self.choice="benefit_context" if self.mean>=EPS else "margin"
        elif self.nonzero>=MIN_NONZERO:
            # Heuristic deadband, not a confidence interval or sequential guarantee.
            if self.mean-self.se>EPS:self.choice="benefit_context"
            elif self.mean+self.se<-EPS:self.choice="margin"
        return self.choice
    def count(self):
        # Escalate only with prior delivered evidence and an ambiguous estimate.
        if self.mean is None:return 2
        return 4 if self.nonzero<MIN_NONZERO or abs(self.mean)<=EPS+self.se else 2
    def state(self):
        return {"policy":self.choice,"mean_pp":self.mean,"se_pp":self.se,"nonzero_batches":self.nonzero,"delivered":self.delivered}
def experiment(seed,scenario,paths):
    root=1010000000+seed*100000+SCENARIOS.index(scenario)*10000
    a.safety_snapshot(paths)
    model=m.fit(m.data(root,2048,a.source(scenario)))
    def validation():
        for i in range(32):
            a.safety_snapshot(paths)
            yield m.data(root+i+1,N,a.source(scenario))
    initial=m.gate(model,validation())[B]["policy"]
    judges={k:Judge(initial,k=="argos4") for k in ("argos4","themis_uniform2","themis_target2","themis_adaptive")}
    events=[]
    for t in range(a.BATCHES):
        time.sleep(.05);safe=a.safety_snapshot(paths)
        for j in judges.values():j.observe(t)
        rows=a.stream(root+100+t,scenario,t)
        p=m.priorities([x[:4] for x,y in rows],model)
        margin=m.select(p["margin"],B);context=m.select(p["benefit_context"],B)
        diff=margin^context
        audits={
            "argos4":sample(random.Random(root+1000+t),diff,4,False),
            "themis_uniform2":sample(random.Random(root+2000+t),diff,2,False),
            "themis_target2":sample(random.Random(root+3000+t),diff,2,True),
            "themis_adaptive":sample(random.Random(root+4000+t),diff,judges["themis_adaptive"].count(),True)}
        selected={"margin":margin,"metis":margin if initial=="margin" else context}
        controls={"argos4":"audit_metis4","themis_uniform2":"audit_metis2","themis_target2":"audit_metis_target2","themis_adaptive":"audit_metis_adaptive"}
        for name,au in audits.items():
            selected[name]=a.extend(p[judges[name].choice],set(au))
            selected[controls[name]]=a.extend(p[initial],set(au))
            if not set(au)<=selected[name] or not set(au)<=selected[controls[name]]:raise RuntimeError("audit lost")
        # All choices and inclusion probabilities frozen before outcomes.
        out=[b1.outcomes(x,y) for x,y in rows]
        gains=[v[2] for v in out]
        full=b1.evaluate(set(range(N)),out,32);lite=b1.evaluate(set(),out,4)
        arms={k:b1.evaluate(v,out,B) for k,v in selected.items()}
        if set(arms)!=set(MODES):raise RuntimeError("arm mismatch")
        for v in arms.values():
            if v["over"] or v["expanded"]!=K or v["terms"]!=4*N+28*K or v["correct"]!=lite["correct"]+v["helped"]-v["harmed"]:raise RuntimeError("invariant")
        records={}
        for name,au in audits.items():
            value=estimate(au,context,margin,gains)
            records[name]={"indices":sorted(au),"probabilities":[au[i] for i in sorted(au)],
                           "gains":[gains[i] for i in sorted(au)],"ht_pp":value,
                           "disagreement_audits":len(set(au)&diff),"displaced":len(set(au)-selected["metis"]),
                           **judges[name].state()}
            if scenario!="no_feedback":judges[name].pending.append((t+DELAY,value,len(au)))
        h=hashlib.sha256()
        for x,y in rows:h.update(struct.pack("<32dB",*x,y))
        events.append({"batch":t,"sha256":h.hexdigest(),"reverse_probability":a.mixture(scenario,t),"safety":safe,
                       "plain_context_correct":b1.evaluate(context,out,B)["correct"],"disagreement_count":len(diff),
                       "full":full,"lite":lite,"arms":arms,"audits":records})
    return {"seed":seed,"scenario":scenario,"initial_policy":initial,"fit_seed":root,"events":events}
def compact(run):
    result={}
    controls={"argos4":"audit_metis4","themis_uniform2":"audit_metis2","themis_target2":"audit_metis_target2","themis_adaptive":"audit_metis_adaptive"}
    for phase,lo,hi in (("all",0,64),("pre",0,16),("post24",24,64),("late",48,64)):
        es=run["events"][lo:hi];n=len(es)*N
        d={"samples":n,"full":sum(e["full"]["correct"] for e in es),"arms":{},"audits":{}}
        for k in MODES:
            v=[e["arms"][k] for e in es]
            d["arms"][k]={"correct":sum(x["correct"] for x in v),"terms":sum(x["terms"] for x in v),"over":max(x["over"] for x in v)}
        for k,ctrl in controls.items():
            v=[e["audits"][k] for e in es]
            d["audits"][k]={"count":sum(len(x["indices"]) for x in v),"disagreement":sum(x["disagreement_audits"] for x in v),
                            "displaced":sum(x["displaced"] for x in v),"context_batches":sum(x["policy"]=="benefit_context" for x in v),
                            "switches":sum(x["policy"]!=y["policy"] for x,y in zip(v,v[1:])),
                            "gain_vs_matched_pp":100*(d["arms"][k]["correct"]-d["arms"][ctrl]["correct"])/n}
        result[phase]=d
    return result
def aggregate(compacts):
    result={}
    for scenario in SCENARIOS:
        rr=[c for s,c in compacts if s==scenario]
        result[scenario]={}
        for phase in ("all","pre","post24","late"):
            ds=[c[phase] for c in rr];n=sum(x["samples"] for x in ds)
            full=sum(x["full"] for x in ds)
            out={"samples":n,"full_accuracy":full/n,"arms":{},"audits":{}}
            for k in MODES:
                c=sum(d["arms"][k]["correct"] for d in ds)
                out["arms"][k]={"correct":c,"accuracy":c/n,"loss_pp":100*(full-c)/n,"mean_terms":sum(d["arms"][k]["terms"] for d in ds)/n,"max_over":max(d["arms"][k]["over"] for d in ds),
                    "seed_gain_pp_vs_margin":[100*(d["arms"][k]["correct"]-d["arms"]["margin"]["correct"])/d["samples"] for d in ds]}
            for k in ds[0]["audits"]:
                out["audits"][k]={field:sum(d["audits"][k][field] for d in ds) for field in ("count","disagreement","displaced","context_batches","switches")}
                out["audits"][k]["seed_gain_vs_matched_pp"]=[d["audits"][k]["gain_vs_matched_pp"] for d in ds]
            result[scenario][phase]=out
    return result
def atomic(path,writer):
    tmp=path.with_name(path.name+".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        writer(f);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def encode(obj):return json.dumps(obj,sort_keys=True,separators=(",",":"),allow_nan=False)
def save(path,run):
    payload=encode(run)
    envelope={"sha256":hashlib.sha256(payload.encode()).hexdigest(),"run":run}
    atomic(path,lambda f:f.write(encode(envelope)))
def load(path,seed,scenario):
    obj=json.loads(path.read_text())
    run=obj["run"]
    if hashlib.sha256(encode(run).encode()).hexdigest()!=obj["sha256"]:raise RuntimeError("checkpoint checksum mismatch")
    if (run["seed"],run["scenario"])!=(seed,scenario) or [e["batch"] for e in run["events"]]!=list(range(a.BATCHES)):raise RuntimeError("checkpoint identity mismatch")
    return run
def main():
    p=argparse.ArgumentParser();p.add_argument("--smoke",action="store_true")
    p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if git("status","--porcelain","--untracked-files=no"):raise RuntimeError("tracked tree dirty: commit or revert changes first")
    paths=b1.sensor_paths()
    seeds=(2399,) if args.smoke else SEEDS
    config={"experiment":"ATH-001-BENEFIT-04-THEMIS","revision":git("rev-parse","HEAD"),"smoke":args.smoke,
            "exploratory":True,"schema_version":1,"data":"synthetic","seeds":list(seeds),"scenarios":list(SCENARIOS),
            "batch_size":N,"batches":a.BATCHES,"budget":B,"window":WINDOW,"delay":DELAY,"epsilon_pp":EPS,
            "min_nonzero":MIN_NONZERO,"uniform_mix":MIX,"safety_min_available_kib":a.MIN_AVAILABLE_KIB,
            "safety_temperature_limit_c":a.TEMP_LIMIT,"environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()}}
    folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True)
    output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output must be outside checkpoint directory")
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=config:raise RuntimeError("checkpoint revision/config mismatch")
        else:
            if list(folder.glob("run-*.json")):raise RuntimeError("orphan checkpoints")
            atomic(manifest,lambda f:f.write(encode(config)))
        keys=[(s,c,folder/f"run-{s}-{c}.json") for s in seeds for c in SCENARIOS]
        compacts=[]
        for seed,scenario,path in keys:
            if path.exists():
                run=load(path,seed,scenario)
                print(f"THEMIS {seed} {scenario} resumed",file=sys.stderr,flush=True)
            else:
                run=experiment(seed,scenario,paths);save(path,run)
                print(f"THEMIS {seed} {scenario} checkpoint saved",file=sys.stderr,flush=True)
            compacts.append((scenario,compact(run)));del run
        summary=aggregate(compacts)
        def write(f):
            f.write(encode({**config,"process_peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"summary":summary})[:-1]+',"runs":[')
            for i,(seed,scenario,path) in enumerate(keys):
                if i:f.write(",")
                f.write(encode(load(path,seed,scenario)))
            f.write("]}\n")
        atomic(output,write)
        print(f"THEMIS output {output}",file=sys.stderr,flush=True)
if __name__=="__main__":main()
