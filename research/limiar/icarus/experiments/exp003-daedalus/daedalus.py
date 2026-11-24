"""DAEDALUS: causal conditional computation under feature-term budgets."""
import argparse
import json
import math
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "exp002-feather"))
from feather import dataset, DIM, CHEAP, WEIGHTS, THRESHOLDS

SEEDS = (11, 29, 47, 71, 97, 113, 137, 163, 191, 223)
REGIMES = {"LIBERTAS":32, "AURORA":24, "HORIZON":16, "ECLIPSE":8}
MODES = ("full", "lite", "fixed", "fixed_guarded", "adaptive")
EXTRA = DIM - CHEAP

def margin(x):
    return sum(x[i]*WEIGHTS[i] for i in range(CHEAP))

def finish(x, score):
    return score + sum(x[i]*WEIGHTS[i] for i in range(CHEAP,DIM))

def calibrate(rows):
    # Calibration only. Choose best accuracy under each mean budget.
    stats = []
    for t in THRESHOLDS:
        correct = cost = 0
        for x,y in rows:
            s = margin(x)
            c = CHEAP
            if abs(s) < t:
                s = finish(x,s)
                c = DIM
            correct += int(s >= 0) == y
            cost += c
        stats.append((t,correct,cost))
    return {b:max((r for r in stats if r[2] <= b*len(rows)),
                  key=lambda r:(r[1],r[2],-r[0]))[0] for b in REGIMES.values()}

class Controller:
    def __init__(self, budget, threshold, adaptive):
        self.budget = budget
        self.credit = 0
        self.threshold = min(threshold, 12.)
        self.adaptive = adaptive
        self.actual = 0
        self.count = 0
    def decide(self, score):
        self.credit += self.budget - CHEAP
        wants = self.budget == DIM or abs(score) < self.threshold
        expand = wants and self.credit >= EXTRA
        if expand:
            self.credit -= EXTRA
        cost = DIM if expand else CHEAP
        self.actual += cost
        self.count += 1
        if self.adaptive and self.budget < DIM:
            # bounded integral feedback; no labels or future samples
            self.threshold = min(12., max(0., self.threshold + .12*(self.budget-cost)/EXTRA))
        return expand, wants and not expand

def evaluate(rows, schedule, mode, thresholds):
    if mode not in MODES or sum(n for _,n in schedule) != len(rows):
        raise ValueError("invalid schedule or mode")
    offset = 0
    segments = []
    total_start = time.process_time_ns()
    for name,n in schedule:
        budget = REGIMES[name]
        t = thresholds[budget]
        ctrl = Controller(budget,t,mode=="adaptive")
        correct = terms = forced = early = 0
        max_over = 0
        start = time.process_time_ns()
        for j in range(n):
            x,y = rows[offset+j]
            s = margin(x)
            if mode == "full":
                expand = True
            elif mode == "lite":
                expand = False
            elif mode == "fixed":
                expand = abs(s) < t
            else:
                expand, denied = ctrl.decide(s)
                forced += denied
            cost = DIM if expand else CHEAP
            if expand:
                s = finish(x,s)
            correct += int(s >= 0) == y
            early += not expand
            terms += cost
            max_over = max(max_over,terms-(j+1)*budget)
        elapsed = time.process_time_ns()-start
        segments.append({"regime":name,"samples":n,"budget":budget,"correct":correct,
                         "accuracy":correct/n,"terms":terms,"mean_terms":terms/n,
                         "relative_budget_error":(terms-n*budget)/(n*budget),
                         "max_prefix_overrun_terms":max_over,"early_fraction":early/n,
                         "forced_lite":forced,"cpu_ns":elapsed,
                         "final_threshold":ctrl.threshold if mode in ("adaptive","fixed_guarded") else None})
        offset += n
    n = len(rows)
    return {"accuracy":sum(s["correct"] for s in segments)/n,
            "mean_terms":sum(s["terms"] for s in segments)/n,
            "cpu_ns":time.process_time_ns()-total_start,"segments":segments}

def experiment(seed,n):
    # New seeds via namespace, disjoint from FEATHER calibration and holdout.
    cal=dataset(100000+2*seed,n)
    thresholds=calibrate(cal)
    rows=dataset(100001+2*seed,4*n)
    schedules={name:[(name,4*n)] for name in REGIMES}
    schedules["VARIABLE"]=[(k,n) for k in ("AURORA","ECLIPSE","LIBERTAS","HORIZON")]
    out={}
    for name,schedule in schedules.items():
        out[name]={}
        for mode in MODES:
            evaluate(rows,schedule,mode,thresholds) # warmup
            out[name][mode]=[]
        for i in range(3):
            for mode in MODES[i:]+MODES[:i]:
                out[name][mode].append(evaluate(rows,schedule,mode,thresholds))
        for mode,runs in out[name].items():
            out[name][mode]={**runs[0],"cpu_ns":statistics.median(r["cpu_ns"] for r in runs),
                             "cpu_samples_ns":[r["cpu_ns"] for r in runs]}
    return {"seed":seed,"thresholds":{str(k):v if math.isfinite(v) else "never_exit" for k,v in thresholds.items()},
            "scenarios":out}

def summarize(runs):
    out={}
    for scenario in runs[0]["scenarios"]:
        out[scenario]={}
        for mode in MODES:
            rs=[r["scenarios"][scenario][mode] for r in runs]
            seg=[s for r in rs for s in r["segments"]]
            out[scenario][mode]={"mean_accuracy":statistics.mean(r["accuracy"] for r in rs),
                "mean_terms":statistics.mean(r["mean_terms"] for r in rs),
                "mean_cpu_ns":statistics.mean(r["cpu_ns"] for r in rs),
                "mean_absolute_segment_budget_error":statistics.mean(abs(s["relative_budget_error"]) for s in seg),
                "max_prefix_overrun_terms":max(s["max_prefix_overrun_terms"] for s in seg),
                "segments_within_5pct":sum(abs(s["relative_budget_error"])<=.05 for s in seg),
                "segment_count":len(seg)}
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--samples",type=int,default=1000,help="samples per variable regime; calibration uses same count")
    a=p.parse_args()
    if not 100<=a.samples<=5000:
        p.error("samples must be 100..5000")
    try:
        revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=Path(__file__).parent,
                                         text=True,stderr=subprocess.DEVNULL).strip()
    except (OSError,subprocess.CalledProcessError):
        revision=None
    runs=[experiment(s,a.samples) for s in SEEDS]
    print(json.dumps({"experiment":"EXP-003-DAEDALUS","schema_version":1,"data":"synthetic",
                      "revision":revision,"environment":{"python":platform.python_version(),
                      "kernel":platform.release(),"machine":platform.machine()},
                      "samples_per_regime":a.samples,"runs":runs,"summary":summarize(runs)},
                     indent=2,allow_nan=False))
if __name__=="__main__":
    main()
