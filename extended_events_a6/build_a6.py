"""A6 builder: EIA-930 load and ERA5 (Open-Meteo) footprint weather for the new eras.
Mirrors build_data_spans.py / build_miso.py: same columns, cleaning thresholds and points.
Usage: build_a6.py RAWDIR"""
import json, math, os, sys, time, urllib.request
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = sys.argv[1]
USECOLS = ["Balancing Authority", "Data Date", "Hour Number", "Local Time at End of Hour",
           "UTC Time at End of Hour", "Demand Forecast (MW)", "Demand (MW)",
           "Net Generation (MW)", "Total Interchange (MW)"]
SYS = {"pjm": dict(ba="PJM", glitch=170000.0, lats=[40.0, 41.25, 42.5], lons=[-88.0, -84.5, -81.0, -77.5, -74.0]),
       "miso": dict(ba="MISO", glitch=150000.0, lats=[38.5, 41.5, 44.5], lons=[-95.5, -93.0, -90.5, -88.0, -85.5])}
ERAS = {"2019": ("2017-01-01", "2018-11-30", "2018-12-01", "2019-02-28"),
        "2024": ("2022-01-01", "2023-11-30", "2023-12-01", "2024-02-29"),
        "2025": ("2023-01-01", "2024-11-30", "2024-12-01", "2025-02-28"),
        "2026": ("2024-01-01", "2025-11-30", "2025-12-01", "2026-02-28")}
SYS_ERAS = {"pjm": ["2019", "2024", "2025", "2026"], "miso": ["2024", "2025", "2026"]}
FILES = ["2016_Jul_Dec", "2017_Jan_Jun", "2017_Jul_Dec", "2018_Jan_Jun", "2018_Jul_Dec", "2019_Jan_Jun",
         "2021_Jul_Dec", "2022_Jan_Jun", "2022_Jul_Dec", "2023_Jan_Jun", "2023_Jul_Dec", "2024_Jan_Jun",
         "2024_Jul_Dec", "2025_Jan_Jun", "2025_Jul_Dec", "2026_Jan_Jun"]

def load_ba(ba, files):
    fr = []
    for f in files:
        df = pd.read_csv(f"{RAW}/EIA930_BALANCE_{f}.csv", usecols=USECOLS, low_memory=False)
        fr.append(df[df["Balancing Authority"] == ba].copy())
    out = pd.concat(fr, ignore_index=True)
    for c in ["Demand Forecast (MW)", "Demand (MW)", "Net Generation (MW)", "Total Interchange (MW)"]:
        out[c] = pd.to_numeric(out[c].astype(str).str.replace(",", ""), errors="coerce")
    out["ts_utc"] = pd.to_datetime(out["UTC Time at End of Hour"], utc=True)
    out["ts_local"] = pd.to_datetime(out["Local Time at End of Hour"])
    return out.sort_values("ts_utc").drop_duplicates(subset=["ts_utc"]).reset_index(drop=True)

def window(df, d0, d1):
    ld = df["ts_local"].dt.date
    m = (ld >= pd.Timestamp(d0).date()) & (ld <= pd.Timestamp(d1).date())
    w = df.loc[m, ["ts_utc", "ts_local", "Demand (MW)", "Demand Forecast (MW)",
                   "Net Generation (MW)", "Total Interchange (MW)"]].copy()
    w.columns = ["timestamp_utc_end_of_hour", "timestamp_local_end_of_hour", "demand_mw",
                 "demand_forecast_mw", "net_generation_mw", "total_interchange_mw"]
    return w

def clean(w, name, glitch):
    for col in ["demand_mw", "demand_forecast_mw", "net_generation_mw"]:
        n = int((w[col].abs() > glitch).sum())
        if n: print(f"CLEAN {name}: {col} {n} values > {glitch:.0f} -> NaN")
        w.loc[w[col].abs() > glitch, col] = float("nan")
    return w

def qa(name, w):
    span = int((w["timestamp_utc_end_of_hour"].iloc[-1] - w["timestamp_utc_end_of_hour"].iloc[0]).total_seconds() // 3600) + 1
    print(f"LOAD {name}: rows={len(w)} span_h={span} missing={span-len(w)} nan_demand={int(w['demand_mw'].isna().sum())}")

def fetch(sysname, tag, d0, d1):
    s = SYS[sysname]; path = f"{HERE}/{sysname}/data_events/weather/_chunks/{tag}.csv"
    if os.path.exists(path):
        c = pd.read_csv(path); c["timestamp_utc"] = pd.to_datetime(c["timestamp_utc"], utc=True); return c
    pts = [(a, o) for a in s["lats"] for o in s["lons"]]
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={','.join(str(p[0]) for p in pts)}&longitude={','.join(str(p[1]) for p in pts)}"
           f"&start_date={d0}&end_date={d1}"
           "&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m"
           "&models=era5&timezone=UTC&wind_speed_unit=ms")
    for k in range(5):
        try:
            data = json.loads(urllib.request.urlopen(url, timeout=600).read().decode()); break
        except Exception as e:
            print(f"WEATHER {tag} retry {k}: {e}"); time.sleep(30 * (k + 1))
    else:
        raise SystemExit(f"weather {tag} failed")
    data = data if isinstance(data, list) else [data]
    fr = []
    for loc in data:
        h = loc["hourly"]
        t = pd.DataFrame({"timestamp_utc": pd.to_datetime(h["time"], utc=True), "t2m_c": h["temperature_2m"],
                          "d2m_c": h["dew_point_2m"], "ws_ms": h["wind_speed_10m"], "wd_deg": h["wind_direction_10m"]})
        rad = t["wd_deg"] * math.pi / 180.0
        t["u10_ms"] = -t["ws_ms"] * rad.map(math.sin); t["v10_ms"] = -t["ws_ms"] * rad.map(math.cos)
        fr.append(t)
    allp = pd.concat(fr)
    agg = allp.groupby("timestamp_utc").agg(t2m_c=("t2m_c", "mean"), d2m_c=("d2m_c", "mean"),
          u10_ms=("u10_ms", "mean"), v10_ms=("v10_ms", "mean"), wind_speed_ms=("ws_ms", "mean"),
          n_points=("t2m_c", "count")).reset_index()
    agg["temperature_f"] = agg["t2m_c"] * 9 / 5 + 32
    agg["wind_speed_mph"] = agg["wind_speed_ms"] * 2.23694
    agg.to_csv(path, index=False)
    print(f"WEATHER {tag}: rows={len(agg)} points={int(agg['n_points'].min())} nan={int(agg['t2m_c'].isna().sum())}")
    time.sleep(3)
    return agg

if __name__ == "__main__":
    for sysname, eras in SYS_ERAS.items():
        s = SYS[sysname]
        df = load_ba(s["ba"], FILES)
        for era in eras:
            t0, t1, e0, e1 = ERAS[era]
            for nm, a, b in [(f"train_{era}", t0, t1), (f"eval_{era}", e0, e1)]:
                w = clean(window(df, a, b), f"{sysname} {nm}", s["glitch"])
                w.to_csv(f"{HERE}/{sysname}/data_events/load/{nm}_{sysname}_load_eia930.csv", index=False); qa(f"{sysname} {nm}", w)
            y0, y1 = int(t0[:4]), int(e1[:4])
            parts = [fetch(sysname, f"{y}_{(f'{y}-12-31' if y < y1 else e1)}", f"{y}-01-01", f"{y}-12-31" if y < y1 else e1) for y in range(y0, y1 + 1)]
            w = pd.concat(parts).drop_duplicates("timestamp_utc").sort_values("timestamp_utc")
            w["timestamp_utc"] = pd.to_datetime(w["timestamp_utc"], utc=True)
            w = w[(w.timestamp_utc >= pd.Timestamp(t0, tz="UTC")) & (w.timestamp_utc < pd.Timestamp(e1, tz="UTC") + pd.Timedelta(days=1))]
            w.to_csv(f"{HERE}/{sysname}/data_events/weather/w{era}_{sysname}.csv", index=False)
            print(f"SPAN {sysname} {era}: rows={len(w)}")
    print("BUILD DONE")
