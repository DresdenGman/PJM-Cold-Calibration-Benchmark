#!/usr/bin/env python3
"""Data builder: training spans + Dec-Feb evaluation windows for the
2018 and 2022 events. Same sources, columns and conventions as build_data_events.py
(EIA-930 BALANCE PJM rows; Open-Meteo archive ERA5 15-point footprint mean).
Usage: build_data_spans.py [load|weather|assemble|all]"""
import json, math, os, sys, time, urllib.request
import pandas as pd

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events")
RAW = f"{BASE}/_raw_eia930"
CHUNKS = f"{BASE}/weather/_chunks"
os.makedirs(CHUNKS, exist_ok=True)

# ---------------- Load: filter PJM rows from EIA-930 BALANCE files ----------------
USECOLS = ["Balancing Authority", "Data Date", "Hour Number",
           "Local Time at End of Hour", "UTC Time at End of Hour",
           "Demand Forecast (MW)", "Demand (MW)", "Net Generation (MW)",
           "Total Interchange (MW)"]

def load_pjm(files):
    frames = []
    for f in files:
        df = pd.read_csv(f"{RAW}/{f}", usecols=USECOLS, low_memory=False)
        df = df[df["Balancing Authority"] == "PJM"].copy()
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["ts_utc"] = pd.to_datetime(out["UTC Time at End of Hour"], utc=True)
    out["ts_local"] = pd.to_datetime(out["Local Time at End of Hour"])
    out = out.sort_values("ts_utc").drop_duplicates(subset=["ts_utc"]).reset_index(drop=True)
    return out

def window(df, d0, d1):
    # local-date window inclusive, based on the local end-of-hour timestamp's date
    loc_dates = df["ts_local"].dt.date
    m = (loc_dates >= pd.Timestamp(d0).date()) & (loc_dates <= pd.Timestamp(d1).date())
    w = df.loc[m, ["ts_utc", "ts_local", "Demand (MW)", "Demand Forecast (MW)",
                   "Net Generation (MW)", "Total Interchange (MW)"]].copy()
    w.columns = ["timestamp_utc_end_of_hour", "timestamp_local_end_of_hour",
                 "demand_mw", "demand_forecast_mw", "net_generation_mw",
                 "total_interchange_mw"]
    return w

def clean(w, name):
    # EIA-930 glitch guard: PJM's all-time record peak is 165,563 MW (Aug 2006);
    # any demand/forecast/generation cell above 170,000 MW in 2016-2023 data is a
    # reporting glitch. Such cells are set to NaN and printed, never dropped.
    # total_interchange_mw is a signed flow (negatives = net imports) and is NOT touched.
    for col in ["demand_mw", "demand_forecast_mw", "net_generation_mw"]:
        bad = w[w[col].abs() > 170000]
        for _, r in bad.iterrows():
            print(f"CLEAN {name}: {col} at local {r['timestamp_local_end_of_hour']} "
                  f"value {r[col]} -> NaN", flush=True)
        w.loc[w[col].abs() > 170000, col] = float("nan")
    return w

def qa_load(name, w):
    span_h = int((w["timestamp_utc_end_of_hour"].iloc[-1] -
                  w["timestamp_utc_end_of_hour"].iloc[0]).total_seconds() // 3600) + 1
    gaps = int((w["timestamp_utc_end_of_hour"].diff().dt.total_seconds().dropna() != 3600).sum())
    nans = {c: int(w[c].isna().sum()) for c in
            ["demand_mw", "demand_forecast_mw", "net_generation_mw", "total_interchange_mw"]}
    imax = w["demand_mw"].idxmax()
    print(f"LOAD {name}: rows={len(w)} utc_span_hours={span_h} missing_hours={span_h-len(w)} "
          f"gap_breaks={gaps} nans={nans}", flush=True)
    print(f"  max demand={w.loc[imax,'demand_mw']:.1f} MW at local "
          f"{w.loc[imax,'timestamp_local_end_of_hour']} utc {w.loc[imax,'timestamp_utc_end_of_hour']}", flush=True)

def build_load():
    pjm_a = load_pjm(["EIA930_BALANCE_2016_Jan_Jun.csv", "EIA930_BALANCE_2016_Jul_Dec.csv",
                      "EIA930_BALANCE_2017_Jan_Jun.csv", "EIA930_BALANCE_2017_Jul_Dec.csv",
                      "EIA930_BALANCE_2018_Jan_Jun.csv"])
    tr_a = clean(window(pjm_a, "2016-01-01", "2017-11-30"), "train_2016_2017")
    tr_a.to_csv(f"{BASE}/load/train_2016_2017_pjm_load_eia930.csv", index=False)
    qa_load("train_2016_2017", tr_a)
    ev_a = clean(window(pjm_a, "2017-12-01", "2018-02-28"), "eval_2017dec_2018feb")
    ev_a.to_csv(f"{BASE}/load/eval_2017dec_2018feb_pjm_load_eia930.csv", index=False)
    qa_load("eval_2017dec_2018feb", ev_a)

    pjm_b = load_pjm(["EIA930_BALANCE_2020_Jan_Jun.csv", "EIA930_BALANCE_2020_Jul_Dec.csv",
                      "EIA930_BALANCE_2021_Jan_Jun.csv", "EIA930_BALANCE_2021_Jul_Dec.csv",
                      "EIA930_BALANCE_2022_Jul_Dec.csv", "EIA930_BALANCE_2023_Jan_Jun.csv"])
    tr_b = clean(window(pjm_b, "2020-01-01", "2021-12-31"), "train_2020_2021")
    tr_b.to_csv(f"{BASE}/load/train_2020_2021_pjm_load_eia930.csv", index=False)
    qa_load("train_2020_2021", tr_b)
    ev_b = clean(window(pjm_b, "2022-12-01", "2023-02-28"), "eval_2022dec_2023feb")
    ev_b.to_csv(f"{BASE}/load/eval_2022dec_2023feb_pjm_load_eia930.csv", index=False)
    qa_load("eval_2022dec_2023feb", ev_b)
    print("LOAD DONE", flush=True)

# ---------------- Weather: Open-Meteo archive (ERA5), footprint point-grid mean ----------------
LATS = [40.0, 41.25, 42.5]
LONS = [-88.0, -84.5, -81.0, -77.5, -74.0]
POINTS = [(la, lo) for la in LATS for lo in LONS]

def fetch_chunk(tag, d0, d1):
    path = f"{CHUNKS}/{tag}.csv"
    if os.path.exists(path):
        print(f"WEATHER {tag}: chunk exists, skip", flush=True)
        return
    lat_s = ",".join(str(p[0]) for p in POINTS)
    lon_s = ",".join(str(p[1]) for p in POINTS)
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat_s}&longitude={lon_s}&start_date={d0}&end_date={d1}"
           "&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m"
           "&models=era5&timezone=UTC&wind_speed_unit=ms")
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=600) as r:
                data = json.loads(r.read().decode())
            break
        except Exception as e:
            last_err = e
            print(f"WEATHER {tag}: attempt {attempt+1} failed: {e}", flush=True)
            time.sleep(20)
    else:
        raise RuntimeError(f"chunk {tag} failed after retries: {last_err}")
    if isinstance(data, dict):
        data = [data]
    frames = []
    for loc in data:
        h = loc["hourly"]
        t = pd.DataFrame({
            "timestamp_utc": pd.to_datetime(h["time"], utc=True),
            "t2m_c": h["temperature_2m"],
            "d2m_c": h["dew_point_2m"],
            "ws_ms": h["wind_speed_10m"],
            "wd_deg": h["wind_direction_10m"],
        })
        rad = t["wd_deg"] * math.pi / 180.0
        t["u10_ms"] = -t["ws_ms"] * rad.map(math.sin)
        t["v10_ms"] = -t["ws_ms"] * rad.map(math.cos)
        frames.append(t)
    allp = pd.concat(frames)
    agg = allp.groupby("timestamp_utc").agg(
        t2m_c=("t2m_c", "mean"), d2m_c=("d2m_c", "mean"),
        u10_ms=("u10_ms", "mean"), v10_ms=("v10_ms", "mean"),
        wind_speed_ms=("ws_ms", "mean"), n_points=("t2m_c", "count")).reset_index()
    agg["temperature_f"] = agg["t2m_c"] * 9 / 5 + 32
    agg["wind_speed_mph"] = agg["wind_speed_ms"] * 2.23694
    agg = agg[["timestamp_utc", "t2m_c", "d2m_c", "u10_ms", "v10_ms",
               "wind_speed_ms", "temperature_f", "wind_speed_mph", "n_points"]]
    agg.to_csv(path, index=False)
    print(f"WEATHER {tag}: rows={len(agg)} {d0}..{d1} points={agg['n_points'].iloc[0]} "
          f"min_t2m={agg['t2m_c'].min():.1f}C max_t2m={agg['t2m_c'].max():.1f}C "
          f"nan_rows={int(agg['t2m_c'].isna().sum())}", flush=True)

# priority order: evaluation windows first, then training years
CHUNK_PLAN = [
    ("eval18", "2017-12-01", "2018-02-28"),
    ("eval22", "2022-12-01", "2023-02-28"),
    ("train16", "2016-01-01", "2016-12-31"),
    ("train17", "2017-01-01", "2017-11-30"),
    ("train20", "2020-01-01", "2020-12-31"),
    ("train21", "2021-01-01", "2021-12-31"),
    ("pre22", "2022-01-01", "2022-11-30"),
]

def build_weather():
    for tag, d0, d1 in CHUNK_PLAN:
        fetch_chunk(tag, d0, d1)
    print("WEATHER DONE", flush=True)

def assemble():
    def span(tags, out_name):
        frames = [pd.read_csv(f"{CHUNKS}/{t}.csv", parse_dates=["timestamp_utc"]) for t in tags]
        w = pd.concat(frames, ignore_index=True).sort_values("timestamp_utc") \
              .drop_duplicates(subset=["timestamp_utc"]).reset_index(drop=True)
        span_h = int((w["timestamp_utc"].iloc[-1] - w["timestamp_utc"].iloc[0]).total_seconds() // 3600) + 1
        gaps = int((w["timestamp_utc"].diff().dt.total_seconds().dropna() != 3600).sum())
        w.to_csv(f"{BASE}/weather/{out_name}", index=False)
        print(f"SPAN {out_name}: rows={len(w)} utc_span_hours={span_h} missing_hours={span_h-len(w)} "
              f"gap_breaks={gaps} nan_t2m={int(w['t2m_c'].isna().sum())} "
              f"points_min={int(w['n_points'].min())} points_max={int(w['n_points'].max())}", flush=True)
    span(["train16", "train17", "eval18"], "span2016_2018feb_weather_openmeteo_era5_footprint_mean.csv")
    span(["train20", "train21", "pre22", "eval22"], "span2020_2023feb_weather_openmeteo_era5_footprint_mean.csv")
    print("ASSEMBLE DONE", flush=True)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("load", "all"):
        build_load()
    if mode in ("weather", "all"):
        build_weather()
    if mode in ("assemble", "all"):
        assemble()
