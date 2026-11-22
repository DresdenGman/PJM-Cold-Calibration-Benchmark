"""A8: replace the weather of every row of an era frame by the day-ahead GEFS control forecast
(00 UTC run of local date d-1, forecast hours 24-54, linear in time), rebuild all derived weather
features, and write the frame and H-DA features to a8/<system>/experiments/prepped.
Usage: build_a8_frames.py SYSTEM ERA SOURCE_EXPDIR"""
import os, sys, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
system, era, src = sys.argv[1], sys.argv[2], sys.argv[3]
EXP = os.path.join(HERE, system, "experiments"); sys.path.insert(0, EXP); os.chdir(EXP)
import exp_common as C
import prep_data as PD
from features import build_masked_features
COLS = [f"p{i}" for i in (range(15) if system == "pjm" else range(15, 30))]

def table():
    out = {}
    for f in sorted(glob.glob(os.path.join(HERE, "raw_ctl", "*.csv"))):
        d = pd.read_csv(f)
        if d.empty: continue
        t = d[d["var"] == "TMP"].set_index("fh")[COLS].mean(axis=1).sort_index()
        u = d[d["var"] == "UGRD"].set_index("fh")[COLS].sort_index()
        v = d[d["var"] == "VGRD"].set_index("fh")[COLS].sort_index()
        ws = np.sqrt(u.values ** 2 + v.values ** 2).mean(axis=1) if len(u) and len(v) else None
        out[pd.Timestamp(os.path.basename(f)[:10]).date()] = (t.index.values.astype(float), t.values,
                                                              u.index.values.astype(float), ws)
    return out

fr = pd.read_pickle(os.path.join(src, "prepped", f"era{era}.pkl"))
tab = table()
T = np.full(len(fr), np.nan); W = np.full(len(fr), np.nan)
ts = pd.to_datetime(fr["ts_utc"], utc=True)
for i, (d, t) in enumerate(zip(fr["ts_local"].dt.date.values, ts)):
    c = d - pd.Timedelta(days=1).to_pytimedelta()
    if c not in tab: continue
    fh, tv, fw, wv = tab[c]
    L = (t - pd.Timestamp(c, tz="UTC")).total_seconds() / 3600.0
    if fh.min() <= L <= fh.max(): T[i] = np.interp(L, fh, tv)
    if wv is not None and fw.min() <= L <= fw.max(): W[i] = np.interp(L, fw, wv)
out = fr[["ts_utc", "load", "split", "ts_local"]].copy()
out["t2m_c"] = T
out["temp_f"] = T * 9.0 / 5.0 + 32.0
out["wind_mph"] = W * 2.23694
out["wind_chill_f"] = PD.nws_wind_chill_f(out["temp_f"], out["wind_mph"])
out["hdh_f"] = np.clip(65.0 - out["temp_f"], 0.0, None)
out["cdh_f"] = np.clip(out["temp_f"] - 65.0, 0.0, None)
df = PD.finalize(out, era)
df["t2m_c_era5"] = fr["t2m_c"].values           # kept for the diagnostic only, never a feature
df.to_pickle(os.path.join("prepped", f"era{era}.pkl"))
build_masked_features(df, "HDA").to_pickle(os.path.join("prepped", f"era{era}_XDA.pkl"))
build_masked_features(df, "H1H").to_pickle(os.path.join("prepped", f"era{era}_X1H.pkl"))
ok = np.isfinite(T) & np.isfinite(fr["t2m_c"].values)
e = T[ok] - fr["t2m_c"].values[ok]
info = dict(system=system, era=era, rows=len(df), t_missing=int(np.isnan(T).sum()), w_missing=int(np.isnan(W).sum()),
            t_missing_by_part={p: int(np.isnan(T[(df.part == p).values]).sum()) for p in ["fit", "tune", "cal", "eval"]},
            bias_vs_era5=float(e.mean()), mae_vs_era5=float(np.abs(e).mean()), corr=float(np.corrcoef(T[ok], fr["t2m_c"].values[ok])[0, 1]))
json.dump(info, open(os.path.join("logs", f"a8_frame_{era}.json"), "w"), indent=1)
print(json.dumps(info))
