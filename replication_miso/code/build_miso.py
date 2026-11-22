"""A4 builder: MISO load (EIA-930) and ERA5 footprint weather, per PRESPEC_A4_MISO.md.
Mirrors build_data_spans.py; only the BA code, glitch threshold and grid points differ."""
import json, math, os, sys, time, urllib.request
import pandas as pd
ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = sys.argv[1]
OUT = f"{ROOT}/data_events"
USECOLS = ["Balancing Authority", "Data Date", "Hour Number", "Local Time at End of Hour",
           "UTC Time at End of Hour", "Demand Forecast (MW)", "Demand (MW)",
           "Net Generation (MW)", "Total Interchange (MW)"]
GLITCH = 150000.0

def load_ba(files, ba="MISO"):
    fr = []
    for f in files:
        df = pd.read_csv(f"{RAW}/{f}", usecols=USECOLS, low_memory=False)
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

def clean(w, name):
    for col in ["demand_mw", "demand_forecast_mw", "net_generation_mw"]:
        bad = w[w[col].abs() > GLITCH]
        for _, r in bad.iterrows():
            print(f"CLEAN {name}: {col} at {r['timestamp_local_end_of_hour']} value {r[col]} -> NaN")
        w.loc[w[col].abs() > GLITCH, col] = float("nan")
    return w

def qa(name, w):
    span = int((w["timestamp_utc_end_of_hour"].iloc[-1] - w["timestamp_utc_end_of_hour"].iloc[0]).total_seconds() // 3600) + 1
    print(f"LOAD {name}: rows={len(w)} span_h={span} missing={span-len(w)} "
          f"nan_demand={int(w['demand_mw'].isna().sum())} nan_fcst={int(w['demand_forecast_mw'].isna().sum())}")

def build_load():
    f16_18 = ["EIA930_BALANCE_2016_Jan_Jun.csv", "EIA930_BALANCE_2016_Jul_Dec.csv",
              "EIA930_BALANCE_2017_Jan_Jun.csv", "EIA930_BALANCE_2017_Jul_Dec.csv",
              "EIA930_BALANCE_2018_Jan_Jun.csv", "EIA930_BALANCE_2018_Jul_Dec.csv",
              "EIA930_BALANCE_2019_Jan_Jun.csv"]
    a = load_ba(f16_18)
    for name, d0, d1 in [("train_2016_2017", "2016-01-01", "2017-11-30"),
                         ("eval_2017dec_2018feb", "2017-12-01", "2018-02-28"),
                         ("train_2017_2018", "2017-01-01", "2018-11-30"),
                         ("eval_2018dec_2019feb", "2018-12-01", "2019-02-28")]:
        w = clean(window(a, d0, d1), name); w.to_csv(f"{OUT}/load/{name}_miso_load_eia930.csv", index=False); qa(name, w)
    b = load_ba(["EIA930_BALANCE_2020_Jan_Jun.csv", "EIA930_BALANCE_2020_Jul_Dec.csv",
                 "EIA930_BALANCE_2021_Jan_Jun.csv", "EIA930_BALANCE_2021_Jul_Dec.csv",
                 "EIA930_BALANCE_2022_Jul_Dec.csv", "EIA930_BALANCE_2023_Jan_Jun.csv"])
    for name, d0, d1 in [("train_2020_2021", "2020-01-01", "2021-12-31"),
                         ("eval_2022dec_2023feb", "2022-12-01", "2023-02-28")]:
        w = clean(window(b, d0, d1), name); w.to_csv(f"{OUT}/load/{name}_miso_load_eia930.csv", index=False); qa(name, w)

LATS = [38.5, 41.5, 44.5]
LONS = [-95.5, -93.0, -90.5, -88.0, -85.5]
POINTS = [(la, lo) for la in LATS for lo in LONS]

def fetch(tag, d0, d1):
    path = f"{OUT}/weather/_chunks/{tag}.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    lat_s = ",".join(str(p[0]) for p in POINTS); lon_s = ",".join(str(p[1]) for p in POINTS)
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={lat_s}&longitude={lon_s}&start_date={d0}&end_date={d1}"
           "&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m"
           "&models=era5&timezone=UTC&wind_speed_unit=ms")
    for k in range(4):
        try:
            data = json.loads(urllib.request.urlopen(url, timeout=600).read().decode()); break
        except Exception as e:
            print(f"WEATHER {tag} retry {k}: {e}"); time.sleep(20 * (k + 1))
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
    time.sleep(2)
    return agg

def build_weather():
    for span, years in [("span2016_2019feb", [("2016-01-01", "2016-12-31"), ("2017-01-01", "2017-12-31"),
                                               ("2018-01-01", "2018-12-31"), ("2019-01-01", "2019-02-28")]),
                        ("span2020_2023feb", [("2020-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31"),
                                               ("2022-01-01", "2022-12-31"), ("2023-01-01", "2023-02-28")])]:
        parts = [fetch(f"{span}_{d0[:4]}", d0, d1) for d0, d1 in years]
        w = pd.concat(parts).drop_duplicates("timestamp_utc").sort_values("timestamp_utc")
        w.to_csv(f"{OUT}/weather/{span}_weather_openmeteo_era5_miso_footprint_mean.csv", index=False)
        print(f"SPAN {span}: rows={len(w)}")

if __name__ == "__main__":
    build_load(); build_weather(); print("BUILD DONE")
