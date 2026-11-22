"""A5: fetch GEFS 2 m temperature at the PJM and MISO footprint points.

For each 00 UTC cycle, each member and forecast hours 24-54 (6-hourly), read the
TMP:2 m message by byte range (from the .idx), decode with ecCodes, interpolate
bilinearly to the 30 footprint points, and write one CSV per cycle to raw/.
Usage: fetch_gefs.py START END [--workers N]   (dates YYYY-MM-DD, inclusive)
"""
import argparse, os, sys, time, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import eccodes

BASE = "https://noaa-gefs-pds.s3.amazonaws.com"
HERE = os.path.dirname(os.path.abspath(__file__))
FHS = [24, 30, 36, 42, 48, 54]
PJM = [(a, o) for a in [40.0, 41.25, 42.5] for o in [-88.0, -84.5, -81.0, -77.5, -74.0]]
MISO = [(a, o) for a in [38.5, 41.5, 44.5] for o in [-95.5, -93.0, -90.5, -88.0, -85.5]]
PTS = PJM + MISO
V12_START = dt.date(2020, 9, 23)

def get(url, rng=None, tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(url)
            if rng:
                req.add_header("Range", f"bytes={rng[0]}-{rng[1]}")
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(1.5 * (k + 1))
        except Exception:
            time.sleep(1.5 * (k + 1))
    raise RuntimeError(f"failed {url}")

def layouts(day):
    d = day.strftime("%Y%m%d")
    if day >= V12_START:
        return [lambda m, fh: f"{BASE}/gefs.{d}/00/atmos/pgrb2ap5/{m}.t00z.pgrb2a.0p50.f{fh:03d}"]
    return [lambda m, fh: f"{BASE}/gefs.{d}/00/pgrb2a/{m}.t00z.pgrb2af{fh:03d}",
            lambda m, fh: f"{BASE}/gefs.{d}/00/pgrb2a/{m}.t00z.pgrb2af{fh:02d}",
            lambda m, fh: f"{BASE}/gefs.{d}/00/{m}.t00z.pgrb2af{fh:03d}"]

def members(day):
    n = 30 if day >= V12_START else 20
    return ["gec00"] + [f"gep{i:02d}" for i in range(1, n + 1)]

def interp(msg):
    gid = eccodes.codes_new_from_message(msg)
    try:
        ni = eccodes.codes_get(gid, "Ni"); nj = eccodes.codes_get(gid, "Nj")
        la0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
        lo0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
        dla = eccodes.codes_get(gid, "jDirectionIncrementInDegrees")
        dlo = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
        jpos = eccodes.codes_get(gid, "jScansPositively")
        v = eccodes.codes_get_values(gid).reshape(nj, ni) - 273.15
    finally:
        eccodes.codes_release(gid)
    out = []
    for lat, lon in PTS:
        lon = lon % 360.0
        fj = (lat - la0) / dla if jpos else (la0 - lat) / dla
        fi = ((lon - lo0) % 360.0) / dlo
        j0, i0 = int(np.floor(fj)), int(np.floor(fi))
        wj, wi = fj - j0, fi - i0
        i1 = (i0 + 1) % ni
        val = ((1 - wj) * ((1 - wi) * v[j0, i0] + wi * v[j0, i1])
               + wj * ((1 - wi) * v[j0 + 1, i0] + wi * v[j0 + 1, i1]))
        out.append(val)
    return out

def one(day, lay, m, fh):
    url = lay(m, fh)
    idx = get(url + ".idx")
    if idx is None:
        return None
    lines = idx.decode().splitlines()
    for k, line in enumerate(lines):
        if ":TMP:2 m above ground:" in line:
            start = int(line.split(":")[1])
            end = int(lines[k + 1].split(":")[1]) - 1 if k + 1 < len(lines) else ""
            msg = get(url, (start, end))
            return [day.isoformat(), m, fh] + [f"{x:.3f}" for x in interp(msg)]
    return None

def cycle(day, pool):
    out = os.path.join(HERE, "raw", f"{day.isoformat()}.csv")
    if os.path.exists(out):
        return "skip"
    lay = None
    for L in layouts(day):
        if get(L("gec00", 24) + ".idx") is not None:
            lay = L; break
    if lay is None:
        open(out + ".missing", "w").write("no cycle\n"); return "missing"
    jobs = [(day, lay, m, fh) for m in members(day) for fh in FHS]
    rows = list(pool.map(lambda a: one(*a), jobs))
    ok = [r for r in rows if r is not None]
    hdr = "cycle,member,fh," + ",".join(f"p{i}" for i in range(len(PTS)))
    with open(out + ".tmp", "w") as f:
        f.write(hdr + "\n" + "\n".join(",".join(map(str, r)) for r in ok) + "\n")
    os.replace(out + ".tmp", out)
    return f"{len(ok)}/{len(jobs)}"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("start"); ap.add_argument("end")
    ap.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    d0, d1 = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    with ThreadPoolExecutor(a.workers) as pool:
        d = d0
        while d <= d1:
            t = time.time(); r = cycle(d, pool)
            print(d, r, f"{time.time()-t:.1f}s", flush=True)
            d += dt.timedelta(days=1)
