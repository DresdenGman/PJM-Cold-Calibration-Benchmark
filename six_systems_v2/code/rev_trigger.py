"""v13b revision (post hoc): event-stratum calibration.
For each target event of a system:
 (i)  LOEO-all: C1-type cutoff from all other events of the system (corrected normaliser), applied to every hour;
 (ii) past-only: the same from events of earlier eras only, applied to every hour;
 (iii) triggered: the past-only cutoff applied only to hours whose day-ahead forecast footprint temperature is below
      the era's cold threshold (2nd percentile of training temperature, the cold-spell rule); C1 elsewhere.
Reports event, winter and placebo coverage, winter width relative to C1, and repair conditions (a)-(d) with (b) at
equal headroom against C0x. Usage: rev_trigger.py SYSTEMS -> analysis/rev_trigger_<systems>.csv"""
import os, sys
import numpy as np, pandas as pd
import a9_common as A, a9_job
import prep_data as PD
systems = sys.argv[1].split(",")
rows = []
for s in systems:
    C, CAL, JF, F7, JobA9 = a9_job.setup(s)
    ev = A.events(s); eras = sorted(ev, key=int)
    eras = [e for e in eras if os.path.exists(os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz"))]
    jobs, frames = {}, {}
    for e in eras:
        df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{s}_{e}_gefs.pkl")); df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)
        frames[e] = df; jobs[e] = JobA9(e, "HDA", "L1", df, np.load(os.path.join(A.HERE, "preds", f"{s}_{e}_L1_gefs.npz"))["P_raw"], C.QUANTILES, lambda m: None)
    def ev_idx(j, e): return j.valid_idx(j.eval_mask & (j.loc >= pd.Timestamp(ev[e]["start"])) & (j.loc < pd.Timestamp(ev[e]["end"])))
    era_sc = {e: CAL.era_scale_abs(jobs[e].bundle(jobs[e].part_idx("cal")), jobs[e].grid) for e in eras}
    pool_b = {e: jobs[e].bundle(ev_idx(jobs[e], e)) for e in eras}
    plac = pd.read_csv(os.path.join(A.HERE, "work", s, "placebo_windows.csv"))
    for e in eras:
        jt = jobs[e]; df = frames[e]; g = jt.grid; i50 = C.qidx(g, 0.5)
        thr = PD.cold_threshold(df.loc[df["split"] == "train", "t2m_c"]); cold = (df["t2m_c"].values < thr)
        es = pd.Timestamp(ev[e]["start"]); idx = ev_idx(jt, e)
        win_idx = jt.valid_idx(jt.eval_mask)
        pw = [(jt.valid_idx(jt.eval_mask & (jt.loc >= pd.Timestamp(w.start_local)) & (jt.loc < pd.Timestamp(w.end_local))), pd.Timestamp(w.start_local))
              for w in plac[plac.era == int(e)].itertuples()]
        def c1(cut, ix): return jt.all_bounds("C1", jt.bundle(jt.cal_idx(cut)), ix)[0.10]
        def pooled_q(others, cut):
            if not others: return None
            st = CAL.era_scale_abs(jt.bundle(jt.cal_idx(cut)), g)
            sc = np.concatenate([CAL.cqr_scores(pool_b[o]["y"], pool_b[o]["P"], 0.10, g) / era_sc[o] for o in others])
            return C.expansion_only(C.order_statistic_Q(sc, 0.10) * st)
        lo0, hi0 = CAL._cols(jt.P, 0.10, g)
        def bounds(variant, cut, ix):
            l1, h1 = c1(cut, ix)
            if variant == "C1": return l1, h1
            others = [o for o in eras if o != e] if variant == "loeo_all" else [o for o in eras if int(o) < int(e)]
            q = pooled_q(others, cut)
            if q is None: return None
            lp, hp = lo0[ix] - q, hi0[ix] + q
            if variant == "triggered":
                t = cold[ix]; return np.where(t, lp, l1), np.where(t, hp, h1)
            return lp, hp
        y = jt.y; q50 = jt.P[:, i50]; base_h = np.mean(hi0[idx] - q50[idx])
        def ex_c0x(H): return float(np.mean(y[idx] > q50[idx] + (H / base_h) * (hi0[idx] - q50[idx])))
        w1 = c1(None, win_idx); w1w = np.mean(w1[1] - w1[0])
        for v in ["C1", "loeo_all", "past_only", "triggered"]:
            b = bounds(v, es, idx)
            if b is None: rows.append(dict(system=s, era=int(e), variant=v, available=False)); continue
            lo, hi = b; cov = float(np.mean((y[idx] >= lo) & (y[idx] <= hi)))
            wb = bounds(v, None, win_idx); wcov = float(np.mean((y[win_idx] >= wb[0]) & (y[win_idx] <= wb[1]))); wr = float(np.mean(wb[1] - wb[0]) / w1w)
            pl = [bounds(v, ws, ix) for ix, ws in pw if len(ix)]
            pidx = np.concatenate([ix for ix, ws in pw if len(ix)]) if pl else np.array([], int)
            pcov = float(np.mean((y[pidx] >= np.concatenate([p[0] for p in pl])) & (y[pidx] <= np.concatenate([p[1] for p in pl])))) if pl else np.nan
            H = float(np.mean(hi - q50[idx])); ex = float(np.mean(y[idx] > hi))
            rec = dict(system=s, era=int(e), variant=v, available=True, event_cov=cov, winter_cov=wcov, width_ratio=wr, placebo_cov=pcov,
                       trig_share_event=float(cold[idx].mean()), trig_share_winter=float(cold[win_idx].mean()),
                       a=bool(0.85 <= cov <= 0.95), b=bool(np.isfinite(H) and ex < ex_c0x(H) - 1e-9), c=bool(wr <= 1.35), d=bool(pcov <= 0.95))
            rec["repaired"] = rec["a"] and rec["b"] and rec["c"] and rec["d"]; rows.append(rec)
        print(s, e, {r["variant"]: (round(r.get("event_cov", np.nan), 3), round(r.get("width_ratio", np.nan), 2), r.get("repaired")) for r in rows if r["system"] == s and r["era"] == int(e)}, flush=True)
out = os.path.join(A.HERE, "analysis", f"rev_trigger_{'_'.join(systems)}.csv"); pd.DataFrame(rows).to_csv(out, index=False); print("wrote", out)
