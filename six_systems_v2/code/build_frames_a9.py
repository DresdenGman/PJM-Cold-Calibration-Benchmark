"""A9: long-history era frames. Usage: build_frames_a9.py SYSTEM ERA WEATHER(gefs|era5)"""
import os, sys, glob, json
import numpy as np, pandas as pd
import a9_common as A
import prep_data as PD
HERE = A.HERE
system, era, weather = sys.argv[1:4]
COLS = A.gefs_cols(system)
e0, e1 = A.eval_span(system, era)
train_end = (pd.Timestamp(e0) - pd.Timedelta(days=1)).date()
if system == "pjm" and era == "2014":
    f = pd.read_csv(os.path.join(HERE, "era2014_base.csv"))   # PJM metered load + ERA5 columns of the original 2014 frame
    f["ts_utc"] = pd.to_datetime(f["ts_utc"], utc=True)
    f = f[f["ts_utc"].dt.tz_convert("America/New_York").dt.date <= pd.Timestamp(e1).date()]
    loads = f[["ts_utc", "load"]].copy(); base_weather = f[["ts_utc", "t2m_c", "temp_f", "wind_mph"]].copy()
else:
    ba, glitch = A.BA[system]
    use = ["Balancing Authority", "Local Time at End of Hour", "UTC Time at End of Hour", "Demand (MW)"]
    fr = []
    for fn in sorted(glob.glob(os.path.join(HERE, "raw_eia", "EIA930_BALANCE_*.csv"))):
        d = pd.read_csv(fn, usecols=use, low_memory=False); fr.append(d[d["Balancing Authority"] == ba])
    d = pd.concat(fr, ignore_index=True)
    d["Demand (MW)"] = pd.to_numeric(d["Demand (MW)"].astype(str).str.replace(",", ""), errors="coerce")
    d["ts_utc"] = pd.to_datetime(d["UTC Time at End of Hour"], utc=True) - pd.Timedelta(hours=1)
    d["ts_local_end"] = pd.to_datetime(d["Local Time at End of Hour"])
    d = d.sort_values("ts_utc").drop_duplicates("ts_utc")
    ld = d["ts_local_end"].dt.date
    d = d[(ld >= pd.Timestamp("2015-07-01").date()) & (ld <= pd.Timestamp(e1).date())]
    d.loc[d["Demand (MW)"].abs() > glitch, "Demand (MW)"] = np.nan
    loads = pd.DataFrame({"ts_utc": d["ts_utc"].reset_index(drop=True), "load": d["Demand (MW)"].astype(float).reset_index(drop=True)})
    base_weather = None
grid = pd.date_range(loads.ts_utc.min(), loads.ts_utc.max(), freq="1h", tz="UTC")
out = pd.DataFrame({"ts_utc": grid}).merge(loads, on="ts_utc", how="left")
out["ts_local"] = out["ts_utc"].dt.tz_convert("America/New_York")
out["load_raw"] = out["load"]
out["shed"] = False
if system in A.SHED:                                    # A11: flagged load-shed days excluded (load set to NaN)
    s0, s1 = A.SHED[system]; ld_ = out["ts_local"].dt.date
    out["shed"] = ((ld_ >= pd.Timestamp(s0).date()) & (ld_ <= pd.Timestamp(s1).date())).values
    out.loc[out["shed"], "load"] = np.nan
loc = out["ts_local"].dt.date
out["split"] = np.where(loc <= train_end, "train", np.where((loc >= pd.Timestamp(e0).date()) & (loc <= pd.Timestamp(e1).date()), "eval", "gap"))
if weather == "gefs":
    tab = {}
    for fn in sorted(glob.glob(os.path.join(A.gefs_dir(system), "*.csv"))):
        d = pd.read_csv(fn)
        if d.empty: continue
        t = d[d["var"] == "TMP"].set_index("fh")[COLS].mean(axis=1).sort_index()
        u = d[d["var"] == "UGRD"].set_index("fh")[COLS].sort_index(); v = d[d["var"] == "VGRD"].set_index("fh")[COLS].sort_index()
        ws = np.sqrt(u.values ** 2 + v.values ** 2).mean(axis=1)
        tab[pd.Timestamp(os.path.basename(fn)[:10]).date()] = (t.index.values.astype(float), t.values, u.index.values.astype(float), ws)
    T = np.full(len(out), np.nan); Wd = np.full(len(out), np.nan)
    for i, (dd, ts) in enumerate(zip(loc.values, out["ts_utc"])):
        c = dd - pd.Timedelta(days=1).to_pytimedelta()
        if c not in tab: continue
        fh, tv, fw, wv = tab[c]; L = (ts - pd.Timestamp(c, tz="UTC")).total_seconds() / 3600.0
        if fh.min() <= L <= fh.max(): T[i] = np.interp(L, fh, tv)
        if fw.min() <= L <= fw.max(): Wd[i] = np.interp(L, fw, wv)
    out["t2m_c"] = T; out["temp_f"] = T * 9 / 5 + 32; out["wind_mph"] = Wd * 2.23694
else:
    if base_weather is not None:
        out = out.merge(base_weather, on="ts_utc", how="left")
    else:
        w = pd.concat([pd.read_csv(f) for f in glob.glob(A.era5_glob(system))])
        w["ts_utc"] = pd.to_datetime(w["timestamp_utc"], utc=True); w = w.drop_duplicates("ts_utc")
        out = out.merge(w[["ts_utc", "t2m_c", "temperature_f", "wind_speed_mph"]].rename(columns={"temperature_f": "temp_f", "wind_speed_mph": "wind_mph"}), on="ts_utc", how="left")
out["wind_chill_f"] = PD.nws_wind_chill_f(out["temp_f"], out["wind_mph"])
out["hdh_f"] = np.clip(65.0 - out["temp_f"], 0.0, None)
out["cdh_f"] = np.clip(out["temp_f"] - 65.0, 0.0, None)
df = PD.finalize(out, era)
mon = df["ts_local"].dt.month.values; yr = df["ts_local"].dt.year.values
df["winter"] = np.where(np.isin(mon, [12, 1, 2]), np.where(mon == 12, yr + 1, yr), -1)
df["part"] = np.where(df["split"] == "eval", "eval", np.where((df["split"] == "train") & (df["winter"] > 0), "cal",
                      np.where(df["split"] == "train", "fit", "gap")))
df.to_pickle(os.path.join(HERE, "frames", f"{system}_{era}_{weather}.pkl"))
info = dict(system=system, era=era, weather=weather, rows=len(df), start=str(df.ts_local.min()), train_end=str(train_end),
            winters=sorted(int(w) for w in df.loc[df.part == "cal", "winter"].unique()),
            load_nan_train=int(df.loc[df.split == "train", "load"].isna().sum()), load_nan_eval=int(df.loc[df.split == "eval", "load"].isna().sum()),
            T_nan=int(df["t2m_c"].isna().sum()), T_nan_eval=int(df.loc[df.split == "eval", "t2m_c"].isna().sum()))
json.dump(info, open(os.path.join(HERE, "frames", f"{system}_{era}_{weather}.json"), "w"))
print(json.dumps(info))
