"""ASCENSION: paired architecture/language ablation; research only."""
import argparse
import ctypes as ct
import json
import math
import platform
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"exp003-daedalus"))
from daedalus import dataset,calibrate,margin,finish,evaluate,REGIMES

SEEDS=(251,263,277,293,307,311,331,347,359,373,389,401,419,431,443,457,467,479,491,503)
PY_MODES=("py_full","py_lite","py_guarded","A1","A2","A3","A4")
C_MODES={"c_full":0,"c_lite":1,"c_guarded":2,"c_A1":3,"c_A3":4,"c_native":5}
MODES=PY_MODES+tuple(C_MODES)

class Result(ct.Structure):
    _fields_=[(k,ct.c_uint64) for k in ("correct","terms","forced","over")]

def load_native(path):
    lib=ct.CDLL(str(Path(path).resolve()))
    lib.asc_run.argtypes=[ct.POINTER(ct.c_double),ct.POINTER(ct.c_uint8),
        ct.c_size_t,ct.c_int,ct.c_double,ct.c_int,ct.POINTER(Result)]
    lib.asc_run.restype=ct.c_int
    return lib

def pack(rows):
    return ((ct.c_double*(32*len(rows)))(*(v for x,y in rows for v in x)),
            (ct.c_uint8*len(rows))(*(y for x,y in rows)))

def record(name,n,correct,terms,forced,over):
    b=REGIMES[name]
    return {"regime":name,"samples":n,"budget":b,"correct":correct,"terms":terms,
            "forced_lite":forced,"max_prefix_overrun_terms":over,
            "relative_budget_error":(terms-n*b)/(n*b)}

def python_segment(rows,name,t,mode):
    b=REGIMES[name]
    n=len(rows)
    t=min(t,12.)
    ticks=round(t*700)
    credit=correct=terms=forced=over=err=0
    if mode=="A4" and b==32:
        correct=sum(int(finish(x,margin(x))>=0)==y for x,y in rows)
        return record(name,n,correct,32*n,0,0)
    for i,(x,y) in enumerate(rows,1):
        s=margin(x)
        credit+=b-4
        wants=b==32 or (abs(s)<t if mode=="A2" else abs(s)*700<ticks)
        expand=wants and credit>=28
        if expand:
            credit-=28
            s=finish(x,s)
        elif wants:
            forced+=1
        cost=32 if expand else 4
        terms+=cost
        correct+=int(s>=0)==y
        over=max(over,terms-i*b)
        if b!=32:
            if mode=="A2":
                err+=b-cost
                if i%16==0:
                    t=min(12.,max(0.,t+.12*err/28))
                    err=0
            else:
                err+=3*(b-cost)
                if mode=="A3" or i%16==0:
                    ticks=min(8400,max(0,ticks+err))
                    err=0
    return record(name,n,correct,terms,forced,over)

def run(mode,segments,thresholds,lib):
    start=time.process_time_ns()
    records=[]
    for name,rows,packed in segments:
        b=REGIMES[name]
        t=thresholds[b]
        if mode in C_MODES:
            r=Result()
            if lib.asc_run(*packed,len(rows),b,t,C_MODES[mode],ct.byref(r)):
                raise RuntimeError("native kernel failed")
            s=record(name,len(rows),r.correct,r.terms,r.forced,r.over)
        elif mode in ("A2","A3","A4"):
            s=python_segment(rows,name,t,mode)
        else:
            old={"py_full":"full","py_lite":"lite","py_guarded":"fixed_guarded","A1":"adaptive"}[mode]
            z=evaluate(rows,[(name,len(rows))],old,thresholds)["segments"][0]
            s=record(name,len(rows),z["correct"],z["terms"],z["forced_lite"],z["max_prefix_overrun_terms"])
        records.append(s)
    cpu=time.process_time_ns()-start
    n=sum(s["samples"] for s in records)
    return {"accuracy":sum(s["correct"] for s in records)/n,
            "mean_terms":sum(s["terms"] for s in records)/n,"cpu_ns":cpu,"segments":records}

def experiment(seed,n,lib):
    thresholds=calibrate(dataset(200000+2*seed,n))
    rows=dataset(200001+2*seed,4*n)
    whole=pack(rows)
    schedules={k:[(k,rows,whole)] for k in REGIMES}
    schedules["VARIABLE"]=[]
    for i,k in enumerate(("AURORA","ECLIPSE","LIBERTAS","HORIZON")):
        seg=rows[i*n:(i+1)*n]
        schedules["VARIABLE"].append((k,seg,pack(seg)))
    out={}
    for scenario,segments in schedules.items():
        runs={m:[] for m in MODES}
        for m in MODES: run(m,segments,thresholds,lib)
        for i in range(5):
            shift=(seed+i*3)%len(MODES)
            for m in MODES[shift:]+MODES[:shift]:
                runs[m].append(run(m,segments,thresholds,lib))
        out[scenario]={}
        for m,rs in runs.items():
            if any(r["segments"]!=rs[0]["segments"] for r in rs):
                raise RuntimeError("non-deterministic metrics")
            out[scenario][m]={**rs[0],"cpu_ns":st.median(r["cpu_ns"] for r in rs),
                              "cpu_samples_ns":[r["cpu_ns"] for r in rs]}
    return {"seed":seed,"scenarios":out,
            "thresholds":{str(k):v if math.isfinite(v) else "never_exit" for k,v in thresholds.items()}}

def summary(runs):
    out={}
    for scenario in runs[0]["scenarios"]:
        out[scenario]={}
        for m in MODES:
            rs=[r["scenarios"][scenario][m] for r in runs]
            refs=[r["scenarios"][scenario]["A1"] for r in runs]
            seg=[s for r in rs for s in r["segments"]]
            out[scenario][m]={"mean_accuracy":st.mean(r["accuracy"] for r in rs),
                "mean_terms":st.mean(r["mean_terms"] for r in rs),
                "mean_cpu_ns":st.mean(r["cpu_ns"] for r in rs),
                "mean_paired_cpu_reduction_vs_A1":st.mean(1-r["cpu_ns"]/a["cpu_ns"] for r,a in zip(rs,refs)),
                "mean_accuracy_loss_pp_vs_A1":100*st.mean(a["accuracy"]-r["accuracy"] for r,a in zip(rs,refs)),
                "mean_abs_budget_error":st.mean(abs(s["relative_budget_error"]) for s in seg),
                "max_prefix_overrun_terms":max(s["max_prefix_overrun_terms"] for s in seg),
                "segments_within_1pct":sum(abs(s["relative_budget_error"])<=.01 for s in seg),
                "segment_count":len(seg)}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--samples",type=int,default=1000)
    p.add_argument("--library",default=str(HERE/"libascension.so"))
    p.add_argument("--compiler-info",default="not recorded")
    a=p.parse_args()
    if not 100<=a.samples<=5000: p.error("samples must be 100..5000")
    lib=load_native(a.library)
    try:
        rev=subprocess.check_output(["git","rev-parse","HEAD"],cwd=HERE,text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError): rev=None
    runs=[experiment(s,a.samples,lib) for s in SEEDS]
    print(json.dumps({"experiment":"EXP-004-ASCENSION","schema_version":1,
        "data":"synthetic","revision":rev,"compiler_info":a.compiler_info,
        "environment":{"python":platform.python_version(),"kernel":platform.release(),"machine":platform.machine()},
        "samples_per_regime":a.samples,"runs":runs,"summary":summary(runs)},indent=2,allow_nan=False))
if __name__=="__main__": main()
