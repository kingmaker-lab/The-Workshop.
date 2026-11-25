"""OMEGA terminal protocol. Python prepares/evaluates; standalone C performs inference."""
import argparse,bisect,collections,csv,ctypes as C,hashlib,itertools,json,math,os,platform,random,re,statistics as st,struct,subprocess,sys,time,fcntl
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"ath005-atlas"))
import atlas as a
t=a.t
EXE=HERE/"omega";LIB=HERE/"libomega.so"
PROTOCOL=HERE.parent/"OMEGA-FINAL-PROTOCOL.md"
EDGES=(.02,.05,.10,.20,.40,.60)
CLASSES=("dws","ups","wlk","jog","sit","std")
TRIALS={"dws":(1,2,11),"ups":(3,4,12),"wlk":(7,8,15),"jog":(9,16),"sit":(5,13),"std":(6,14)}
ARMS=("full","omega","lite","static")
GRID=list(itertools.product((1,2,3),(0.,.02,.05,.10)))
SIZES=(1,16,64,256)
def require(ok,msg):
    if not ok:raise RuntimeError(msg)
def digest(p):return a.digest(p)
def write(p,v):t.atomic(p,lambda f:f.write(t.encode(v)+"\n"))
def read(p):return json.loads(p.read_text())
def split():
    ids=list(range(1,25));random.Random(20261125).shuffle(ids)
    return {k:sorted(v) for k,v in zip(("fit","benefit","tune","test"),(ids[:8],ids[8:12],ids[12:16],ids[16:]))}
def guard():
    return a.a.safety_snapshot(a.a.b1.sensor_paths())
def identity():
    require(sys.byteorder=="little" and platform.machine()=="x86_64","native format requires little-endian x86_64")
    require(not t.git("status","--porcelain","--untracked-files=no"),"tracked revision must be clean")
    return {"revision":t.git("rev-parse","HEAD"),"exe":digest(EXE),"lib":digest(LIB),"protocol":digest(PROTOCOL),
            "kernel":platform.release(),"machine":platform.machine(),"python":platform.python_version()}
def sources(root):
    out={}
    for act in CLASSES:
        for tr in TRIALS[act]:
            for s in range(1,25):
                p=root/f"{act}_{tr}"/f"sub_{s}.csv"
                require(p.is_file(),f"missing {p}")
                out[(s,tr,CLASSES.index(act)+1)]=p
    require(len(out)==360,"recording count")
    return out
def hashes(root,src):
    out={}
    for p in src.values():guard();out[str(p.relative_to(root))]=digest(p)
    return out
def feature_fn():
    lib=C.CDLL(str(LIB));fn=lib.omega_features;ptr=C.POINTER(C.c_double)
    fn.argtypes=[ptr,ptr];fn.restype=C.c_int
    def features(x):
        out=(C.c_double*30)();require(fn((C.c_double*768)(*x),out)==0,"feature extraction")
        return tuple(out)
    return features
def reference(x):
    v=[x[j*128:(j+1)*128] for j in range(6)]
    means=[math.fsum(z)/128 for z in v];var=[math.fsum((b-m)**2 for b in z)/128 for z,m in zip(v,means)]
    tail=[math.fsum((z[i]-z[i-k])**2 for i in range(k,128))/(128-k) for z in v for k in (1,8,32)]
    return means+var+tail
def equivalent(x,feat):
    require(all(math.isclose(v,w,rel_tol=1e-8,abs_tol=1e-10) for v,w in zip(feat(x),reference(x))),"fused/reference mismatch")
def windows(p):
    cols=[f"{k}.{axis}" for k in ("gravity","userAcceleration","rotationRate") for axis in "xyz"]
    with p.open(newline="",encoding="utf-8-sig") as f:
        reader=csv.DictReader(f);require(reader.fieldnames and set(cols)<=set(reader.fieldnames),f"columns {p}")
        buf=[[] for _ in range(6)];n=0
        for line in reader:
            z=[float(line[c]) for c in cols];require(all(math.isfinite(v) and abs(v)<1e6 for v in z),f"invalid value {p}")
            for j in range(3):buf[j].append(z[j]+z[j+3]);buf[j+3].append(z[j+6])
            n+=1
            if n%128==0:yield tuple(itertools.chain.from_iterable(buf));buf=[[] for _ in range(6)]
def pack_data(path,src,ids,feat=None,fit=False,smoke=False):
    tmp=path.with_suffix(".tmp");counts=collections.Counter();means=[0.]*30;m2=[0.]*30;sums=[[0.]*30 for _ in range(6)];classes=[0]*6;n=0
    with tmp.open("wb") as f:
        f.write(b"OMEGA001")
        for (s,tr,y),p in sorted(src.items()):
            if s not in ids:continue
            guard();pos=f.tell();f.write(struct.pack("<4I",s,tr,0,y));k=0
            for x in windows(p):
                if feat is not None:equivalent(x,feat)
                if fit:
                    v=feat(x);n+=1;classes[y-1]+=1
                    for j,z in enumerate(v):
                        d=z-means[j];means[j]+=d/n;m2[j]+=d*(z-means[j]);sums[y-1][j]+=z
                f.write(struct.pack("<768d",*x));k+=1
                if k%64==0:guard()
                if smoke and k==64:break
            require(k>0,f"empty recording {p}")
            end=f.tell();f.seek(pos);f.write(struct.pack("<4I",s,tr,k,y));f.seek(end)
            counts[f"{s}:{tr}:{y}"]=k
            if smoke and len(counts)>=2:break
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    model=None
    if fit:
        require(min(classes)>0,"missing fit class")
        centers=[v/classes[i] for i in range(6) for v in sums[i]]
        scale=[1/math.sqrt(max(v/n,1e-8)) for v in m2]
        coarse=[st.mean(centers[i*30+j] for i in group) for group in (range(4),range(4,6)) for j in range(12)]
        model={"centers":centers,"scale":scale,"coarse":coarse,"counts":classes,"rows":n}
    return dict(counts),model
def model_file(path,model,table):
    with path.open("wb") as f:f.write(struct.pack("<248d",*(model["centers"]+model["scale"]+model["coarse"]+table)))
def call(out,model,data,size,q,th,reps,mode,cap,seed):
    guard();env={**os.environ,"OMEGA_SEED":str(seed)}
    # Preserve failed/partial CSV rather than overwrite it.
    tmp=out.with_suffix(".partial")
    if tmp.exists():raise RuntimeError(f"preserve existing partial: {tmp}")
    with tmp.open("w") as f:
        rc=subprocess.run([str(EXE),str(model),str(data),str(size),str(q),repr(th),str(reps),str(mode),str(cap)],stdout=f,env=env,check=False).returncode
    require(rc==0,f"native return {rc}; partial preserved at {tmp}")
    tmp.rename(out);guard()
def parse(path,size,q,th,reps,mode,table,expected=None,allow_cut=False):
    batches={};end=None;order=[]
    arms=range(4) if mode==-1 else (mode,)
    with path.open() as f:
        for line in f:
            r=line.rstrip("\n").split(",")
            require(end is None,"output after END")
            if r[0]=="END":
                require(len(r)==5,"END schema");end=list(map(int,r[1:]));continue
            require(r[0]=="B" and len(r)>=16,"B schema")
            s,tr,b,n,rep,arm,cpu,wall,correct,expanded,over=map(int,r[1:12])
            y,p,mask,g=[tuple(map(int,v)) for v in r[12:16]];m=tuple(map(float,r[16:]))
            require(1<=s<=24 and 1<=n<=size and 0<=rep<reps and arm in arms and cpu>0 and wall>0,"invalid record")
            require(all(len(v)==n for v in (y,p,mask,g,m)) and all(1<=v<=6 for v in y+p) and len(set(y))==1 and all(v in (0,1) for v in mask),"invalid vectors")
            require(correct==sum(v==w for v,w in zip(y,p)) and expanded==sum(mask) and over==0,"incorrect count/overrun")
            if arm==0:require(mask==(1,)*n and g==(2,)*n and m==(0.,)*n,"full invariants")
            else:
                require(all(v in (0,1) for v in g) and all(0<=v<1 and math.isfinite(v) for v in m),"cheap metadata")
                count=0;want=[]
                for i,(gg,mm) in enumerate(zip(g,m)):
                    cap=(i+1)*q//4
                    take=int(arm==3 and cap>i*q//4 or arm==1 and count<cap and table[gg*7+bisect.bisect_right(EDGES,mm)]>th)
                    count+=take;want.append(take);require(count<=cap,"prefix")
                require(tuple(want)==mask,"selection replay")
            z=batches.setdefault(b,{"subject":s,"trial":tr,"labels":list(y),"arms":{}})
            require((s,tr,list(y))==(z["subject"],z["trial"],z["labels"]),"batch mismatch")
            ar=z["arms"].setdefault(str(arm),{"pred":list(p),"mask":list(mask),"group":list(g),"margin":list(m),"times":{}})
            require((list(p),list(mask),list(g),list(m))==(ar["pred"],ar["mask"],ar["group"],ar["margin"]) and str(rep) not in ar["times"],"repeat mismatch")
            ar["times"][str(rep)]=[cpu,wall];order.append((b,rep,arm))
    require(end is not None and end[0]==len(batches) and list(batches)==list(range(len(batches))) and end[1] in (0,1) and end[2]>0 and end[3]>0,"incomplete output")
    require(allow_cut or end[1]==0,"unexpected truncation")
    counts=collections.Counter()
    for z in batches.values():
        n=len(z["labels"]);counts[f'{z["subject"]}:{z["trial"]}:{z["labels"][0]}']+=n
        require(set(z["arms"])=={str(v) for v in arms} and all(len(v["times"])==reps for v in z["arms"].values()),"missing arm/repetition")
        if mode==-1:
            ar=z["arms"];f=ar["0"];l=ar["2"]
            for k in ("1","3"):
                v=ar[k];require(v["margin"]==l["margin"] and v["group"]==l["group"],"cheap parity")
                require(v["pred"]==[ff if take else ll for ff,ll,take in zip(f["pred"],l["pred"],v["mask"])],"expansion parity")
    if expected is not None:
        if end[1]==0:require(dict(counts)==expected,"dataset coverage")
        else:require(all(k in expected and v<=expected[k] for k,v in counts.items()),"partial coverage")
    return {"batches":list(batches.values()),"end":{"batches":end[0],"cut":bool(end[1]),"rss_kib":end[2],"elapsed_ns":end[3]},"order":order}
def summary(result):
    subjects={}
    for z in result["batches"]:
        s=subjects.setdefault(str(z["subject"]),{"n":0,"arms":{}});y=z["labels"];s["n"]+=len(y)
        for k,v in z["arms"].items():
            ar=s["arms"].setdefault(k,{"correct":0,"expanded":0,"cpu":0,"wall":0,"confusion":[[0]*6 for _ in range(6)]})
            ar["correct"]+=sum(a==b for a,b in zip(y,v["pred"]));ar["expanded"]+=sum(v["mask"])
            ar["cpu"]+=st.median(x[0] for x in v["times"].values());ar["wall"]+=st.median(x[1] for x in v["times"].values())
            for a,b in zip(y,v["pred"]):ar["confusion"][a-1][b-1]+=1
    n=sum(v["n"] for v in subjects.values());require(n>0,"no observations")
    out={}
    for k in next(iter(subjects.values()))["arms"]:
        out[k]={"macro":st.mean(100*v["arms"][k]["correct"]/v["n"] for v in subjects.values()),
                "pooled":100*sum(v["arms"][k]["correct"] for v in subjects.values())/n,
                "expanded":sum(v["arms"][k]["expanded"] for v in subjects.values()),"cpu":sum(v["arms"][k]["cpu"] for v in subjects.values())}
        if all("0" in v["arms"] for v in subjects.values()):out[k]["ratio"]=math.exp(st.mean(math.log(v["arms"][k]["cpu"]/v["arms"]["0"]["cpu"]) for v in subjects.values()))
    return {"n":n,"subjects":subjects,"arms":out}
def learn(res):
    counts=[[0]*7 for _ in range(2)];gain=[[0]*7 for _ in range(2)]
    for z in res["batches"]:
        f=z["arms"]["0"];l=z["arms"]["2"]
        for y,p,v,g,m in zip(z["labels"],f["pred"],l["pred"],l["group"],l["margin"]):
            b=bisect.bisect_right(EDGES,m);counts[g][b]+=1;gain[g][b]+=int(p==y)-int(v==y)
    pooled=[sum(gain[g][b] for g in range(2))/(16+sum(counts[g][b] for g in range(2))) for b in range(7)]
    table=[(gain[g][b]+32*pooled[b])/(counts[g][b]+32) for g in range(2) for b in range(7)]
    return {"counts":counts,"gain":gain,"table":table}
def choose(grid):
    good=[v for v in grid if v["loss"]<=1 and v["ratio"]<=.5]
    cpu=[v for v in grid if v["ratio"]<=.5]
    return min(good or cpu,key=lambda v:(-v["macro"],v["ratio"],v["q"],-v["threshold"])) if good or cpu else min(grid,key=lambda v:(v["ratio"],-v["macro"],v["q"],-v["threshold"]))
def smoke(root,folder):
    require(not folder.exists(),"new smoke directory required");folder.mkdir(parents=True)
    feat=feature_fn();rng=random.Random(5100)
    for x in ([0.]*768,[1e5]*768,[1e5+rng.uniform(-.01,.01) for _ in range(768)],[rng.gauss(0,1) for _ in range(768)]):
        equivalent(x,feat)
    src=sources(root);ids=split()["fit"]
    counts,model=pack_data(folder/"fit.bin",src,ids,feat,fit=True)
    small,_=pack_data(folder/"smoke.bin",src,ids,feat,smoke=True)
    model_file(folder/"model.bin",model,[.1]*14)
    call(folder/"smoke.csv",folder/"model.bin",folder/"smoke.bin",64,2,0.,3,-1,0,0)
    res=parse(folder/"smoke.csv",64,2,0.,3,-1,[.1]*14,small)
    write(folder/"smoke.json",{"identity":identity(),"fit":counts,"summary":summary(res),"integrity":"passed"})
def freeze(root,folder):
    require(not folder.exists(),"new freeze directory required");folder.mkdir(parents=True)
    ident=identity();src=sources(root);sh=hashes(root,src);spl=split();feat=feature_fn()
    fit,model=pack_data(folder/"fit.bin",src,spl["fit"],feat,True)
    bf,_=pack_data(folder/"benefit.bin",src,spl["benefit"],feat)
    tu,_=pack_data(folder/"tune.bin",src,spl["tune"],feat)
    model_file(folder/"base.bin",model,[0.]*14)
    call(folder/"benefit.csv",folder/"base.bin",folder/"benefit.bin",64,2,0.,1,-1,0,0)
    learned=learn(parse(folder/"benefit.csv",64,2,0.,1,-1,[0.]*14,bf));table=learned["table"]
    model_file(folder/"model.bin",model,table);grid=[]
    for i,(q,th) in enumerate(GRID):
        print("CALIBRATION",i+1,"/12",flush=True);p=folder/f"tune-{i:02}.csv"
        call(p,folder/"model.bin",folder/"tune.bin",64,q,th,5,-1,0,0)
        v=summary(parse(p,64,q,th,5,-1,table,tu))
        grid.append({"q":q,"threshold":th,"macro":v["arms"]["1"]["macro"],"loss":v["arms"]["0"]["macro"]-v["arms"]["1"]["macro"],"ratio":v["arms"]["1"]["ratio"],"raw_sha256":digest(p)})
    chosen=choose(grid)
    lock={"identity":ident,"source_sha256":sh,"splits":spl,"fit_counts":fit,"benefit_counts":bf,"tune_counts":tu,"model":model,"learned":learned,"grid":grid,"chosen":chosen,"model_sha256":digest(folder/"model.bin"),"created_utc":time.time()}
    write(folder/"freeze.json",lock);print("FROZEN",chosen,flush=True)
def get_lock(folder):
    p=folder/"freeze.json";lock=read(p);require(lock["identity"]==identity(),"frozen code/binary/environment mismatch")
    require(lock["model_sha256"]==digest(folder/"model.bin") and lock["chosen"]==choose(lock["grid"]),"frozen model/selection mismatch")
    return lock
def prepare_test(root,folder):
    lock=get_lock(folder);src=sources(root);require(hashes(root,src)==lock["source_sha256"],"source files changed")
    require(not (folder/"test.json").exists(),"test already prepared")
    counts,_=pack_data(folder/"test.bin",src,lock["splits"]["test"])
    write(folder/"test.json",{"freeze_sha256":digest(folder/"freeze.json"),"test_sha256":digest(folder/"test.bin"),"counts":counts})
def stage(folder,prefix,model,data,size,q,th,reps,mode,cap,seed,table,counts,resume):
    out=folder/(prefix+".csv")
    if not out.exists():
        partial=out.with_suffix(".partial")
        if partial.exists():
            require(resume and not out.with_suffix(".first-partial").exists(),"only one resumption")
            partial.rename(out.with_suffix(".first-partial"))
        call(out,model,data,size,q,th,reps,mode,cap,seed)
    return parse(out,size,q,th,reps,mode,table,counts,cap>0)
def session(folder,i,resume):
    lock=get_lock(folder);meta=read(folder/"test.json")
    require(meta["freeze_sha256"]==digest(folder/"freeze.json") and meta["test_sha256"]==digest(folder/"test.bin"),"test fixture changed")
    require(1<=i<=5,"session 1..5")
    d=folder/f"s{i:02}";d.mkdir(exist_ok=True)
    with (d/".lock").open("a") as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require(not (d/"session.json").exists(),"completed session cannot be repeated")
        attempts=d/"attempts.json";history=read(attempts) if attempts.exists() else []
        require((not history and not resume) or (len(history)==1 and resume),"one explicit resumption only")
        history.append(time.time());write(attempts,history)
        q=lock["chosen"]["q"];th=lock["chosen"]["threshold"];table=lock["learned"]["table"]
        args=(folder/"model.bin",folder/"test.bin")
        primary=stage(d,"primary",*args,64,q,th,7,-1,0,i,table,meta["counts"],resume)
        memory={}
        for arm in ((0,1) if i%2 else (1,0)):
            v=stage(d,f"memory-{arm}",*args,64,q,th,1,arm,0,i,table,meta["counts"],resume)
            require([z["arms"][str(arm)]["pred"] for z in v["batches"]]==[z["arms"][str(arm)]["pred"] for z in primary["batches"]],"standalone prediction parity")
            memory[str(arm)]=v["end"]
        stress={}
        if i==5:
            for size in SIZES:
                stress[str(size)]={}
                for arm in (0,1):
                    stress[str(size)][str(arm)]=stage(d,f"stress-{size}-{arm}",*args,size,q,th,1,arm,15,i,table,meta["counts"],resume)
        obj={"session":i,"freeze_sha256":meta["freeze_sha256"],"test_sha256":meta["test_sha256"],"starts":history,"finished":time.time(),"primary":primary,"summary":summary(primary),"memory":memory,"stress":stress,
             "csv_sha256":{p.name:digest(p) for p in sorted(d.glob("*.csv"))}}
        write(d/"session.json",obj);print("COMPLETE",i,flush=True)
def upper(v,tcrit):
    return st.mean(v)+tcrit*st.stdev(v)/math.sqrt(len(v))
def fingerprint(res):
    return [(z["subject"],z["trial"],z["labels"],{k:(v["pred"],v["mask"],v["group"],v["margin"]) for k,v in z["arms"].items()}) for z in res["batches"]]
def percentile(v,p):
    return sorted(v)[max(0,math.ceil(p*len(v))-1)]
def stress_summary(stress):
    out={}
    for size,arms in stress.items():
        n=min(len(v["batches"]) for v in arms.values());entry={"common_batches":n,"arms":{}}
        for k,v in arms.items():
            z=v["batches"][:n]
            if not z:entry["arms"][k]={"completed":v["end"],"common_rows":0};continue
            rows=sum(len(b["labels"]) for b in z);cpu=[b["arms"][k]["times"]["0"][0] for b in z];wall=[b["arms"][k]["times"]["0"][1] for b in z]
            entry["arms"][k]={"completed":v["end"],"common_rows":rows,"cpu_ns":sum(cpu),"wall_ns":sum(wall),"active_rows_per_sec":rows*1e9/sum(wall),"wall_p50_p95_p99_ns":[percentile(wall,p) for p in (.5,.95,.99)],"expansions":sum(sum(b["arms"][k]["mask"]) for b in z)}
        out[size]=entry
    return out
def analyze(folder):
    lock=get_lock(folder);meta=read(folder/"test.json");sessions=[];finger=None
    require(meta["freeze_sha256"]==digest(folder/"freeze.json"),"freeze hash")
    q=lock["chosen"]["q"];th=lock["chosen"]["threshold"];table=lock["learned"]["table"]
    for i in range(1,6):
        d=folder/f"s{i:02}";s=read(d/"session.json");require(s["session"]==i and s["freeze_sha256"]==meta["freeze_sha256"] and s["test_sha256"]==meta["test_sha256"],"session identity")
        require(all(digest(d/p)==h for p,h in s["csv_sha256"].items()),"CSV hash")
        primary=parse(d/"primary.csv",64,q,th,7,-1,table,meta["counts"]);require(s["primary"]==primary and s["summary"]==summary(primary),"primary summary")
        f=fingerprint(primary);require(finger is None or f==finger,"cross-session prediction mismatch");finger=f
        for arm in (0,1):
            m=parse(d/f"memory-{arm}.csv",64,q,th,1,arm,table,meta["counts"])
            require(m["end"]==s["memory"][str(arm)] and [z["arms"][str(arm)]["pred"] for z in m["batches"]]==[z["arms"][str(arm)]["pred"] for z in primary["batches"]],"standalone mismatch")
        if i==5:
            for size in SIZES:
                for arm in (0,1):
                    require(s["stress"][str(size)][str(arm)]==parse(d/f"stress-{size}-{arm}.csv",size,q,th,1,arm,table,meta["counts"],True),"stress mismatch")
        sessions.append(s)
    sub=sessions[0]["summary"]["subjects"];require(set(map(int,sub))==set(lock["splits"]["test"]),"eight test subjects")
    losses=[100*(v["arms"]["0"]["correct"]-v["arms"]["1"]["correct"])/v["n"] for v in sub.values()]
    ratios=[math.log(s["summary"]["arms"]["1"]["ratio"]) for s in sessions]
    mem=[math.log(s["memory"]["1"]["rss_kib"]/s["memory"]["0"]["rss_kib"]) for s in sessions]
    qual=upper(losses,1.894578605061305);cpu=math.exp(upper(ratios,2.13184678632665));memory=math.exp(upper(mem,2.13184678632665))
    quality=qual<=1;speed=cpu<=.5;ram=memory<=.75
    verdict="ASCENSION" if quality and speed and ram else "PARTIAL ASCENSION" if quality or speed else "LIMIT REACHED"
    obj={"verdict":verdict,"primary_passed":quality and speed,"quality_passed":quality,"cpu_50_passed":speed,"cpu_superiority":cpu<1,"memory_25_passed":ram,"native_standalone_parity":True,"logical_prefix_violations":0,
         "quality_loss_pp":st.mean(losses),"quality_upper95_pp":qual,"cpu_ratio":math.exp(st.mean(ratios)),"cpu_upper95":cpu,"memory_ratio":math.exp(st.mean(mem)),"memory_upper95":memory,
         "subject_losses_pp":losses,"session_cpu_ratios":[math.exp(v) for v in ratios],"session_memory_ratios":[math.exp(v) for v in mem],"rows":sessions[0]["summary"]["n"],"chosen":lock["chosen"],"session_sha256":[digest(folder/f"s{i:02}"/"session.json") for i in range(1,6)],"freeze_sha256":meta["freeze_sha256"],"test_sha256":meta["test_sha256"],
         "summary":sessions[0]["summary"],"stress":stress_summary(sessions[-1]["stress"]),"sessions":[{"session":s["session"],"starts":s["starts"],"finished":s["finished"],"memory":s["memory"]} for s in sessions]}
    write(folder/"omega-final.json",obj);print(json.dumps({k:v for k,v in obj.items() if k not in ("summary","stress","sessions")},indent=2))
def main():
    p=argparse.ArgumentParser();p.add_argument("action",choices=("smoke","freeze","prepare-test","run","analyze"));p.add_argument("--data",type=Path);p.add_argument("--work",type=Path,required=True);p.add_argument("--session",type=int);p.add_argument("--resume",action="store_true");v=p.parse_args()
    folder=v.work.resolve();identity()
    if v.action in ("smoke","freeze","prepare-test"):require(v.data is not None,"--data required")
    if v.action=="smoke":smoke(v.data.resolve(),folder)
    elif v.action=="freeze":freeze(v.data.resolve(),folder)
    elif v.action=="prepare-test":prepare_test(v.data.resolve(),folder)
    elif v.action=="run":require(v.session is not None,"--session required");session(folder,v.session,v.resume)
    else:analyze(folder)
if __name__=="__main__":main()
