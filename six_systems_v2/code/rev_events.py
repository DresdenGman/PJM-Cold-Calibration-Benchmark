"""v13 revision (exploratory), per event, L1 GEFS A9 design, all 38 events with predictions on disk:
 (1) location/dispersion decomposition of C1 event coverage: as issued; recentred on the event's mean
     error of the median (oracle); recentred and rescaled so the half-width matches the event's error
     dispersion relative to the calibration set's (oracle);
 (2) forecaster support: share of event hours colder than the coldest training hour;
 (3) condition (b) at equal headroom: the C0x family is evaluated exactly at the calibrator's own
     upper headroom (C0x = proportional expansion of the C0 interval about the median);
 (4) null-window attainability of condition (a) for C1 and for the selected calibrator.
Usage: rev_events.py [SYSTEMS]  -> analysis/rev_events.csv"""
import os, sys, glob
import numpy as np, pandas as pd
import a9_common as A, a9_job
systems = sys.argv[1].split(",") if len(sys.argv) > 1 else ["pjm", "miso", "ercot", "spp", "nyiso", "isone"]
FD = os.path.join(os.path.dirname(A.HERE), "final_data")
SEL = pd.concat([pd.read_csv(os.path.join(FD, "a9_events_L1_gefs.csv")), pd.read_csv(os.path.join(FD, "a11_events.csv"))])
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
rows = []
for s in systems:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    for e, nm in A.events(s).items():
        pp = os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz"); rp = os.path.join(A.HERE, "results", f"a9_{s}_{e}_L1_gefs.csv")
        if not (os.path.exists(pp) and os.path.exists(rp)): print("skip", s, e, flush=True); continue
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)
        jb = JobA9(e, "HDA", "L1", df, np.load(pp)["P_raw"], C.QUANTILES, lambda m: None)
        RES = pd.read_csv(rp); g = lambda c, sc: RES[(RES.calibrator == c) & (RES.scope == sc)].iloc[0]
        es, ee = pd.Timestamp(nm["start"]), pd.Timestamp(nm["end"])
        idx = jb.valid_idx(jb.eval_mask & (jb.loc >= es) & (jb.loc < ee)); cal = jb.bundle(jb.cal_idx(es))
        y = jb.y[idx]; q = jb.P[idx]; i50, i95 = C.qidx(jb.grid, 0.5), C.qidx(jb.grid, 0.95); q50 = q[:, i50]
        lo, hi = jb.all_bounds("C1", cal, idx)[0.10]
        cov = lambda l, h: float(np.mean((y >= l) & (y <= h)))
        err = y - q50; m = err.mean(); cal_err = cal["y"] - cal["P"][:, i50]
        r = np.std(err - m) / np.std(cal_err)
        c_, h_ = (lo + hi) / 2 + m, (hi - lo) / 2
        rec = dict(system=s, era=int(e), n=len(idx), c1_ev=cov(lo, hi), c1_recentred=cov(lo + m, hi + m),
                   c1_recentred_rescaled=cov(c_ - r * h_, c_ + r * h_), c1_rescaled_only=cov((lo + hi) / 2 - r * h_, (lo + hi) / 2 + r * h_),
                   disp_ratio=float(r), mean_err=float(m))
        tr_T = df.loc[df["split"] == "train", "t2m_c"]; evT = df["t2m_c"].values[idx]
        rec["share_below_train_min"] = float(np.mean(evT < tr_T.min())); rec["share_below_train_p01"] = float(np.mean(evT < tr_T.quantile(0.01)))
        # (3) condition (b) at equal headroom
        hi0 = q[:, i95]; base = np.mean(hi0 - q50); nmn = nm["name"]
        def ex_c0x_at(H):
            k = H / base; return float(np.mean(y > q50 + k * (hi0 - q50)))
        rx = g("C0x", nmn); rec["c0x_check"] = ex_c0x_at(rx.upper_headroom) - rx.exceedance_freq   # should be ~0
        sel = SEL[(SEL.system == s) & (SEL.era == int(e))].iloc[0]
        for c in CALS:
            rr = g(c, nmn)
            rec[f"b_eq_{c}"] = bool(np.isfinite(rr.upper_headroom) and rr.exceedance_freq < ex_c0x_at(rr.upper_headroom) - 1e-9)   # v14: tolerance, ties are not wins
        rec["chat"] = sel.chat
        # (4) null-window attainability of (a)
        L = int((ee - es) / pd.Timedelta(hours=1)); wins = []
        for i in np.where(jb.eval_mask)[0]:
            ws = jb.loc.iloc[i]
            if ws.hour != 0: continue
            we = ws + pd.Timedelta(hours=L)
            if ws < ee and we > es: continue
            mm = jb.eval_mask & (jb.loc >= ws) & (jb.loc < we)
            if mm.sum() < L: continue
            wins.append((ws, jb.valid_idx(mm)))
        for tag, c in [("C1", "C1"), ("chat", sel.chat)]:
            covs = []
            for ws, wi in wins:
                b = jb.all_bounds(c, jb.bundle(jb.cal_idx(ws)), wi)[0.10] if c != "C3" else C.nest_bounds({a: jb.bounds_aci(wi, a) for a in C.ALPHA_LEVELS})[0.10]
                covs.append(float(np.mean((jb.y[wi] >= b[0]) & (jb.y[wi] <= b[1]))))
            covs = np.array(covs); rec[f"ok_{tag}"] = float(np.mean((covs >= 0.85) & (covs <= 0.95))); rec[f"nullmed_{tag}"] = float(np.median(covs))
            if tag == "C1": rec["pct_C1"] = float(np.mean(covs < rec["c1_ev"]))
        rec["n_windows"] = len(wins); rows.append(rec); print(s, e, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in rec.items() if k in ("c1_ev", "c1_recentred", "c1_recentred_rescaled", "c0x_check", "ok_C1", "ok_chat")}, flush=True)
out = os.path.join(A.HERE, "analysis", "rev_events.csv")
old = pd.read_csv(out) if os.path.exists(out) else pd.DataFrame()
new = pd.DataFrame(rows)
if len(old): new = pd.concat([old[~old.set_index(["system", "era"]).index.isin(new.set_index(["system", "era"]).index)], new])
new.to_csv(out, index=False); print("rows", len(new))
