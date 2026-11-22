"""A5: run C5 (ensemble-spread scaling) next to C0 and C4 for one cell, using
the archived base predictions. Usage: job_c5.py SYSTEM ERA LEARNER
SYSTEM in {PJM, MISO}; H-DA arm only (A5 scope)."""
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
O = os.path.dirname(HERE)
EXPDIR = {"PJM": os.path.join(O, "code"),                       # repository layout
          "MISO": os.path.join(O, "replication_miso", "code")}
# Requires the archived base predictions prepped/pred_<era>_HDA_<learner>.npz in each
# EXPDIR, produced by the fit jobs (code/run_all.sh, replication_miso/code).
system, era, learner = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, EXPDIR[system]); os.chdir(EXPDIR[system])
import exp_common as C
import calibrators as CAL
import job_fit as JF
sys.path.insert(0, HERE)
from build_spread import spread_for_frame

C5_GAMMA_GRID = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0]

def c5_select_gammas(tune, sigma0):
    """As CAL.c4_select_gammas with hdh -> z (rows with finite z only)."""
    grid = tune["grid"]
    keep = np.isfinite(tune["z"])
    y, P, z = tune["y"][keep], tune["P"][keep], tune["z"][keep]
    n = len(y); cut = int(np.floor(n * (1.0 - C.C4_HOLDOUT_FRAC)))
    out = {}
    for alpha in C.ALPHA_LEVELS:
        lo_c, hi_c = CAL._cols(P, alpha, grid)
        d = {"hi": y - hi_c, "lo": lo_c - y}
        for side in ["hi", "lo"]:
            best = None
            for g in C5_GAMMA_GRID:
                s_fit = sigma0 * (1.0 + g * z[:cut]); s_hold = sigma0 * (1.0 + g * z[cut:])
                q = C.expansion_only(C.order_statistic_Q(d[side][:cut] / s_fit, alpha / 2.0))
                bound = (hi_c[cut:] + q * s_hold) if side == "hi" else (lo_c[cut:] - q * s_hold)
                rate = float(np.mean(y[cut:] > bound)) if side == "hi" else float(np.mean(y[cut:] < bound))
                key = (abs(rate - alpha / 2.0), float(np.mean(q * s_hold)), g)
                if best is None or key < best[0]:
                    best = (key, g)
            out[(alpha, side)] = best[1]
    return out

def bounds_C5(cal, sigma0, gammas, P_new, z_new, alpha):
    grid = cal["grid"]
    keep = np.isfinite(cal["z"])
    zc = cal["z"][keep]; zfill = float(np.median(zc))
    z_new = np.where(np.isfinite(z_new), z_new, zfill)
    g_hi, g_lo = gammas[(alpha, "hi")], gammas[(alpha, "lo")]
    lo_c, hi_c = CAL._cols(cal["P"][keep], alpha, grid)
    y = cal["y"][keep]
    q_hi = C.expansion_only(C.order_statistic_Q((y - hi_c) / (sigma0 * (1.0 + g_hi * zc)), alpha / 2.0))
    q_lo = C.expansion_only(C.order_statistic_Q((lo_c - y) / (sigma0 * (1.0 + g_lo * zc)), alpha / 2.0))
    lo_n, hi_n = CAL._cols(P_new, alpha, grid)
    return (lo_n - q_lo * sigma0 * (1.0 + g_lo * z_new),
            hi_n + q_hi * sigma0 * (1.0 + g_hi * z_new))

class JobC5(JF.Job):
    def __init__(self, *a, z=None, **k):
        super().__init__(*a, **k); self.z = z; self._c5 = None
    def bundle(self, idx):
        b = super().bundle(idx); b["z"] = self.z[np.asarray(idx)]; return b
    def _c5_params(self):
        if self._c5 is None:
            tune = self.tune_bundle()
            s0 = CAL.c4_sigma0(tune)       # sigma0 exactly as C4 (all D_tune rows)
            gam = c5_select_gammas(tune, s0)
            self._c5 = (s0, gam)
            self.log(f"C5 sigma0={s0:.1f}; tune rows with z={int(np.isfinite(tune['z']).sum())}/{len(tune['z'])}; "
                     f"gammas={ {a: (gam[(a, 'hi')], gam[(a, 'lo')]) for a in C.ALPHA_LEVELS} }")
        return self._c5
    def bounds(self, calibrator, cal, idx, alpha):
        if calibrator == "C5":
            s0, gam = self._c5_params()
            sub = self.bundle(idx)
            return bounds_C5(cal, s0, gam, sub["P"], sub["z"], alpha)
        return super().bounds(calibrator, cal, idx, alpha)

frame = pd.read_pickle(os.path.join("prepped", f"era{era}.pkl"))
xname, grid = JF.cell_spec(era, "HDA", learner)
P_raw = np.load(os.path.join("prepped", f"pred_{era}_HDA_{learner}.npz"))["P_raw"]
z, nmem = spread_for_frame(frame, system)
JF.CALIBRATORS = ["C0", "C4", "C5"]
log = []
job = JobC5(era, "HDA", learner, frame, P_raw, grid, log.append, z=z)
rows, _ = job.run()
rows.insert(0, "system", system)
ev = (frame["split"] == "eval").values
meta = dict(system=system, era=era, learner=learner,
            z_missing_eval=int(np.isnan(z[ev]).sum()), n_eval=int(ev.sum()),
            z_missing_tune=int(np.isnan(z[(frame["part"] == "tune").values]).sum()),
            z_missing_cal=int(np.isnan(z[(frame["part"] == "cal").values]).sum()),
            members=sorted(set(int(m) for m in nmem[nmem > 0])), log=log)
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
rows.to_csv(os.path.join(HERE, "results", f"c5_{system}_{era}_HDA_{learner}.csv"), index=False)
np.save(os.path.join(HERE, "results", f"z_{system}_{era}.npy"), z)
json.dump(meta, open(os.path.join(HERE, "results", f"c5_{system}_{era}_HDA_{learner}.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in meta.items() if k != "log"}))
