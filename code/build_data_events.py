#!/usr/bin/env python3
"""Data builder: PJM load (EIA-930) + footprint weather (Open-Meteo ERA5)
for the 2015 / 2018 / 2022 cold events. Event windows are event +/- 14 days (local dates)."""
import json, math, os, urllib.request
import pandas as pd

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events")
RAW = f"{BASE}/_raw_eia930"

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

def qa_load(name, w, archive_peak_mw, archive_peak_local):
    gaps = int((w["timestamp_utc_end_of_hour"].diff().dt.total_seconds().dropna() != 3600).sum())
    imax = w["demand_mw"].idxmax()
    print(f"LOAD {name}: rows={len(w)} gap_breaks={gaps} nan_demand={int(w['demand_mw'].isna().sum())}")
    print(f"  max demand={w.loc[imax,'demand_mw']:.1f} MW at local {w.loc[imax,'timestamp_local_end_of_hour']} "
          f"| archive peak={archive_peak_mw} MW at {archive_peak_local} | delta={w.loc[imax,'demand_mw']-archive_peak_mw:+.1f} MW")

pjm18 = load_pjm(["EIA930_BALANCE_2017_Jul_Dec.csv", "EIA930_BALANCE_2018_Jan_Jun.csv"])
w18 = window(pjm18, "2017-12-14", "2018-01-21")
w18.to_csv(f"{BASE}/load/E2018_pjm_load_eia930.csv", index=False)
qa_load("E2018", w18, 137465.3, "2018-01-05 23:00")

pjm22 = load_pjm(["EIA930_BALANCE_2022_Jul_Dec.csv", "EIA930_BALANCE_2023_Jan_Jun.csv"])
w22 = window(pjm22, "2022-12-09", "2023-01-09")
w22.to_csv(f"{BASE}/load/E2022_pjm_load_eia930.csv", index=False)
qa_load("E2022", w22, 134699.1, "2022-12-23 23:00")

# ---------------- Weather: Open-Meteo archive (ERA5), footprint point-grid mean ----------------
LATS = [40.0, 41.25, 42.5]
LONS = [-88.0, -84.5, -81.0, -77.5, -74.0]
POINTS = [(la, lo) for la in LATS for lo in LONS]

def fetch_weather(tag, d0, d1):
    lat_s = ",".join(str(p[0]) for p in POINTS)
    lon_s = ",".join(str(p[1]) for p in POINTS)
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat_s}&longitude={lon_s}&start_date={d0}&end_date={d1}"
           "&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m"
           "&models=era5&timezone=UTC&wind_speed_unit=ms")
    with urllib.request.urlopen(url, timeout=300) as r:
        data = json.loads(r.read().decode())
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
    agg.to_csv(f"{BASE}/weather/{tag}_weather_openmeteo_era5_footprint_mean.csv", index=False)
    print(f"WEATHER {tag}: rows={len(agg)} points={agg['n_points'].iloc[0]} "
          f"min_t2m={agg['t2m_c'].min():.1f}C max_t2m={agg['t2m_c'].max():.1f}C "
          f"nan_rows={int(agg['t2m_c'].isna().sum())}")

fetch_weather("E2015", "2015-02-06", "2015-03-06")
fetch_weather("E2018", "2017-12-14", "2018-01-21")
fetch_weather("E2022", "2022-12-09", "2023-01-09")
print("DONE")
