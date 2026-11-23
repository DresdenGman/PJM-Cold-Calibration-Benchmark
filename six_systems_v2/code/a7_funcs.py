"""C6 and C7 functions copied from remedies_a7/job_a7.py (unchanged)."""
import numpy as np
from scipy.optimize import minimize
import exp_common as C
import calibrators as CAL
H_GRID = [1.0, 2.0, 4.0, 8.0]
FALLBACKS = {"C7": 0}

# ------------------------------------------------------------------ C6
def weighted_cutoffs(s_cal, T_cal, T_new, h, alpha):
    order = np.argsort(s_cal); s = s_cal[order]; Tc = T_cal[order]
    out = np.empty(len(T_new))
    for k0 in range(0, len(T_new), 512):
        Tn = T_new[k0:k0 + 512]
        w = np.exp(-((Tc[None, :] - Tn[:, None]) ** 2) / (2.0 * h * h))
        tot = w.sum(axis=1) + 1.0                     # test point's own weight (at +inf)
        cdf = np.cumsum(w, axis=1) / tot[:, None]
        idx = (cdf >= 1.0 - alpha).argmax(axis=1)
        ok = cdf[np.arange(len(Tn)), idx] >= 1.0 - alpha
        out[k0:k0 + 512] = np.where(ok, s[idx], np.inf)
    return np.maximum(out, 0.0)                      # expansion-only

def c6_select_h(tune, alpha):
    y, P, T = tune["y"], tune["P"], tune["temp"]
    n = len(y); cut = int(np.floor(n * (1.0 - C.C4_HOLDOUT_FRAC)))
    s = CAL.cqr_scores(y, P, alpha, tune["grid"])
    lo, hi = CAL._cols(P, alpha, tune["grid"])
    best = None
    for h in H_GRID:
        q = weighted_cutoffs(s[:cut], T[:cut], T[cut:], h, alpha)
        cov = float(np.mean((y[cut:] >= lo[cut:] - q) & (y[cut:] <= hi[cut:] + q)))
        width = float(np.mean(np.where(np.isfinite(q), hi[cut:] - lo[cut:] + 2 * q, 1e12)))
        key = (abs(cov - (1 - alpha)), width, -h)
        if best is None or key < best[0]:
            best = (key, h)
    return best[1]

def bounds_C6(cal, h, P_new, T_new, alpha):
    s = CAL.cqr_scores(cal["y"], cal["P"], alpha, cal["grid"])
    q = weighted_cutoffs(s, cal["temp"], T_new, h, alpha)
    lo, hi = CAL._cols(P_new, alpha, cal["grid"])
    return lo - q, hi + q

# ------------------------------------------------------------------ C7
def gpd_fit(e, x):
    def nll(th):
        a, b, xi = th
        sig = np.exp(a + b * x)
        if abs(xi) < 1e-6:
            return float(np.sum(np.log(sig) + e / sig))
        z = 1.0 + xi * e / sig
        if np.any(z <= 0):
            return 1e18
        return float(np.sum(np.log(sig) + (1.0 + 1.0 / xi) * np.log(z)))
    x0 = np.array([np.log(max(np.mean(e), 1.0)), 0.0, 0.1])
    r = minimize(nll, x0, method="Nelder-Mead", options=dict(maxiter=4000, xatol=1e-6, fatol=1e-6))
    return r.x if (r.success and np.isfinite(r.fun) and r.fun < 1e17) else None

def side_cut(d, x_cal, x_new, beta):
    u = float(np.quantile(d, 0.8)); exc = d > u
    pu = float(np.mean(exc)); e = d[exc] - u
    th = gpd_fit(e, x_cal[exc]) if exc.sum() >= 20 else None
    if th is None:
        return None
    a, b, xi = th; sig = np.exp(a + b * x_new)
    if abs(xi) < 1e-6:
        q = u + sig * np.log(pu / beta)
    else:
        q = u + sig / xi * ((pu / beta) ** xi - 1.0)
    return np.maximum(q, 0.0)

def bounds_C7(cal, P_new, hdh_new, alpha):
    lo_c, hi_c = CAL._cols(cal["P"], alpha, cal["grid"])
    qh = side_cut(cal["y"] - hi_c, cal["hdh"], hdh_new, alpha / 2.0)
    ql = side_cut(lo_c - cal["y"], cal["hdh"], hdh_new, alpha / 2.0)
    lo, hi = CAL._cols(P_new, alpha, cal["grid"])
    if qh is None or ql is None:
        FALLBACKS["C7"] += 1
        return CAL.bounds_C1(cal, P_new, alpha)
    return lo - ql, hi + qh

