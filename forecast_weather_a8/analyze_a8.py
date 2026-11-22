"""A8: score the forecast-weather benchmark against F1-F3 (PLAN_A8.md). H-DA, L1, chronological."""
import os, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.dirname(HERE)
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4"]
REAN = {"PJM": pd.concat([pd.read_csv(f"{O}/pjm02/experiments/results/results_matrix.csv"), pd.read_csv(f"{O}/a6/pjm/experiments/results/results_matrix_a6.csv")]),
        "MISO": pd.concat([pd.read_csv(f"{O}/miso/experiments/results/results_matrix.csv"), pd.read_csv(f"{O}/a6/miso/experiments/results/results_matrix_a6.csv")])}
C5 = glob.glob(f"{HERE}/c5/results/c5_*_HDA_*.csv")
C5 = pd.concat([pd.read_csv(f) for f in C5]) if C5 else pd.DataFrame()
rows = []
for s, d in [("PJM", "pjm"), ("MISO", "miso")]:
    ev = {int(k): v["name"] for k, v in json.load(open(f"{HERE}/{d}/experiments/events_a6.json")).items()}
    df = pd.concat([pd.read_csv(f) for f in glob.glob(f"{HERE}/{d}/experiments/results/frag_*_HDA_*.csv")])
    df.to_csv(f"{HERE}/{d}/experiments/results/results_matrix_a8.csv", index=False)
    eras = sorted(e for e in ev if len(df[(df.era == e)]))
    def g(D, e, c, sc, L="L1"):
        r = D[(D.era == e) & (D.horizon == "HDA") & (D.learner == L) & (D.calibrator == c) & (D.scope == sc) & (D.eval_mode == "chronological")]
        assert len(r) == 1, (s, e, c, sc, len(r)); return r.iloc[0]
    delta = {c: {e: g(df, e, "C0", ev[e]).winkler90 - g(df, e, c, ev[e]).winkler90 for e in eras} for c in CALS}
    for e in eras:
        e0, p0 = g(df, e, "C0", ev[e]), g(df, e, "C0", "eval_winter")
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in eras if k != e))
        rc, wc, pl = g(df, e, chat, ev[e]), g(df, e, chat, "eval_winter"), g(df, e, chat, "placebo")
        winfl = wc.mean_width90 / p0.mean_width90 - 1
        rr = g(REAN[s], e, "C0", ev[e]); rp = g(REAN[s], e, "C0", "eval_winter")
        rec = dict(system=s, era=e, event_fc=e0.cov90, period_fc=p0.cov90, gap_fc=100 * (p0.cov90 - e0.cov90),
                   event_re=rr.cov90, period_re=rp.cov90, c3_fc=g(df, e, "C3", ev[e]).cov90, chat=chat,
                   chat_cov=rc.cov90, winfl=winfl, plac=pl.cov90,
                   rep=bool(0.85 <= rc.cov90 <= 0.95 and winfl <= 0.35 and pl.cov90 <= 0.95))
        if len(C5):
            q = C5[(C5.system == s) & (C5.era == e) & (C5.learner == "L1") & (C5.calibrator == "C5")]
            if len(q):
                c5e = q[q.scope == ev[e]].iloc[0]; c5w = q[q.scope == "eval_winter"].iloc[0]; c5p = q[q.scope == "placebo"].iloc[0]
                wi5 = c5w.mean_width90 / p0.mean_width90 - 1
                rec.update(c5=c5e.cov90, c5_winfl=wi5, c5_plac=c5p.cov90,
                           c5_ac=bool(0.85 <= c5e.cov90 <= 0.95 and wi5 <= 0.35), c5_d=bool(c5p.cov90 <= 0.95))
        rows.append(rec)
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(R.round(3).to_string(index=False))
n = len(R); b = int((R.event_fc < R.period_fc).sum())
print(f"\nF1: below in {b}/{n} (need >= {int(np.ceil(2*n/3))}) -> {'PASS' if b >= np.ceil(2*n/3) else 'FAIL'}")
r = int(R.rep.sum()); print(f"F2: repaired (a)&(c)&(d) in {r}/{n} (pass if <= {int(np.floor(n/3))}) -> {'PASS' if r <= np.floor(n/3) else 'FAIL'}")
if "c5" in R:
    X = R.dropna(subset=["c5"]); ac = int(X.c5_ac.sum()); dd = bool(X.c5_d.all())
    print(f"F3: C5 (a)&(c) in {ac}/{len(X)} (need >= {int(np.ceil(len(X)/2))}), (d) all={dd} -> {'SUPPORTED' if ac >= np.ceil(len(X)/2) and dd else 'NOT SUPPORTED'}")
print(f"event cov90 forecast minus reanalysis: mean {100*(R.event_fc-R.event_re).mean():+.1f} pp, range {100*(R.event_fc-R.event_re).min():+.1f} to {100*(R.event_fc-R.event_re).max():+.1f}")
R.to_csv(f"{HERE}/a8_summary.csv", index=False)
