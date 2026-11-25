"""PROMETHEUS: passive observer ablation, HELIOS v0.2. Research only."""
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
from helios import (HERE, dataset, calibrate, load_native, pack, run, cpu_ticks,
                    memory, temperature, psi, frequency, observe, choose_budget,
                    guard, percentile, BUDGET_NAMES)

SEEDS=tuple(range(901,941,2))
MODES=("full_repack","full_cached","fixed_cached","helios_repack",
       "fast_repack","fast_cached")

def sensor_paths():
    paths=[]
    for hw in Path("/sys/class/hwmon").glob("hwmon*"):
        try: name=(hw/"name").read_text().strip()
        except OSError: continue
        if name in ("coretemp","k10temp","zenpower"):
            paths.extend(hw.glob("temp*_input"))
    for z in Path("/sys/class/thermal").glob("thermal_zone*"):
        try: name=(z/"type").read_text().strip()
        except OSError: continue
        if name in ("x86_pkg_temp","cpu-thermal","cpu_thermal"):
            paths.append(z/"temp")
    return tuple(paths)

def cached_temperature(paths):
    vals=[]
    for p in paths:
        try:
            v=float(p.read_text())/1000
            if 0<v<150: vals.append(v)
        except (OSError,ValueError): pass
    # If a known sensor disappears, rediscover rather than trusting stale data.
    return max(vals) if vals and len(vals)==len(paths) else temperature()

def safety_snapshot(paths):
    m=memory()
    o={"mem_available_kib":m.get("MemAvailable"),
       "mem_total_kib":m.get("MemTotal"),"temperature_c":cached_temperature(paths)}
    guard(o,False)
    if paths and o["temperature_c"] is None:
        raise RuntimeError("Safety stop: previously discovered temperature unavailable")
    return o

def target_budget(obs):
    busy=obs.get("cpu_busy")
    avail=obs.get("mem_available_kib")
    total=obs.get("mem_total_kib")
    mp=obs.get("memory_psi_avg10")
    if busy is None or avail is None or not total: return 8
    mem=8 if avail<256*1024 or avail/total<.10 or (mp or 0)>=5 else 16 if avail/total<.20 else 32
    cpu=8 if busy>=.75 else 16 if busy>=.45 else 24 if busy>=.25 else 32
    return min(mem,cpu)

class BudgetPolicy:
    def __init__(self):
        self.budget=8
        self.up=0
    def update(self,target,refreshed):
        if target<self.budget:
            self.budget=target
            self.up=0
        elif target==self.budget:
            self.up=0
        elif refreshed:
            self.up+=1
            if self.up>=2:
                self.budget=min(target,self.budget+8)
                self.up=0
        return self.budget

class FastObserver:
    def __init__(self,paths):
        self.paths=paths
        self.prev=cpu_ticks()
        self.last=None
        self.last_diag=None
        self.interval=.15
        self.policy=BudgetPolicy()
        self.cached={}
    def sample(self):
        safety=safety_snapshot(self.paths)
        now=time.monotonic()
        refresh=self.last is None or now-self.last>=self.interval
        if refresh:
            ticks=cpu_ticks()
            dt=ticks[0]-self.prev[0]
            busy=max(0.,min(1.,1-(ticks[1]-self.prev[1])/dt)) if dt>0 else None
            old=self.cached.get("cpu_busy")
            self.interval=.5 if busy is not None and old is not None and abs(busy-old)<.1 else .15
            self.cached.update(cpu_busy=busy,memory_psi_avg10=psi("memory"))
            self.prev=ticks
            self.last=now
        if self.last_diag is None or now-self.last_diag>=1.:
            self.cached.update(cpu_psi_avg10=psi("cpu"),frequency_khz=frequency())
            self.last_diag=now
        obs={**self.cached,**safety}
        target=target_budget(obs)
        budget=self.policy.update(target,refresh)
        return obs,budget,refresh,now-self.last,now-self.last_diag

def timed(fn):
    w=time.perf_counter_ns();c=time.process_time_ns()
    result=fn()
    return result,time.perf_counter_ns()-w,time.process_time_ns()-c

def phase(seed,thresholds,lib,batch_size,batches):
    # One bounded buffer per batch; no background load, no full dataset retained.
    paths,setup_w,setup_c=timed(sensor_paths)
    oldprev=cpu_ticks()
    fast=FastObserver(paths)
    events=[]
    for i in range(batches):
        time.sleep(.10)
        # Fresh safety check before allocating test rows.
        safety_snapshot(paths)
        rows=dataset(40000000+seed*1000+i,batch_size)
        packed,pw,pc=timed(lambda:pack(rows))
        def old_read():
            nonlocal oldprev
            oldprev,o=observe(oldprev)
            guard(o,False)
            return o,choose_budget(o)
        # Rotate observer order; two observations are close, not simultaneous.
        if i%2:
            (obs,b,refreshed,age,diag_age),fw,fc=timed(fast.sample)
            (old,ob),ow,oc=timed(old_read)
        else:
            (old,ob),ow,oc=timed(old_read)
            (obs,b,refreshed,age,diag_age),fw,fc=timed(fast.sample)
        # Common guard charged to static policies separately. Check each execution.
        results={}
        shift=(seed+i)%len(MODES)
        for mode in MODES[shift:]+MODES[:shift]:
            _,sw,sc=timed(lambda:safety_snapshot(paths))
            is_fast=mode.startswith("fast")
            is_old=mode=="helios_repack"
            cached=mode.endswith("cached")
            budget=b if is_fast else ob if is_old else 16 if mode=="fixed_cached" else 32
            native="c_full" if mode.startswith("full") else "c_native"
            def evaluate():
                buf=packed if cached else pack(rows)
                return run(native,[(BUDGET_NAMES[budget],rows,buf)],thresholds,lib)
            r,w,c=timed(evaluate)
            # Cached buffer construction charged once per independent request;
            # also report the resident-buffer path separately.
            policy_w=fw if is_fast else ow if is_old else 0
            policy_c=fc if is_fast else oc if is_old else 0
            results[mode]={"budget":budget,"accuracy":r["accuracy"],"mean_terms":r["mean_terms"],
                "max_prefix_overrun_terms":r["segments"][0]["max_prefix_overrun_terms"],
                "evaluation_cpu_ns":r["cpu_ns"],"execution_wall_ns":w,"execution_cpu_ns":c,
                "safety_wall_ns":sw,"safety_cpu_ns":sc,
                "policy_wall_ns":policy_w,"policy_cpu_ns":policy_c,
                "charged_pack_cpu_ns":pc if cached else 0,
                "charged_pack_wall_ns":pw if cached else 0,
                "inclusive_cpu_ns":c+sc+policy_c+(pc if cached else 0),
                "inclusive_wall_ns":w+sw+policy_w+(pw if cached else 0),
                "resident_cpu_ns":c+sc+policy_c}
        events.append({"batch":i,"telemetry":obs,"original_telemetry":old,
            "policy_refreshed":refreshed,"policy_age_s":age,"diagnostic_age_s":diag_age,
            "original_observer_cpu_ns":oc,"fast_observer_cpu_ns":fc,
            "original_observer_wall_ns":ow,"fast_observer_wall_ns":fw,
            "pack_cpu_ns":pc,"pack_wall_ns":pw,"strategies":results})
    return {"sensor_setup_cpu_ns":setup_c,"sensor_setup_wall_ns":setup_w,"events":events}

def summarize(runs):
    events=[e for r in runs for e in r["events"]]
    if not events:return None
    old=sum(e["original_observer_cpu_ns"] for e in events)
    new=sum(e["fast_observer_cpu_ns"] for e in events)+sum(r["sensor_setup_cpu_ns"] for r in runs)
    out={"batches":len(events),"original_observer_mean_cpu_ns":old/len(events),
         "fast_observer_amortized_cpu_ns":new/len(events),
         "observer_cpu_reduction":1-new/old if old else None,
         "refreshes":sum(e["policy_refreshed"] for e in events),"strategies":{}}
    for mode in MODES:
        rs=[e["strategies"][mode] for e in events]
        ws=[r["inclusive_wall_ns"] for r in rs]
        out["strategies"][mode]={"mean_accuracy":st.mean(r["accuracy"] for r in rs),
            "mean_terms":st.mean(r["mean_terms"] for r in rs),
            "mean_inclusive_cpu_ns":st.mean(r["inclusive_cpu_ns"] for r in rs),
            "mean_resident_cpu_ns":st.mean(r["resident_cpu_ns"] for r in rs),
            "p50_wall_ns":percentile(ws,.5),"p95_wall_ns":percentile(ws,.95),
            "p99_wall_ns":percentile(ws,.99),
            "max_prefix_overrun_terms":max(r["max_prefix_overrun_terms"] for r in rs),
            "budget_counts":{str(b):sum(r["budget"]==b for r in rs) for b in BUDGET_NAMES}}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seeds",type=int,default=20)
    p.add_argument("--batch-size",type=int,default=64)
    p.add_argument("--batches",type=int,default=24)
    p.add_argument("--observe-only",action="store_true")
    a=p.parse_args()
    if not 1<=a.seeds<=20 or not 32<=a.batch_size<=128 or not 8<=a.batches<=48:
        p.error("seeds 1..20, batch-size 32..128, batches 8..48")
    if a.observe_only:
        m=memory()
        print(json.dumps({"experiment":"PROMETHEUS-PREFLIGHT","mem_available_kib":m.get("MemAvailable"),
            "temperature_c":temperature(),"cpu_psi_avg10":psi("cpu"),"memory_psi_avg10":psi("memory")},indent=2))
        return
    safety_snapshot(sensor_paths())
    lib=load_native(HERE.parent/"exp004-ascension"/"libascension.so")
    runs=[]
    for seed in SEEDS[:a.seeds]:
        safety_snapshot(sensor_paths())
        thresholds=calibrate(dataset(400000+2*seed,1000))
        r=phase(seed,thresholds,lib,a.batch_size,a.batches)
        runs.append({"seed":seed,**r})
        print("PROMETHEUS seed %d complete"%seed,file=sys.stderr,flush=True)
    rev=subprocess.run(["git","rev-parse","HEAD"],cwd=HERE,capture_output=True,text=True).stdout.strip()
    print(json.dumps({"experiment":"EXP-005-HELIOS-PROMETHEUS","schema_version":1,
        "scenario":"PASSIVE_CONTENTION","pressure_opt_in":False,"data":"synthetic",
        "revision":rev,"environment":{"python":platform.python_version(),"kernel":platform.release(),
        "machine":platform.machine(),"affinity_cpu_count":len(os.sched_getaffinity(0))},
        "batch_size":a.batch_size,"batches_per_seed":a.batches,"runs":runs,"summary":summarize(runs)},indent=2,allow_nan=False))
if __name__=="__main__":main()
