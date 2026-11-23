"""Map NCAR-mirror ERA5 footprint means onto the Open-Meteo ERA5 series by linear regression fitted on
overlapping winter months (leave-one-month-out check reported). Usage: harmonize_ncar.py OVERLAP_CSV[,..] OM_CSV RAW_CSV OUT_CSV"""
import sys, numpy as np, pandas as pd
ov, om, raw, out = sys.argv[1].split(","), sys.argv[2], sys.argv[3], sys.argv[4]
o = pd.read_csv(om, parse_dates=["timestamp_utc"])
M = pd.concat([pd.read_csv(f, parse_dates=["timestamp_utc"]) for f in ov]).merge(o, on="timestamp_utc", suffixes=("_n", "_o"))
M["mo"] = M.timestamp_utc.dt.month; fit = {}
for c in ["t2m_c", "wind_speed_ms"]:
    b, a = np.polyfit(M[c + "_n"], M[c + "_o"], 1); fit[c] = (a, b)
    r = M[c + "_o"] - (a + b * M[c + "_n"]); print(f"{c}: a={a:.3f} b={b:.4f} resid MAE {r.abs().mean():.3f} sd {r.std():.3f} (raw MAE {(M[c+'_o']-M[c+'_n']).abs().mean():.3f})")
    for mo in M.mo.unique():   # leave-one-month-out
        tr, te = M[M.mo != mo], M[M.mo == mo]; bb, aa = np.polyfit(tr[c + "_n"], tr[c + "_o"], 1)
        print(f"   LOMO month {mo}: MAE {(te[c+'_o'] - (aa + bb*te[c+'_n'])).abs().mean():.3f}")
R = pd.read_csv(raw)
for c in ["t2m_c", "wind_speed_ms"]: R[c] = fit[c][0] + fit[c][1] * R[c]
R["temperature_f"] = R.t2m_c * 9 / 5 + 32; R["wind_speed_mph"] = R.wind_speed_ms * 2.2369362920544
R.to_csv(out, index=False); print("wrote", out, len(R))
