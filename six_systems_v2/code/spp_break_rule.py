"""Reporting-break rule for the EIA-930 day-ahead demand forecast (shared with the companion study):
flag a balancing-authority-month whose median ratio of forecast to demand differs by more than 7% from that
authority's 2016-2024 median. Writes analysis/break_rule.csv and prints flagged winter-relevant months."""
import os, glob, numpy as np, pandas as pd
import a9_common as A
BAS = {"pjm": "PJM", "miso": "MISO", "ercot": "ERCO", "spp": "SWPP", "nyiso": "NYIS", "isone": "ISNE"}
use = ["Balancing Authority", "UTC Time at End of Hour", "Demand (MW)", "Demand Forecast (MW)"]
fr = []
for fn in sorted(glob.glob(os.path.join(A.HERE, "raw_eia", "EIA930_BALANCE_*.csv"))):
    d = pd.read_csv(fn, usecols=use, low_memory=False); fr.append(d[d["Balancing Authority"].isin(BAS.values())])
d = pd.concat(fr, ignore_index=True)
for c in ["Demand (MW)", "Demand Forecast (MW)"]: d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", ""), errors="coerce")
d = d[(d["Demand (MW)"] > 0) & (d["Demand Forecast (MW)"] > 0)]
d["month"] = pd.to_datetime(d["UTC Time at End of Hour"]).dt.to_period("M"); d["r"] = d["Demand Forecast (MW)"] / d["Demand (MW)"]
M = d.groupby(["Balancing Authority", "month"]).r.median().reset_index()
base = M[(M.month.dt.year >= 2016) & (M.month.dt.year <= 2024)].groupby("Balancing Authority").r.median()
M["base"] = M["Balancing Authority"].map(base); M["dev"] = M.r / M.base - 1; M["flag"] = M.dev.abs() > 0.07
M.to_csv(os.path.join(A.HERE, "analysis", "break_rule.csv"), index=False)
f = M[M.flag]; print(f.to_string(index=False))
