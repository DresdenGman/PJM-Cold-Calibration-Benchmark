"""A5: hourly ensemble spread z_t for every row of an era frame.

z_t = SD (ddof=1) across members of the footprint-mean 2 m temperature, from the
00 UTC cycle of local date d-1 for target local date d, linearly interpolated in
forecast hour (24-54, 6-hourly). Returns a float array aligned with the frame
(NaN where no cycle is available) and a dict of counts.
"""
import os, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
COLS = {"PJM": [f"p{i}" for i in range(15)], "MISO": [f"p{i}" for i in range(15, 30)]}

_cache = {}
def cycle_table(system):
    """{cycle_date: (fh array, sd array, n_members)}"""
    if system in _cache:
        return _cache[system]
    out = {}
    raw = sorted(glob.glob(os.path.join(HERE, "raw", "*.csv")))
    if raw:
        frames = [(os.path.basename(f)[:10], pd.read_csv(f)) for f in raw]
    else:   # repository copy: all cycles in one file
        allc = pd.read_csv(os.path.join(HERE, "data", "gefs_t2m_footprint_points.csv.gz"))
        frames = [(c, d) for c, d in allc.groupby("cycle")]
    for name, d in frames:
        if d.empty:
            continue
        d["fm"] = d[COLS[system]].mean(axis=1)
        g = d.groupby("fh")["fm"]
        sd = g.std(ddof=1); n = g.count()
        out[pd.Timestamp(name).date()] = (
            sd.index.values.astype(float), sd.values, int(n.min()))
    _cache[system] = out
    return out

def spread_for_frame(frame, system):
    tab = cycle_table(system)
    loc_date = frame["ts_local"].dt.date.values
    ts_utc = pd.to_datetime(frame["ts_utc"], utc=True)
    z = np.full(len(frame), np.nan)
    nmem = np.zeros(len(frame), dtype=int)
    for i, (d, t) in enumerate(zip(loc_date, ts_utc)):
        cyc = d - pd.Timedelta(days=1).to_pytimedelta()
        if cyc not in tab:
            continue
        fh, sd, nm = tab[cyc]
        lead = (t - pd.Timestamp(cyc, tz="UTC")).total_seconds() / 3600.0
        if lead < fh.min() or lead > fh.max():
            continue
        z[i] = np.interp(lead, fh, sd); nmem[i] = nm
    return z, nmem
