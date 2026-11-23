"""A9: ERA5 footprint means (Open-Meteo archive) for 2015-07-01..2026-02-28, PJM and MISO.
Same points, variables and aggregation as the existing builders."""
import json, os, time, subprocess
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
SYS = {"ercot": ([29.5, 31.0, 32.5], [-98.5, -97.5, -96.5, -95.5, -94.5]),
       "spp": ([35.5, 37.5, 39.5], [-99.5, -98.0, -96.5, -95.0, -93.5]),
       "nyiso": ([40.75, 42.0, 43.0], [-79.0, -77.0, -75.5, -74.5, -73.75]),
       "isone": ([41.5, 42.5, 43.5], [-73.0, -72.0, -71.0, -70.5, -70.0])}
def fetch(sysname, d0, d1):
    path = f"{HERE}/era5/{sysname}_{d0}_{d1}.csv"
    if os.path.exists(path): return
    lats, lons = SYS[sysname]; pts = [(a, o) for a in lats for o in lons]
    url = ("https://archive-api.open-meteo.com/v1/archive"
           f"?latitude={','.join(str(p[0]) for p in pts)}&longitude={','.join(str(p[1]) for p in pts)}"
           f"&start_date={d0}&end_date={d1}&hourly=temperature_2m,dew_point_2m,wind_speed_10m,wind_direction_10m"
           "&models=era5&timezone=UTC&wind_speed_unit=ms")
    for k in range(6):
        try:
            data = json.loads(subprocess.run([('curl.exe' if os.name == 'nt' else 'curl'), '-sSfL', '--max-time', '600', url], check=True, capture_output=True).stdout.decode()); break
        except Exception as e:
            print(f"{sysname} {d0} retry {k}: {e}", flush=True); time.sleep(60 * (k + 1))
    else:
        raise SystemExit(f"failed {sysname} {d0}")
    data = data if isinstance(data, list) else [data]
    fr = [pd.DataFrame({"timestamp_utc": pd.to_datetime(l["hourly"]["time"], utc=True), "t2m_c": l["hourly"]["temperature_2m"],
                        "ws_ms": l["hourly"]["wind_speed_10m"]}) for l in data]
    agg = pd.concat(fr).groupby("timestamp_utc").agg(t2m_c=("t2m_c", "mean"), wind_speed_ms=("ws_ms", "mean"),
                                                     n_points=("t2m_c", "count")).reset_index()
    agg["temperature_f"] = agg["t2m_c"] * 9 / 5 + 32
    agg["wind_speed_mph"] = agg["wind_speed_ms"] * 2.23694
    agg.to_csv(path, index=False)
    print(f"{sysname} {d0}..{d1}: rows={len(agg)} points={int(agg.n_points.min())} nan={int(agg.t2m_c.isna().sum())}", flush=True)
    time.sleep(20)
if __name__ == "__main__":
    for s in ["ercot", "spp", "nyiso", "isone"]:
        for y in range(2015, 2027):
            d0 = "2015-07-01" if y == 2015 else f"{y}-01-01"; d1 = "2026-02-28" if y == 2026 else f"{y}-12-31"
            fetch(s, d0, d1)
    print("ERA5 DONE")
