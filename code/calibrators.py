"""Calibrators per METHODS_FORMULAS v2.1 §§1-4 + C0x baseline.

A "bundle" is a dict with y, P (pointwise-SORTED base quantiles, v2.1 §0),
temp (deg C), hdh (deg C-hours), grid (the quantile grid P follows).
All conformal cutoffs use the §0 order-statistic operator; all corrections
are expansion-only (Q+ = max(0, Q)); +inf cutoffs yield infinite intervals
and are preserved (never capped, never dropped).
"""
import numpy as np

import exp_common as C


def _pair(alpha, grid):
    return C.pair_for_alpha(alpha, grid)


def _cols(P, alpha, grid):
    lo_t, hi_t = _pair(alpha, grid)
    return P[:, C.qidx(grid, lo_t)], P[:, C.qidx(grid, hi_t)]


def bounds_C0(P, alpha, grid):
    lo, hi = _cols(P, alpha, grid)
    return lo.copy(), hi.copy()


def cqr_scores(y, P, alpha, grid):
    lo, hi = _cols(P, alpha, grid)
    return np.maximum(lo - y, y - hi)


def bounds_C1(cal, P_new, alpha):
    grid = cal["grid"]
    q = C.expansion_only(C.order_statistic_Q(
        cqr_scores(cal["y"], cal["P"], alpha, grid), alpha))
    lo, hi = _cols(P_new, alpha, grid)
    return lo - q, hi + q


def _bin_idx(temp):
    return np.clip(np.searchsorted(C.TEMP_BIN_EDGES, temp, side="right") - 1,
                   0, len(C.TEMP_BIN_EDGES) - 2)


def _bin_Qs(cal, alpha):
    """Per-bin Q_k and global Q via the §0 operator on D_cal scores."""
    s = cqr_scores(cal["y"], cal["P"], alpha, cal["grid"])
    b = _bin_idx(cal["temp"])
    qg = C.order_statistic_Q(s, alpha)
    Q, ns = [], []
    for k in range(len(C.TEMP_BIN_EDGES) - 1):
        sk = s[b == k]
        ns.append(len(sk))
        Q.append(C.order_statistic_Q(sk, alpha))
    return np.array(Q), qg, np.array(ns)


def bounds_C2a(cal, P_new, temp_new, alpha):
    """Guarantee-preserving track: Q_k^use = max(Q_k, Q_global), expansion-only."""
    Q, qg, _ = _bin_Qs(cal, alpha)
    quse = np.array([C.expansion_only(max(qk, qg)) for qk in Q])
    lo, hi = _cols(P_new, alpha, cal["grid"])
    q = quse[_bin_idx(temp_new)]
    return lo - q, hi + q


def bounds_C2b(cal, P_new, temp_new, alpha):
    """Shrinkage heuristic (no Mondrian guarantee): Q~_k = (n_k Q_k + m Q_g) /
    (n_k + m), m = 50; n_k = 0 -> Q_g; Q_k = +inf with n_k > 0 -> +inf."""
    Q, qg, ns = _bin_Qs(cal, alpha)
    qt = np.empty_like(Q)
    for k in range(len(Q)):
        if ns[k] == 0:
            qt[k] = qg
        elif np.isinf(Q[k]):
            qt[k] = np.inf
        else:
            qt[k] = (ns[k] * Q[k] + C.MONDRIAN_SHRINK_M * qg) \
                / (ns[k] + C.MONDRIAN_SHRINK_M)
    qt = np.array([C.expansion_only(v) for v in qt])
    lo, hi = _cols(P_new, alpha, cal["grid"])
    q = qt[_bin_idx(temp_new)]
    return lo - q, hi + q


def bounds_C0x(cal, P_new, alpha):
    """Proportional-expansion baseline: smallest k in C0X_K_GRID whose
    D_cal coverage reaches nominal; expansion around q_0.5."""
    grid = cal["grid"]
    lo_c, hi_c = _cols(cal["P"], alpha, grid)
    med_c = cal["P"][:, C.qidx(grid, 0.5)]
    y = cal["y"]
    k_use = C.C0X_K_GRID[-1]
    for k in C.C0X_K_GRID:
        lo = med_c - k * (med_c - lo_c)
        hi = med_c + k * (hi_c - med_c)
        if np.mean((y >= lo) & (y <= hi)) >= 1.0 - alpha:
            k_use = k
            break
    lo_n, hi_n = _cols(P_new, alpha, grid)
    med_n = P_new[:, C.qidx(grid, 0.5)]
    return med_n - k_use * (med_n - lo_n), med_n + k_use * (hi_n - med_n)


# --------------------------------------------------------------------- C4 (§3)
def c4_sigma0(tune):
    med = tune["P"][:, C.qidx(tune["grid"], 0.5)]
    return max(C.SIGMA0_FLOOR_MW, float(np.median(np.abs(tune["y"] - med))))


def c4_select_gammas(tune, sigma0):
    """Per-alpha, per-side independent grid search on the D_tune inner
    holdout (last 25%). Objective: side exceedance rate closest to
    beta = alpha/2; ties -> smaller mean added margin -> smaller gamma."""
    grid = tune["grid"]
    y, P, hdh = tune["y"], tune["P"], tune["hdh"]
    n = len(y)
    cut = int(np.floor(n * (1.0 - C.C4_HOLDOUT_FRAC)))
    out = {}
    for alpha in C.ALPHA_LEVELS:
        lo_c, hi_c = _cols(P, alpha, grid)
        d = {"hi": y - hi_c, "lo": lo_c - y}
        for side in ["hi", "lo"]:
            best = None
            for g in C.C4_GAMMA_GRID:
                s_fit = sigma0 * (1.0 + g * hdh[:cut])
                s_hold = sigma0 * (1.0 + g * hdh[cut:])
                q = C.expansion_only(C.order_statistic_Q(
                    d[side][:cut] / s_fit, alpha / 2.0))
                if side == "hi":
                    bound = hi_c[cut:] + q * s_hold
                    rate = float(np.mean(y[cut:] > bound))
                    margin = float(np.mean(q * s_hold))
                else:
                    bound = lo_c[cut:] - q * s_hold
                    rate = float(np.mean(y[cut:] < bound))
                    margin = float(np.mean(q * s_hold))
                key = (abs(rate - alpha / 2.0), margin, g)
                if best is None or key < best[0]:
                    best = (key, g)
            out[(alpha, side)] = best[1]
    return out


def bounds_C4(cal, tune, sigma0, gammas, P_new, hdh_new, alpha):
    grid = cal["grid"]
    g_hi, g_lo = gammas[(alpha, "hi")], gammas[(alpha, "lo")]
    lo_c, hi_c = _cols(cal["P"], alpha, grid)
    s_cal = {"hi": sigma0 * (1.0 + g_hi * cal["hdh"]),
             "lo": sigma0 * (1.0 + g_lo * cal["hdh"])}
    q_hi = C.expansion_only(C.order_statistic_Q(
        (cal["y"] - hi_c) / s_cal["hi"], alpha / 2.0))
    q_lo = C.expansion_only(C.order_statistic_Q(
        (lo_c - cal["y"]) / s_cal["lo"], alpha / 2.0))
    lo_n, hi_n = _cols(P_new, alpha, grid)
    return (lo_n - q_lo * sigma0 * (1.0 + g_lo * hdh_new),
            hi_n + q_hi * sigma0 * (1.0 + g_hi * hdh_new))


# --------------------------------------------------------------------- C3 (§4 ACI)
class ACIRunner:
    """Projected ACI with delayed, batched feedback (v2.1 §4).

    Items are scored forecasts: v = target-hour grid position,
    a = v + 2 (label available = hour end + 1h), E = CQR score at the
    FIXED target level alpha*. State (alpha_t) is per (alpha*, horizon,
    learner) — one runner per alpha*. Issuance proceeds in batches: at
    issuance position s, pending error updates with a < s are applied
    first (in v order), then the clock window
    I(s) = {i : s - 2160 <= v_i < s, a_i < s} supplies the cutoff via
    the §0 operator at level alpha_t; the batch's intervals are frozen.
    """

    def __init__(self, alpha_star, grid):
        self.alpha_star = alpha_star
        self.grid = grid
        self.alpha_t = alpha_star
        self.items_v, self.items_a, self.items_E = [], [], []
        self.pending = []          # (a, v, err) not yet applied, v-ordered
        self.applied = 0

    def seed(self, v, E):
        v = np.asarray(v)
        self.items_v.extend(v.tolist())
        self.items_a.extend((v + 2).tolist())
        self.items_E.extend(np.asarray(E, dtype=float).tolist())

    def _apply_updates(self, s):
        self.pending.sort(key=lambda t: t[1])
        while self.pending and self.pending[0][0] < s:
            _, _, err = self.pending.pop(0)
            self.alpha_t = float(np.clip(
                self.alpha_t + C.ACI_ETA * (self.alpha_star - err),
                *C.ACI_ALPHA_CLIP))
            self.applied += 1

    def issue_batch(self, s, row_pos, P_rows, y_rows):
        """Issue intervals for one batch. Returns (lo, hi) arrays."""
        self._apply_updates(s)
        v = np.asarray(self.items_v)
        a = np.asarray(self.items_a)
        E = np.asarray(self.items_E)
        if len(v):
            m = (v >= s - C.ACI_WINDOW_H) & (v < s) & (a < s)
            w = E[m]
        else:
            w = np.array([])
        q = C.expansion_only(C.order_statistic_Q(w, self.alpha_t))
        lo_c, hi_c = _cols(P_rows, self.alpha_star, self.grid)
        lo, hi = lo_c - q, hi_c + q
        # register issued items (scores fixed at alpha*; errors pending)
        E_new = np.maximum(lo_c - y_rows, y_rows - hi_c)
        for j, pos in enumerate(row_pos):
            self.items_v.append(int(pos))
            self.items_a.append(int(pos) + 2)
            self.items_E.append(float(E_new[j]))
            err = 0.0 if (lo[j] <= y_rows[j] <= hi[j]) else 1.0
            self.pending.append((int(pos) + 2, int(pos), err))
        return lo, hi


# ---------------------------------------------------------------- LOEO (retrospective)
def _era_scale(bundle, grid):
    s = cqr_scores(bundle["y"], bundle["P"], 0.10, grid)
    return max(float(np.median(s[np.isfinite(s)])), C.SIGMA0_FLOOR_MW)


def bounds_C1_loeo(pools, target, P_new, alpha, grid):
    st = _era_scale(target, target["grid"])
    norm = [cqr_scores(b["y"], b["P"], alpha, b["grid"]) / _era_scale(b, b["grid"])
            for b in pools]
    q = C.expansion_only(
        C.order_statistic_Q(np.concatenate(norm), alpha) * st)
    lo, hi = _cols(P_new, alpha, grid)
    return lo - q, hi + q


def bounds_C2_loeo(pools, target, P_new, temp_new, alpha, grid, track):
    st = _era_scale(target, target["grid"])
    alln = np.concatenate([cqr_scores(b["y"], b["P"], alpha, b["grid"])
                           / _era_scale(b, b["grid"]) for b in pools])
    allb = np.concatenate([_bin_idx(b["temp"]) for b in pools])
    qg = C.order_statistic_Q(alln, alpha) * st
    Q = np.full(len(C.TEMP_BIN_EDGES) - 1, qg)
    for k in range(len(Q)):
        sk = alln[allb == k]
        nk = len(sk)
        if track == "C2a":
            qk = C.order_statistic_Q(sk, alpha) * st if nk else np.inf
            Q[k] = C.expansion_only(max(qk, qg))
        else:
            if nk == 0:
                Q[k] = C.expansion_only(qg)
            else:
                qk = C.order_statistic_Q(sk, alpha) * st
                if np.isinf(qk):
                    Q[k] = np.inf
                else:
                    Q[k] = C.expansion_only(
                        (nk * qk + C.MONDRIAN_SHRINK_M * qg)
                        / (nk + C.MONDRIAN_SHRINK_M))
    lo, hi = _cols(P_new, alpha, grid)
    q = Q[_bin_idx(temp_new)]
    return lo - q, hi + q


def bounds_C0x_loeo(pools, P_new, alpha, grid):
    lo_t, hi_t = C.pair_for_alpha(alpha, grid)
    ilo, ihi, imed = (C.qidx(grid, lo_t), C.qidx(grid, hi_t),
                      C.qidx(grid, 0.5))
    k_use = C.C0X_K_GRID[-1]
    for k in C.C0X_K_GRID:
        covs = []
        for b in pools:
            bg = b["grid"]
            blo_t, bhi_t = C.pair_for_alpha(alpha, bg)
            blo, bhi, bmed = (b["P"][:, C.qidx(bg, blo_t)],
                              b["P"][:, C.qidx(bg, bhi_t)],
                              b["P"][:, C.qidx(bg, 0.5)])
            lo = bmed - k * (bmed - blo)
            hi = bmed + k * (bhi - bmed)
            covs.append(np.mean((b["y"] >= lo) & (b["y"] <= hi)))
        if float(np.mean(covs)) >= 1.0 - alpha:
            k_use = k
            break
    lo_n = P_new[:, imed] - k_use * (P_new[:, imed] - P_new[:, ilo])
    hi_n = P_new[:, imed] + k_use * (P_new[:, ihi] - P_new[:, imed])
    return lo_n, hi_n


def bounds_C4_loeo(pools_cal, pools_tune, target_tune, P_new, hdh_new,
                   alpha, grid):
    """Retrospective C4: gammas from pooled other-era D_tune (single pooled
    sigma0 over the pooled tune rows — documented approximation), cutoffs
    from pooled other-era D_cal side scores normalized by each era's own
    sigma0; target scale from the target era's own sigma0 (scale-only)."""
    pooled_tune = dict(
        y=np.concatenate([b["y"] for b in pools_tune]),
        P=np.concatenate([b["P"] for b in pools_tune]),
        hdh=np.concatenate([b["hdh"] for b in pools_tune]), grid=grid)
    s0_pool = c4_sigma0(pooled_tune)
    gammas = c4_select_gammas(pooled_tune, s0_pool)
    g_hi, g_lo = gammas[(alpha, "hi")], gammas[(alpha, "lo")]
    sh, sl = [], []
    for b in pools_cal:
        s0_b = c4_sigma0_for(b, b["grid"])
        lo_c, hi_c = _cols(b["P"], alpha, b["grid"])
        sh.append((b["y"] - hi_c) / (s0_b * (1.0 + g_hi * b["hdh"])))
        sl.append((lo_c - b["y"]) / (s0_b * (1.0 + g_lo * b["hdh"])))
    q_hi = C.expansion_only(C.order_statistic_Q(np.concatenate(sh), alpha / 2.0))
    q_lo = C.expansion_only(C.order_statistic_Q(np.concatenate(sl), alpha / 2.0))
    s0_t = c4_sigma0(target_tune)
    lo_n, hi_n = _cols(P_new, alpha, grid)
    return (lo_n - q_lo * s0_t * (1.0 + g_lo * hdh_new),
            hi_n + q_hi * s0_t * (1.0 + g_hi * hdh_new))


def c4_sigma0_for(bundle, grid):
    med = bundle["P"][:, C.qidx(grid, 0.5)]
    return max(C.SIGMA0_FLOOR_MW,
               float(np.median(np.abs(bundle["y"] - med))))
