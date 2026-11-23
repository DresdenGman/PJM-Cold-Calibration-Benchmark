"""v13 revision: leave-one-event-out contrast with the corrected (positive, era-D_cal) normaliser.
For each target event, the calibration set is REPLACED by the other events' hours of the same system
(each normalised by its own era's D_cal scale); the cutoff is rescaled by the target's own calibration
scale (D_cal plus pre-event hours). Usage: rev_loeo.py SYSTEM -> analysis/rev_loeo_<system>.csv"""
import os, sys
import numpy as np, pandas as pd
import a9_common as A, a9_job
s = sys.argv[1]; C, CAL, JF, F7, JobA9 = a9_job.setup(s)
FD = os.path.join(os.path.dirname(A.HERE), "final_data"); EV = pd.read_csv(os.path.join(FD, "a9_events_L1_gefs.csv"))
ev = A.events(s); jobs = {}
for e in A.ERAS[s]:
    df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)
    jobs[e] = JobA9(e, "HDA", "L1", df, np.load(os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz"))["P_raw"], C.QUANTILES, lambda m: None)
def ev_idx(j, e): return j.valid_idx(j.eval_mask & (j.loc >= pd.Timestamp(ev[e]["start"])) & (j.loc < pd.Timestamp(ev[e]["end"])))
era_sc = {e: CAL.era_scale_abs(jobs[e].bundle(jobs[e].part_idx("cal")), jobs[e].grid) for e in jobs}
rows = []
for e, jt in jobs.items():
    es = pd.Timestamp(ev[e]["start"]); idx = ev_idx(jt, e); sub = jt.bundle(idx)
    st = CAL.era_scale_abs(jt.bundle(jt.cal_idx(es)), jt.grid)
    others = [o for o in jobs if o != e]; pools = [jobs[o].bundle(ev_idx(jobs[o], o)) for o in others]; scs = [era_sc[o] for o in others]
    rec = dict(system=s, era=int(e), target_scale=st)
    r0 = EV[(EV.system == s) & (EV.era == int(e))].iloc[0]
    for c in ["C1", "C2a", "C2b", "C4"]:
        if c == "C1": lo, hi = CAL.bounds_C1_loeo_v13(pools, scs, st, sub["P"], 0.10, jt.grid)
        elif c == "C4": lo, hi = CAL.bounds_C4_loeo_v13(pools, scs, st, None, sub["P"], sub["hdh"], 0.10, jt.grid)
        else: lo, hi = CAL.bounds_C2_loeo_v13(pools, scs, st, sub["P"], sub["temp"], 0.10, jt.grid, c)
        cov = float(np.mean((sub["y"] >= lo) & (sub["y"] <= hi))); ninf = int((~np.isfinite(lo) | ~np.isfinite(hi)).sum())
        rec[f"loeo_{c}"] = cov; rec[f"chron_{c}"] = r0[f"ev_{c}"]; rec[f"gap_{c}"] = 100 * (cov - r0[f"ev_{c}"])
        rec[f"finite_{c}"] = bool(ninf == 0 and r0[f"inf_{c}"] == 0)
    rows.append(rec); print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rec.items() if not k.startswith("chron")}, flush=True)
pd.DataFrame(rows).to_csv(os.path.join(A.HERE, "analysis", f"rev_loeo_{s}.csv"), index=False)
