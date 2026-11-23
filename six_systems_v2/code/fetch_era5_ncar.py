"""ERA5 footprint means from the NSF NCAR ERA5 mirror on AWS (s3://nsf-ncar-era5, public, ds633.0),
read remotely chunk by chunk (no full-file download). Same output format as the Open-Meteo fetcher.
Usage: fetch_era5_ncar.py SYSTEM YYYYMM [YYYYMM ...] OUTCSV"""
import sys, calendar
import numpy as np, pandas as pd, fsspec, h5py
system, months, out = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
PTS = {"isone": ([41.5, 42.5, 43.5], [-73.0, -72.0, -71.0, -70.5, -70.0])}[system]
lats, lons = PTS; pts = [(la, lo) for la in lats for lo in lons]
VAR = {"2t": ("128_167_2t", "VAR_2T"), "10u": ("128_165_10u", "VAR_10U"), "10v": ("128_166_10v", "VAR_10V")}
frames = []
for ym in months:
    y, m = int(ym[:4]), int(ym[4:]); last = calendar.monthrange(y, m)[1]
    vals = {}
    for v, (code, name) in VAR.items():
        u = f"https://nsf-ncar-era5.s3.amazonaws.com/e5.oper.an.sfc/{ym}/e5.oper.an.sfc.{code}.ll025sc.{ym}0100_{ym}{last:02d}23.nc"
        with fsspec.open(u, block_size=4 * 2**20).open() as f, h5py.File(f, "r") as h:
            la, lo = h["latitude"][:], h["longitude"][:]
            i0, i1 = int(np.where(la == max(lats))[0][0]), int(np.where(la == min(lats))[0][0])
            j0, j1 = int(np.where(lo == min(lons) % 360)[0][0]), int(np.where(lo == max(lons) % 360)[0][0])
            blk = h[name][:, i0:i1 + 1, j0:j1 + 1].astype(float)
            t = pd.to_datetime(h["utc_date"][:].astype(str), format="%Y%m%d%H", utc=True)
            sub = np.stack([blk[:, int(np.where(la[i0:i1+1] == p[0])[0][0]), int(np.where(lo[j0:j1+1] == p[1] % 360)[0][0])] for p in pts], axis=1)
            vals[v] = (t, sub); print(ym, v, sub.shape, flush=True)
    t = vals["2t"][0]
    tc = (vals["2t"][1] - 273.15).mean(axis=1); ws = np.hypot(vals["10u"][1], vals["10v"][1]).mean(axis=1)
    frames.append(pd.DataFrame({"timestamp_utc": t, "t2m_c": tc, "wind_speed_ms": ws, "n_points": len(pts)}))
D = pd.concat(frames); D["temperature_f"] = D.t2m_c * 9 / 5 + 32; D["wind_speed_mph"] = D.wind_speed_ms * 2.2369362920544
D.to_csv(out, index=False); print("wrote", out, len(D))
