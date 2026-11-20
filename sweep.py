#!/usr/bin/env python3
"""Run a sweep of optimizations (objective x polarization x volume fraction) in parallel.

    python sweep.py              # 60x60, 20 runs, ~10 min on 8 cores
    python sweep.py --n 40       # faster, coarser
Each run writes results_sweep/<objective>_<pol>_vf<vf>/viewer.json. Then run build_viewer.py.
"""
import argparse, itertools, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=60)
ap.add_argument("--jobs", type=int, default=8)
ap.add_argument("--objectives", default="energy,eta")
ap.add_argument("--pols", default="+,x")
ap.add_argument("--volfracs", default="0.2,0.3,0.4,0.5,0.6")
args = ap.parse_args()

env = dict(os.environ, OMP_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
runs = list(itertools.product(args.objectives.split(","), args.pols.split(","), args.volfracs.split(",")))


def run(job):
    obj, pol, vf = job
    out = f"results_sweep/{obj}_{'plus' if pol == '+' else 'cross'}_vf{vf}"
    os.makedirs(out, exist_ok=True)
    cmd = [sys.executable, "run_poc.py", "--n", str(args.n), "--objective", obj, "--pol", pol,
           "--volfrac", vf, "--out", out, "--no-plots"]
    with open(os.path.join(out, "run.log"), "w") as log:
        rc = subprocess.call(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
    print(f"{'ok ' if rc == 0 else 'FAIL'} {out}", flush=True)
    return rc


with ThreadPoolExecutor(args.jobs) as ex:
    rcs = list(ex.map(run, runs))
print(f"{rcs.count(0)}/{len(rcs)} runs succeeded")
