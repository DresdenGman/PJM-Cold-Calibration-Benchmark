"""v15 (A4, post hoc): upper-tail exceedance and an issuance-safe recentring calibrator.
C9 shifts the C1 interval by the mean error of the median forecast (y - q50) over the 7 local days ending
two days before the target day (labels released by issuance at 10:00 on d-1), width unchanged.
Reports event / winter / placebo two-sided cov90 and upper exceedance (load above the upper bound, nominal
0.05) for C1 and C9. Usage: rev_shift.py SYSTEMS -> analysis/rev_shift_<systems>.csv"""
import os, sys
import numpy as np, pandas as pd
import a9_common as A, a9_job
systems = sys.argv[1].split(","); rows = []
for s in systems:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    ev = A.events(s); plac = pd.read_csv(os.path.join(A.HERE, "work", s, "placebo_windows.csv"))
    for e in sorted(ev, key=int):
        pp = os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz")
        if not os.path.exists(pp): print("skip", s, e); continue
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)
        jb = JobA9(e, "HDA", "L1", df, np.load(pp)["P_raw"], C.QUANTILES, lambda m: None)
        q50 = jb.P[:, C.qidx(jb.grid, 0.5)]; err = jb.y - q50
        day = jb.loc.dt.normalize()
        daily = pd.Series(err).groupby(day.values).mean()                       # NaN-skipping daily mean error
        roll = daily.rolling(7, min_periods=4).mean().shift(2)                  # days d-8 .. d-2
        shift = roll.reindex(day.values).values; shift = np.where(np.isfinite(shift), shift, 0.0)
        es, ee = pd.Timestamp(ev[e]["start"]), pd.Timestamp(ev[e]["end"])
        scopes = {"event": (jb.valid_idx(jb.eval_mask & (jb.loc >= es) & (jb.loc < ee)), es), "winter": (jb.valid_idx(jb.eval_mask), None)}
        pw = [(jb.valid_idx(jb.eval_mask & (jb.loc >= pd.Timestamp(w.start_local)) & (jb.loc < pd.Timestamp(w.end_local))), pd.Timestamp(w.start_local)) for w in plac[plac.era == int(e)].itertuples()]
        rec = dict(system=s, era=int(e))
        def score(idx_cut_list, tag):
            ys, los, his, shs = [], [], [], []
            for idx, cut in idx_cut_list:
                if not len(idx): continue
                lo, hi = jb.all_bounds("C1", jb.bundle(jb.cal_idx(cut)), idx)[0.10]
                ys.append(jb.y[idx]); los.append(lo); his.append(hi); shs.append(shift[idx])
            y, lo, hi, sh = map(np.concatenate, (ys, los, his, shs))
            for c, (l, h) in {"C1": (lo, hi), "C9": (lo + sh, hi + sh)}.items():
                rec[f"{tag}_cov_{c}"] = float(np.mean((y >= l) & (y <= h))); rec[f"{tag}_upx_{c}"] = float(np.mean(y > h))
            rec[f"{tag}_meanshift"] = float(np.mean(sh))
        score([scopes["event"]], "event"); score([scopes["winter"]], "winter"); score(pw, "placebo")
        rows.append(rec); print(s, e, {k: round(v, 3) for k, v in rec.items() if isinstance(v, float) and ("event" in k)}, flush=True)
pd.DataFrame(rows).to_csv(os.path.join(A.HERE, "analysis", f"rev_shift_{'_'.join(systems)}.csv"), index=False)
