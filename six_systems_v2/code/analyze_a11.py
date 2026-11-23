"""A11 scoring (PLAN_A11.md): K1, K2, K3 and censored bounds for flagged load-shed hours.
Usage: analyze_a11.py SYSTEMS(comma)"""
import os, sys, glob
import numpy as np, pandas as pd
import a9_common as A
systems = sys.argv[1].split(",")
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
RES = pd.concat([pd.read_csv(f) for s in systems for f in glob.glob(os.path.join(A.HERE, "results", f"a9_{s}_*_L1_gefs.csv"))], ignore_index=True)
def g(s, e, c, sc):
    r = RES[(RES.system == s) & (RES.era == int(e)) & (RES.calibrator == c) & (RES.scope == sc)]; assert len(r) == 1, (s, e, c, sc, len(r)); return r.iloc[0]
rows = []
for s in systems:
    ev = A.events(s); eras = sorted(ev)
    delta = {c: {e: g(s, e, "C0", ev[e]["name"]).winkler90 - g(s, e, c, ev[e]["name"]).winkler90 for e in eras} for c in CALS}
    for e in eras:
        evd = ev[e]; nm = evd["name"]; c0e, c0p, c1e, c1p = g(s, e, "C0", nm), g(s, e, "C0", "eval_winter"), g(s, e, "C1", nm), g(s, e, "C1", "eval_winter")
        def conds(c):
            r, w, p = g(s, e, c, nm), g(s, e, c, "eval_winter"), g(s, e, c, "placebo")
            r0, rx = g(s, e, "C0", nm), g(s, e, "C0x", nm)
            pareto = (r.exceedance_freq <= rx.exceedance_freq) and (r.upper_headroom <= rx.upper_headroom); interp = False
            if rx.upper_headroom != r0.upper_headroom and min(r0.upper_headroom, rx.upper_headroom) <= r.upper_headroom <= max(r0.upper_headroom, rx.upper_headroom):
                interp = r.exceedance_freq < r0.exceedance_freq + (rx.exceedance_freq - r0.exceedance_freq) * (r.upper_headroom - r0.upper_headroom) / (rx.upper_headroom - r0.upper_headroom)
            wr = w.mean_width90 / c1p.mean_width90
            return dict(cov=r.cov90, inf=int(r.n_inf90), a=bool(0.85 <= r.cov90 <= 0.95), b=bool(pareto or interp), c=bool(wr <= 1.35), d=bool(p.cov90 <= 0.95), wr=wr, plac=p.cov90)
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in eras if k != e)); cc = conds(chat)
        rows.append(dict(system=s, era=e, n=int(c0e.n), window=f"{evd['start'][:10]}..{evd['end'][:10]}", c0_ev=c0e.cov90, c0_per=c0p.cov90,
                         c1_ev=c1e.cov90, c1_per=c1p.cov90, gap_c1=100 * (c1p.cov90 - c1e.cov90), chat=chat, chat_cov=cc["cov"], chat_inf=cc["inf"],
                         chat_wr=cc["wr"], chat_plac=cc["plac"], repaired=all(cc[k] for k in "abcd"),
                         any_pass=",".join(c for c in CALS if all(conds(c)[k] for k in "abcd")),
                         **{f"ev_{c}": g(s, e, c, nm).cov90 for c in CALS}, **{f"inf_{c}": int(g(s, e, c, nm).n_inf90) for c in CALS}))
R = pd.DataFrame(rows); n = len(R); pd.set_option("display.width", 240)
print(R[["system", "era", "n", "window", "c0_ev", "c0_per", "c1_ev", "c1_per", "gap_c1", "chat", "chat_cov", "chat_inf", "chat_wr", "chat_plac", "repaired", "any_pass"]].round(3).to_string(index=False))
K1 = int((R.gap_c1 >= 10).sum()); K2 = int(R.repaired.sum())
print(f"\nK1: C1 gap >= 10 pp in {K1}/{n} (need >= {int(np.ceil(n/2))}) -> {'PASS' if K1 >= np.ceil(n/2) else 'FAIL'}")
print(f"K2: repaired by out-of-event selection in {K2}/{n} (pass if <= {n//3}) -> {'PASS' if K2 <= n//3 else 'FAIL'}")
print(f"K3 (A11 part): events where no calibrator meets (a)-(d): {int((R.any_pass == '').sum())}/{n}")
# censored bounds for flagged shed hours inside event windows (C1 and the selected calibrator)
import a9_job
cb = []
for s in systems:
    if s not in A.SHED: continue
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    for e, nm in A.events(s).items():
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); loc = df.ts_local.dt.tz_localize(None)
        win = ((loc >= pd.Timestamp(nm["start"])) & (loc < pd.Timestamp(nm["end"])) & (df.split == "eval")).values
        shed = win & df["shed"].values
        if not shed.any(): continue
        P = np.load(os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz"))["P_raw"]
        jb = JobA9(e, "HDA", "L1", df, P, C.QUANTILES, lambda m: None)
        sidx = np.where(shed & np.isfinite(P).all(axis=1))[0]; oidx = jb.valid_idx(win & ~df["shed"].values)
        cal = jb.bundle(jb.cal_idx(pd.Timestamp(nm["start"])))
        for c in ["C1", R[(R.system == s) & (R.era == e)].chat.iloc[0]]:
            lo, hi = jb.bounds(c, cal, sidx, 0.10)
            yr = df["load_raw"].values[sidx]; certain_miss = int((yr > hi).sum()); undet = len(sidx) - certain_miss
            lo_o, hi_o = jb.bounds(c, cal, oidx, 0.10) if len(oidx) else (np.array([]), np.array([]))
            cov_o = int(((jb.y[oidx] >= lo_o) & (jb.y[oidx] <= hi_o)).sum()); N = len(oidx) + len(sidx)
            cb.append(dict(system=s, era=e, calibrator=c, unflagged_hours=len(oidx), flagged_hours=len(sidx), certain_miss=certain_miss,
                           cov_lower=(cov_o) / N, cov_upper=(cov_o + undet) / N, cov_unflagged=cov_o / max(1, len(oidx))))
CB = pd.DataFrame(cb); print("\nCensored bounds over the whole event window (flagged hours treated as censored):"); print(CB.round(3).to_string(index=False))
R.to_csv(os.path.join(A.HERE, "a11_events.csv"), index=False); CB.to_csv(os.path.join(A.HERE, "a11_censored.csv"), index=False)
