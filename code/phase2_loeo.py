"""Phase 2 (v2.1): retrospective leave-one-event-out (LOEO) transfer.

For each (horizon, learner) cell and target era, the target event's
intervals are calibrated ONLY on the other two eras' D_cal bundles
(event-specific: their D_cal_train + their pre-event eval hours), with
cross-era score pooling as documented in calibrators.bounds_*_loeo.
eval_mode='loeo_transfer'. C3 has no LOEO variant (online method) -> n/a
in J3. Output: results/frag_loeo_<horizon>_<learner>.csv.
"""
import os
import time

import numpy as np
import pandas as pd

import exp_common as C
import calibrators as CAL
from job_fit import Job, cell_spec

EXP = os.path.dirname(os.path.abspath(__file__))
ERAS = ["2014", "2018", "2022"]


def main():
    loglines = []
    t0 = time.time()
    frames = {e: pd.read_pickle(os.path.join(EXP, "prepped", f"era{e}.pkl"))
              for e in ERAS}
    for horizon in ["H1H", "HDA"]:
        for learner in ["L1", "L2", "L3"]:
            jobs = {}
            for e in ERAS:
                _, grid = cell_spec(e, horizon, learner)
                P_raw = np.load(os.path.join(
                    EXP, "prepped", f"pred_{e}_{horizon}_{learner}.npz"))["P_raw"]
                jobs[e] = Job(e, horizon, learner, frames[e], P_raw, grid,
                              loglines.append)
            rows = []
            for target in ERAS:
                jt = jobs[target]
                grid = jt.grid
                nev = C.NAMED_EVENTS[target]
                ev_start, ev_end = pd.Timestamp(nev["start"]), pd.Timestamp(nev["end"])
                mask = jt.eval_mask & (jt.loc >= ev_start) & (jt.loc < ev_end)
                idx = jt.valid_idx(mask)
                target_cal = jt.bundle(jt.cal_idx(ev_start))
                pools_cal, pools_tune = [], []
                for other in ERAS:
                    if other == target:
                        continue
                    jo = jobs[other]
                    o_start = pd.Timestamp(C.NAMED_EVENTS[other]["start"])
                    pools_cal.append(jo.bundle(jo.cal_idx(o_start)))
                    pools_tune.append(jo.tune_bundle())
                sub = jt.bundle(idx)
                # C4 LOEO pools tune/cal rows across eras and needs a common
                # quantile grid; the mixed-grid cell (H1H x L1, where 2014
                # uses the 7-quantile reproduction grid) is skipped.
                calnames = ["C1", "C2a", "C2b", "C0x", "C4"]
                if any(len(b["P"][0]) != len(sub["P"][0])
                       for b in pools_cal + pools_tune):
                    calnames.remove("C4")
                    loglines.append(
                        f"[{horizon}/{learner}] C4 LOEO skipped for target "
                        f"{target}: mixed quantile grids across eras")
                for calname in calnames:
                    bounds = {}
                    for alpha in C.ALPHA_LEVELS:
                        if calname == "C1":
                            lo, hi = CAL.bounds_C1_loeo(pools_cal, target_cal,
                                                        sub["P"], alpha, grid)
                        elif calname in ("C2a", "C2b"):
                            lo, hi = CAL.bounds_C2_loeo(
                                pools_cal, target_cal, sub["P"], sub["temp"],
                                alpha, grid, calname)
                        elif calname == "C0x":
                            lo, hi = CAL.bounds_C0x_loeo(pools_cal, sub["P"],
                                                         alpha, grid)
                        else:
                            lo, hi = CAL.bounds_C4_loeo(
                                pools_cal, pools_tune, jt.tune_bundle(),
                                sub["P"], sub["hdh"], alpha, grid)
                        bounds[alpha] = (lo, hi)
                    bounds = C.nest_bounds(bounds)
                    r = jt.metric_row(nev["name"], calname, idx, bounds)
                    r["eval_mode"] = "loeo_transfer"
                    rows.append(r)
            out = pd.DataFrame(rows)
            path = os.path.join(EXP, "results",
                                f"frag_loeo_{horizon}_{learner}.csv")
            out.to_csv(path, index=False)
            loglines.append(f"[{horizon}/{learner}] LOEO -> {path} "
                            f"({time.time() - t0:.1f}s)")
    with open(os.path.join(EXP, "logs", "phase2_loeo.log"), "w") as f:
        f.write("\n".join(loglines) + "\n")
    print("\n".join(loglines), flush=True)


if __name__ == "__main__":
    main()
