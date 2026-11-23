"""A9 analysis against PLAN_A9.md: G1-G4 and the diagnostics.
Usage: analyze_a9.py WEATHER [LEARNER]"""
import os, sys, glob
import numpy as np, pandas as pd
import a9_common as A
weather = sys.argv[1]; learner = sys.argv[2] if len(sys.argv) > 2 else "L1"
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
RES = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(A.HERE, "results", f"a9_*_{learner}_{weather}.csv"))], ignore_index=True)
def g(s, e, c, sc):
    r = RES[(RES.system == s) & (RES.era == int(e)) & (RES.calibrator == c) & (RES.scope == sc)]
    assert len(r) == 1, (s, e, c, sc, len(r)); return r.iloc[0]
rows = []
for s in ["pjm", "miso"]:
    ev = A.events(s); eras = [e for e in A.ERAS[s] if len(RES[(RES.system == s) & (RES.era == int(e))])]
    delta = {c: {e: g(s, e, "C0", ev[e]["name"]).winkler90 - g(s, e, c, ev[e]["name"]).winkler90 for e in eras} for c in CALS}
    for e in eras:
        nm = ev[e]["name"]
        c0e, c0p, c1e, c1p = g(s, e, "C0", nm), g(s, e, "C0", "eval_winter"), g(s, e, "C1", nm), g(s, e, "C1", "eval_winter")
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in eras if k != e))
        def conds(c):
            r, w, p = g(s, e, c, nm), g(s, e, c, "eval_winter"), g(s, e, c, "placebo")
            r0, rx = g(s, e, "C0", nm), g(s, e, "C0x", nm)
            pareto = (r.exceedance_freq <= rx.exceedance_freq) and (r.upper_headroom <= rx.upper_headroom)
            interp = False
            if rx.upper_headroom != r0.upper_headroom and min(r0.upper_headroom, rx.upper_headroom) <= r.upper_headroom <= max(r0.upper_headroom, rx.upper_headroom):
                ex_at = r0.exceedance_freq + (rx.exceedance_freq - r0.exceedance_freq) * (r.upper_headroom - r0.upper_headroom) / (rx.upper_headroom - r0.upper_headroom)
                interp = r.exceedance_freq < ex_at
            wr = w.mean_width90 / c1p.mean_width90
            return dict(cov=r.cov90, inf=int(r.n_inf90), a=bool(0.85 <= r.cov90 <= 0.95), b=bool(pareto or interp),
                        c=bool(wr <= 1.35), d=bool(p.cov90 <= 0.95), wr=wr, plac=p.cov90)
        cc = conds(chat)
        allpass = [c for c in CALS if all(conds(c)[k] for k in "abcd")]
        rows.append(dict(system=s, era=e, c0_ev=c0e.cov90, c0_per=c0p.cov90, c1_ev=c1e.cov90, c1_per=c1p.cov90,
                         gap_c0=100 * (c0p.cov90 - c0e.cov90), gap_c1=100 * (c1p.cov90 - c1e.cov90),
                         chat=chat, chat_cov=cc["cov"], chat_inf=cc["inf"], chat_wr=cc["wr"], chat_plac=cc["plac"],
                         a=cc["a"], b=cc["b"], c=cc["c"], d=cc["d"], repaired=all(cc[k] for k in "abcd"), any_pass=",".join(allpass),
                         **{f"ev_{c}": g(s, e, c, nm).cov90 for c in ["C0"] + CALS},
                         **{f"inf_{c}": int(g(s, e, c, nm).n_inf90) for c in ["C0"] + CALS},
                         **{f"per_{c}": g(s, e, c, "eval_winter").cov90 for c in ["C0"] + CALS},
                         **{f"wr_{c}": g(s, e, c, "eval_winter").mean_width90 / c1p.mean_width90 for c in ["C0"] + CALS},
                         **{f"pl_{c}": g(s, e, c, "placebo").cov90 for c in ["C0"] + CALS}))
R = pd.DataFrame(rows); n = len(R)
G1 = int((R.gap_c1 >= 10).sum()); G2 = int(R.repaired.sum())
print(f"[{weather} {learner}] events={n}")
print(f"G1: C1 gap >= 10 pp in {G1}/{n} (need >= 9) -> {'PASS' if G1 >= 9 else 'FAIL'}")
print(f"G2: repaired by out-of-event selection in {G2}/{n} (pass if <= 4) -> {'PASS' if G2 <= 4 else 'FAIL'}")
print("any calibrator meeting (a)-(d):", {f"{r.system} {r.era}": r.any_pass for r in R.itertuples() if r.any_pass})
import a9_job
diag, nulls, loeo = [], [], []
for s in ["pjm", "miso"]:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    ev = A.events(s); eras = sorted(R[R.system == s].era)
    jobs = {}
    for e in eras:
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_{weather}.pkl"))
        P = np.load(os.path.join(A.HERE, "preds", f"{s}_{e}_{learner}_{weather}.npz"))["P_raw"]
        jobs[e] = JobA9(e, "HDA", learner, df, P, C.QUANTILES, lambda m: None)
    for e in eras:
        jb = jobs[e]; nm = ev[e]; es, ee = pd.Timestamp(nm["start"]), pd.Timestamp(nm["end"])
        idx = jb.valid_idx(jb.eval_mask & (jb.loc >= es) & (jb.loc < ee))
        grid = jb.grid; q = jb.P
        q05, q50, q95 = q[:, C.qidx(grid, 0.05)], q[:, C.qidx(grid, 0.5)], q[:, C.qidx(grid, 0.95)]
        err = jb.y[idx] - q50[idx]; half = (q95[idx] - q05[idx]) / 2
        miss = (jb.y[idx] < q05[idx]) | (jb.y[idx] > q95[idx])
        diag.append(dict(system=s, era=e, mean_err=float(err.mean()), mean_half=float(half.mean()),
                         bias_ratio=float(err.mean() / half.mean()), share_above=float((jb.y[idx] > q95[idx]).sum() / max(1, miss.sum()))))
        L = int((ee - es) / pd.Timedelta(hours=1))
        evrows = np.where(jb.eval_mask)[0]; locs = jb.loc
        wins = []
        for i in evrows:
            ws = locs.iloc[i]
            if ws.hour != 0: continue
            we = ws + pd.Timedelta(hours=L)
            if ws < ee and we > es: continue
            m = jb.eval_mask & (jb.loc >= ws) & (jb.loc < we)
            if m.sum() < L: continue
            wins.append((ws, jb.valid_idx(m)))
        rec = dict(system=s, era=e, n_windows=len(wins))
        for c in ["C0"] + CALS:
            covs = []
            for ws, wi in wins:
                if c == "C3":
                    b = C.nest_bounds({a: jb.bounds_aci(wi, a) for a in C.ALPHA_LEVELS})
                else:
                    b = jb.all_bounds(c, jb.bundle(jb.cal_idx(ws)), wi)
                lo, hi = b[0.10]; covs.append(float(np.mean((jb.y[wi] >= lo) & (jb.y[wi] <= hi))))
            covs = np.array(covs); evc = g(s, e, c, nm["name"]).cov90
            rec[f"pct_{c}"] = float(np.mean(covs < evc)); rec[f"ok_{c}"] = float(np.mean((covs >= 0.85) & (covs <= 0.95)))
            rec[f"med_{c}"] = float(np.median(covs))
        nulls.append(rec)
    for e in eras:
        jt = jobs[e]; nm = ev[e]; es, ee = pd.Timestamp(nm["start"]), pd.Timestamp(nm["end"])
        idx = jt.valid_idx(jt.eval_mask & (jt.loc >= es) & (jt.loc < ee))
        target = jt.bundle(jt.cal_idx(es)); sub = jt.bundle(idx)
        pools = []
        for o in eras:
            if o == e: continue
            jo = jobs[o]; no = ev[o]
            pools.append(jo.bundle(jo.valid_idx(jo.eval_mask & (jo.loc >= pd.Timestamp(no["start"])) & (jo.loc < pd.Timestamp(no["end"])))))
        rec = dict(system=s, era=e)
        for c in ["C1", "C2a", "C2b", "C4"]:
            if c == "C1":
                lo, hi = CAL.bounds_C1_loeo(pools, target, sub["P"], 0.10, jt.grid)
            elif c in ("C2a", "C2b"):
                lo, hi = CAL.bounds_C2_loeo(pools, target, sub["P"], sub["temp"], 0.10, jt.grid, c)
            else:
                lo, hi = CAL.bounds_C4_loeo(pools, pools, target, sub["P"], sub["hdh"], 0.10, jt.grid)
            cov = float(np.mean((sub["y"] >= lo) & (sub["y"] <= hi))); inf_l = int((~np.isfinite(lo) | ~np.isfinite(hi)).sum())
            ch = g(s, e, c, nm["name"])
            rec[f"loeo_{c}"] = cov; rec[f"chron_{c}"] = ch.cov90; rec[f"gap_{c}"] = 100 * (cov - ch.cov90)
            rec[f"finite_{c}"] = bool(inf_l == 0 and ch.n_inf90 == 0)
        loeo.append(rec)
D = pd.DataFrame(diag); NW = pd.DataFrame(nulls); LO = pd.DataFrame(loeo)
G3 = int((NW.pct_C0 < 0.10).sum())
print(f"G3: C0 event below 10th percentile of null windows in {G3}/{n} (need >= 9) -> {'PASS' if G3 >= 9 else 'FAIL'}")
g4 = {c: (float(LO[LO[f'finite_{c}']][f'gap_{c}'].abs().mean()) if LO[f'finite_{c}'].any() else float('nan')) for c in ["C2a", "C2b"]}
print(f"G4: mean |LOEO gap| finite cells: C2a {g4['C2a']:.1f} pp (n={int(LO.finite_C2a.sum())}), C2b {g4['C2b']:.1f} pp (n={int(LO.finite_C2b.sum())}) -> {'PASS' if np.nanmax(list(g4.values())) >= 10 else 'FAIL'}")
pd.set_option("display.width", 250)
print(R[["system", "era", "c0_ev", "c0_per", "c1_ev", "c1_per", "gap_c1", "chat", "chat_cov", "chat_inf", "chat_wr", "chat_plac", "a", "b", "c", "d", "any_pass"]].round(3).to_string(index=False))
print(D.round(3).to_string(index=False)); print(NW.round(3).to_string(index=False)); print(LO.round(3).to_string(index=False))
tag = f"{learner}_{weather}"
for nmx, X in [("events", R), ("bias", D), ("null", NW), ("loeo", LO)]:
    X.to_csv(os.path.join(A.HERE, f"a9_{nmx}_{tag}.csv"), index=False)
