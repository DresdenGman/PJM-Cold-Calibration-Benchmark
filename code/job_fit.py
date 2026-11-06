"""One matrix job (v2.1): fit one learner on D_fit only for one era/horizon,
predict on the full era grid, calibrate with C0/C0x/C1/C2a/C2b/C3/C4 under
the chronological discipline (sigma0/gamma from D_tune only; conformal
cutoffs from D_cal = D_cal_train + event-specific pre-event eval hours),
nest endpoints outward (§7), and emit metric rows + bootstrap tuples.

Usage:
  job_fit.py --era 2014 --horizon H1H --learner L1
  job_fit.py --era 2014 --learner L3     (horizon-invariant; emits both)
Outputs: results/frag_<era>_<horizon>_<learner>.csv,
         results/pinball_<era>_<horizon>_<learner>.csv,
         prepped/pred_<era>_<horizon>_<learner>.npz,
         prepped/tuples_<era>_<horizon>_<learner>.npz,
         logs/job_<era>_<horizon>_<learner>.log
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

import exp_common as C
import calibrators as CAL
import learners as LRN
from features import _issuance_positions

EXP = os.path.dirname(os.path.abspath(__file__))
FRAG_COLS = ["era", "horizon", "learner", "calibrator", "eval_mode", "scope",
             "n", "cov80", "cov90", "cov95", "cov98", "pinball90", "winkler90",
             "mean_width90", "upper_headroom", "exceedance_freq",
             "crossing_rate", "n_inf90"]
CALIBRATORS = ["C0", "C0x", "C1", "C2a", "C2b", "C3", "C4"]


class Job:
    def __init__(self, era, horizon, learner, frame, P_raw, grid, log):
        self.era, self.horizon, self.learner = era, horizon, learner
        self.frame, self.grid, self.log = frame, grid, log
        self.P_raw = P_raw
        self.P = C.rearrange(P_raw.copy())          # q-hat := sorted (§0)
        self.y = frame["load"].values
        self.temp = frame["t2m_c"].values
        self.hdh = frame["hdh_c"].values
        self.finite = np.isfinite(P_raw).all(axis=1) & np.isfinite(self.y)
        self.cross = np.zeros(len(frame), dtype=bool)
        f = np.isfinite(P_raw).all(axis=1)
        self.cross[f] = (np.diff(P_raw[f], axis=1) < 0).any(axis=1)
        self.q50 = self.P[:, C.qidx(grid, 0.5)]
        part = frame["part"].values
        self.part = part
        self.eval_mask = (frame["split"] == "eval").values
        self.loc = frame["ts_local"].dt.tz_localize(None)
        self.max_wink_dev = 0.0
        self._c4 = None
        self._aci_bounds = None

    # ------------------------------------------------------------ bundles
    def bundle(self, idx):
        idx = np.asarray(idx)
        return dict(y=self.y[idx], P=self.P[idx], temp=self.temp[idx],
                    hdh=self.hdh[idx], grid=self.grid)

    def valid_idx(self, mask):
        idx = np.where(mask)[0]
        return idx[self.finite[idx]]

    def part_idx(self, part):
        return np.where((self.part == part) & self.finite)[0]

    def tune_bundle(self):
        return self.bundle(self.part_idx("tune"))

    def cal_idx(self, cut):
        """D_cal rows: D_cal_train + eval rows strictly before `cut`."""
        base = self.part_idx("cal")
        if cut is None:
            return base
        pre = np.where(self.eval_mask & (self.loc < cut))[0]
        idx = np.concatenate([base, pre])
        return idx[self.finite[idx]]

    # ------------------------------------------------------------ bounds
    def _c4_params(self):
        if self._c4 is None:
            tune = self.tune_bundle()
            s0 = CAL.c4_sigma0(tune)
            gam = CAL.c4_select_gammas(tune, s0)
            self._c4 = (tune, s0, gam)
            self.log(f"C4 sigma0={s0:.1f} MW; gammas="
                     f"{ {a: (gam[(a, 'hi')], gam[(a, 'lo')]) for a in C.ALPHA_LEVELS} }")
        return self._c4

    def bounds(self, calibrator, cal, idx, alpha):
        sub = self.bundle(idx)
        if calibrator == "C0":
            return CAL.bounds_C0(sub["P"], alpha, self.grid)
        if calibrator == "C1":
            return CAL.bounds_C1(cal, sub["P"], alpha)
        if calibrator == "C2a":
            return CAL.bounds_C2a(cal, sub["P"], sub["temp"], alpha)
        if calibrator == "C2b":
            return CAL.bounds_C2b(cal, sub["P"], sub["temp"], alpha)
        if calibrator == "C0x":
            return CAL.bounds_C0x(cal, sub["P"], alpha)
        if calibrator == "C4":
            tune, s0, gam = self._c4_params()
            return CAL.bounds_C4(cal, tune, s0, gam, sub["P"], sub["hdh"],
                                 alpha)
        raise ValueError(calibrator)

    # ------------------------------------------------------------ ACI (§4)
    def aci_bounds(self):
        """Returns {alpha: (lo_arr, hi_arr)} over grid rows (NaN if not issued)."""
        if self._aci_bounds is not None:
            return self._aci_bounds
        cal_pos = self.part_idx("cal")
        ev_pos = np.where(self.eval_mask & self.finite)[0]
        ev_pos = ev_pos[np.argsort(self.frame["ts_utc"].values[ev_pos])]
        if self.horizon == "H1H":
            batches = [(int(p), [int(p)]) for p in ev_pos]
        else:
            ipos = _issuance_positions(self.frame)
            groups = {}
            for p in ev_pos:
                groups.setdefault(int(ipos[p]), []).append(int(p))
            batches = [(s, sorted(ps)) for s, ps in sorted(groups.items())
                       if s >= 0]
        out = {}
        for alpha in C.ALPHA_LEVELS:
            runner = CAL.ACIRunner(alpha, self.grid)
            seed_E = CAL.cqr_scores(self.y[cal_pos], self.P[cal_pos],
                                    alpha, self.grid)
            runner.seed(cal_pos, seed_E)
            lo_a = np.full(len(self.frame), np.nan)
            hi_a = np.full(len(self.frame), np.nan)
            for s, rows in batches:
                rows = np.array(rows)
                lo, hi = runner.issue_batch(s, rows, self.P[rows],
                                            self.y[rows])
                lo_a[rows], hi_a[rows] = lo, hi
            out[alpha] = (lo_a, hi_a)
            self.log(f"ACI alpha={alpha}: applied updates={runner.applied}, "
                     f"final alpha_t={runner.alpha_t:.4f}")
        self._aci_bounds = out
        return out

    def bounds_aci(self, idx, alpha):
        lo_a, hi_a = self.aci_bounds()[alpha]
        return lo_a[idx], hi_a[idx]

    # ------------------------------------------------------------ metrics
    def metric_row(self, scope, calibrator, idx, bounds_by_alpha):
        y = self.y[idx]
        row = dict(era=self.era, horizon=self.horizon, learner=self.learner,
                   calibrator=calibrator, eval_mode="chronological",
                   scope=scope, n=int(len(idx)))
        for alpha in C.ALPHA_LEVELS:
            lo, hi = bounds_by_alpha[alpha]
            row[C.COV_OF_ALPHA[alpha]] = float(
                np.mean((y >= lo) & (y <= hi))) if len(y) else np.nan
        lo, hi = bounds_by_alpha[0.10]
        row["n_inf90"] = 0
        for _k in ("winkler90", "mean_width90", "upper_headroom",
                   "exceedance_freq", "pinball90"):
            row[_k] = np.nan
        if len(y):
            fin = np.isfinite(lo) & np.isfinite(hi)
            row["n_inf90"] = int((~fin).sum())
            met_w = C.winkler(y, lo, hi, 0.10)
            row["winkler90"] = float(np.mean(met_w))
            row["mean_width90"] = float(np.mean(hi - lo))
            row["upper_headroom"] = float(np.mean(hi - self.q50[idx]))
            row["exceedance_freq"] = float(np.mean(y > hi))
            p_alpha = C.endpoint_pinball(y, lo, hi, 0.10)
            row["pinball90"] = float(np.mean(p_alpha))
            if fin.any():
                dev = np.max(np.abs(met_w[fin] - 2.0 * p_alpha[fin] / 0.10))
                self.max_wink_dev = max(self.max_wink_dev, float(dev))
        row["crossing_rate"] = float(np.mean(self.cross[idx])) if len(idx) else np.nan
        return row

    def all_bounds(self, calibrator, cal, idx):
        """All-alpha bounds for a scope, nested outward (§7)."""
        if calibrator == "C3":
            b = {a: self.bounds_aci(idx, a) for a in C.ALPHA_LEVELS}
        else:
            b = {a: self.bounds(calibrator, cal, idx, a)
                 for a in C.ALPHA_LEVELS}
        return C.nest_bounds(b)

    def run(self):
        era = self.era
        nev = C.NAMED_EVENTS[era]
        ev_start, ev_end = pd.Timestamp(nev["start"]), pd.Timestamp(nev["end"])
        ev_len = int((ev_end - ev_start) / pd.Timedelta(hours=1))
        onset_end = ev_start + pd.Timedelta(hours=min(72, ev_len))
        scopes = [(nev["name"],
                   self.eval_mask & (self.loc >= ev_start) & (self.loc < ev_end),
                   ev_start),
                  (f"onset_{era}",
                   self.eval_mask & (self.loc >= ev_start) & (self.loc < onset_end),
                   ev_start),
                  ("eval_winter", self.eval_mask, None)]
        rows, pinball_rows = [], []
        tuples = {}
        for scope, mask, cut in scopes:
            idx = self.valid_idx(mask)
            cal = self.bundle(self.cal_idx(cut))
            for calname in CALIBRATORS:
                b = self.all_bounds(calname, cal, idx)
                rows.append(self.metric_row(scope, calname, idx, b))
                if scope == nev["name"]:
                    tuples[calname] = b[0.10]
            if scope in (nev["name"], "eval_winter"):
                sub = self.bundle(idx)
                for j, tau in enumerate(self.grid):
                    pinball_rows.append(dict(
                        era=era, horizon=self.horizon, learner=self.learner,
                        scope=scope, tau=float(tau),
                        pinball=float(np.mean(C.pinball(
                            sub["y"], sub["P"][:, j], float(tau))))))
        np.savez_compressed(
            os.path.join(EXP, "prepped",
                         f"tuples_{era}_{self.horizon}_{self.learner}.npz"),
            idx=self.valid_idx(scopes[0][1]), y=self.y[self.valid_idx(scopes[0][1])],
            q50=self.q50[self.valid_idx(scopes[0][1])],
            **{f"{c}_lo": tuples[c][0] for c in CALIBRATORS},
            **{f"{c}_hi": tuples[c][1] for c in CALIBRATORS})

        spells = pd.read_csv(os.path.join(EXP, "cold_spell_events.csv"))
        spells = spells[spells["era"] == int(era)]
        placebos = pd.read_csv(os.path.join(EXP, "placebo_windows.csv"))
        placebos = placebos[placebos["era"] == int(era)]
        for label, table in [("cold_spells", spells), ("placebo", placebos)]:
            wins = []
            for _, w in table.iterrows():
                ws, we = pd.Timestamp(w["start_local"]), pd.Timestamp(w["end_local"])
                m = self.eval_mask & (self.loc >= ws) & (self.loc < we)
                wins.append((self.valid_idx(m), ws))
            if not wins:
                continue
            all_idx = np.concatenate([w[0] for w in wins])
            for calname in CALIBRATORS:
                per_win, pooled = [], {}
                for alpha in C.ALPHA_LEVELS:
                    los, his = [], []
                    for idx_w, ws in wins:
                        if calname == "C3":
                            b = C.nest_bounds({a: self.bounds_aci(idx_w, a)
                                               for a in C.ALPHA_LEVELS})
                            lo, hi = b[alpha]
                        else:
                            cal = self.bundle(self.cal_idx(ws))
                            b = self.all_bounds(calname, cal, idx_w)
                            lo, hi = b[alpha]
                        los.append(lo)
                        his.append(hi)
                    pooled[alpha] = (np.concatenate(los), np.concatenate(his))
                r = self.metric_row(label, calname, all_idx, pooled)
                rows.append(r)
                # event-macro: average the per-window metric rows
                win_rows = []
                for idx_w, ws in wins:
                    if calname == "C3":
                        b = C.nest_bounds({a: self.bounds_aci(idx_w, a)
                                           for a in C.ALPHA_LEVELS})
                    else:
                        cal = self.bundle(self.cal_idx(ws))
                        b = self.all_bounds(calname, cal, idx_w)
                    win_rows.append(self.metric_row(label, calname, idx_w, b))
                macro = dict(win_rows[0])
                nonempty = [wr for wr in win_rows if wr["n"] > 0]
                for k in ["cov80", "cov90", "cov95", "cov98", "pinball90",
                          "winkler90", "mean_width90", "upper_headroom",
                          "exceedance_freq", "crossing_rate"]:
                    macro[k] = float(np.mean([wr[k] for wr in nonempty])) \
                        if nonempty else np.nan
                macro["n"] = int(sum(wr["n"] for wr in win_rows))
                macro["n_inf90"] = int(sum(wr["n_inf90"] for wr in win_rows))
                macro["scope"] = label + "_macro"
                rows.append(macro)
        return pd.DataFrame(rows), pd.DataFrame(pinball_rows)


def emit(era, horizon, learner, frame, P_raw, grid, loglines):
    job = Job(era, horizon, learner, frame, P_raw, grid, loglines.append)
    out, pinb = job.run()
    for c in FRAG_COLS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[FRAG_COLS]
    path = os.path.join(EXP, "results", f"frag_{era}_{horizon}_{learner}.csv")
    out.to_csv(path, index=False)
    pinb.to_csv(os.path.join(
        EXP, "results", f"pinball_{era}_{horizon}_{learner}.csv"), index=False)
    ev = np.where(job.eval_mask & job.finite)[0]
    if len(ev):
        loglines.append(
            f"first valid eval row: {frame['ts_local'].iloc[ev[0]]} "
            f"({len(ev)} of {int(job.eval_mask.sum())} eval rows)")
    loglines.append(f"max |Winkler - 2P/alpha| deviation: "
                    f"{job.max_wink_dev:.3e}")
    loglines.append(f"wrote {path} ({len(out)} rows)")
    return out


def cell_spec(era, horizon, learner):
    """(X frame name, quantile grid) for a matrix cell."""
    if era == "2014" and horizon == "H1H" and learner == "L1":
        return "X1", C.QUANTILES_REPRO      # §0 reproduction exception
    if horizon == "H1H":
        return "X1H", C.QUANTILES
    return "XDA", C.QUANTILES


def fit_and_emit(era, horizon, learner):
    loglines = []
    t0 = time.time()
    frame = pd.read_pickle(os.path.join(EXP, "prepped", f"era{era}.pkl"))
    xname, grid = cell_spec(era, horizon, learner)
    X = pd.read_pickle(os.path.join(EXP, "prepped", f"era{era}_{xname}.pkl"))
    y = frame["load"].values
    fit_mask = (frame["part"] == "fit").values
    if learner == "L2":
        loglines.append(f"L2 params: {LRN.L2_PARAMS}")
    loglines.append(f"cell: X={xname}, quantiles={len(grid)}, "
                    f"fit rows={int(fit_mask.sum())}")
    fn = LRN.fit_predict_L1 if learner == "L1" else LRN.fit_predict_L2
    P_raw = fn(X.values[fit_mask], y[fit_mask], X.values, grid)
    loglines.append(f"[{era}/{horizon}/{learner}] fit+predict "
                    f"{time.time() - t0:.1f}s")
    np.savez_compressed(os.path.join(
        EXP, "prepped", f"pred_{era}_{horizon}_{learner}.npz"), P_raw=P_raw)
    emit(era, horizon, learner, frame, P_raw, grid, loglines)
    loglines.append(f"total {time.time() - t0:.1f}s")
    with open(os.path.join(EXP, "logs",
                           f"job_{era}_{horizon}_{learner}.log"), "w") as f:
        f.write("\n".join(loglines) + "\n")
    print("\n".join(loglines), flush=True)


def run_l3(era):
    loglines = []
    t0 = time.time()
    frame = pd.read_pickle(os.path.join(EXP, "prepped", f"era{era}.pkl"))
    fit_mask = (frame["part"] == "fit").values
    model = LRN.L3Model().fit(frame[fit_mask])
    loglines.append(f"[{era}/L3] GCV={model.gcv_:.6g} lambda={model.lambda_} "
                    f"knots={np.round(model.knots_, 2).tolist()} "
                    f"bin_groups={model.bin_groups_} "
                    f"scale_beta={np.round(model.scale_beta_, 4).tolist()}")
    P_raw = model.predict_quantiles(frame, C.QUANTILES)
    loglines.append(f"[{era}/L3] fit+predict {time.time() - t0:.1f}s")
    for horizon in ["H1H", "HDA"]:
        np.savez_compressed(os.path.join(
            EXP, "prepped", f"pred_{era}_{horizon}_L3.npz"), P_raw=P_raw)
        emit(era, horizon, "L3", frame, P_raw, C.QUANTILES, loglines)
    loglines.append(f"total {time.time() - t0:.1f}s")
    with open(os.path.join(EXP, "logs", f"job_{era}_L3.log"), "w") as f:
        f.write("\n".join(loglines) + "\n")
    print("\n".join(loglines), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--era", required=True)
    ap.add_argument("--horizon", default="H1H")
    ap.add_argument("--learner", required=True)
    a = ap.parse_args()
    if a.learner == "L3":
        run_l3(a.era)
    else:
        fit_and_emit(a.era, a.horizon, a.learner)
