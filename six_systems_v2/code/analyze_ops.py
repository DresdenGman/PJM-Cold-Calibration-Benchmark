"""Operational reading of event-window intervals: if day-ahead reserves were sized to the upper
endpoint of the nominal 90% interval, how often and by how much would load exceed it?
Reads the event tuples saved by job_fit.Job.run (y, q50 and each calibrator's 90% endpoints).
Usage: analyze_ops.py TAG SYSTEM:DIR [SYSTEM:DIR ...]   (DIR holds prepped/tuples_<era>_HDA_<learner>.npz)"""
import os, sys, glob, re
import numpy as np, pandas as pd
tag = sys.argv[1]; rows = []
for spec in sys.argv[2:]:
    system, d = spec.split(":", 1)
    for f in sorted(glob.glob(os.path.join(d, "prepped", "tuples_*_HDA_L1.npz"))):
        era = re.search(r"tuples_(\d+)_HDA", f).group(1); z = np.load(f)
        y, q50 = z["y"], z["q50"]; peak = float(np.max(y))
        cals = sorted({k[:-3] for k in z.files if k.endswith("_hi")})
        hi0 = z["C0_hi"]
        for c in cals:
            hi = z[f"{c}_hi"]; fin = np.isfinite(hi)
            exc = fin & (y > hi); sh = np.where(exc, y - hi, 0.0)
            rows.append(dict(design=tag, system=system, era=era, calibrator=c, hours=len(y), inf_hours=int((~fin).sum()),
                             exceed_hours=int(exc.sum()), exceed_share=float(exc.mean()),
                             max_shortfall_mw=float(sh.max()), mean_shortfall_mw_when_exceeded=float(sh[exc].mean()) if exc.any() else 0.0,
                             shortfall_mwh=float(sh.sum()), max_shortfall_pct_peak=100 * float(sh.max()) / peak,
                             extra_headroom_mw=float(np.nanmean(np.where(fin, hi - hi0, np.nan))) if fin.any() else np.nan,
                             peak_mw=peak))
R = pd.DataFrame(rows); pd.set_option("display.width", 220)
out = f"ops_{tag}.csv"; R.to_csv(out, index=False)
print(R[R.calibrator.isin(["C0", "C1", "C2a", "C3", "C4", "C7"])][["system", "era", "calibrator", "exceed_hours", "hours", "inf_hours", "max_shortfall_mw", "max_shortfall_pct_peak", "shortfall_mwh", "extra_headroom_mw"]].round(1).to_string(index=False))
