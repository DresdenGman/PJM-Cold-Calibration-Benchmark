"""Data preparation (v2.1): one continuous hourly frame per era, three-way
split (§0), cold-spell population (§6) and placebo windows — all BEFORE any
fitting.

Eras / sources / conventions as before (see PHASE2B): 2014 PJM metered
table (read-only), 2018/2022 EIA-930 demand + Open-Meteo ERA5 weather,
hour-beginning UTC grid, EIA load placed at end-1h, NWS wind chill derived
for EIA eras, no cleaning beyond the Phase 2b/2c builders.

Splits (§0): within each era's training period, by time order:
  D_fit = all but the last (273+92) days; D_tune = the 273 days before
  D_cal_train; D_cal_train = the last 92 days of training.
Thermal memory (§0): M = T at era start; M_t = 0.04 T_t + 0.96 M_{t-1};
missing T forward-filled and counted.
"""
import os
import numpy as np
import pandas as pd

import exp_common as C
from features import build_h1h_features, build_masked_features

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(PROJ, "code")
# The assembled 2014 modelling table is not redistributed with this
# repository; build it from the public sources as documented in
# DATA_SOURCES.md and place it at this path.
TABLE_2014 = os.path.join(PROJ, "data", "era2014",
                          "pjm_era5_modeling_table_2010_2014.csv")
DE = os.path.join(PROJ, "data", "events")
LOG = []


def log(msg):
    print(msg)
    LOG.append(str(msg))


def nws_wind_chill_f(temp_f, wind_mph):
    T = np.asarray(temp_f, dtype=float)
    V = np.asarray(wind_mph, dtype=float)
    v_pow = np.power(np.maximum(V, 0.0), 0.16)
    wc = 35.74 + 0.6215 * T - 35.75 * v_pow + 0.4275 * T * v_pow
    return np.where((T <= 50.0) & (V >= 3.0), wc, T)


def finalize(df, era):
    df = df.sort_values("ts_utc").reset_index(drop=True)
    df["hdh_c"] = np.clip(C.HDH_BASE_C - df["t2m_c"], 0.0, None)
    T = df["t2m_c"].values.astype(float)
    n_nan = int(np.isnan(T).sum())
    if n_nan:
        log(f"[{era}] {n_nan} missing T hours forward-filled for "
            f"thermal memory (counted per v2.1 §0)")
        T = pd.Series(T).ffill().bfill().values
    mem = np.empty(len(T))
    mem[0] = T[0]
    for t in range(1, len(T)):
        mem[t] = 0.04 * T[t] + 0.96 * mem[t - 1]
    df["mem_c"] = mem
    df["n_missing_T"] = n_nan
    df["era"] = era
    # three-way split on training rows (time order)
    part = np.where(df["split"] == "train", "fit",
                    np.where(df["split"] == "eval", "eval", "gap"))
    tr_pos = np.where(df["split"] == "train")[0]
    n_cal = C.CAL_TRAIN_DAYS * 24
    n_tune = C.TUNE_DAYS * 24
    if len(tr_pos) > n_cal + n_tune:
        part[tr_pos[-n_cal:]] = "cal"
        part[tr_pos[-(n_cal + n_tune):-n_cal]] = "tune"
    df["part"] = part
    return df


def era_2014():
    df = pd.read_csv(TABLE_2014)
    ts_utc = pd.to_datetime(df["timestamp_utc"], format="%m/%d/%Y %I:%M:%S %p")
    out = pd.DataFrame()
    out["ts_utc"] = ts_utc.dt.tz_localize("UTC")
    out["load"] = df["actual_load_mw"].astype(float)
    out["temp_f"] = df["temperature_f"].astype(float)
    out["wind_chill_f"] = df["wind_chill_f"].astype(float)
    out["wind_mph"] = df["wind_speed_mph"].astype(float)
    out["hdh_f"] = df["hdh"].astype(float)
    out["cdh_f"] = df["cdh"].astype(float)
    out["t2m_c"] = (out["temp_f"] - 32.0) * 5.0 / 9.0
    out["split"] = np.where(df["source_year"] <= 2013, "train", "eval")
    out["ts_local"] = out["ts_utc"].dt.tz_convert("America/New_York")
    return finalize(out, "2014")


def era_eia(era, train_file, eval_file, weather_file):
    tr = pd.read_csv(os.path.join(DE, "load", train_file))
    ev = pd.read_csv(os.path.join(DE, "load", eval_file))
    w = pd.read_csv(os.path.join(DE, "weather", weather_file))

    def load_series(d, split):
        end = pd.to_datetime(d["timestamp_utc_end_of_hour"], utc=True)
        return pd.DataFrame({"ts_utc": end - pd.Timedelta(hours=1),
                             "load": d["demand_mw"].astype(float),
                             "split": split})

    loads = pd.concat([load_series(tr, "train"), load_series(ev, "eval")])
    loads = loads.drop_duplicates("ts_utc").set_index("ts_utc")
    wts = pd.to_datetime(w["timestamp_utc"], utc=True)
    wea = pd.DataFrame({"ts_utc": wts, "t2m_c": w["t2m_c"].astype(float),
                        "temp_f": w["temperature_f"].astype(float),
                        "wind_mph": w["wind_speed_mph"].astype(float)})
    wea = wea.drop_duplicates("ts_utc").set_index("ts_utc")
    grid = pd.date_range(wea.index.min(), wea.index.max(), freq="1h", tz="UTC")
    out = pd.DataFrame({"ts_utc": grid}).set_index("ts_utc")
    out["load"] = loads["load"]
    out["split"] = loads["split"].fillna("gap")
    for c in ["t2m_c", "temp_f", "wind_mph"]:
        out[c] = wea[c]
    out = out.reset_index()
    out["wind_chill_f"] = nws_wind_chill_f(out["temp_f"], out["wind_mph"])
    out["hdh_f"] = np.clip(65.0 - out["temp_f"], 0.0, None)
    out["cdh_f"] = np.clip(out["temp_f"] - 65.0, 0.0, None)
    out["ts_local"] = out["ts_utc"].dt.tz_convert("America/New_York")
    return finalize(out, era)


# ---------------------------------------------------------------- §6 cold spells
def cold_threshold(train_T):
    """theta = training order statistic T_(ceil(0.02 n)) (no interpolation)."""
    s = np.sort(np.asarray(train_T, dtype=float))
    s = s[np.isfinite(s)]
    k = int(np.ceil(0.02 * len(s)))
    return float(s[k - 1])


def cold_spells(df, era, thr):
    ev = df[df["split"] == "eval"].reset_index(drop=True)
    T = ev["t2m_c"].values
    below = np.isfinite(T) & (T < thr)   # missing T breaks runs (not below)
    runs = []
    i = 0
    while i < len(ev):
        if below[i]:
            j = i
            while j + 1 < len(ev) and below[j + 1]:
                j += 1
            runs.append([i, j])
            i = j + 1
        else:
            i += 1
    kept = [r for r in runs if r[1] - r[0] + 1 >= 24]      # >=24h FIRST
    merged = []
    for r in kept:                                          # then merge g<=12
        if merged and r[0] - merged[-1][1] - 1 <= 12:
            merged[-1][1] = r[1]
        else:
            merged.append(list(r))
    rows = []
    for k, (a, b) in enumerate(merged):
        seg = ev.iloc[a:b + 1]
        rows.append(dict(
            era=era, spell_id=f"{era}_S{k+1}",
            start_local=seg["ts_local"].iloc[0].strftime("%Y-%m-%d %H:%M"),
            end_local=(seg["ts_local"].iloc[-1]
                       + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            hours=int(b - a + 1), n_below=int(below[a:b + 1].sum()),
            min_temp_c=float(seg["t2m_c"].min()),
            mean_temp_c=float(seg["t2m_c"].mean()),
            threshold_c=thr))
    return pd.DataFrame(rows)


def placebo_windows(df, era, thr):
    ev = df[df["split"] == "eval"].reset_index(drop=True)
    nev = C.NAMED_EVENTS[era]
    nstart, nend = pd.Timestamp(nev["start"]), pd.Timestamp(nev["end"])
    L = int((nend - nstart) / pd.Timedelta(hours=1))
    loc = ev["ts_local"]
    winter = loc.dt.month.isin([12, 1, 2]).values
    below = (ev["t2m_c"] < thr).values
    load_ok = ev["load"].notna().values
    cands = []
    for i in range(0, len(ev) - L + 1):
        if not winter[i] or loc.iloc[i].hour != 0:
            continue
        ws = loc.iloc[i].tz_localize(None)
        we = loc.iloc[i + L - 1].tz_localize(None) + pd.Timedelta(hours=1)
        if ws < nend and we > nstart:
            continue
        if below[i:i + L].any() or not load_ok[i:i + L].all():
            continue
        cands.append(i)
    rows = []
    picks = sorted({cands[0], cands[len(cands) // 2], cands[-1]}) if cands else []
    for k, i in enumerate(picks):
        seg = ev.iloc[i:i + L]
        rows.append(dict(
            era=era, placebo_id=f"{era}_P{k+1}",
            start_local=seg["ts_local"].iloc[0].strftime("%Y-%m-%d %H:%M"),
            end_local=(seg["ts_local"].iloc[-1]
                       + pd.Timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            hours=int(L), mean_temp_c=float(seg["t2m_c"].mean())))
    return pd.DataFrame(rows)


def main():
    eras = {
        "2014": era_2014(),
        "2018": era_eia("2018", "train_2016_2017_pjm_load_eia930.csv",
                        "eval_2017dec_2018feb_pjm_load_eia930.csv",
                        "span2016_2018feb_weather_openmeteo_era5_footprint_mean.csv"),
        "2022": era_eia("2022", "train_2020_2021_pjm_load_eia930.csv",
                        "eval_2022dec_2023feb_pjm_load_eia930.csv",
                        "span2020_2023feb_weather_openmeteo_era5_footprint_mean.csv"),
    }
    spells_all, placebos_all = [], []
    for era, df in eras.items():
        X1 = build_h1h_features(df)
        X1H = build_masked_features(df, "H1H")
        XDA = build_masked_features(df, "HDA")
        df.to_pickle(os.path.join(EXP, "prepped", f"era{era}.pkl"))
        X1.to_pickle(os.path.join(EXP, "prepped", f"era{era}_X1.pkl"))
        X1H.to_pickle(os.path.join(EXP, "prepped", f"era{era}_X1H.pkl"))
        XDA.to_pickle(os.path.join(EXP, "prepped", f"era{era}_XDA.pkl"))
        for part in ["fit", "tune", "cal", "eval"]:
            m = (df["part"] == part).values
            log(f"[{era}] part={part}: rows={int(m.sum())} "
                f"X1H invalid={int((~np.isfinite(X1H.values[m]).all(axis=1)).sum())} "
                f"XDA invalid={int((~np.isfinite(XDA.values[m]).all(axis=1)).sum())}")
        thr = cold_threshold(df.loc[df["split"] == "train", "t2m_c"])
        sp = cold_spells(df, era, thr)
        spells_all.append(sp)
        log(f"[{era}] cold threshold (train order stat) = {thr:.3f} C; "
            f"spells = {len(sp)}")
        pl = placebo_windows(df, era, thr)
        placebos_all.append(pl)
        log(f"[{era}] placebo windows = {len(pl)}")
    pd.concat(spells_all).to_csv(os.path.join(EXP, "cold_spell_events.csv"),
                                 index=False)
    pd.concat(placebos_all).to_csv(os.path.join(EXP, "placebo_windows.csv"),
                                   index=False)
    with open(os.path.join(EXP, "logs", "prep_log.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
    log("saved cold_spell_events.csv / placebo_windows.csv BEFORE any fitting")


if __name__ == "__main__":
    main()
