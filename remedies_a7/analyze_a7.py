"""A7: score C6 and C7 against PLAN_A7.md (L1, H-DA, chronological, all 13 events).
Also checks that C0 and C4 rerun here reproduce the archived/A6 rows."""
import os, glob, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.dirname(HERE)
A = pd.concat([pd.read_csv(f) for f in glob.glob(f"{HERE}/results/a7_*_HDA_*.csv")], ignore_index=True)
ev = {}
for s, d, old in [("PJM", "pjm", {2014: "event_2014_vortex", 2018: "event_2018_snap", 2022: "event_2022_elliott"}),
                  ("MISO", "miso", {2018: "event_2018_snap", 2019: "event_2019_vortex", 2022: "event_2022_elliott"})]:
    ev[s] = dict(old); ev[s].update({int(k): v["name"] for k, v in json.load(open(f"{O}/a6/{d}/experiments/events_a6.json")).items()})
REF = pd.concat([pd.read_csv(f"{O}/pjm02/experiments/results/results_matrix.csv").assign(system="PJM"),
                 pd.read_csv(f"{O}/miso/experiments/results/results_matrix.csv").assign(system="MISO"),
                 pd.read_csv(f"{O}/a6/pjm/experiments/results/results_matrix_a6.csv").assign(system="PJM"),
                 pd.read_csv(f"{O}/a6/miso/experiments/results/results_matrix_a6.csv").assign(system="MISO")])
REF = REF[REF.eval_mode == "chronological"]
mx = 0
for _, r in A[A.calibrator.isin(["C0", "C4"])].iterrows():
    q = REF[(REF.system == r.system) & (REF.era == r.era) & (REF.horizon == "HDA") & (REF.learner == r.learner) & (REF.calibrator == r.calibrator) & (REF.scope == r.scope)]
    assert len(q) == 1, (r.system, r.era, r.calibrator, r.scope, len(q))
    mx = max(mx, abs(q.iloc[0].cov90 - r.cov90), abs(q.iloc[0].mean_width90 - r.mean_width90) / q.iloc[0].mean_width90)
print(f"reproduction of C0/C4 rows: max difference {mx:.2e}")
def g(s, e, L, c, sc):
    r = A[(A.system == s) & (A.era == e) & (A.learner == L) & (A.calibrator == c) & (A.scope == sc)]; assert len(r) == 1; return r.iloc[0]
rows = []
for s in ev:
    for e, name in sorted(ev[s].items()):
        for L in ["L1", "L2", "L3"]:
            w0 = g(s, e, L, "C0", "eval_winter")
            rec = dict(system=s, era=e, learner=L, c0=g(s, e, L, "C0", name).cov90, c4=g(s, e, L, "C4", name).cov90)
            for c in ["C6", "C7"]:
                r = g(s, e, L, c, name); w = g(s, e, L, c, "eval_winter"); p = g(s, e, L, c, "placebo")
                wi = w.mean_width90 / w0.mean_width90 - 1
                rec.update({c: r.cov90, f"{c}_inf": int(r.n_inf90), f"{c}_winfl": wi, f"{c}_plac": p.cov90,
                            f"{c}_a": bool(0.85 <= r.cov90 <= 0.95), f"{c}_c": bool(wi <= 0.35), f"{c}_d": bool(p.cov90 <= 0.95)})
            rows.append(rec)
R = pd.DataFrame(rows); pd.set_option("display.width", 250)
L1 = R[R.learner == "L1"]
print(L1[["system", "era", "c0", "c4", "C6", "C6_inf", "C6_winfl", "C6_plac", "C7", "C7_inf", "C7_winfl", "C7_plac"]].round(3).to_string(index=False))
for c in ["C6", "C7"]:
    ac = int((L1[f"{c}_a"] & L1[f"{c}_c"]).sum()); d = bool(L1[f"{c}_d"].all()); n = len(L1)
    print(f"{c}: (a)&(c) in {ac}/{n} (need >= {int(np.ceil(n/2))}), (d) all={d} -> {'SUPPORTED' if ac >= np.ceil(n/2) and d else 'NOT SUPPORTED'}; "
          f"beats C4 on event cov90 in {int((L1[c] > L1.c4).sum())}/{n}; (a) alone {int(L1[f'{c}_a'].sum())}/{n}")
R.to_csv(f"{HERE}/a7_summary.csv", index=False)
