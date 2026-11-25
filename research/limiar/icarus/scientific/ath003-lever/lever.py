"""LEVER: last exploratory native engineering pilot. Standard library only."""
import argparse
import ctypes as C
import hashlib
import itertools
import json
import math
import os
import platform
import random
import resource
import statistics as st
import sys
import time
from pathlib import Path
import fcntl
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath003-archimedes"))
import arch
t=arch.t;a=arch.a
MODES=("full","lite","static","rank","causal","fast","margin_only","heap_only")
SCENARIOS=("iid","adverse")
def native():
    lib=C.CDLL(str(HERE/"liblever.so"));fn=lib.lever_run
    fn.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_uint8),C.c_size_t,C.c_int,C.c_int,C.c_int,C.c_double,C.POINTER(arch.Result),C.POINTER(C.c_uint8)]
    fn.restype=C.c_int
    def run(x,y,n,b,w,mode,threshold):
        out=arch.Result();mask=(C.c_uint8*n)()
        rc=fn(x,y,n,b,w,mode,threshold,C.byref(out),mask)
        if rc:raise RuntimeError(f"lever_run {rc}")
        return {k:getattr(out,k) for k,_ in arch.Result._fields_},tuple(mask)
    return run
def latent(rng,scenario):
    cheap=[rng.gauss(0,1) for _ in range(4)]
    # Stress margin ranking: larger tails on high-margin rows, tiny on low-margin.
    sigma=1. if scenario=="iid" else (.10 if abs(sum(cheap))<1. else 3.)
    tail=[rng.gauss(0,sigma) for _ in range(28)]
    label=int(sum(cheap)+.15*sum(tail)+rng.gauss(0,.35)>=0)
    return cheap,tail,label
def fixture(root,n,w,scenario):
    rng=random.Random(root);raw=random.Random(root+1)
    stride=4+28*w;x=(C.c_double*(n*stride))();y=(C.c_uint8*n)()
    cheap=[];full=[];latent_hash=hashlib.sha256()
    import struct
    for i in range(n):
        v,tail,label=latent(rng,scenario);off=i*stride
        latent_hash.update(struct.pack("<32dB",*v,*tail,label))
        for j,z in enumerate(v):x[off+j]=z
        actual=0.
        # Gaussian bridge: condition raw group sum on a fixed latent feature.
        # Identical latent scores and labels across W, floating roundoff only.
        for j,z in enumerate(tail):
            noise=[raw.gauss(0,1) for _ in range(w)]
            avg=sum(noise)/w;shift=z/math.sqrt(w)
            q=0.
            for h,val in enumerate(noise):
                v0=val-avg+shift;x[off+4+j*w+h]=v0;q+=v0
            actual+=.15*(q/math.sqrt(w))
        cheap.append(sum(v));full.append(sum(v)+actual);y[i]=label
    h=hashlib.sha256();h.update(memoryview(x).cast("B"));h.update(memoryview(y).cast("B"))
    return x,y,cheap,full,h.hexdigest(),latent_hash.hexdigest()
def causal_mask(cheap,b,th):
    n=len(cheap);k=n*(b-4)//28;count=0;out=[]
    for i,v in enumerate(cheap):
        q=(i+1)*(b-4)//28
        selected=int(count<q and (abs(v)<th or k-count==n-i))
        out.append(selected);count+=selected
    return tuple(out)
def calibrate(root,n,b,scenario):
    # Independent calibration: maximize correct among 9 prespecified thresholds.
    rng=random.Random(root);rows=[]
    for _ in range(16):
        batch=[latent(rng,scenario) for _ in range(n)]
        cheap=[sum(v) for v,_,_ in batch]
        full=[sum(v)+.15*sum(tail) for v,tail,_ in batch]
        rows.append((cheap,full,[y for _,_,y in batch]))
    candidates=(0.,.25,.5,.75,1.,1.5,2.,3.,8.)
    scores=[]
    for th in candidates:
        correct=0
        for c,f,y in rows:
            mask=causal_mask(c,b,th)
            correct+=sum(((f[i] if mask[i] else c[i])>=0)==y[i] for i in range(n))
        scores.append(correct)
    return candidates[max(range(len(scores)),key=lambda i:(scores[i],-i))],scores
def check(r,mask,y,c,f,n,b,w,mode,th):
    k=n*(b-4)//28
    if mode>=6:
        assert r["terms"]==r["raw_reads"]==4*n and r["over"]==r["correct"]==0
        assert r["expanded"]==sum(mask)==(k if mode==7 else 0)
        assert math.isclose(r["checksum"],sum(c),rel_tol=1e-12,abs_tol=1e-10)
        if mode==7:assert {i for i,v in enumerate(mask) if v}==a.m.select([-abs(v) for v in c],b)
        return
    arch.check(r,mask,y,c,f,n,b,w,0 if mode==0 else 1 if mode==1 else 3 if mode in (3,5) else 2)
    if mode==4:assert mask==causal_mask(c,b,th)
def group(run,key,budgets,reps,paths):
    seed,n,w,scenario=key
    root=seed*1000000+n*1000+SCENARIOS.index(scenario)*100
    a.safety_snapshot(paths)
    x,y,c,f,digest,latent_digest=fixture(root,n,w,scenario)
    events=[]
    for b in budgets:
        a.safety_snapshot(paths)
        th,scores=calibrate(root+50+b,n,b,scenario)
        rng=random.Random(root+w*100+b)
        order=list(range(len(MODES)));rng.shuffle(order);expected={}
        for mode in order:
            r,mask=run(x,y,n,b,w,mode,th);check(r,mask,y,c,f,n,b,w,mode,th);expected[mode]=(r,mask)
        assert expected[3][1]==expected[5][1]
        trials=[]
        for rep in range(reps):
            safe=a.safety_snapshot(paths);rng.shuffle(order);arms={}
            for mode in order:
                r,mask=run(x,y,n,b,w,mode,th);old,om=expected[mode]
                assert mask==om and all(r[k]==old[k] for k in r if k not in ("cpu_ns","wall_ns"))
                arms[MODES[mode]]=r
            trials.append({"rep":rep,"order":[MODES[i] for i in order],"safety":safe,"arms":arms})
            time.sleep(.02)
        events.append({"budget":b,"threshold":th,"calibration_correct":scores,"trials":trials})
    return {"key":list(key),"fixture_sha256":digest,"latent_sha256":latent_digest,"events":events}
def summarize(groups):
    cells={}
    for g in groups:
        seed,n,w,s=g["key"]
        for e in g["events"]:
            arms={}
            for m in MODES:
                v=[r["arms"][m] for r in e["trials"]]
                arms[m]={"cpu_ns":st.median(r["cpu_ns"] for r in v),"wall_ns":st.median(r["wall_ns"] for r in v),"correct":v[0]["correct"],"over":v[0]["over"]}
            cells.setdefault(f'{s}/{n}/{w}/{e["budget"]}',[]).append({"seed":seed,"arms":arms})
    result={}
    for key,v in cells.items():
        n=int(key.split("/")[1]);arms={}
        for m in MODES[:6]:
            arms[m]={"cpu_ratio_median":st.median(r["arms"][m]["cpu_ns"]/max(1,r["arms"]["full"]["cpu_ns"]) for r in v),
                     "loss_pp":100*sum(r["arms"]["full"]["correct"]-r["arms"][m]["correct"] for r in v)/(n*len(v))}
        result[key]={"arms":arms,"seed_results":v,"heap_increment_cpu_ns_median":st.median(r["arms"]["heap_only"]["cpu_ns"]-r["arms"]["margin_only"]["cpu_ns"] for r in v)}
    return result
def save(path,g):
    data=t.encode(g)
    t.atomic(path,lambda f:f.write(t.encode({"sha256":hashlib.sha256(data.encode()).hexdigest(),"group":g})))
def load(path,key):
    obj=json.loads(path.read_text());g=obj["group"]
    if g["key"]!=list(key) or hashlib.sha256(t.encode(g).encode()).hexdigest()!=obj["sha256"]:raise RuntimeError("checkpoint mismatch")
    return g
def main():
    p=argparse.ArgumentParser();p.add_argument("--smoke",action="store_true")
    p.add_argument("--session",required=True);p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if not __debug__ or t.git("status","--porcelain","--untracked-files=no"):raise RuntimeError("assertions and clean tracked revision required")
    seeds=(2599,) if args.smoke else (2601,2603,2605)
    sizes=(64,) if args.smoke else (64,256)
    works=(1,4,64) if args.smoke else (1,2,3,4,6,8,12,16,64)
    budgets=(16,32) if args.smoke else (16,24,32);reps=3 if args.smoke else 5
    paths=a.b1.sensor_paths();a.safety_snapshot(paths);run=native()
    config={"experiment":"ATH-003-ARCHIMEDES-02-LEVER","schema_version":1,"exploratory":True,"session":args.session,
            "smoke":args.smoke,"revision":t.git("rev-parse","HEAD"),"binary_sha256":hashlib.sha256((HERE/"liblever.so").read_bytes()).hexdigest(),
            "seeds":list(seeds),"sizes":list(sizes),"works":list(works),"budgets":list(budgets),"scenarios":list(SCENARIOS),"reps":reps,
            "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine(),"byteorder":sys.byteorder},
            "safety_min_available_kib":a.MIN_AVAILABLE_KIB,"safety_temperature_limit_c":a.TEMP_LIMIT}
    folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True);output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output must be outside checkpoint folder")
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=config:raise RuntimeError("checkpoint configuration mismatch")
        else:
            if list(folder.glob("group-*.json")):raise RuntimeError("orphan checkpoints")
            t.atomic(manifest,lambda f:f.write(t.encode(config)))
        files=[]
        for key in itertools.product(seeds,sizes,works,SCENARIOS):
            path=folder/("group-%d-%d-%d-%s.json"%key)
            if path.exists():load(path,key)
            else:save(path,group(run,key,budgets,reps,paths))
            files.append((path,key));print("LEVER",key,"checkpoint ready",file=sys.stderr,flush=True)
        summary=summarize(load(path,key) for path,key in files)
        def write(f):
            f.write(t.encode({**config,"process_peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"summary":summary})[:-1]+',"groups":[')
            for i,(path,key) in enumerate(files):
                if i:f.write(",")
                f.write(t.encode(load(path,key)))
            f.write("]}\n")
        t.atomic(output,write)
if __name__=="__main__":main()
