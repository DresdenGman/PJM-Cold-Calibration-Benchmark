"""A10 scoring against PLAN_A10.md (H1, H2), GEFS weather."""
import os, glob
import numpy as np, pandas as pd
import a9_common as A
R = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(A.HERE, "results", "a10_*_gefs.csv"))], ignore_index=True)
def g(s, e, L, c, sc):
    r = R[(R.system == s) & (R.era == int(e)) & (R.learner == L) & (R.calibrator == c) & (R.scope == sc)]
    assert len(r) == 1, (s, e, L, c, sc, len(r)); return r.iloc[0]
H1_EVENTS = [("pjm", "2014"), ("pjm", "2018"), ("pjm", "2022"), ("miso", "2018"), ("miso", "2022"), ("miso", "2025"), ("miso", "2026")]
rows = []
for s, e in H1_EVENTS:
    nm = A.events(s)[e]["name"]; c1p = g(s, e, "L1", "C1", "eval_winter")
    for c in ["C8a", "C8b"]:
        r, w, p = g(s, e, "L1", c, nm), g(s, e, "L1", c, "eval_winter"), g(s, e, "L1", c, "placebo")
        wr = w.mean_width90 / c1p.mean_width90
        rows.append(dict(system=s, era=e, cal=c, ev=r.cov90, inf=int(r.n_inf90), wr=wr, plac=p.cov90,
                         ok=bool(0.85 <= r.cov90 <= 0.95 and wr <= 1.35 and p.cov90 <= 0.95)))
H1 = pd.DataFrame(rows)
n_ok = len(set((r.system, r.era) for r in H1.itertuples() if r.ok))
print(H1.round(3).to_string(index=False))
print(f"H1: C8a or C8b meets (a),(c),(d) in {n_ok}/7 events (need >= 3) -> {'PASS' if n_ok >= 3 else 'FAIL'}")
# H2: holiday-aware L1h vs L1
import a9_job
out = []
for s in ["pjm", "miso"]:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    for e in A.ERAS[s]:
        nm = A.events(s)[e]; df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl"))
        rec = dict(system=s, era=e)
        for L in ["L1", "L1h"]:
            P = np.load(os.path.join(A.HERE, "preds", f"{s}_{e}_{L}_gefs.npz"))["P_raw"]
            jb = JobA9(e, "HDA", L, df, P, C.QUANTILES, lambda m: None)
            idx = jb.valid_idx(jb.eval_mask & (jb.loc >= pd.Timestamp(nm["start"])) & (jb.loc < pd.Timestamp(nm["end"])))
            q = jb.P; gr = jb.grid
            err = jb.y[idx] - q[idx, C.qidx(gr, 0.5)]; half = (q[idx, C.qidx(gr, 0.95)] - q[idx, C.qidx(gr, 0.05)]) / 2
            rec[f"bias_{L}"] = float(err.mean() / half.mean())
            rec[f"c1ev_{L}"] = g(s, e, L, "C1", nm["name"]).cov90; rec[f"c1per_{L}"] = g(s, e, L, "C1", "eval_winter").cov90
            rec[f"c0ev_{L}"] = g(s, e, L, "C0", nm["name"]).cov90
        out.append(rec)
H2 = pd.DataFrame(out)
H2["d_c1ev"] = 100 * (H2.c1ev_L1h - H2.c1ev_L1); H2["d_c1per"] = 100 * (H2.c1per_L1h - H2.c1per_L1)
print(H2.round(3).to_string(index=False))
el = H2[H2.era == "2022"]
ok = bool((el.d_c1ev >= 10).all() and (el.bias_L1h.abs() < el.bias_L1.abs()).all() and (H2.d_c1per.abs() <= 2).all())
print(f"H2: Elliott C1 gain {list(el.d_c1ev.round(1))} pp; |bias| {list(el.bias_L1.abs().round(2))} -> {list(el.bias_L1h.abs().round(2))}; max |full-period change| {H2.d_c1per.abs().max():.1f} pp -> {'PASS' if ok else 'FAIL'}")
H1.to_csv(os.path.join(A.HERE, "a10_H1.csv"), index=False); H2.to_csv(os.path.join(A.HERE, "a10_H2.csv"), index=False)
