"""A5: evaluate C5 against the pre-specified criteria S1-S3 (PLAN_A5.md)."""
import os, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.dirname(HERE)
ARCH = {"PJM": pd.read_csv(f"{O}/pjm02/experiments/results/results_matrix.csv"),
        "MISO": pd.read_csv(f"{O}/miso/experiments/results/results_matrix.csv")}
EV = {("PJM", 2018): "event_2018_snap", ("PJM", 2022): "event_2022_elliott",
      ("MISO", 2018): "event_2018_snap", ("MISO", 2019): "event_2019_vortex",
      ("MISO", 2022): "event_2022_elliott"}
new = pd.concat([pd.read_csv(f) for f in glob.glob(f"{HERE}/results/c5_*_HDA_*.csv")], ignore_index=True)

def g(df, era, learner, cal, scope):
    r = df[(df.era == era) & (df.horizon == "HDA") & (df.learner == learner) & (df.calibrator == cal)
           & (df.scope == scope) & (df.eval_mode == "chronological")]
    assert len(r) == 1, (era, learner, cal, scope, len(r)); return r.iloc[0]

# 1. reproduction check: C0 and C4 rows equal the archived rows
mx = 0.0
for _, r in new[new.calibrator.isin(["C0", "C4"])].iterrows():
    a = g(ARCH[r.system], r.era, r.learner, r.calibrator, r.scope)
    for c in ["cov80", "cov90", "cov95", "cov98", "mean_width90", "winkler90"]:
        if np.isfinite(a[c]) or np.isfinite(r[c]):
            mx = max(mx, abs(a[c] - r[c]) / max(1.0, abs(a[c])))
print(f"reproduction of archived C0/C4 rows: max relative difference {mx:.2e}")

def frontier_win(sysname, era, learner):
    e = EV[(sysname, era)]
    r0, rx = g(ARCH[sysname], era, learner, "C0", e), g(ARCH[sysname], era, learner, "C0x", e)
    rc = g(new[new.system == sysname], era, learner, "C5", e)
    e0, h0, ex, hx, ec, hc = r0.exceedance_freq, r0.upper_headroom, rx.exceedance_freq, rx.upper_headroom, rc.exceedance_freq, rc.upper_headroom
    pareto = (ec <= ex) and (hc <= hx); interp = False
    if hx != h0 and min(h0, hx) <= hc <= max(h0, hx):
        interp = ec < e0 + (ex - e0) * (hc - h0) / (hx - h0)
    return bool(pareto or interp)

recs = []
for (s, era), e in EV.items():
    for L in ["L1", "L2", "L3"]:
        N = new[new.system == s]
        c5, c4, c0 = g(N, era, L, "C5", e), g(N, era, L, "C4", e), g(N, era, L, "C0", e)
        w5, w0 = g(N, era, L, "C5", "eval_winter"), g(N, era, L, "C0", "eval_winter")
        pl = g(N, era, L, "C5", "placebo")
        recs.append(dict(system=s, era=era, learner=L, c0=c0.cov90, c4=c4.cov90, c5=c5.cov90,
                         c5_inf=int(c5.n_inf90), c5_cov98=c5.cov98, period_c5=w5.cov90,
                         width_infl=w5.mean_width90 / w0.mean_width90 - 1, placebo=pl.cov90,
                         a=bool(0.85 <= c5.cov90 <= 0.95), b=frontier_win(s, era, L),
                         c=bool(w5.mean_width90 / w0.mean_width90 - 1 <= 0.35), d=bool(pl.cov90 <= 0.95),
                         c5_gt_c4=bool(c5.cov90 > c4.cov90)))
R = pd.DataFrame(recs)
pd.set_option("display.width", 200)
print(R.round(3).to_string(index=False))
L1 = R[R.learner == "L1"]
S1 = int(L1.c5_gt_c4.sum()); S2a = int((L1.a & L1.c).sum()); S2d = bool(L1.d.all())
print(f"\nS1 (C5 > C4 in >=4/5): {S1}/5 -> {'PASS' if S1 >= 4 else 'FAIL'}")
print(f"S2 ((a)&(c) in >=3/5 and (d) in all 5): (a)&(c) {S2a}/5, (d) all={S2d} -> {'PASS' if S2a >= 3 and S2d else 'FAIL'}")
for s, need in [("PJM", 2), ("MISO", 2)]:
    for Lr in ["L1", "L2", "L3"]:
        X = R[(R.system == s) & (R.learner == Lr)]
        ok = int((X.a & X.b).sum()) >= need and bool((X.c & X.d).all())
        print(f"S3 {s} {Lr}: (a)&(b) {int((X.a & X.b).sum())}/{len(X)}, (c)&(d) all={bool((X.c & X.d).all())} -> {'PASS' if ok else 'FAIL'}")
R.to_csv(f"{HERE}/results/c5_summary.csv", index=False)
