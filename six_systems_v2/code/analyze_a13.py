"""A13 2x2 factorial (descriptive): C1 event / full-period cov90 by design, L1, GEFS day-ahead weather.
v13 corners: S+A = D3, L+A = D1b, S+W = D2, L+W = A9. v12 corners kept as sensitivity: SAo = A8 refit of the
original design, LAo = D1 (fit on D_fit only)."""
import os, glob
import numpy as np, pandas as pd
import a9_common as A
W = os.path.dirname(A.HERE); rng = np.random.default_rng(42)
A8 = {"pjm": "PJM", "miso": "MISO"}
def a9res(tag, s, e):
    f = os.path.join(A.HERE, "results", f"{tag}_{s}_{e}_L1_gefs.csv")
    if not os.path.exists(f): return None
    r = pd.read_csv(f); n = A.events(s)[str(e)]["name"]
    g = lambda sc: r[(r.calibrator == "C1") & (r.scope == sc)].cov90.iloc[0]
    return g(n), g("eval_winter")
rows = []
for s in ["pjm", "miso"]:
    m8 = pd.read_csv(os.path.join(W, "repo", "forecast_weather_a8", "results", s, "results_matrix_a8.csv"))
    for e in A.ERAS[s]:
        e = int(e); n = A.events(s)[str(e)]["name"]
        q = m8[(m8.era == e) & (m8.horizon == "HDA") & (m8.learner == "L1") & (m8.calibrator == "C1") & (m8.eval_mode == "chronological")]
        sa = (q[q.scope == n].cov90.iloc[0], q[q.scope == "eval_winter"].cov90.iloc[0]) if len(q) else (np.nan, np.nan)
        rec = dict(system=s, era=e, SAo_ev=sa[0], SAo_per=sa[1])
        for k, tag in [("SA", "a13D3"), ("LA", "a13D1b"), ("LAo", "a13D1"), ("SW", "a13D2"), ("LW", "a9")]:
            v = a9res(tag, s, e); rec[f"{k}_ev"], rec[f"{k}_per"] = v if v else (np.nan, np.nan)
        rows.append(rec)
D = pd.DataFrame(rows)
for k in ["SA", "LA", "SW", "LW", "SAo", "LAo"]: D[f"{k}_gap"] = 100 * (D[f"{k}_per"] - D[f"{k}_ev"])
def boot(df, col, B=10000):
    d = df.dropna(subset=[col]); cl = d.groupby("era")[col].apply(list).to_dict(); keys = list(cl); bs = []
    for _ in range(B):
        pick = rng.choice(keys, size=len(keys), replace=True); bs.append(np.mean([v for kk in pick for v in cl[kk]]))
    return d[col].mean(), *np.percentile(bs, [2.5, 97.5]), len(d)
out = []
for k in ["SA", "LA", "SW", "LW", "SAo", "LAo"]:
    for c in ["ev", "per", "gap"]:
        est, lo, hi, n = boot(D, f"{k}_{c}"); out.append((k, c, est, lo, hi, n))
    out.append((k, "n_gap10", int((D[f"{k}_gap"] >= 10).sum()), np.nan, np.nan, int(D[f"{k}_gap"].notna().sum())))
S = pd.DataFrame(out, columns=["design", "quantity", "estimate", "ci_lo", "ci_hi", "n"])
os.makedirs(os.path.join(A.HERE, "analysis"), exist_ok=True)
D.to_csv(os.path.join(A.HERE, "analysis", "a13_events.csv"), index=False); S.to_csv(os.path.join(A.HERE, "analysis", "a13_summary.csv"), index=False)
pd.set_option("display.width", 200); print(D.round(3).to_string()); print(S.round(3).to_string())
