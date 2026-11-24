"""EXP-00X ICARO. Locked final synthetic benchmark; no artificial load."""
import argparse
import ctypes as ct
import hashlib
import json
import math
import platform
import resource
import statistics as st
import struct
import subprocess
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"exp006-solaris"))
import solaris as sol
from prometheus import dataset,calibrate,load_native,pack,run,FastObserver,sensor_paths,safety_snapshot,timed,percentile,BUDGET_NAMES
from helios import observe,guard,cpu_ticks,choose_budget
SEEDS=tuple(range(1301,1361,2))
MODES=("helios","prometheus","solar_full","solar_fixed","solar_reset","solar_persistent","icaro")
REPLAY=("reset","persistent","rank","rank_reset_cost","rank_persistent_cost")
# Announced budgets repeat every eight batches; not simulated physical pressure.
SCHEDULE=(8,8,16,16,24,24,32,32)*3
class R(ct.Structure):
    _fields_=[(k,ct.c_uint64) for k in ("correct","terms","forced","over")]
def load():
    lib=ct.CDLL(str(HERE/"libicaro.so"))
    lib.solar_new.argtypes=[ct.POINTER(ct.c_double)];lib.solar_new.restype=ct.c_void_p
    lib.solar_free.argtypes=[ct.c_void_p];lib.solar_free.restype=None
    lib.solar_step.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_size_t,ct.c_int,ct.POINTER(sol.Result)]
    lib.solar_step.restype=ct.c_int
    lib.icaro_step.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_size_t,ct.POINTER(sol.Result)]
    lib.icaro_step.restype=ct.c_int
    lib.icaro_replay_new.argtypes=[ct.POINTER(ct.c_double)];lib.icaro_replay_new.restype=ct.c_void_p
    lib.icaro_replay.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_size_t,ct.c_int,ct.c_int,ct.c_int,ct.POINTER(R)]
    lib.icaro_replay.restype=ct.c_int
    return lib
def native_step(lib,state,data,n):
    r=sol.Result();rc=lib.icaro_step(state,ct.c_char_p(data),len(data),n,ct.byref(r))
    if rc:raise RuntimeError("ICARO stop "+str(rc))
    return {k:getattr(r,k) for k,_ in sol.Result._fields_}
def replay(lib,state,data,n,b,mode,cap=-1):
    r=R();rc=lib.icaro_replay(state,ct.c_char_p(data),len(data),n,b,mode,cap,ct.byref(r))
    if rc:raise RuntimeError("replay failed "+str(rc))
    return {k:getattr(r,k) for k,_ in R._fields_}
def thresholds(seed):
    return {b:min(12.,v) for b,v in calibrate(dataset(600000+2*seed,1000)).items()}
def batch(seed,i,n):
    return sol.encode(dataset(60000000+seed*1000+i,n))
def trial(seed,n,batches,lib,asc):
    th=thresholds(seed);arr=(ct.c_double*4)(*(th[b] for b in (8,16,24,32)))
    paths=sensor_paths();safety_snapshot(paths)
    states={};offline={};setup={};events=[]
    try:
        def old_init():return sensor_paths(),cpu_ticks()
        (old_paths,prev),_,setup["helios"]=timed(old_init)
        fast,_,setup["prometheus"]=timed(lambda:FastObserver(sensor_paths()))
        for m in MODES[2:]:
            state,_,cost=timed(lambda:lib.solar_new(arr))
            if not state:raise RuntimeError("native safety preflight failed")
            states[m]=state;setup[m]=cost
        for name in ("live","scheduled"):
            s=lib.icaro_replay_new(arr)
            if not s:raise RuntimeError("replay allocation failed")
            offline[name]=s
        for i in range(batches):
            time.sleep(.10);safety_snapshot(paths)
            data=batch(seed,i,n);rs={}
            shift=(seed+i)%len(MODES)
            for m in MODES[shift:]+MODES[:shift]:
                if m in states:
                    if m=="icaro":r,w,c=timed(lambda:native_step(lib,states[m],data,n))
                    else:r,w,c=timed(lambda:sol.step(lib,states[m],data,n,MODES.index(m)-2))
                    r.update(accuracy=r["correct"]/n,mean_terms=r["terms"]/n,total_cpu_ns=c,total_wall_ns=w)
                else:
                    def baseline():
                        nonlocal prev
                        t=time.process_time_ns()
                        if m=="helios":
                            prev,o=observe(prev);guard(o,False);b=choose_budget(o)
                        else:o,b,*_=fast.sample()
                        obs=time.process_time_ns()-t
                        safety_snapshot(old_paths if m=="helios" else paths)
                        rows=sol.decode(data,n)
                        a=run("c_native",[(BUDGET_NAMES[b],rows,pack(rows))],th,asc)
                        return {"accuracy":a["accuracy"],"mean_terms":a["mean_terms"],"budget":b,"over":a["segments"][0]["max_prefix_overrun_terms"],"observer_cpu_ns":obs,"telemetry":o}
                    r,w,c=timed(baseline);r.update(total_cpu_ns=c,total_wall_ns=w)
                rs[m]=r
            matches={}
            for name,b in (("live",rs["icaro"]["budget"]),("scheduled",SCHEDULE[i%len(SCHEDULE)])):
                safety_snapshot(paths)
                s=offline[name]
                a=replay(lib,s,data,n,b,0);p=replay(lib,s,data,n,b,1)
                rank=replay(lib,s,data,n,b,2)
                ra=replay(lib,s,data,n,b,3,(a["terms"]-4*n)//28)
                rp=replay(lib,s,data,n,b,3,(p["terms"]-4*n)//28)
                if ra["terms"]!=a["terms"] or rp["terms"]!=p["terms"] or any(x["over"] for x in (a,p,rank,ra,rp)):
                    raise RuntimeError("matched replay invariant violated")
                if name=="live" and (rank["correct"],rank["terms"])!=(rs["icaro"]["correct"],rs["icaro"]["terms"]):
                    raise RuntimeError("live/replay rank mismatch")
                matches[name]={"budget":b,"reset":a,"persistent":p,"rank":rank,"rank_reset_cost":ra,"rank_persistent_cost":rp}
            events.append({"batch":i,"input_sha256":hashlib.sha256(data).hexdigest(),"strategies":rs,"matched":matches})
    finally:
        for s in (*states.values(),*offline.values()):lib.solar_free(s)
    return {"seed":seed,"thresholds":th,"setup_cpu_ns":setup,"events":events}
def summary(runs,n):
    # Use identical SOLARIS summary definitions for all live modes.
    old=sol.MODES
    try:
        sol.MODES=MODES
        live=sol.summarize(runs,n)
    finally:sol.MODES=old
    ev=[e for r in runs for e in r["events"]];re={}
    for name in ("live","scheduled"):
        re[name]={}
        for b in (0,8,16,24,32):
            rows=[e["matched"][name] for e in ev if not b or e["matched"][name]["budget"]==b]
            if not rows:continue
            re[name][str(b or "all")]={m:{"accuracy":sum(r[m]["correct"] for r in rows)/(n*len(rows)),
                 "mean_terms":sum(r[m]["terms"] for r in rows)/(n*len(rows)),
                 "max_prefix_overrun":max(r[m]["over"] for r in rows),"batches":len(rows)} for m in REPLAY}
    v=live["icaro"]
    seed_losses=[100*st.mean(e["strategies"]["solar_full"]["accuracy"]-e["strategies"]["icaro"]["accuracy"] for e in r["events"]) for r in runs]
    criteria={"observer_ge_90pct":v["observer_reduction_vs_helios"]>=.9,
        "cpu_ge_50pct":v["cpu_reduction_vs_prometheus"]>=.5,
        "loss_le_1pp":v["accuracy_loss_pp_vs_full"]<=1.,
        "no_prefix_violation":all(s["max_prefix_overrun"]==0 for s in live.values()),
        "30_seeds":len(runs)==30}
    return {"live":live,"matched":re,"seed_accuracy_loss_pp":seed_losses,"criteria":criteria,
        "all_predeclared_criteria_met":all(criteria.values())}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--smoke",action="store_true",help="one separate pilot seed, excluded from final")
    p.add_argument("--compiler-info",default="not recorded")
    p.add_argument("--fixture",type=Path)
    a=p.parse_args()
    if sys.byteorder!="little" or struct.calcsize("d")!=8:p.error("requires little-endian binary64")
    safety_snapshot(sensor_paths())
    if a.fixture:
        with a.fixture.open("xb") as f:
            th=thresholds(1299);f.write(struct.pack("=4d",*(th[b] for b in (8,16,24,32))))
            for i in range(24):f.write(batch(1299,i,64))
        return
    lib=load();asc=load_native(HERE.parent/"exp004-ascension"/"libascension.so")
    seeds=(1299,) if a.smoke else SEEDS
    runs=[]
    for seed in seeds:
        runs.append(trial(seed,64,24,lib,asc))
        print("ICARO seed %d complete"%seed,file=sys.stderr,flush=True)
    rev=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True).stdout.strip()
    dirty=subprocess.run(["git","status","--porcelain","--untracked-files=no"],cwd=HERE,capture_output=True,text=True).stdout.strip()
    print(json.dumps({"experiment":"EXP-00X-ICARO","schema_version":1,"revision":rev,"tracked_tree_dirty":bool(dirty),
      "data":"synthetic","pilot":a.smoke,"compiler_info":a.compiler_info,"environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
      "batch_size":64,"batches_per_seed":24,"process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "runs":runs,"summary":summary(runs,64)},indent=2,allow_nan=False))
if __name__=="__main__":main()
