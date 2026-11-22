"""Amendment A2 sensitivity arm MW (prior-winter history calibration).

Identical to the frozen chronological arm EXCEPT the calibration pool:
D_cal_train (last 92 training days) is replaced by ALL Dec-Feb (DJF) hours
strictly before the D_cal start whose scores are out-of-sample for the
scoring model:
  - D_tune winter rows: predictions of the frozen era model (already OOS);
  - D_fit winter rows: winter-blocked cross-fitting (refit excluding that
    winter block, predict only that block).
The pre-event eval extension, the S0 operator, calibrator implementations
and evaluation scopes are unchanged. No LOEO era-median normalisation.
C3 is untouched by construction (its seed enters via part 'cal' positions,
exactly as frozen; the trailing 2160h window makes pooled seeds inert).

Outputs: results/frag_mw_<era>_<horizon>_<learner>.csv (eval_mode=mwinter),
         logs/job_mw_<era>_<horizon>_<learner>.log
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

import exp_common as C
import learners as LRN
import job_fit as JF

EXP = os.path.dirname(os.path.abspath(__file__))
CALIBRATORS = JF.CALIBRATORS


def winter_id(ts):
    """Meteorological winter id: Dec of year Y and Jan/Feb of Y+1 -> Y."""
    y, m = ts.year, ts.month
    return y if m == 12 else (y - 1 if m in (1, 2) else None)


def build_P_mw(era, horizon, learner, log):
    frame = pd.read_pickle(os.path.join(EXP, "prepped", f"era{era}.pkl"))
    xname, grid = JF.cell_spec(era, horizon, learner)
    X = pd.read_pickle(os.path.join(EXP, "prepped", f"era{era}_{xname}.pkl"))
    P = np.load(os.path.join(
        EXP, "prepped", f"pred_{era}_{horizon}_{learner}.npz"))["P_raw"].copy()
    loc = frame["ts_local"].dt.tz_localize(None)
    part = frame["part"].values
    y = frame["load"].values
    months = loc.dt.month.values
    wids = np.array([winter_id(t) if m in (12, 1, 2) else -1
                     for t, m in zip(loc, months)], dtype=int)
    fit_rows = np.where(part == "fit")[0]
    blocks = sorted({int(w) for w in wids[fit_rows] if w >= 0})
    for w in blocks:
        block_pos = np.where((part == "fit") & (wids == w))[0]
        train_mask = (part == "fit") & (wids != w)
        if learner == "L3":
            model = LRN.L3Model().fit(frame[train_mask])
            Pb = model.predict_quantiles(frame.iloc[block_pos], C.QUANTILES)
        else:
            fn = LRN.fit_predict_L1 if learner == "L1" else LRN.fit_predict_L2
            Pb = fn(X.values[train_mask], y[train_mask],
                    X.values[block_pos], grid)
        P[block_pos] = Pb
        log(f"cross-fit winter {w}: refit on {int(train_mask.sum())} rows, "
            f"predicted {len(block_pos)} block rows")
    pool_mask = np.isin(part, ["fit", "tune"]) & (wids >= 0)
    pool_pos = np.where(pool_mask)[0]
    comp = {}
    for w in sorted({int(v) for v in wids[pool_pos]}):
        comp[w] = int((wids[pool_pos] == w).sum())
    log(f"MW pool: {len(pool_pos)} DJF rows; per-winter rows {comp}; "
        f"sources fit={int(((part[pool_pos]=='fit')).sum())} "
        f"tune={int(((part[pool_pos]=='tune')).sum())}")
    return frame, P, grid, pool_pos


class MWJob(JF.Job):
    def __init__(self, *a, pool_pos=None, **kw):
        super().__init__(*a, **kw)
        self.pool_pos = pool_pos

    def cal_idx(self, cut):
        """MW pool + the same pre-event eval extension as frozen."""
        base = self.pool_pos
        if cut is None:
            idx = base
        else:
            pre = np.where(self.eval_mask & (self.loc < cut))[0]
            idx = np.concatenate([base, pre])
        return idx[self.finite[idx]]

    def run_mw(self):
        era = self.era
        nev = C.NAMED_EVENTS[era]
        ev_start, ev_end = pd.Timestamp(nev["start"]), pd.Timestamp(nev["end"])
        ev_len = int((ev_end - ev_start) / pd.Timedelta(hours=1))
        onset_end = ev_start + pd.Timedelta(hours=min(72, ev_len))
        scopes = [(nev["name"],
                   self.eval_mask & (self.loc >= ev_start)
                   & (self.loc < ev_end), ev_start),
                  (f"onset_{era}",
                   self.eval_mask & (self.loc >= ev_start)
                   & (self.loc < onset_end), ev_start),
                  ("eval_winter", self.eval_mask, None)]
        rows = []
        for scope, mask, cut in scopes:
            idx = self.valid_idx(mask)
            cal = self.bundle(self.cal_idx(cut))
            for calname in CALIBRATORS:
                b = self.all_bounds(calname, cal, idx)
                rows.append(self.metric_row(scope, calname, idx, b))
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
                pooled = {}
                for alpha in C.ALPHA_LEVELS:
                    los, his = [], []
                    for idx_w, ws in wins:
                        cal = self.bundle(self.cal_idx(ws))
                        b = self.all_bounds(calname, cal, idx_w)
                        lo, hi = b[alpha]
                        los.append(lo)
                        his.append(hi)
                    pooled[alpha] = (np.concatenate(los), np.concatenate(his))
                rows.append(self.metric_row(label, calname, all_idx, pooled))
        out = pd.DataFrame(rows)
        out["eval_mode"] = "mwinter"
        return out


def run_cell(era, horizon, learner):
    loglines = []
    t0 = time.time()
    frame, P, grid, pool_pos = build_P_mw(era, horizon, learner,
                                          loglines.append)
    job = MWJob(era, horizon, learner, frame, P, grid, loglines.append,
                pool_pos=pool_pos)
    out = job.run_mw()
    for c in JF.FRAG_COLS:
        if c not in out.columns:
            out[c] = np.nan
    out = out[JF.FRAG_COLS]
    path = os.path.join(EXP, "results",
                        f"frag_mw_{era}_{horizon}_{learner}.csv")
    out.to_csv(path, index=False)
    loglines.append(f"[{era}/{horizon}/{learner}] total "
                    f"{time.time() - t0:.1f}s; wrote {path} ({len(out)} rows)")
    with open(os.path.join(EXP, "logs",
                           f"job_mw_{era}_{horizon}_{learner}.log"),
              "w") as f:
        f.write("\n".join(loglines) + "\n")
    print("\n".join(loglines), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--era", required=True)
    ap.add_argument("--horizon", default="HDA")
    ap.add_argument("--learner", required=True)
    a = ap.parse_args()
    if a.learner == "L3":
        for hz in ["HDA", "H1H"]:
            run_cell(a.era, hz, "L3")
    else:
        run_cell(a.era, a.horizon, a.learner)
