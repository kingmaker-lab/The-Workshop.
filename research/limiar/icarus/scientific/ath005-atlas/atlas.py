"""ATLAS-01 MOTION, subject-disjoint exploratory pilot, standard library."""
import argparse
import ctypes as C
import hashlib
import itertools
import json
import math
import platform
import random
import resource
import statistics as st
import sys
import time
from contextlib import ExitStack
from pathlib import Path
import fcntl
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath003-lever"))
import lever as l
t=l.t;a=l.a
CHANNELS=("total_acc_x","total_acc_y","total_acc_z","body_gyro_x","body_gyro_y","body_gyro_z")
N=64;D=768;F=30;MODES=("full","lite","static","causal");QUOTAS=(1,2,3)
class Result(C.Structure):
    _fields_=[(k,C.c_uint64) for k in ("cpu_ns","wall_ns","correct","expanded","features","over")]
def native():
    lib=C.CDLL(str(HERE/"libatlas.so"))
    ptr=C.POINTER(C.c_double);byte=C.POINTER(C.c_uint8)
    feat=lib.atlas_features;feat.argtypes=[ptr,ptr];feat.restype=C.c_int
    run=lib.atlas_run
    run.argtypes=[ptr,byte,C.c_size_t,C.c_int,C.c_int,C.c_double,ptr,ptr,C.POINTER(Result),byte,byte,ptr];run.restype=C.c_int
    def features(x):
        f=(C.c_double*F)()
        if feat((C.c_double*D)(*x),f):raise RuntimeError("features")
        return tuple(f)
    def evaluate(rows,q,mode,th,model):
        n=len(rows);x=(C.c_double*(n*D))()
        for i,(_,_,v) in enumerate(rows):x[i*D:(i+1)*D]=v
        y=(C.c_uint8*n)(*(r[1] for r in rows));cent=(C.c_double*(6*F))(*model["centers"]);scale=(C.c_double*F)(*model["scale"])
        out=Result();p=(C.c_uint8*n)();m=(C.c_uint8*n)();marg=(C.c_double*n)()
        if run(x,y,n,q,mode,th,cent,scale,C.byref(out),p,m,marg):raise RuntimeError("native")
        return {k:getattr(out,k) for k,_ in Result._fields_},tuple(p),tuple(m),tuple(marg)
    return features,evaluate
def paths(root,split):
    d=root/split
    return [d/f"subject_{split}.txt",d/f"y_{split}.txt"]+[d/"Inertial Signals"/f"{k}_{split}.txt" for k in CHANNELS]
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(65536),b""):h.update(block)
    return h.hexdigest()
def rows(root,split,allowed):
    with ExitStack() as stack:
        streams=[stack.enter_context(p.open()) for p in paths(root,split)]
        for lines in itertools.zip_longest(*streams):
            if any(x is None for x in lines):raise ValueError("unequal input lengths")
            s,y=map(int,lines[:2])
            if not 1<=s<=30 or not 1<=y<=6:raise ValueError("subject/label")
            if s not in allowed:continue
            ch=[tuple(map(float,line.split())) for line in lines[2:]]
            if any(len(v)!=128 or not all(map(math.isfinite,v)) for v in ch):raise ValueError("invalid signal")
            yield s,y,tuple(itertools.chain.from_iterable(ch))
def batches(stream):
    batch=[]
    for row in stream:
        if batch and (len(batch)==N or batch[0][0]!=row[0]):
            yield batch;batch=[]
        batch.append(row)
    if batch:yield batch
def train(root,ids,feat,guard):
    means=[0.]*F;m2=[0.]*F;counts=[0]*6;sums=[[0.]*F for _ in range(6)];n=0
    for _,y,x in rows(root,"train",ids):
        f=feat(x);n+=1;counts[y-1]+=1
        for j,z in enumerate(f):
            delta=z-means[j];means[j]+=delta/n;m2[j]+=delta*(z-means[j]);sums[y-1][j]+=z
        if n%64==0:guard()
    if min(counts)==0:raise RuntimeError("missing training class")
    return {"centers":[z/counts[k] for k in range(6) for z in sums[k]],
            "scale":[1/math.sqrt(max(v/n,1e-8)) for v in m2],"counts":counts,"rows":n}
def select(marg,q,th):
    n=len(marg);k=n*q//4;count=0;mask=[]
    for i,v in enumerate(marg):
        take=int(count<(i+1)*q//4 and (v<th or k-count==n-i))
        mask.append(take);count+=take
    return tuple(mask)
def calibrate(root,ids,run,model,guard):
    data=[]
    for batch in batches(rows(root,"train",ids)):
        guard();_,p,_,m=run(batch,2,0,0.,model);_,lite,_,lm=run(batch,2,1,0.,model)
        assert m==lm
        data.append((tuple(r[1] for r in batch),p,lite,m))
    vals=sorted(v for _,_,_,m in data for v in m)
    if not vals:raise RuntimeError("empty calibration")
    thresholds=sorted(set([0.]+[vals[int((len(vals)-1)*q/20)] for q in range(1,21)]+[math.nextafter(vals[-1],math.inf)]))
    out={}
    for q in QUOTAS:
        scores=[]
        for th in thresholds:
            correct=0
            for y,p,lite,m in data:
                mask=select(m,q,th)
                correct+=sum((p[i] if mask[i] else lite[i])==y[i] for i in range(len(y)))
            scores.append(correct)
        best=max(range(len(scores)),key=lambda i:(scores[i],-i))
        out[str(q)]={"threshold":thresholds[best],"candidates":thresholds,"scores":scores}
    return out,len(vals)
def check(result,mode,q,th,y,full,lite,m):
    r,p,mask,marg=result;n=len(y)
    assert marg==m and r["correct"]==sum(v==w for v,w in zip(p,y))
    expected=(1,)*n if mode==0 else (0,)*n if mode==1 else tuple(int((i+1)*q//4>i*q//4) for i in range(n)) if mode==2 else select(m,q,th)
    assert mask==expected and sum(mask)==r["expanded"]==(n if mode==0 else 0 if mode==1 else n*q//4)
    assert r["over"]==0 and r["features"]==6*n+24*sum(mask)
    assert p==tuple(full[i] if v else lite[i] for i,v in enumerate(mask))
    assert r["cpu_ns"]>0 and r["wall_ns"]>0
def measure(batch,index,run,model,cal,guard,reps):
    y=tuple(r[1] for r in batch);events=[]
    for q in QUOTAS:
        th=cal[str(q)]["threshold"]
        guard();full=run(batch,q,0,th,model);lite=run(batch,q,1,th,model)
        expected={}
        for mode in range(4):
            r=full if mode==0 else lite if mode==1 else run(batch,q,mode,th,model)
            check(r,mode,q,th,y,full[1],lite[1],full[3]);expected[mode]=r
        rnd=random.Random(4100+index*4+q);trials=[]
        for rep in range(reps):
            safe=guard();order=list(range(4));rnd.shuffle(order);arms={}
            for mode in order:
                r=run(batch,q,mode,th,model)
                check(r,mode,q,th,y,full[1],lite[1],full[3])
                assert r[1:]==expected[mode][1:]
                arms[MODES[mode]]=r[0]
            trials.append({"order":[MODES[i] for i in order],"safety":safe,"arms":arms})
            time.sleep(.02)
        events.append({"quota":q,"trials":trials,"predictions":{MODES[i]:list(expected[i][1]) for i in range(4)},"masks":{MODES[i]:list(expected[i][2]) for i in range(4)}})
    return {"index":index,"subject":batch[0][0],"labels":list(y),"events":events}
def summarize(groups):
    out={}
    for q in QUOTAS:
        subjects={}
        for g in groups:
            e=next(e for e in g["events"] if e["quota"]==q)
            s=subjects.setdefault(str(g["subject"]),{"rows":0,"arms":{m:{"correct":0,"cpu_ns":0.,"features":0,"confusion":[[0]*6 for _ in range(6)]} for m in MODES}})
            s["rows"]+=len(g["labels"])
            for m in MODES:
                arm=s["arms"][m];v=[r["arms"][m] for r in e["trials"]]
                arm["correct"]+=v[0]["correct"];arm["features"]+=v[0]["features"];arm["cpu_ns"]+=st.median(r["cpu_ns"] for r in v)
                for y,p in zip(g["labels"],e["predictions"][m]):arm["confusion"][y-1][p-1]+=1
        n=sum(s["rows"] for s in subjects.values());arms={}
        for m in MODES:
            acc=100*sum(s["arms"][m]["correct"] for s in subjects.values())/n
            ratio=math.exp(st.mean(math.log(s["arms"][m]["cpu_ns"]/s["arms"]["full"]["cpu_ns"]) for s in subjects.values()))
            arms[m]={"accuracy_pct":acc,"cpu_ratio_subject_geomean":ratio,"correct":sum(s["arms"][m]["correct"] for s in subjects.values()),
                     "features":sum(s["arms"][m]["features"] for s in subjects.values()),
                     "subject_mean_accuracy_pct":st.mean(100*s["arms"][m]["correct"]/s["rows"] for s in subjects.values())}
        out[str(q)]={"rows":n,"arms":arms,"subjects":subjects}
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument("--data",type=Path,required=True);p.add_argument("--smoke",action="store_true");p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    if not __debug__ or t.git("status","--porcelain","--untracked-files=no"):raise RuntimeError("clean tracked revision and assertions required")
    root=args.data.resolve();sensors=a.b1.sensor_paths();guard=lambda:a.safety_snapshot(sensors)
    guard();feat,run=native()
    trainids=set(map(int,paths(root,"train")[0].read_text().split()))
    testids=set(map(int,paths(root,"test")[0].read_text().split()))
    if len(trainids)!=21 or len(testids)!=9 or trainids&testids or trainids|testids!=set(range(1,31)):raise ValueError("unexpected official subject split")
    calids=set(sorted(trainids)[-6:]);fitids=trainids-calids
    model=train(root,fitids,feat,guard);cal,calrows=calibrate(root,calids,run,model,guard)
    split="train" if args.smoke else "test";ids=calids if args.smoke else testids;reps=3 if args.smoke else 5
    cfg={"experiment":"ATH-005-ATLAS-01-MOTION","exploratory":True,"smoke":args.smoke,"revision":t.git("rev-parse","HEAD"),
         "binary_sha256":digest(HERE/"libatlas.so"),"files_sha256":{str(p.relative_to(root)):digest(p) for s in ("train","test") for p in paths(root,s)},
         "fit_subjects":sorted(fitids),"cal_subjects":sorted(calids),"test_subjects":sorted(testids),"model":model,"calibration":cal,"calibration_rows":calrows,"reps":reps,
         "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},"timing_scope":"resident prefiltered signals; feature extraction, classification, selection and output only"}
    folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True);output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output outside checkpoint")
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=cfg:raise RuntimeError("checkpoint configuration mismatch")
        else:
            if list(folder.glob("batch-*.json")):raise RuntimeError("orphan checkpoints")
            t.atomic(manifest,lambda f:f.write(t.encode(cfg)))
        groups=[]
        stream=batches(rows(root,split,ids))
        if args.smoke:stream=itertools.islice(stream,2)
        for i,batch in enumerate(stream):
            guard();path=folder/f"batch-{i:04}.json"
            if path.exists():
                env=json.loads(path.read_text());g=env["group"]
                if hashlib.sha256(t.encode(g).encode()).hexdigest()!=env["sha256"] or g["index"]!=i or g["subject"]!=batch[0][0] or g["labels"]!=[r[1] for r in batch]:raise RuntimeError("checkpoint mismatch")
            else:
                g=measure(batch,i,run,model,cal,guard,reps)
                env={"group":g,"sha256":hashlib.sha256(t.encode(g).encode()).hexdigest()}
                t.atomic(path,lambda f:f.write(t.encode(env)))
            groups.append(g);print("ATLAS",i,"subject",g["subject"],"checkpoint ready",file=sys.stderr,flush=True)
        if not args.smoke and (sum(len(g["labels"]) for g in groups)!=2947 or {g["subject"] for g in groups}!=testids):raise RuntimeError("incomplete official test")
        obj={**cfg,"summary":summarize(groups),"groups":groups,"peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        t.atomic(output,lambda f:f.write(t.encode(obj)+"\n"))
if __name__=="__main__":main()
