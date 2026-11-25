"""Bounded native break-even pilot; no Python data generation inside native timing."""
import argparse
import ctypes as C
import hashlib
import json
import math
import platform
import random
import resource
import statistics as st
import sys
import time
from pathlib import Path
import fcntl
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath001-themis"))
import themis as t
a=t.a
MODES=("full","lite","static","rank","random","global")
class Result(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ("cpu_ns","wall_ns","terms","raw_reads","over","correct","expanded")]+[("checksum",C.c_double)]
def native():
    lib=C.CDLL(str(HERE/"libarch.so"))
    fn=lib.arch_run
    fn.argtypes=[C.POINTER(C.c_double),C.POINTER(C.c_uint8),C.c_size_t,C.c_int,C.c_int,C.c_int,C.c_uint64,C.POINTER(Result),C.POINTER(C.c_uint8)]
    fn.restype=C.c_int
    def run(x,y,n,b,w,mode,seed):
        out=Result();mask=(C.c_uint8*n)()
        rc=fn(x,y,n,b,w,mode,seed,C.byref(out),mask)
        if rc:raise RuntimeError(f"arch_run {rc}")
        return {k:getattr(out,k) for k,_ in Result._fields_},tuple(mask)
    return run
def fixture(seed,n,w):
    rng=random.Random(seed)
    stride=4+28*w
    x=(C.c_double*(n*stride))();y=(C.c_uint8*n)()
    cheap=[];full=[]
    scale=1/math.sqrt(w)
    for i in range(n):
        offset=i*stride
        v=0.
        for j in range(4):
            z=rng.gauss(0,1);x[offset+j]=z;v+=z
        tail=0.
        for j in range(28):
            q=0.
            for z in range(w):
                val=rng.gauss(0,1);x[offset+4+j*w+z]=val;q+=val
            tail+=.15*(q*scale)
        cheap.append(v);full.append(v+tail)
        y[i]=int(v+tail+rng.gauss(0,.35)>=0)
    h=hashlib.sha256();h.update(memoryview(x).cast("B"));h.update(memoryview(y).cast("B"))
    return x,y,cheap,full,h.hexdigest()
def check(r,mask,y,cheap,full,n,b,w,mode):
    k=n*(b-4)//28
    wanted=n if mode==0 else 0 if mode==1 else k
    assert sum(mask)==r["expanded"]==wanted
    assert r["terms"]==4*n+28*wanted
    assert r["raw_reads"]==4*n+28*w*wanted
    scores=[full[i] if mask[i] else cheap[i] for i in range(n)]
    assert r["correct"]==sum((v>=0)==y[i] for i,v in enumerate(scores))
    assert math.isclose(r["checksum"],sum(scores),rel_tol=1e-12,abs_tol=1e-10)
    budget=32 if mode==0 else 4 if mode==1 else b
    count=0;over=0
    for i,v in enumerate(mask):
        count+=v;over=max(over,4*(i+1)+28*count-budget*(i+1))
    assert r["over"]==over and (mode==5 or over==0)
    if mode==3:
        expected=a.m.select([-abs(v) for v in cheap],b)
        assert {i for i,v in enumerate(mask) if v}==expected
def group(run,seed,n,w,budgets,reps,paths):
    a.safety_snapshot(paths)
    root=seed*1000000+n*1000+w
    x,y,cheap,full,digest=fixture(root,n,w)
    a.safety_snapshot(paths)
    events=[]
    for b in budgets:
        rnd=random.Random(root+b)
        random_seed=root+b
        # identical masks and outputs across repeats; randomized warmup and timed order.
        order=list(range(len(MODES)));rnd.shuffle(order)
        expected={}
        for mode in order:
            r,mask=run(x,y,n,b,w,mode,random_seed)
            check(r,mask,y,cheap,full,n,b,w,mode)
            expected[mode]=(r,mask)
        trials=[]
        for rep in range(reps):
            safety=a.safety_snapshot(paths)
            order=list(range(len(MODES)));rnd.shuffle(order)
            values={}
            for mode in order:
                r,mask=run(x,y,n,b,w,mode,random_seed)
                old,om=expected[mode]
                assert mask==om
                assert all(r[k]==old[k] for k in r if k not in ("cpu_ns","wall_ns"))
                values[MODES[mode]]=r
            trials.append({"rep":rep,"order":[MODES[i] for i in order],"safety":safety,"arms":values})
            time.sleep(.02)
        events.append({"budget":b,"trials":trials})
    return {"seed":seed,"n":n,"work":w,"fixture_sha256_native_endian":digest,"events":events}
def summarize(groups):
    cells={}
    for g in groups:
        for e in g["events"]:
            key=f'{g["n"]}/{g["work"]}/{e["budget"]}'
            cell=cells.setdefault(key,[])
            arms={}
            for mode in MODES:
                v=[q["arms"][mode] for q in e["trials"]]
                arms[mode]={"cpu_ns":st.median(x["cpu_ns"] for x in v),"wall_ns":st.median(x["wall_ns"] for x in v),
                            "correct":v[0]["correct"],"raw_reads":v[0]["raw_reads"],"terms":v[0]["terms"],"over":v[0]["over"]}
            cell.append({"seed":g["seed"],"arms":arms})
    return {k:{"seed_results":v,"rank_cpu_ratio_median":st.median(x["arms"]["rank"]["cpu_ns"]/max(1,x["arms"]["full"]["cpu_ns"]) for x in v),
               "rank_loss_pp":100*sum(x["arms"]["full"]["correct"]-x["arms"]["rank"]["correct"] for x in v)/(int(k.split("/")[0])*len(v))} for k,v in cells.items()}
def save(path,g):
    payload=t.encode(g);obj={"sha256":hashlib.sha256(payload.encode()).hexdigest(),"group":g}
    t.atomic(path,lambda f:f.write(t.encode(obj)))
def load(path,key):
    obj=json.loads(path.read_text());g=obj["group"]
    if (g["seed"],g["n"],g["work"])!=key or hashlib.sha256(t.encode(g).encode()).hexdigest()!=obj["sha256"]:
        raise RuntimeError("checkpoint mismatch")
    return g
def main():
    p=argparse.ArgumentParser();p.add_argument("--smoke",action="store_true")
    p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if not __debug__:raise RuntimeError("assertions required")
    if t.git("status","--porcelain","--untracked-files=no"):raise RuntimeError("tracked tree dirty")
    seeds=(2499,) if args.smoke else (2501,2503,2505)
    sizes=(64,) if args.smoke else (32,64,128,256)
    works=(1,16,256) if args.smoke else (1,4,16,64,256)
    budgets=(16,32) if args.smoke else (8,16,24,32)
    reps=3 if args.smoke else 7
    paths=a.b1.sensor_paths();a.safety_snapshot(paths)
    libpath=HERE/"libarch.so"
    config={"experiment":"ATH-003-ARCHIMEDES-01","schema_version":1,"exploratory":True,"smoke":args.smoke,"revision":t.git("rev-parse","HEAD"),
            "binary_sha256":hashlib.sha256(libpath.read_bytes()).hexdigest(),"seeds":list(seeds),"sizes":list(sizes),"works":list(works),"budgets":list(budgets),"reps":reps,
            "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine(),"byteorder":sys.byteorder},
            "safety_min_available_kib":a.MIN_AVAILABLE_KIB,"safety_temperature_limit_c":a.TEMP_LIMIT,
            "scope":"resident raw synthetic features, C CPU and wall timing, one invocation per measurement"}
    run=native();folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True)
    output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output must be outside checkpoint folder")
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=config:raise RuntimeError("checkpoint revision/binary/config mismatch")
        else:
            if list(folder.glob("group-*.json")):raise RuntimeError("orphan checkpoints")
            t.atomic(manifest,lambda f:f.write(t.encode(config)))
        keys=[(s,n,w) for s in seeds for n in sizes for w in works]
        files=[]
        for key in keys:
            path=folder/("group-%d-%d-%d.json"%key)
            if path.exists():load(path,key)
            else:save(path,group(run,*key,budgets,reps,paths))
            files.append((path,key))
            print("ARCHIMEDES",key,"checkpoint ready",file=sys.stderr,flush=True)
        summary=summarize(load(path,key) for path,key in files)
        def write(f):
            f.write(t.encode({**config,"process_peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"summary":summary})[:-1]+',"groups":[')
            for i,(path,key) in enumerate(files):
                if i:f.write(",")
                f.write(t.encode(load(path,key)))
            f.write("]}\n")
        t.atomic(output,write)
if __name__=="__main__":main()
