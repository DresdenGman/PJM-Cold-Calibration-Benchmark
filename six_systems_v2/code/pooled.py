"""Pooled event-level estimates with a cluster bootstrap over distinct weather events (exploratory)."""
import os
import numpy as np, pandas as pd
import a9_common as A
rng = np.random.default_rng(42)
WX = {2014: "2014", 2018: "2018", 2019: "2019", 2022: "2022", 2024: "2024", 2025: "2025", 2026: "2026"}
def boot(df, col, B=10000):
    cl = df.groupby("era")[col].apply(list).to_dict(); keys = list(cl)
    est = float(df[col].mean()); bs = []
    for _ in range(B):
        pick = rng.choice(keys, size=len(keys), replace=True)
        vals = [v for k in pick for v in cl[k]]; bs.append(np.mean(vals))
    return est, np.percentile(bs, [2.5, 97.5])
E = pd.read_csv(os.path.join(A.HERE, "analysis", "a9_events_L1_gefs.csv"))
E["gap_c0"] = 100 * (E.c0_per - E.c0_ev); E["gap_c1"] = 100 * (E.c1_per - E.c1_ev)
O = pd.read_csv(os.path.join(os.path.dirname(A.HERE), "a12", "a12_summary.csv"))
out = []
for lab, df, col in [("model C0 gap (pp)", E, "gap_c0"), ("model C1 gap (pp)", E, "gap_c1"), ("model C1 event cov", E, "c1_ev"),
                     ("operator C1 gap (pp)", O, "gap"), ("operator C1 event cov", O, "c1_ev")]:
    est, ci = boot(df, col); out.append((lab, len(df), df.era.nunique(), est, ci[0], ci[1]))
    print(f"{lab}: {est:.3f} [95% cluster-bootstrap {ci[0]:.3f}, {ci[1]:.3f}] over {len(df)} events / {df.era.nunique()} weather events")
pd.DataFrame(out, columns=["quantity", "events", "weather_events", "estimate", "ci_lo", "ci_hi"]).to_csv(os.path.join(A.HERE, "analysis", "pooled.csv"), index=False)
