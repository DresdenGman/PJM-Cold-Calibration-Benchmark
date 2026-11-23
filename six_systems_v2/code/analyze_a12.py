"""A12 scoring (PLAN_A12.md): O1, O2, O3."""
import os, glob
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import a9_common as A
OUT = os.path.join(os.path.dirname(A.HERE), "a12")
R = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(OUT, "results", "a12_*.csv"))])
M = pd.read_csv(os.path.join(A.HERE, "analysis", "a9_events_L1_gefs.csv"))
CALS = ["C2a", "C2b", "C3", "C4", "C6", "C7"]
def g(s, e, c, sc):
    r = R[(R.system == s) & (R.era == int(e)) & (R.calibrator == c) & (R.scope == sc)]; assert len(r) == 1, (s, e, c, sc); return r.iloc[0]
rows = []
for s in ["pjm", "miso"]:
    ev = A.events(s); eras = [e for e in A.ERAS[s] if e != "2014"]
    delta = {c: {e: g(s, e, "C1", ev[e]["name"]).winkler90 - g(s, e, c, ev[e]["name"]).winkler90 for e in eras} for c in CALS}
    for e in eras:
        nm = ev[e]["name"]; c1e, c1p = g(s, e, "C1", nm), g(s, e, "C1", "eval_winter")
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in eras if k != e))
        r, w, p = g(s, e, chat, nm), g(s, e, chat, "eval_winter"), g(s, e, chat, "placebo")
        wr = w.mean_width90 / c1p.mean_width90
        best = {c: g(s, e, c, nm).cov90 for c in ["C1"] + CALS}
        m = M[(M.system == s) & (M.era == int(e))].iloc[0]
        rows.append(dict(system=s, era=e, c1_ev=c1e.cov90, c1_per=c1p.cov90, gap=100 * (c1p.cov90 - c1e.cov90), chat=chat,
                         chat_cov=r.cov90, chat_inf=int(r.n_inf90), chat_wr=wr, chat_plac=p.cov90,
                         repaired=bool(0.85 <= r.cov90 <= 0.95 and wr <= 1.35 and p.cov90 <= 0.95),
                         model_c1_ev=m.c1_ev, model_c1_per=m.c1_per, **{f"ev_{c}": v for c, v in best.items()}))
T = pd.DataFrame(rows); pd.set_option("display.width", 230)
print(T.round(3).to_string(index=False))
n = len(T); o1 = int((T.gap >= 10).sum()); o2 = int(T.repaired.sum())
rho, pv = spearmanr(T.c1_ev, T.model_c1_ev)
print(f"\nO1: C1 gap >= 10 pp in {o1}/{n} (need >= {int(np.ceil(n/2))}) -> {'PASS' if o1 >= np.ceil(n/2) else 'FAIL'}")
print(f"O2: repaired by out-of-event selection in {o2}/{n} (pass if <= {n//3}) -> {'PASS' if o2 <= n//3 else 'FAIL'}")
print(f"O3: Spearman(operator C1 event cov, model C1 event cov) = {rho:.2f} (p={pv:.3f}); mean operator - model = {100*(T.c1_ev-T.model_c1_ev).mean():+.1f} pp")
T.to_csv(os.path.join(OUT, "a12_summary.csv"), index=False)
