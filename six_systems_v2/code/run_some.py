"""A9 scheduler for the compute machine: build frames, then run every cell (fit + calibrators)
with a pool of worker processes. Usage: run_some.py WEATHER WORKERS THREADS LEARNERS(comma)"""
import os, sys, subprocess, time, json
from concurrent.futures import ThreadPoolExecutor
import a9_common as A
weather = sys.argv[1]; workers = int(sys.argv[2]) if len(sys.argv) > 2 else 6; threads = sys.argv[3] if len(sys.argv) > 3 else "4"
LEARN = sys.argv[4].split(",") if len(sys.argv) > 4 else ["L1", "L2", "L3"]
PY = sys.executable; HERE = A.HERE
env = dict(os.environ, OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
def log(msg):
    with open(os.path.join(HERE, f"sched_{weather}_" + ("a10_" if os.environ.get("A10") else "") + ("win" if os.name == "nt" else "mac") + ".log"), "a") as f: f.write(time.strftime("%H:%M:%S ") + msg + "\n")
def build(se):
    s, e = se
    if os.path.exists(os.path.join(HERE, "frames", f"{s}_{e}_{weather}.pkl")): return
    r = subprocess.run([PY, "-W", "ignore", "build_frames_a9.py", s, e, weather], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"frame {s} {e} rc={r.returncode} {r.stdout.strip()[-200:]} {r.stderr.strip()[-300:]}")
cells = [(s, e) for s in ["pjm", "miso"] for e in A.ERAS[s]]
with ThreadPoolExecutor(min(6, workers)) as ex:
    list(ex.map(build, cells))
order = sorted([(s, e, l) for s, e in cells for l in LEARN], key=lambda t: (t[2] == "L3", -int(t[1]) if t[1] != "2014" else -2019))
def run(c):
    s, e, l = c
    out = os.path.join(HERE, "results", ("a10" if os.environ.get("A10") else "a9") + f"_{s}_{e}_{l}_{weather}.csv")
    if os.path.exists(out): return
    t = time.time()
    r = subprocess.run([PY, "-W", "ignore", "run_cell_a9.py", s, e, l, weather], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"cell {s} {e} {l} rc={r.returncode} {round(time.time()-t)}s {r.stdout.strip()[-160:]} {r.stderr.strip()[-400:]}")
with ThreadPoolExecutor(workers) as ex:
    list(ex.map(run, order))
log("ALL DONE")
