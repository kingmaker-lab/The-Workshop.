"""GAUSS-01 locked design: fresh independent seed blocks, native LEVER unchanged."""
import argparse
import hashlib
import json
import math
import platform
import random
import resource
import statistics as st
import sys
import time
import uuid
from pathlib import Path
import fcntl
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath003-lever"))
import lever as l
t=l.t;a=l.a
N,W,B=256,16,16
SESSIONS=5
PER_SESSION=24
REPS=7
MODES={"full":0,"static":2,"rank":3,"causal":4}
T95=2.13184678632665 # one-sided t, df=4
def seeds(session):
    return (2999,) if session==0 else tuple(range(3001+(session-1)*PER_SESSION,3001+session*PER_SESSION))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def group(run,seed,reps,paths,invocation):
    root=seed*1000000+N*1000
    a.safety_snapshot(paths)
    x,y,c,f,digest,latent=l.fixture(root,N,W,"iid")
    a.safety_snapshot(paths)
    th,scores=l.calibrate(root+50+B,N,B,"iid")
    rng=random.Random(root+W*100+B)
    order=list(MODES);rng.shuffle(order);expected={}
    for name in order:
        mode=MODES[name];r,mask=run(x,y,N,B,W,mode,th)
        l.check(r,mask,y,c,f,N,B,W,mode,th);expected[name]=(r,mask)
    trials=[]
    for rep in range(reps):
        safe=a.safety_snapshot(paths);rng.shuffle(order);arms={}
        for name in order:
            r,mask=run(x,y,N,B,W,MODES[name],th);old,om=expected[name]
            if mask!=om or any(r[k]!=old[k] for k in r if k not in ("cpu_ns","wall_ns")):raise RuntimeError("repeat mismatch")
            if r["cpu_ns"]<=0 or r["wall_ns"]<=0:raise RuntimeError("invalid timing")
            arms[name]=r
        trials.append({"rep":rep,"order":list(order),"safety":safe,"arms":arms})
        time.sleep(.02)
    return {"seed":seed,"invocation":invocation,"fixture_sha256":digest,"latent_sha256":latent,"threshold":th,"calibration_correct":scores,"trials":trials}
def save(path,g):
    data=t.encode(g)
    t.atomic(path,lambda f:f.write(t.encode({"sha256":hashlib.sha256(data.encode()).hexdigest(),"group":g})))
def load(path,seed):
    e=json.loads(path.read_text());g=e["group"]
    if g["seed"]!=seed or hashlib.sha256(t.encode(g).encode()).hexdigest()!=e["sha256"]:raise RuntimeError("checkpoint mismatch")
    return g
def config(session):
    return {"experiment":"ATH-004-GAUSS-01","schema_version":1,"session":session,"smoke":session==0,
            "revision":t.git("rev-parse","HEAD"),"binary_sha256":sha(l.HERE/"liblever.so"),"protocol_sha256":sha(HERE/"PROTOCOL.md"),
            "n":N,"work":W,"budget":B,"scenario":"iid","seeds":list(seeds(session)),"reps":3 if session==0 else REPS,
            "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine(),"byteorder":sys.byteorder},
            "safety_min_available_kib":a.MIN_AVAILABLE_KIB,"safety_temperature_limit_c":a.TEMP_LIMIT}
def session_run(args):
    if not __debug__ or t.git("status","--porcelain","--untracked-files=no"):raise RuntimeError("assertions and clean tracked revision required")
    session=args.session
    if session not in range(SESSIONS+1):raise ValueError("session 0 smoke, 1..5 confirmation")
    cfg=config(session);folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True);output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output must be outside checkpoint")
    paths=a.b1.sensor_paths();a.safety_snapshot(paths);run=l.native()
    invocation=uuid.uuid4().hex
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=cfg:raise RuntimeError("configuration mismatch")
        else:
            if list(folder.glob("seed-*.json")):raise RuntimeError("orphan checkpoints")
            t.atomic(manifest,lambda f:f.write(t.encode(cfg)))
        def log(event,**kw):
            with (folder/"invocations.jsonl").open("a") as f:
                f.write(t.encode({"invocation":invocation,"utc_epoch":time.time(),"event":event,**kw})+"\n")
                f.flush()
        log("start")
        try:
            for seed in cfg["seeds"]:
                path=folder/f"seed-{seed}.json"
                if path.exists():load(path,seed)
                else:save(path,group(run,seed,cfg["reps"],paths,invocation))
                print("GAUSS",session,seed,"checkpoint ready",file=sys.stderr,flush=True)
            groups=[load(folder/f"seed-{s}.json",s) for s in cfg["seeds"]]
            log("complete")
            obj={**cfg,"peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 "invocations":[json.loads(x) for x in (folder/"invocations.jsonl").read_text().splitlines()],"groups":groups}
            t.atomic(output,lambda f:f.write(t.encode(obj)+"\n"))
        except BaseException as e:
            log("interrupted",reason=type(e).__name__,detail=str(e)[:200])
            raise
def analyze_session(d):
    session=d["session"]
    if session not in range(1,6) or d["smoke"] or d["seeds"]!=list(seeds(session)) or d["reps"]!=REPS or (d["n"],d["work"],d["budget"],d["scenario"])!=(N,W,B,"iid"):raise ValueError("unexpected session design")
    if [g["seed"] for g in d["groups"]]!=list(seeds(session)):raise ValueError("seed mismatch")
    values={name:[] for name in MODES if name!="full"}
    full_correct=0
    for g in d["groups"]:
        trials=g["trials"]
        if [r["rep"] for r in trials]!=list(range(REPS)):raise ValueError("missing repetitions")
        th=(0.,.25,.5,.75,1.,1.5,2.,3.,8.)
        scores=g["calibration_correct"]
        if len(scores)!=9 or g["threshold"]!=th[max(range(9),key=lambda i:(scores[i],-i))]:raise ValueError("calibration mismatch")
        for r in trials:
            if set(r["arms"])!=set(MODES) or sorted(r["order"])!=sorted(MODES):raise ValueError("arm mismatch")
            for name,v in r["arms"].items():
                k=N if name=="full" else N*(B-4)//28
                if v["over"]!=0 or v["expanded"]!=k or v["terms"]!=4*N+28*k or v["raw_reads"]!=4*N+28*W*k or not 0<=v["correct"]<=N or v["cpu_ns"]<=0 or v["wall_ns"]<=0:raise ValueError("invariant failed")
                if any(v[k]!=trials[0]["arms"][name][k] for k in v if k not in ("cpu_ns","wall_ns")):raise ValueError("repeat mismatch")
        fc=trials[0]["arms"]["full"]["correct"];full_correct+=fc
        ft=st.median(r["arms"]["full"]["cpu_ns"] for r in trials)
        for name in values:
            ac=trials[0]["arms"][name]["correct"]
            at=st.median(r["arms"][name]["cpu_ns"] for r in trials)
            values[name].append((100*(fc-ac)/N,math.log(at/ft),ac))
    return {"session":session,"full_correct":full_correct,"invocations_used":len({g["invocation"] for g in d["groups"]}),
            "arms":{name:{"loss_pp":st.mean(v[0] for v in vals),"log_cpu_ratio":st.mean(v[1] for v in vals),
                          "correct":sum(v[2] for v in vals)} for name,vals in values.items()}}
def upper(xs):
    if len(xs)!=SESSIONS:raise ValueError("all five blocks required")
    return st.mean(xs)+T95*st.stdev(xs)/math.sqrt(SESSIONS)
def analyze(args):
    if len(args.files)!=SESSIONS:raise ValueError("exactly five complete session files required")
    docs=[json.loads(p.read_text()) for p in args.files]
    if sorted(d["session"] for d in docs)!=list(range(1,6)):raise ValueError("distinct sessions 1..5 required")
    for key in ("experiment","schema_version","revision","binary_sha256","protocol_sha256","environment","safety_min_available_kib","safety_temperature_limit_c"):
        if any(d[key]!=docs[0][key] for d in docs):raise ValueError("mixed "+key)
    if docs[0]["experiment"]!="ATH-004-GAUSS-01" or docs[0]["schema_version"]!=1 or docs[0]["protocol_sha256"]!=sha(HERE/"PROTOCOL.md"):raise ValueError("protocol mismatch")
    for k in ("fixture_sha256","latent_sha256"):
        hashes=[g[k] for d in docs for g in d["groups"]]
        if len(set(hashes))!=SESSIONS*PER_SESSION:raise ValueError("duplicate fixture")
    blocks=sorted((analyze_session(d) for d in docs),key=lambda d:d["session"])
    result={}
    for name in ("causal","rank","static"):
        losses=[d["arms"][name]["loss_pp"] for d in blocks];logs=[d["arms"][name]["log_cpu_ratio"] for d in blocks]
        result[name]={"loss_pp":st.mean(losses),"loss_upper_one_sided_95_pp":upper(losses),
                      "cpu_ratio_geometric_mean":math.exp(st.mean(logs)),"cpu_ratio_upper_one_sided_95":math.exp(upper(logs)),
                      "correct":sum(d["arms"][name]["correct"] for d in blocks)}
    c=result["causal"]
    quality=c["loss_upper_one_sided_95_pp"]<=1.
    cpu=c["cpu_ratio_upper_one_sided_95"]<1.
    strong=c["cpu_ratio_upper_one_sided_95"]<=.5
    out={"experiment":"ATH-004-GAUSS-01","revision":docs[0]["revision"],"binary_sha256":docs[0]["binary_sha256"],
         "protocol_sha256":docs[0]["protocol_sha256"],"source_sha256":[sha(p) for p in args.files],
         "independent_seed_blocks":5,"test_rows":SESSIONS*PER_SESSION*N,"full_correct":sum(d["full_correct"] for d in blocks),
         "blocks":blocks,"results":result,"primary":{"quality_noninferiority":quality,"cpu_superiority":cpu,"joint":quality and cpu,"strong_50_percent":quality and strong},
         "caveat":"t bounds approximate, conditional on five independent representative blocks; actual temporal independence not certified by files; rank/static descriptive only"}
    t.atomic(args.output.resolve(),lambda f:f.write(t.encode(out)+"\n"));print(json.dumps(out["primary"],indent=2))
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    r=sub.add_parser("run");r.add_argument("--session",type=int,required=True);r.add_argument("--checkpoint",type=Path,required=True);r.add_argument("--output",type=Path,required=True)
    q=sub.add_parser("analyze");q.add_argument("files",type=Path,nargs="+");q.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    if args.cmd=="run":session_run(args)
    else:analyze(args)
if __name__=="__main__":main()
