"""A9 Job: job_fit.Job with D_tune = D_cal (cross-fitted prior winters), C3 with an item-count
window, and C6/C7. Call setup(system) before use."""
import os
import numpy as np
import a9_common as A

def setup(system):
    os.chdir(os.path.join(A.HERE, "work", system))   # frozen populations
    import exp_common as C
    C.NAMED_EVENTS = {k: v for k, v in A.events(system).items()}
    import calibrators as CAL
    import job_fit as JF
    JF.EXP = os.path.join(A.HERE, "work", system)    # populations + tuples live here, not in repo/code
    import a7_funcs as F7
    base = CAL.ACIRunner if not hasattr(CAL, "_ACI_ORIG") else CAL._ACI_ORIG
    CAL._ACI_ORIG = base

    class ACIItems(base):
        """C3 with a window of the most recent 2,160 scored items (A9)."""
        def issue_batch(self, s, row_pos, P_rows, y_rows):
            self._apply_updates(s)
            v = np.asarray(self.items_v); a = np.asarray(self.items_a); E = np.asarray(self.items_E)
            if len(v):
                ok = a < s; vv, EE = v[ok], E[ok]
                w = EE[np.argsort(vv)][-C.ACI_WINDOW_H:]
            else:
                w = np.array([])
            q = C.expansion_only(C.order_statistic_Q(w, self.alpha_t))
            lo_c, hi_c = CAL._cols(P_rows, self.alpha_star, self.grid)
            lo, hi = lo_c - q, hi_c + q
            E_new = np.maximum(lo_c - y_rows, y_rows - hi_c)
            for j, pos in enumerate(row_pos):
                self.items_v.append(int(pos)); self.items_a.append(int(pos) + 2); self.items_E.append(float(E_new[j]))
                self.pending.append((int(pos) + 2, int(pos), 0.0 if lo[j] <= y_rows[j] <= hi[j] else 1.0))
            return lo, hi
    CAL.ACIRunner = ACIItems

    DT_EDGES = np.array([-np.inf, -8.0, -4.0, 0.0, np.inf])
    def _dt_bin(d):
        return np.clip(np.searchsorted(DT_EDGES, d, side="right") - 1, 0, len(DT_EDGES) - 2)
    def bounds_C8(cal, P_new, dt_new, alpha, track):
        s_ = CAL.cqr_scores(cal["y"], cal["P"], alpha, cal["grid"])
        ok = np.isfinite(cal["dT"]); s_, b = s_[ok], _dt_bin(cal["dT"][ok])
        qg = C.order_statistic_Q(s_, alpha)
        Q = np.empty(len(DT_EDGES) - 1)
        for k in range(len(Q)):
            sk = s_[b == k]; nk = len(sk); qk = C.order_statistic_Q(sk, alpha) if nk else np.inf
            if track == "C8a":
                Q[k] = C.expansion_only(max(qk, qg))
            else:
                Q[k] = C.expansion_only(qg if nk == 0 else (np.inf if np.isinf(qk) else (nk * qk + C.MONDRIAN_SHRINK_M * qg) / (nk + C.MONDRIAN_SHRINK_M)))
        lo, hi = CAL._cols(P_new, alpha, cal["grid"])
        q = Q[_dt_bin(np.where(np.isfinite(dt_new), dt_new, 0.0))]
        return lo - q, hi + q

    class JobA9(JF.Job):
        _h = None
        def bundle(self, idx):
            b = super().bundle(idx)
            idx = np.asarray(idx)
            if "dT24" in self.frame.columns:
                b["dT"] = self.frame["dT24"].values[idx]
            return b
        def tune_bundle(self):
            if os.environ.get("DESIGN") in ("D1", "D1b", "D3"):   # A13 D1 (and v13 D1b/D3): original D_tune
                return self.bundle(self.part_idx("tune"))
            return self.bundle(self.part_idx("cal"))
        def bounds(self, calibrator, cal, idx, alpha):
            sub = self.bundle(idx)
            if calibrator == "C6":
                if self._h is None:
                    tune = self.tune_bundle(); self._h = {a: F7.c6_select_h(tune, a) for a in C.ALPHA_LEVELS}
                    self.log(f"C6 bandwidths={self._h}")
                return F7.bounds_C6(cal, self._h[alpha], sub["P"], sub["temp"], alpha)
            if calibrator == "C7":
                return F7.bounds_C7(cal, sub["P"], sub["hdh"], alpha)
            if calibrator in ("C8a", "C8b"):
                return bounds_C8(cal, sub["P"], sub["dT"], alpha, calibrator)
            return super().bounds(calibrator, cal, idx, alpha)
    JF.CALIBRATORS = ["C0", "C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"] + (["C8a", "C8b"] if os.environ.get("A10") else [])
    return C, CAL, JF, F7, JobA9
