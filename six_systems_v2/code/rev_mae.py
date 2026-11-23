"""v15 (descriptive): event-window and winter point accuracy of the operator's EIA-930 day-ahead forecast and
the L1 median, on hours where both exist. Usage: rev_mae.py SYSTEMS -> analysis/rev_mae_<systems>.csv"""
import os, sys, glob
import numpy as np, pandas as pd
import a9_common as A, a9_job
systems = sys.argv[1].split(","); rows = []
for s in systems:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    ba, glitch = A.BA[s] if s in A.BA else A.A11_SYS[s][:2]
    use = ["Balancing Authority", "UTC Time at End of Hour", "Demand Forecast (MW)"]; fr = []
    for fn in sorted(glob.glob(os.path.join(A.HERE, "raw_eia", "EIA930_BALANCE_*.csv"))):
        d = pd.read_csv(fn, usecols=use, low_memory=False); fr.append(d[d["Balancing Authority"] == ba])
    d = pd.concat(fr, ignore_index=True)
    d["df"] = pd.to_numeric(d["Demand Forecast (MW)"].astype(str).str.replace(",", ""), errors="coerce")
    d["ts_utc"] = pd.to_datetime(d["UTC Time at End of Hour"], utc=True) - pd.Timedelta(hours=1)
    d = d.sort_values("ts_utc").drop_duplicates("ts_utc"); d.loc[(d.df.abs() > glitch) | (d.df <= 0), "df"] = np.nan
    DF = d.set_index("ts_utc")["df"]; ev = A.events(s)
    for e in sorted(ev, key=int):
        if e == "2014": continue
        pp = os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz")
        if not os.path.exists(pp): print("skip", s, e); continue
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)
        jb = JobA9(e, "HDA", "L1", df, np.load(pp)["P_raw"], C.QUANTILES, lambda m: None)
        q50 = jb.P[:, C.qidx(jb.grid, 0.5)]; f = DF.reindex(df["ts_utc"]).values
        es, ee = pd.Timestamp(ev[e]["start"]), pd.Timestamp(ev[e]["end"])
        rec = dict(system=s, era=int(e))
        for tag, mask in [("event", jb.eval_mask & (jb.loc >= es) & (jb.loc < ee)), ("winter", jb.eval_mask)]:
            idx = jb.valid_idx(mask); idx = idx[np.isfinite(f[idx])]; y = jb.y[idx]
            rec[f"{tag}_n"] = len(idx); rec[f"{tag}_mae_op"] = float(np.mean(np.abs(y - f[idx]))); rec[f"{tag}_mae_l1"] = float(np.mean(np.abs(y - q50[idx])))
            rec[f"{tag}_bias_op"] = float(np.mean(y - f[idx])); rec[f"{tag}_bias_l1"] = float(np.mean(y - q50[idx])); rec[f"{tag}_meanload"] = float(np.mean(y))
        rows.append(rec); print(s, e, {k: round(v) for k, v in rec.items() if "mae" in k}, flush=True)
pd.DataFrame(rows).to_csv(os.path.join(A.HERE, "analysis", f"rev_mae_{'_'.join(systems)}.csv"), index=False)
