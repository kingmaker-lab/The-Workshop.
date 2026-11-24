"""HELIOS: bounded local contention and Linux-observed budget selection."""
import argparse
import json
import math
import os
import platform
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"exp004-ascension"))
from ascension import dataset,calibrate,load_native,pack,run

SEEDS=tuple(range(701,741,2))
SCENARIOS=("QUIET_SUN","SOLAR_WIND","SOLAR_FLARE","CORONA","ECLIPSE")
STRATEGIES=("full","lite","fixed_A3","fixed_native","adaptive_A3","adaptive_native")
BUDGET_NAMES={32:"LIBERTAS",24:"AURORA",16:"HORIZON",8:"ECLIPSE"}
TEMP_LIMIT=80.0

def read_text(path):
    try: return Path(path).read_text()
    except OSError: return ""

def memory():
    vals={}
    for line in read_text("/proc/meminfo").splitlines():
        k,_,v=line.partition(":")
        if k in ("MemAvailable","MemTotal"):
            vals[k]=int(v.split()[0])
    return vals

def temperature():
    vals=[]
    for hw in Path("/sys/class/hwmon").glob("hwmon*"):
        if read_text(hw/"name").strip() not in ("coretemp","k10temp","zenpower"): continue
        for p in hw.glob("temp*_input"):
            try:
                t=float(read_text(p))/1000
                if 0<t<150: vals.append(t)
            except ValueError: pass
    for z in Path("/sys/class/thermal").glob("thermal_zone*"):
        if read_text(z/"type").strip() not in ("x86_pkg_temp","cpu-thermal","cpu_thermal"): continue
        try:
            t=float(read_text(z/"temp"))/1000
            if 0<t<150: vals.append(t)
        except ValueError: pass
    return max(vals,default=None)

def cpu_ticks():
    allowed=os.sched_getaffinity(0)
    total=idle=0
    for line in read_text("/proc/stat").splitlines():
        cols=line.split()
        if not cols or not cols[0].startswith("cpu") or not cols[0][3:].isdigit(): continue
        if int(cols[0][3:]) not in allowed: continue
        v=list(map(int,cols[1:9]))
        if len(v)<8: continue
        total+=sum(v); idle+=v[3]+v[4]
    return total,idle

def psi(kind):
    for line in read_text("/proc/pressure/"+kind).splitlines():
        if line.startswith("some "):
            for field in line.split()[1:]:
                if field.startswith("avg10="): return float(field.split("=")[1])
    return None

def frequency():
    vals=[]
    for cpu in os.sched_getaffinity(0):
        try: vals.append(int(read_text("/sys/devices/system/cpu/cpu%d/cpufreq/scaling_cur_freq"%cpu)))
        except ValueError: pass
    return st.mean(vals) if vals else None

def observe(previous):
    now=cpu_ticks()
    dt=now[0]-previous[0]
    busy=max(0.,min(1.,1-(now[1]-previous[1])/dt)) if dt>0 else None
    m=memory()
    return now,{"cpu_busy":busy,"mem_available_kib":m.get("MemAvailable"),
        "mem_total_kib":m.get("MemTotal"),"cpu_psi_avg10":psi("cpu"),
        "memory_psi_avg10":psi("memory"),"temperature_c":temperature(),
        "frequency_khz":frequency()}

def choose_budget(obs):
    # Declared heuristic; no scenario label or test label supplied.
    busy=obs["cpu_busy"]
    avail=obs["mem_available_kib"]
    total=obs["mem_total_kib"]
    if busy is None or avail is None or not total: return 8
    if avail<256*1024 or avail/total<.10 or (obs["memory_psi_avg10"] or 0)>=5: return 8
    if avail/total<.20: return 16
    if busy>=.75: return 8
    if busy>=.45: return 16
    if busy>=.25: return 24
    return 32

def guard(obs,pressure):
    if obs["mem_available_kib"] is None or obs["mem_available_kib"]<512*1024:
        raise RuntimeError("Safety stop: less than 512 MiB available or unknown")
    t=obs["temperature_c"]
    if t is not None and t>=TEMP_LIMIT: raise RuntimeError("Safety stop: CPU >=80 C")
    if pressure and t is None: raise RuntimeError("Pressure requires readable CPU temperature")

def worker(kind):
    # One low-priority process, at most 4 seconds, no network or privileged changes.
    os.nice(10)
    end=time.monotonic()+4
    buf=bytearray(32*1024*1024) if kind=="CORONA" else bytearray()
    for i in range(0,len(buf),4096): buf[i]=1
    start=time.monotonic()
    x=1
    while time.monotonic()<end:
        if temperature() is None or temperature()>=TEMP_LIMIT: return
        m=memory().get("MemAvailable",0)
        if m<512*1024: return
        duty=.35 if kind=="SOLAR_WIND" else .60
        if kind=="SOLAR_FLARE" and int((time.monotonic()-start)/.12)%2: duty=.10
        stop=time.monotonic()+.04*duty
        while time.monotonic()<stop: x=(1664525*x+1013904223)&0xffffffff
        time.sleep(.04*(1-duty))

def launch(kind):
    return subprocess.Popen([sys.executable,str(Path(__file__).resolve()),"--worker",kind],
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def stop(p):
    if p is None: return
    if p.poll() is None: p.terminate()
    try: p.wait(timeout=1)
    except subprocess.TimeoutExpired: p.kill(); p.wait()

def percentile(xs,q):
    return sorted(xs)[max(0,math.ceil(q*len(xs))-1)]

def phase(seed,rows,thresholds,lib,scenario,pressure):
    # Twelve equally sized batches; rotate strategy order. ECLIPSE releases after six.
    prev=cpu_ticks()
    p=None
    events=[]
    n=len(rows)//12
    try:
        if pressure and scenario!="QUIET_SUN":
            _,obs=observe(prev); guard(obs,True)
            p=launch("SOLAR_WIND" if scenario=="ECLIPSE" else scenario)
            time.sleep(.15)
        for i in range(12):
            if scenario=="ECLIPSE" and i==6: stop(p);p=None
            time.sleep(.05)
            start=time.perf_counter_ns()
            cs=time.process_time_ns()
            prev,obs=observe(prev)
            guard(obs,pressure and p is not None)
            budget=choose_budget(obs)
            observer_ns=time.perf_counter_ns()-start
            observer_cpu=time.process_time_ns()-cs
            block=rows[i*n:(i+1)*n]
            modes=STRATEGIES[(seed+i)%len(STRATEGIES):]+STRATEGIES[:(seed+i)%len(STRATEGIES)]
            results={}
            for mode in modes:
                adaptive=mode.startswith("adaptive")
                b=budget if adaptive else (32 if mode=="full" else 8 if mode=="lite" else 16)
                native="c_full" if mode=="full" else "c_lite" if mode=="lite" else "c_A3" if mode.endswith("A3") else "c_native"
                t0=time.perf_counter_ns(); c0=time.process_time_ns()
                packed=pack(block)
                r=run(native,[(BUDGET_NAMES[b],block,packed)],thresholds,lib)
                elapsed=time.perf_counter_ns()-t0
                cpu=time.process_time_ns()-c0
                results[mode]={"budget":b,"accuracy":r["accuracy"],"mean_terms":r["mean_terms"],
                    "max_prefix_overrun_terms":r["segments"][0]["max_prefix_overrun_terms"],
                    "evaluation_cpu_ns":r["cpu_ns"],"batch_wall_ns":elapsed,
                    "batch_cpu_ns":cpu,"policy_inclusive_wall_ns":elapsed+(observer_ns if adaptive else 0),
                    "policy_inclusive_cpu_ns":cpu+(observer_cpu if adaptive else 0)}
            events.append({"batch":i,"pressure_requested":pressure and p is not None,
                "worker_alive":p is not None and p.poll() is None,"telemetry":obs,
                "observer_wall_ns":observer_ns,"observer_cpu_ns":observer_cpu,"strategies":results})
    finally: stop(p)
    return events

def summarize(runs):
    out={}
    for name in runs[0]["scenarios"]:
        out[name]={}
        for mode in STRATEGIES:
            rows=[e["strategies"][mode] for r in runs for e in r["scenarios"][name]]
            times=[r["policy_inclusive_wall_ns"] for r in rows]
            out[name][mode]={"mean_accuracy":st.mean(r["accuracy"] for r in rows),
                "mean_terms":st.mean(r["mean_terms"] for r in rows),
                "mean_budget":st.mean(r["budget"] for r in rows),
                "mean_cpu_ns":st.mean(r["policy_inclusive_cpu_ns"] for r in rows),
                "p50_wall_ns":percentile(times,.5),"p95_wall_ns":percentile(times,.95),
                "p99_wall_ns":percentile(times,.99),
                "max_prefix_overrun_terms":max(r["max_prefix_overrun_terms"] for r in rows),
                "budget_counts":{str(b):sum(r["budget"]==b for r in rows) for b in BUDGET_NAMES}}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pressure",action="store_true",help="opt in to bounded local pressure")
    p.add_argument("--batch-size",type=int,default=128)
    p.add_argument("--seeds",type=int,default=20)
    p.add_argument("--worker",choices=SCENARIOS[1:],help=argparse.SUPPRESS)
    a=p.parse_args()
    if a.worker: worker(a.worker);return
    if not 32<=a.batch_size<=256 or not 1<=a.seeds<=20: p.error("batch-size 32..256, seeds 1..20")
    _,obs=observe(cpu_ticks());guard(obs,a.pressure)
    lib=load_native(HERE.parent/"exp004-ascension"/"libascension.so")
    names=SCENARIOS if a.pressure else SCENARIOS[:1]
    runs=[]
    for seed in SEEDS[:a.seeds]:
        cal=calibrate(dataset(300000+2*seed,1000))
        rows=dataset(300001+2*seed,12*a.batch_size)
        # Counterbalance scenario order; no pressure scenario label enters policy.
        shift=seed%len(names)
        runs.append({"seed":seed,"scenarios":{name:phase(seed,rows,cal,lib,name,a.pressure)
            for name in names[shift:]+names[:shift]}})
        print("HELIOS seed %d complete"%seed,file=sys.stderr,flush=True)
    revision=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True).stdout.strip()
    print(json.dumps({"experiment":"EXP-005-HELIOS","schema_version":1,"data":"synthetic",
        "pressure_opt_in":a.pressure,"revision":revision,"environment":{"python":platform.python_version(),
        "kernel":platform.release(),"machine":platform.machine(),"affinity_cpu_count":len(os.sched_getaffinity(0))},
        "batch_size":a.batch_size,"runs":runs,"summary":summarize(runs)},indent=2,allow_nan=False))
if __name__=="__main__": main()
