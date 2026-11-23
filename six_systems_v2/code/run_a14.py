"""A14: A12 unchanged, applied to the A11 systems (PLAN_A14.md). Usage: run_a14.py SYSTEM"""
import os, sys, glob, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import a9_common as A
system = sys.argv[1]
import a9_job
C, CAL, JF, F7, JobA9 = a9_job.setup(system)
OUT = os.path.join(os.path.dirname(A.HERE), "a14", "results"); os.makedirs(OUT, exist_ok=True)
ba, glitch = A.BA[system] if system in A.BA else A.A11_SYS[system][:2]
use = ["Balancing Authority", "UTC Time at End of Hour", "Demand Forecast (MW)"]
fr = []
for fn in sorted(glob.glob(os.path.join(A.HERE, "raw_eia", "EIA930_BALANCE_*.csv"))):
    d = pd.read_csv(fn, usecols=use, low_memory=False); fr.append(d[d["Balancing Authority"] == ba])
d = pd.concat(fr, ignore_index=True)
d["df"] = pd.to_numeric(d["Demand Forecast (MW)"].astype(str).str.replace(",", ""), errors="coerce")
d["ts_utc"] = pd.to_datetime(d["UTC Time at End of Hour"], utc=True) - pd.Timedelta(hours=1)
d = d.sort_values("ts_utc").drop_duplicates("ts_utc")
bad = (d["df"].abs() > glitch) | (d["df"] <= 0)
d.loc[bad, "df"] = np.nan
DF = d.set_index("ts_utc")["df"]
JF.CALIBRATORS = ["C0", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
for era in sorted(A.events(system), key=int):
    df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{system}_{era}_gefs.pkl"))
    f = DF.reindex(df["ts_utc"]).values
    P = np.repeat(f[:, None], len(C.QUANTILES), axis=1)
    log = []
    job = JobA9(era, "HDA", "OPR", df, P, C.QUANTILES, log.append)
    rows, _ = job.run()
    rows.insert(0, "system", system)
    rows.to_csv(os.path.join(OUT, f"a14_{system}_{era}.csv"), index=False)
    ev = A.events(system)[era]
    m = (df["split"] == "eval").values
    info = dict(system=system, era=era, df_missing_eval=int(np.isnan(f[m]).sum()), df_missing_cal=int(np.isnan(f[(df.part == "cal").values]).sum()),
                glitches_total=int(bad.sum()))
    print(json.dumps(info), flush=True)
