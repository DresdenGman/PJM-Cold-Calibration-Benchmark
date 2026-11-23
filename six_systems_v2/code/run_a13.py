"""A13 scheduler: designs D1 and D2 for L1/GEFS on the 13 PJM/MISO events. Usage: run_a13.py [WORKERS] [THREADS]"""
import os, sys, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import a9_common as A
workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6; threads = sys.argv[2] if len(sys.argv) > 2 else "4"
PY = sys.executable; HERE = A.HERE
def log(m):
    with open(os.path.join(HERE, "sched_a13.log"), "a") as f: f.write(time.strftime("%H:%M:%S ") + m + "\n")
DESIGNS = sys.argv[3].split(",") if len(sys.argv) > 3 else ["D1", "D2"]
jobs = [(d, s, e) for d in DESIGNS for s in ["pjm", "miso"] for e in A.ERAS[s]]
def run(j):
    d, s, e = j
    if os.path.exists(os.path.join(HERE, "results", f"a13{d}_{s}_{e}_L1_gefs.csv")): return
    env = dict(os.environ, DESIGN=d, OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    t = time.time(); r = subprocess.run([PY, "-W", "ignore", "run_cell_a9.py", s, e, "L1", "gefs"], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"{d} {s} {e} rc={r.returncode} {round(time.time()-t)}s {r.stdout.strip()[-120:]} {r.stderr.strip()[-400:]}")
with ThreadPoolExecutor(workers) as ex: list(ex.map(run, sorted(jobs, key=lambda j: (j[0], -int(j[2])))))
log("ALL DONE")
