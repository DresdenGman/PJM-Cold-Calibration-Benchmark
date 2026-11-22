"""A8 fetcher. Mode 'ctl': control-member 2 m temperature and 10 m wind (u, v);
mode 'ens': 2 m temperature of all members used for spread. Forecast hours 24-54, every 6 h,
00 UTC run; values bilinearly interpolated to the 30 footprint points (PJM 15, MISO 15).
Sources: GEFSv12 reforecast (<= 2019-12-31), operational GEFS v11 (2020-01-01..2020-09-22),
operational GEFS v12 (>= 2020-09-23).
Usage: fetch_a8.py MODE START END [--workers N]"""
import argparse, os, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _a5_fetch_ref import get, interp, PTS   # same HTTP retry, decoding and interpolation as A5

HERE = os.path.dirname(os.path.abspath(__file__))
OPS = "https://noaa-gefs-pds.s3.amazonaws.com"
RFC = "https://noaa-gefs-retrospective.s3.amazonaws.com/GEFSv12/reforecast"
FHS = [24, 30, 36, 42, 48, 54]
V12 = dt.date(2020, 9, 23); RFC_END = dt.date(2019, 12, 31)
KEYS = {"TMP": ":TMP:2 m above ground:", "UGRD": ":UGRD:10 m above ground:", "VGRD": ":VGRD:10 m above ground:"}

def source(day):
    return "rfc" if day <= RFC_END else ("v11" if day < V12 else "v12")

def members(day, mode):
    s = source(day)
    if mode == "ctl":
        return ["c00"] if s == "rfc" else ["gec00"]
    if s == "rfc":
        return ["c00", "p01", "p02", "p03", "p04"]
    n = 30 if s == "v12" else 20
    return ["gec00"] + [f"gep{i:02d}" for i in range(1, n + 1)]

def find_ranges(idx_text, key, fh):
    lines = idx_text.splitlines()
    for k, line in enumerate(lines):
        if key in line and f":{fh} hour fcst:" in line:
            start = int(line.split(":")[1])
            end = int(lines[k + 1].split(":")[1]) - 1 if k + 1 < len(lines) else ""
            return start, end
    return None

_idx_cache = {}
def idx_of(url):
    if url not in _idx_cache:
        r = get(url + ".idx"); _idx_cache[url] = r.decode() if r else None
    return _idx_cache[url]

def one(day, m, var, fh):
    d = day.strftime("%Y%m%d"); s = source(day)
    if s == "rfc":
        fname = {"TMP": "tmp_2m", "UGRD": "ugrd_hgt", "VGRD": "vgrd_hgt"}[var]
        urls = [f"{RFC}/{day.year}/{d}00/{m}/Days:1-10/{fname}_{d}00_{m}.grib2"]
    elif s == "v11":
        urls = [f"{OPS}/gefs.{d}/00/pgrb2a/{m}.t00z.pgrb2af{fh:02d}", f"{OPS}/gefs.{d}/00/pgrb2a/{m}.t00z.pgrb2af{fh:03d}"]
    else:
        urls = [f"{OPS}/gefs.{d}/00/atmos/pgrb2ap5/{m}.t00z.pgrb2a.0p50.f{fh:03d}"]
    for url in urls:
        idx = idx_of(url)
        if idx is None:
            continue
        rg = find_ranges(idx, KEYS[var], fh)
        if rg is None:
            continue
        msg = get(url, rg)
        return [day.isoformat(), m, var, fh] + [f"{x:.3f}" for x in interp(msg)]
    return None

def cycle(day, mode, pool):
    out = os.path.join(HERE, f"raw_{mode}", f"{day.isoformat()}.csv")
    if os.path.exists(out):
        return "skip"
    vars_ = ["TMP", "UGRD", "VGRD"] if mode == "ctl" else ["TMP"]
    jobs = [(day, m, v, fh) for m in members(day, mode) for v in vars_ for fh in FHS]
    rows = list(pool.map(lambda a: one(*a), jobs))
    _idx_cache.clear()
    ok = [r for r in rows if r is not None]
    if not ok:
        open(out + ".missing", "w").write("none\n"); return "missing"
    hdr = "cycle,member,var,fh," + ",".join(f"p{i}" for i in range(len(PTS)))
    with open(out + ".tmp", "w") as f:
        f.write(hdr + "\n" + "\n".join(",".join(map(str, r)) for r in ok) + "\n")
    os.replace(out + ".tmp", out)
    return f"{len(ok)}/{len(jobs)}"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["ctl", "ens"]); ap.add_argument("start"); ap.add_argument("end")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    d, d1 = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    with ThreadPoolExecutor(a.workers) as pool:
        while d <= d1:
            t = time.time(); r = cycle(d, a.mode, pool)
            print(d, r, f"{time.time()-t:.1f}s", flush=True)
            d += dt.timedelta(days=1)
