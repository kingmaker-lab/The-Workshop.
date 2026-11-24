"""FEATHER: synthetic conditional computation; research only."""
import argparse
import json
import math
import random
import statistics
import time

DIM, CHEAP = 32, 4
SEEDS = (11, 29, 47, 71, 97)
THRESHOLDS = (0., .25, .5, 1., 1.5, 2., 3., 4., 6., 8., math.inf)
WEIGHTS = (1.0,) * CHEAP + (.15,) * (DIM-CHEAP)

def dataset(seed, n):
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        x = [rng.gauss(0, 1) for _ in range(DIM)]
        y = int(sum(a*b for a,b in zip(x, WEIGHTS)) + rng.gauss(0,.35) >= 0)
        rows.append((x,y))
    return rows

def classify(x, mode, threshold=math.inf):
    if mode not in ("full","lite","dynamic"):
        raise ValueError("invalid mode")
    score = sum(x[i]*WEIGHTS[i] for i in range(CHEAP))
    if mode == "lite" or (mode == "dynamic" and abs(score) >= threshold):
        return int(score >= 0), CHEAP
    score += sum(x[i]*WEIGHTS[i] for i in range(CHEAP,DIM))
    return int(score >= 0), DIM

def evaluate(rows, mode, threshold=math.inf):
    correct = ops = early = 0
    start = time.process_time_ns()
    for x,y in rows:
        pred,cost = classify(x,mode,threshold)
        correct += pred == y
        ops += cost
        early += cost == CHEAP
    elapsed = time.process_time_ns()-start
    n = len(rows)
    return {"accuracy":correct/n,"mean_feature_terms":ops/n,
            "early_fraction":early/n,"cpu_ns":elapsed}

def calibrate(rows):
    full = evaluate(rows,"full")
    candidates = [(t,evaluate(rows,"dynamic",t)) for t in THRESHOLDS]
    eligible = [(t,m) for t,m in candidates if m["accuracy"] >= full["accuracy"]-.01]
    return min(eligible,key=lambda tm:(tm[1]["mean_feature_terms"],-tm[1]["accuracy"],tm[0]))[0]

def experiment(seed,n):
    calibration = dataset(seed*2,n)
    test = dataset(seed*2+1,n)
    threshold = calibrate(calibration)
    modes = ("full","lite","dynamic")
    results = {m:[] for m in modes}
    # Warm all paths, then rotate timing order for three repetitions.
    for m in modes:
        evaluate(test,m,threshold)
    for i in range(3):
        for m in modes[i:]+modes[:i]:
            results[m].append(evaluate(test,m,threshold))
    summary = {m:{**rs[0],"cpu_ns":statistics.median(r["cpu_ns"] for r in rs),
                  "cpu_samples_ns":[r["cpu_ns"] for r in rs]} for m,rs in results.items()}
    f,d = summary["full"],summary["dynamic"]
    return {"seed":seed,"threshold":threshold if math.isfinite(threshold) else "never_exit",
            "models":summary,"accuracy_loss_pp":100*(f["accuracy"]-d["accuracy"]),
            "term_reduction_fraction":1-d["mean_feature_terms"]/f["mean_feature_terms"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--samples",type=int,default=3000)
    a=p.parse_args()
    if not 100 <= a.samples <= 10000:
        p.error("samples must be 100..10000")
    runs=[experiment(s,a.samples) for s in SEEDS]
    print(json.dumps({"experiment":"EXP-002-FEATHER","data":"synthetic",
                      "samples_per_split":a.samples,"runs":runs,
                      "mean_accuracy_loss_pp":statistics.mean(r["accuracy_loss_pp"] for r in runs),
                      "mean_term_reduction_fraction":statistics.mean(r["term_reduction_fraction"] for r in runs)},
                     indent=2,allow_nan=False))
if __name__=="__main__":
    main()
