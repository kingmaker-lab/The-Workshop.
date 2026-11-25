"""KINESIS development-only subject-disjoint cross validation, stdlib."""
import argparse
import bisect
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
from pathlib import Path
import fcntl
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath005-atlas"))
import atlas as a
t=a.t
MODES=("flat_full","hier_full","hier_lite","static","margin","benefit")
EDGES=(.02,.05,.10,.20,.40,.60)
QUOTAS=(1,2,3)
TRAIN_IDS={1,3,5,6,7,8,11,14,15,16,17,19,21,22,23,25,26,27,28,29,30}
TEST_IDS={2,4,9,10,12,13,18,20,24}
def native():
    lib=C.CDLL(str(HERE/"libkinesis.so"));ptr=C.POINTER(C.c_double);byte=C.POINTER(C.c_uint8)
    feat=lib.kin_features;feat.argtypes=[ptr,ptr];feat.restype=C.c_int
    fn=lib.kin_run;fn.argtypes=[ptr,byte,C.c_size_t,C.c_int,C.c_int,C.c_double,ptr,ptr,ptr,ptr,C.POINTER(a.Result),byte,byte,ptr,byte];fn.restype=C.c_int
    def features(x):
        f=(C.c_double*30)()
        if feat((C.c_double*768)(*x),f):raise RuntimeError("features")
        return tuple(f)
    def prepare(batch,model,table):
        n=len(batch);x=(C.c_double*(n*768))()
        for i,(_,_,v) in enumerate(batch):x[i*768:(i+1)*768]=v
        y=(C.c_uint8*n)(*(r[1] for r in batch))
        cent=(C.c_double*180)(*model["centers"]);scale=(C.c_double*30)(*model["scale"])
        coarse=(C.c_double*24)(*model["coarse"]);ben=(C.c_double*14)(*table)
        def run(q,mode,th):
            r=a.Result();p=(C.c_uint8*n)();m=(C.c_uint8*n)();g=(C.c_uint8*n)();marg=(C.c_double*n)()
            if fn(x,y,n,q,mode,th,cent,scale,coarse,ben,C.byref(r),p,m,marg,g):raise RuntimeError("native")
            return {k:getattr(r,k) for k,_ in a.Result._fields_},tuple(p),tuple(m),tuple(marg),tuple(g)
        return run
    return features,prepare
def folds():
    ids=sorted(TRAIN_IDS);random.Random(5201).shuffle(ids)
    out=[]
    for k in range(3):
        ev=set(ids[k*7:(k+1)*7]);rem=sorted(TRAIN_IDS-ev)
        random.Random(5202+k).shuffle(rem)
        fit=set(rem[:8]);benefit=set(rem[8:11]);tune=set(rem[11:])
        assert not (fit&benefit or fit&tune or fit&ev or benefit&tune or benefit&ev or tune&ev)
        assert fit|benefit|tune|ev==TRAIN_IDS
        out.append({"fit":sorted(fit),"benefit_fit":sorted(benefit),"tune":sorted(tune),"eval":sorted(ev)})
    assert set().union(*(set(f["eval"]) for f in out))==TRAIN_IDS
    return out
def fit(root,ids,feat,guard):
    model=a.train(root,set(ids),feat,guard);c=model["centers"]
    # Equal class prior within each coarse group, not subject or test labels.
    model["coarse"]=[sum(c[(g*3+k)*30+j] for k in range(3))/3 for g in range(2) for j in range(12)]
    return model
def observations(root,ids,prepare,model,guard):
    for batch in a.batches(a.rows(root,"train",set(ids))):
        guard();run=prepare(batch,model,[0.]*14)
        _,f,_,m,g=run(2,1,0.);_,l,_,lm,lg=run(2,2,0.)
        assert m==lm and g==lg
        assert all(0<=v<1 and math.isfinite(v) for v in m)
        yield tuple(r[1] for r in batch),f,l,m,g
def learn(root,ids,prepare,model,guard):
    counts=[[0]*7 for _ in range(2)];gain=[[0]*7 for _ in range(2)]
    for y,f,l,m,g in observations(root,ids,prepare,model,guard):
        for yy,ff,ll,mm,gg in zip(y,f,l,m,g):
            b=bisect.bisect_right(EDGES,mm);counts[gg][b]+=1;gain[gg][b]+=int(ff==yy)-int(ll==yy)
    pooled=[sum(gain[k][b] for k in range(2))/(16+sum(counts[k][b] for k in range(2))) for b in range(7)]
    table=[(gain[g][b]+32*pooled[b])/(counts[g][b]+32) for g in range(2) for b in range(7)]
    return {"counts":counts,"gain":gain,"table":table}
def select(values,q,th,benefit=False):
    n=len(values);k=n*q//4;count=0;out=[]
    for i,v in enumerate(values):
        wants=v>th if benefit else v<th
        take=int(count<(i+1)*q//4 and (wants or k-count==n-i))
        out.append(take);count+=take
    return tuple(out)
def tune(root,ids,prepare,model,learned,guard):
    data=list(observations(root,ids,prepare,model,guard));table=learned["table"]
    if not data:raise RuntimeError("empty tuning")
    data=[(y,f,l,m,tuple(table[gg*7+bisect.bisect_right(EDGES,mm)] for mm,gg in zip(m,g))) for y,f,l,m,g in data]
    mvals=sorted(v for _,_,_,m,_ in data for v in m)
    mc=sorted(set([0.]+[mvals[int((len(mvals)-1)*i/20)] for i in range(1,21)]+[math.nextafter(mvals[-1],math.inf)]))
    bc=sorted(set([-2.,2.]+[v for v in table]+[math.nextafter(v,-math.inf) for v in table]))
    out={}
    for q in QUOTAS:
        out[str(q)]={}
        for name,candidates,isben in (("margin",mc,False),("benefit",bc,True)):
            scores=[]
            for th in candidates:
                correct=0
                for y,f,l,m,v in data:
                    mask=select(v if isben else m,q,th,isben)
                    correct+=sum((f[i] if take else l[i])==y[i] for i,take in enumerate(mask))
                scores.append(correct)
            best=max(range(len(scores)),key=lambda i:(scores[i],-i))
            out[str(q)][name]={"threshold":candidates[best],"candidates":candidates,"scores":scores}
    return out,sum(len(y) for y,*_ in data)
def check(res,mode,q,th,y,full,lite,m,g,table):
    r,p,mask,margin,group=res;n=len(y)
    assert r["correct"]==sum(v==w for v,w in zip(p,y)) and all(1<=v<=6 for v in p)
    if mode==0:
        expected=(1,)*n;assert group==(255,)*n and margin==(0.,)*n
    else:
        assert margin==m and group==g and all((v-1)//3==gg for v,gg in zip(p,g))
        values=tuple(table[gg*7+bisect.bisect_right(EDGES,mm)] for mm,gg in zip(m,g))
        expected=(1,)*n if mode==1 else (0,)*n if mode==2 else tuple(int((i+1)*q//4>i*q//4) for i in range(n)) if mode==3 else select(m if mode==4 else values,q,th,mode==5)
        assert p==tuple(full[i] if take else lite[i] for i,take in enumerate(mask))
    assert mask==expected and sum(mask)==r["expanded"]==(n if mode<=1 else 0 if mode==2 else n*q//4)
    bound=n if mode<=1 else 0 if mode==2 else q
    if mode>=3:assert all(v<=(i+1)*bound//4 for i,v in enumerate(itertools.accumulate(mask)))
    assert r["features"]==12*n+18*sum(mask) and r["over"]==0
    assert r["cpu_ns"]>0 and r["wall_ns"]>0
def measure(batch,index,fold,prepare,model,learned,cal,guard,reps):
    y=tuple(r[1] for r in batch);events=[];table=learned["table"]
    run=prepare(batch,model,table)
    for q in QUOTAS:
        guard();th=[0.]*4+[cal[str(q)][m]["threshold"] for m in ("margin","benefit")]
        f=run(q,1,0.);l=run(q,2,0.);m=f[3];g=f[4]
        expected={}
        for mode in range(6):
            res=f if mode==1 else l if mode==2 else run(q,mode,th[mode])
            check(res,mode,q,th[mode],y,f[1],l[1],m,g,table);expected[mode]=res
        rng=random.Random(5300+fold*10000+index*4+q);trials=[]
        for rep in range(reps):
            safe=guard();order=list(range(6));rng.shuffle(order);arms={}
            for mode in order:
                res=run(q,mode,th[mode]);check(res,mode,q,th[mode],y,f[1],l[1],m,g,table)
                assert res[1:]==expected[mode][1:]
                arms[MODES[mode]]=res[0]
            trials.append({"order":[MODES[i] for i in order],"safety":safe,"arms":arms})
            time.sleep(.02)
        events.append({"quota":q,"trials":trials,"predictions":{MODES[i]:list(expected[i][1]) for i in range(6)},
                       "masks":{MODES[i]:list(expected[i][2]) for i in range(6)},"coarse_groups":list(g),"margins":list(m)})
    return {"index":index,"fold":fold,"subject":batch[0][0],"labels":list(y),"events":events}
def summarize(groups):
    out={}
    for q in QUOTAS:
        subjects={}
        for g in groups:
            e=next(v for v in g["events"] if v["quota"]==q);y=g["labels"]
            s=subjects.setdefault(str(g["subject"]),{"rows":0,"coarse_correct":0,"fold":g["fold"],"arms":{m:{"correct":0,"cpu_ns":0.,"features":0,"confusion":[[0]*6 for _ in range(6)]} for m in MODES}})
            assert s["fold"]==g["fold"]
            s["rows"]+=len(y);s["coarse_correct"]+=sum((v-1)//3==gg for v,gg in zip(y,e["coarse_groups"]))
            for m in MODES:
                arm=s["arms"][m];v=[r["arms"][m] for r in e["trials"]]
                arm["correct"]+=v[0]["correct"];arm["features"]+=v[0]["features"];arm["cpu_ns"]+=st.median(r["cpu_ns"] for r in v)
                for yy,p in zip(y,e["predictions"][m]):arm["confusion"][yy-1][p-1]+=1
        n=sum(s["rows"] for s in subjects.values());arms={}
        for m in MODES:
            corr=sum(s["arms"][m]["correct"] for s in subjects.values())
            ratios={ref:math.exp(st.mean(math.log(s["arms"][m]["cpu_ns"]/s["arms"][ref]["cpu_ns"]) for s in subjects.values())) for ref in ("flat_full","hier_full")}
            arms[m]={"correct":corr,"accuracy_pct":100*corr/n,"cpu_ratios":ratios,"features":sum(s["arms"][m]["features"] for s in subjects.values()),
                     "subject_mean_accuracy_pct":st.mean(100*s["arms"][m]["correct"]/s["rows"] for s in subjects.values())}
        out[str(q)]={"rows":n,"coarse_accuracy_pct":100*sum(s["coarse_correct"] for s in subjects.values())/n,"arms":arms,"subjects":subjects}
    return out
def envelope(path,value):
    t.atomic(path,lambda f:f.write(t.encode({"sha256":hashlib.sha256(t.encode(value).encode()).hexdigest(),"value":value})))
def load(path):
    e=json.loads(path.read_text());v=e["value"]
    if hashlib.sha256(t.encode(v).encode()).hexdigest()!=e["sha256"]:raise RuntimeError("checkpoint digest mismatch")
    return v
def main():
    p=argparse.ArgumentParser();p.add_argument("--data",type=Path,required=True);p.add_argument("--smoke",action="store_true");p.add_argument("--checkpoint",type=Path,required=True);p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    if not __debug__ or t.git("status","--porcelain","--untracked-files=no"):raise RuntimeError("clean tracked revision and assertions required")
    root=args.data.resolve()
    if not all(p.is_file() for p in a.paths(root,"train")):raise FileNotFoundError("point --data to UCI HAR Dataset folder containing train/")
    ids=set(map(int,a.paths(root,"train")[0].read_text().split()))
    if ids!=TRAIN_IDS:raise ValueError("unexpected official training subjects")
    sensors=a.a.b1.sensor_paths();guard=lambda:a.a.safety_snapshot(sensors)
    guard();feat,prepare=native();splits=folds();reps=3 if args.smoke else 5
    cfg={"experiment":"ATH-005-ATLAS-02-KINESIS","exploratory":True,"smoke":args.smoke,"revision":t.git("rev-parse","HEAD"),"binary_sha256":a.digest(HERE/"libkinesis.so"),
         "files_sha256":{str(p.relative_to(root)):a.digest(p) for p in a.paths(root,"train")},"excluded_motion_test_subjects":sorted(TEST_IDS),"splits":splits,"reps":reps,
         "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},"timing_scope":"resident prefiltered signals; native extraction, classification, selection and output"}
    folder=args.checkpoint.resolve();folder.mkdir(parents=True,exist_ok=True);output=args.output.resolve()
    if output.parent==folder:raise RuntimeError("output outside checkpoint")
    with (folder/".lock").open("a") as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);manifest=folder/"manifest.json"
        if manifest.exists():
            if json.loads(manifest.read_text())!=cfg:raise RuntimeError("checkpoint config mismatch")
        else:
            if list(folder.glob("fold-*")):raise RuntimeError("orphan checkpoints")
            t.atomic(manifest,lambda f:f.write(t.encode(cfg)))
        groups=[];models=[]
        for k,split in enumerate(splits[:1] if args.smoke else splits):
            path=folder/f"fold-{k}-model.json"
            if path.exists():fm=load(path)
            else:
                model=fit(root,split["fit"],feat,guard);learned=learn(root,split["benefit_fit"],prepare,model,guard)
                cal,n=tune(root,split["tune"],prepare,model,learned,guard)
                fm={"fold":k,"split":split,"model":model,"learned":learned,"calibration":cal,"tune_rows":n};envelope(path,fm)
            assert fm["fold"]==k and fm["split"]==split;models.append(fm)
            stream=a.batches(a.rows(root,"train",set(split["eval"])))
            if args.smoke:stream=itertools.islice(stream,2)
            for i,batch in enumerate(stream):
                guard();path=folder/f"fold-{k}-batch-{i:04}.json"
                if path.exists():
                    g=load(path)
                    assert (g["fold"],g["index"],g["subject"],g["labels"])==(k,i,batch[0][0],[r[1] for r in batch])
                else:
                    g=measure(batch,i,k,prepare,fm["model"],fm["learned"],fm["calibration"],guard,reps);envelope(path,g)
                groups.append(g);print("KINESIS",k,i,"subject",g["subject"],"checkpoint ready",file=sys.stderr,flush=True)
        if not args.smoke and (sum(len(g["labels"]) for g in groups)!=7352 or {g["subject"] for g in groups}!=TRAIN_IDS):raise RuntimeError("incomplete development evaluation")
        obj={**cfg,"models":models,"summary":summarize(groups),"groups":groups,"peak_rss_kib_current_invocation":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        t.atomic(output,lambda f:f.write(t.encode(obj)+"\n"))
if __name__=="__main__":main()
