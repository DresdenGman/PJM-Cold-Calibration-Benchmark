"""Mechanism and early warning (exploratory, post hoc): (1) does the event location bias predict
event coverage through a shifted-distribution model, (2) does an ex-ante 'beyond-history'
measure of the event's forecast temperature predict failure?"""
import os
import numpy as np, pandas as pd
from scipy.stats import norm, spearmanr
import a9_common as A
E = pd.read_csv(os.path.join(A.HERE, "analysis", "a9_events_L1_gefs.csv"))
B = pd.read_csv(os.path.join(A.HERE, "analysis", "a9_bias_L1_gefs.csv"))
X = E.merge(B, on=["system", "era"])
# (1) shifted-Gaussian model: C0 90% interval half-width h = z*sigma with z chosen so that the era's
# full-period C0 coverage is reproduced (z = Phi^-1((1+cov_per)/2)); a location shift of b half-widths gives
# coverage Phi(z(1-b)) - Phi(-z(1+b)).
z = norm.ppf((1 + X.c0_per) / 2)
X["pred_c0_ev"] = norm.cdf(z * (1 - X.bias_ratio)) - norm.cdf(-z * (1 + X.bias_ratio))
r1 = spearmanr(X.pred_c0_ev, X.c0_ev); mae1 = float(np.abs(X.pred_c0_ev - X.c0_ev).mean())
# (2) beyond-history: share of event hours whose forecast footprint temperature is below the 1st percentile
# of all prior-winter (D_cal) forecast temperatures, and the event's minimum temperature minus the D_cal minimum.
rows = []
for r in X.itertuples():
    s, e = r.system, str(r.era)
    df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl"))
    ev = A.events(s)[e]; loc = df.ts_local.dt.tz_localize(None)
    em = ((loc >= pd.Timestamp(ev["start"])) & (loc < pd.Timestamp(ev["end"])) & (df.split == "eval")).values
    cal_T = df.loc[df.part == "cal", "t2m_c"].dropna().values; ev_T = df.loc[em, "t2m_c"].dropna().values
    p01 = np.percentile(cal_T, 1)
    rows.append(dict(system=s, era=r.era, share_below_p01=float(np.mean(ev_T < p01)), excess_min=float(ev_T.min() - cal_T.min()),
                     n_cal_colder_than_ev_median=int(np.sum(cal_T <= np.median(ev_T))), cal_hours=len(cal_T)))
H = pd.DataFrame(rows); X = X.merge(H, on=["system", "era"])
pd.set_option("display.width", 220)
print(X[["system", "era", "c0_ev", "c0_per", "bias_ratio", "pred_c0_ev", "c1_ev", "gap_c1", "share_below_p01", "excess_min", "n_cal_colder_than_ev_median"]].round(3).to_string(index=False))
print(f"\n(1) shifted-Gaussian prediction of C0 event coverage: Spearman {r1.correlation:.2f} (p={r1.pvalue:.4f}), MAE {mae1:.3f}")
for col in ["share_below_p01", "excess_min", "n_cal_colder_than_ev_median"]:
    rr = spearmanr(X[col], X.c1_ev); rb = spearmanr(X[col], X.bias_ratio)
    print(f"(2) {col}: Spearman with C1 event coverage {rr.correlation:+.2f} (p={rr.pvalue:.3f}); with bias ratio {rb.correlation:+.2f} (p={rb.pvalue:.3f})")
X.to_csv(os.path.join(A.HERE, "analysis", "mechanism_L1_gefs.csv"), index=False)
