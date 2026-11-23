"""A11 scheduler: GEFS frames and L1 cells for the new systems (eras with a named event).
Usage: run_a11.py SYSTEMS(comma) [WORKERS] [THREADS]"""
import os, sys, subprocess, time
from concurrent.futures import ThreadPoolExecutor
import a9_common as A
systems = sys.argv[1].split(","); workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6; threads = sys.argv[3] if len(sys.argv) > 3 else "4"
PY = sys.executable; HERE = A.HERE
env = dict(os.environ, OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
def log(m):
    with open(os.path.join(HERE, "sched_a11.log"), "a") as f: f.write(time.strftime("%H:%M:%S ") + m + "\n")
cells = [(s, e) for s in systems for e in A.events(s)]
def build(c):
    s, e = c
    if os.path.exists(os.path.join(HERE, "frames", f"{s}_{e}_gefs.pkl")): return
    r = subprocess.run([PY, "-W", "ignore", "build_frames_a9.py", s, e, "gefs"], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"frame {s} {e} rc={r.returncode} {r.stderr.strip()[-300:]}")
with ThreadPoolExecutor(6) as ex: list(ex.map(build, cells))
def run(c):
    s, e = c
    if os.path.exists(os.path.join(HERE, "results", f"a9_{s}_{e}_L1_gefs.csv")): return
    t = time.time()
    r = subprocess.run([PY, "-W", "ignore", "run_cell_a9.py", s, e, "L1", "gefs"], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"cell {s} {e} L1 rc={r.returncode} {round(time.time()-t)}s {r.stdout.strip()[-150:]} {r.stderr.strip()[-400:]}")
with ThreadPoolExecutor(workers) as ex: list(ex.map(run, sorted(cells, key=lambda c: -int(c[1]))))
log("ALL DONE")
