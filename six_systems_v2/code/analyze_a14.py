"""A14 scoring (PLAN_A14.md): P1, P2 on the A11 systems, and pooled operator-forecast inference over all
systems (A12 + A14) with the outbreak clusters of rev_inference.py."""
import os, glob, itertools
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats import spearmanr
import a9_common as A
W = os.path.dirname(A.HERE); FD = os.path.join(W, "final_data")
R = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(W, "a14", "results", "a14_*.csv"))])
M = pd.read_csv(os.path.join(FD, "a11_events.csv"))
CALS = ["C2a", "C2b", "C3", "C4", "C6", "C7"]
def g(s, e, c, sc):
    r = R[(R.system == s) & (R.era == int(e)) & (R.calibrator == c) & (R.scope == sc)]; assert len(r) == 1, (s, e, c, sc); return r.iloc[0]
rows = []
for s in ["ercot", "spp", "nyiso", "isone"]:
    ev = A.events(s); eras = sorted(ev, key=int)
    delta = {c: {e: g(s, e, "C1", ev[e]["name"]).winkler90 - g(s, e, c, ev[e]["name"]).winkler90 for e in eras} for c in CALS}
    for e in eras:
        nm = ev[e]["name"]; c1e, c1p = g(s, e, "C1", nm), g(s, e, "C1", "eval_winter")
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in eras if k != e))
        r, w, p = g(s, e, chat, nm), g(s, e, chat, "eval_winter"), g(s, e, chat, "placebo")
        wr = w.mean_width90 / c1p.mean_width90
        m = M[(M.system == s) & (M.era == int(e))].iloc[0]
        rows.append(dict(system=s, era=int(e), n=int(c1e.n), c1_ev=c1e.cov90, c1_per=c1p.cov90, gap=100 * (c1p.cov90 - c1e.cov90), chat=chat,
                         chat_cov=r.cov90, chat_inf=int(r.n_inf90), chat_wr=wr, chat_plac=p.cov90, c1_upx=c1e.exceedance_freq,
                         repaired=bool(0.85 <= r.cov90 <= 0.95 and wr <= 1.35 and p.cov90 <= 0.95), model_c1_ev=m.c1_ev, model_c1_per=m.c1_per))
T = pd.DataFrame(rows); pd.set_option("display.width", 230); print(T.round(3).to_string(index=False))
n = len(T); p1 = int((T.gap >= 10).sum()); p2 = int(T.repaired.sum())
Tx = T[~((T.system == "spp") & (T.era == 2026))]; print(f"Without SPP 2026 (series break): P1 {int((Tx.gap >= 10).sum())}/{len(Tx)}, P2 {int(Tx.repaired.sum())}/{len(Tx)}")
print(f"\nP1: C1 gap >= 10 pp in {p1}/{n} (need >= {int(np.ceil(n/2))}) -> {'PASS' if p1 >= np.ceil(n/2) else 'FAIL'}")
print(f"P2: repaired (a,c,d) in {p2}/{n} (pass if <= {n//3}) -> {'PASS' if p2 <= n//3 else 'FAIL'}")
rho, pv = spearmanr(T.c1_ev, T.model_c1_ev); print(f"Spearman(operator, L1) C1 event cov = {rho:.2f} (p={pv:.3f})")
T.to_csv(os.path.join(W, "a14", "a14_summary.csv"), index=False)
# pooled over all operator events: A12 (PJM, MISO) + A14
O12 = pd.read_csv(os.path.join(FD, "a12_summary.csv"))[["system", "era", "c1_ev", "c1_per", "gap", "repaired"]]
Op = pd.concat([O12, T[["system", "era", "c1_ev", "c1_per", "gap", "repaired"]]], ignore_index=True)
CL = pd.read_csv(os.path.join(FD, "rev_clusters.csv"))[["system", "era", "cluster"]]
Op = Op.merge(CL, on=["system", "era"]); rng = np.random.default_rng(2026)
def infer(d, col):
    v = d[col].values; cl = d.cluster.values; keys = np.unique(cl); G = len(keys); n = len(v); est = v.mean()
    u = v - est; S_ = np.array([u[cl == k].sum() for k in keys]); se = np.sqrt((G / (G - 1)) * np.sum(S_ ** 2)) / n
    tq = stats.t.ppf(0.975, G - 1); sums = np.array([v[cl == k].sum() for k in keys]); obs = sums.sum(); tol = 1e-9 * max(1, abs(obs))
    flips = itertools.product([-1, 1], repeat=G) if G <= 16 else (rng.choice([-1, 1], G) for _ in range(100000))
    sims = np.array([np.dot(f, sums) for f in flips])
    return dict(n=n, G=G, est=est, lo=est - tq * se, hi=est + tq * se, p_flip=float(np.mean(np.abs(sims) >= abs(obs) - tol)))
# Deviation (documented): SPP's EIA-930 day-ahead forecast runs 10-17% above its reported demand from May 2025 to
# June 2026 (a definitional break in the series), so the SPP 2026 operator event is not comparable; excluded from the
# primary pooled result, reported with it as a sensitivity.
BREAK = (Op.system == "spp") & (Op.era == 2026)
OpAll = Op.copy(); Op = Op[~BREAK].reset_index(drop=True)
out = []
for nm_, d in [("operator_with_spp2026", OpAll), ("operator_all", Op), ("operator_noERCOT", Op[Op.system != "ercot"]), ("operator_A14only", Op[Op.system.isin(["ercot", "spp", "nyiso", "isone"])])]:
    r = infer(d.reset_index(drop=True), "gap"); r["set"] = nm_; r["mean_ev"] = d.c1_ev.mean(); r["mean_per"] = d.c1_per.mean()
    r["n_gap10"] = int((d.gap >= 10).sum()); r["n_repaired"] = int(d.repaired.sum()); r["n_rep_gap10"] = int(((d.gap >= 10) & d.repaired).sum()); out.append(r)
P = pd.DataFrame(out); print(P.round(3).to_string(index=False)); P.to_csv(os.path.join(W, "a14", "a14_pooled.csv"), index=False)
