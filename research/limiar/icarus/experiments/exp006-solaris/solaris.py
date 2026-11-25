"""SOLARIS paired resident binary-input benchmark. Research only."""
import argparse
import ctypes as ct
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
sys.path.insert(0,str(HERE.parent/"exp005-helios"))
from prometheus import (dataset,calibrate,load_native,pack,run,FastObserver,sensor_paths,
    safety_snapshot,timed,percentile,BUDGET_NAMES)
from helios import observe,guard,cpu_ticks,choose_budget
SEEDS=tuple(range(1101,1161,2))
MODES=("helios","prometheus","solar_full","solar_fixed","solar_reset","solar_persistent")
class Result(ct.Structure):
    _fields_=[(k,ct.c_uint64) for k in ("correct","terms","forced","over","observer_cpu_ns","cpu_ns","wall_ns")]+[(k,ct.c_int64) for k in ("available_kib","temp_milli")]+[(k,ct.c_double) for k in ("busy","mem_psi","cpu_psi","freq_khz","policy_age")]+[(k,ct.c_int) for k in ("budget","refreshed","ticks")]
def load():
    lib=ct.CDLL(str(HERE/"libsolaris.so"))
    lib.solar_new.argtypes=[ct.POINTER(ct.c_double)]
    lib.solar_new.restype=ct.c_void_p
    lib.solar_free.argtypes=[ct.c_void_p];lib.solar_free.restype=None
    lib.solar_step.argtypes=[ct.c_void_p,ct.c_void_p,ct.c_size_t,ct.c_size_t,ct.c_int,ct.POINTER(Result)]
    lib.solar_step.restype=ct.c_int
    lib.solar_target.argtypes=[ct.c_double,ct.c_int64,ct.c_int64,ct.c_double]
    lib.solar_target.restype=ct.c_int
    return lib
def encode(rows):
    n=len(rows)
    return struct.pack("="+str(n*32)+"d",*(v for x,y in rows for v in x))+bytes(y for x,y in rows)
def decode(data,n):
    vals=struct.unpack_from("="+str(n*32)+"d",data)
    ys=data[n*256:]
    if len(ys)!=n or any(y>1 for y in ys) or not all(math.isfinite(v) for v in vals):raise ValueError("invalid batch")
    return [(vals[i*32:(i+1)*32],y) for i,y in enumerate(ys)]
def step(lib,state,data,n,mode):
    # Binary bytes already exist for both baselines; ctypes pointer overhead included by outer timer.
    r=Result()
    status=lib.solar_step(state,ct.c_char_p(data),len(data),n,mode,ct.byref(r))
    if status:raise RuntimeError("SOLARIS safety/input stop "+str(status))
    return {k:getattr(r,k) for k,_ in Result._fields_}
def experiment(seed,n,batches,lib,asc):
    safety_snapshot(sensor_paths())
    th=calibrate(dataset(500000+2*seed,1000))
    th={b:min(12.,v) for b,v in th.items()}
    thresholds=(ct.c_double*4)(*(th[b] for b in (8,16,24,32)))
    states={};setup={};events=[]
    try:
        paths,_,hc=timed(sensor_paths)
        prev,_,pc=timed(cpu_ticks)
        setup["helios"]=hc+pc
        def make_fast():
            return FastObserver(sensor_paths())
        fast,_,setup["prometheus"]=timed(make_fast)
        for mode in MODES[2:]:
            state,_,cost=timed(lambda:lib.solar_new(thresholds))
            if not state:raise RuntimeError("SOLARIS initialization safety stop")
            states[mode]=state;setup[mode]=cost
        for i in range(batches):
            time.sleep(.10)
            safety_snapshot(paths)
            data=encode(dataset(50000000+seed*1000+i,n))
            shift=(seed+i)%len(MODES);rs={}
            for mode in MODES[shift:]+MODES[:shift]:
                if mode in states:
                    r,w,c=timed(lambda:step(lib,states[mode],data,n,MODES.index(mode)-2))
                    r.update(accuracy=r["correct"]/n,mean_terms=r["terms"]/n,total_cpu_ns=c,total_wall_ns=w)
                else:
                    def baseline():
                        nonlocal prev
                        t=time.process_time_ns()
                        if mode=="helios":
                            prev,o=observe(prev);guard(o,False);b=choose_budget(o)
                        else:
                            o,b,*_=fast.sample()
                        obs_cpu=time.process_time_ns()-t
                        safety_snapshot(paths)
                        rows=decode(data,n)
                        a=run("c_native",[(BUDGET_NAMES[b],rows,pack(rows))],th,asc)
                        return {"accuracy":a["accuracy"],"mean_terms":a["mean_terms"],"budget":b,
                            "over":a["segments"][0]["max_prefix_overrun_terms"],"observer_cpu_ns":obs_cpu,"telemetry":o}
                    r,w,c=timed(baseline);r.update(total_cpu_ns=c,total_wall_ns=w)
                rs[mode]=r
            events.append({"batch":i,"strategies":rs})
    finally:
        for state in states.values():lib.solar_free(state)
    return {"seed":seed,"setup_cpu_ns":setup,"events":events}
def summarize(runs,n):
    count=sum(len(r["events"]) for r in runs);out={}
    for m in MODES:
        rs=[e["strategies"][m] for r in runs for e in r["events"]]
        setup=sum(r["setup_cpu_ns"][m] for r in runs)
        cpu=sum(r["total_cpu_ns"] for r in rs)
        wall=[r["total_wall_ns"] for r in rs]
        out[m]={"accuracy":st.mean(r["accuracy"] for r in rs),"mean_terms":st.mean(r["mean_terms"] for r in rs),
            "amortized_cpu_ns":(cpu+setup)/count,"observer_amortized_cpu_ns":(sum(r["observer_cpu_ns"] for r in rs)+setup)/count,
            "p50_ns":percentile(wall,.5),"p95_ns":percentile(wall,.95),"p99_ns":percentile(wall,.99),
            "active_samples_per_second":n*count/(sum(wall)/1e9),"max_prefix_overrun":max(r["over"] for r in rs),
            "budget_counts":{str(b):sum(r["budget"]==b for r in rs) for b in (8,16,24,32)}}
    for m in MODES[2:]:
        v=out[m]
        v["observer_reduction_vs_helios"]=1-v["observer_amortized_cpu_ns"]/out["helios"]["observer_amortized_cpu_ns"]
        v["cpu_reduction_vs_prometheus"]=1-v["amortized_cpu_ns"]/out["prometheus"]["amortized_cpu_ns"]
        v["accuracy_loss_pp_vs_full"]=100*(out["solar_full"]["accuracy"]-v["accuracy"])
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=30);p.add_argument("--batch-size",type=int,default=64)
    p.add_argument("--batches",type=int,default=24);p.add_argument("--compiler-info",default="not recorded")
    p.add_argument("--fixture",type=Path,help="write a small native CLI input and exit")
    a=p.parse_args()
    if not 1<=a.seeds<=30 or not 32<=a.batch_size<=256 or not 8<=a.batches<=48:p.error("invalid bounds")
    if sys.byteorder!="little" or struct.calcsize("d")!=8:p.error("requires little-endian binary64")
    safety_snapshot(sensor_paths())
    if a.fixture:
        th=calibrate(dataset(502202,1000))
        with a.fixture.open("xb") as f:
            f.write(struct.pack("=4d",*(min(12.,th[b]) for b in (8,16,24,32))))
            for i in range(a.batches):f.write(encode(dataset(51101000+i,a.batch_size)))
        return
    lib=load();asc=load_native(HERE.parent/"exp004-ascension"/"libascension.so")
    runs=[]
    for seed in SEEDS[:a.seeds]:
        runs.append(experiment(seed,a.batch_size,a.batches,lib,asc))
        print("SOLARIS seed %d complete"%seed,file=sys.stderr,flush=True)
    rev=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True).stdout.strip()
    print(json.dumps({"experiment":"EXP-006-SOLARIS","schema_version":1,"revision":rev,"data":"synthetic",
        "compiler_info":a.compiler_info,"environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
        "batch_size":a.batch_size,"batches_per_seed":a.batches,"process_peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "runs":runs,"summary":summarize(runs,a.batch_size)},indent=2,allow_nan=False))
if __name__=="__main__":main()
