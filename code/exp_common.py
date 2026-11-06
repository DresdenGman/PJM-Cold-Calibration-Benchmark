"""Shared constants and operators — METHODS_FORMULAS v2.1 + Freeze Amendment A1.

Spec version: METHODS_FORMULAS v2.1 (formula-gate revision, 2026-11-05).
"""
import numpy as np

# ------------------------------------------------------------------ §0 grids
# 15 quantiles, explicitly enumerated in v2.1 §0.
QUANTILES = np.array([0.01, 0.025, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50,
                      0.60, 0.70, 0.80, 0.90, 0.95, 0.975, 0.99])
# Exception (§0): L1 2014 H-1H reproduction arm keeps the PHASE2A 7-quantile set.
QUANTILES_REPRO = np.array([0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99])

ALPHA_LEVELS = [0.20, 0.10, 0.05, 0.02]
COV_OF_ALPHA = {0.20: "cov80", 0.10: "cov90", 0.05: "cov95", 0.02: "cov98"}


def pair_for_alpha(alpha, grid):
    """Interval endpoint taus for central (1-alpha): exact if on the grid,
    else the outward bracketing pair (largest grid tau <= alpha/2,
    smallest grid tau >= 1-alpha/2). The bracketing case is the §0 rule
    for the 7-quantile reproduction arm."""
    lo_t, hi_t = alpha / 2.0, 1.0 - alpha / 2.0
    below = [t for t in grid if t <= lo_t + 1e-12]
    above = [t for t in grid if t >= hi_t - 1e-12]
    lo = max(below) if below else float(np.min(grid))
    hi = min(above) if above else float(np.max(grid))
    return float(lo), float(hi)


def qidx(grid, tau):
    return int(np.argmin(np.abs(np.asarray(grid) - tau)))


# ------------------------------------------------------------------ §0 operator
def order_statistic_Q(scores, beta):
    """Q_beta(S): k = ceil((n+1)(1-beta)); S_(k) if 1<=k<=n; +inf if
    k = n+1 or n = 0. NO interpolation, NO max-capping (v2.1 §0)."""
    s = np.sort(np.asarray(scores, dtype=float))
    s = s[np.isfinite(s)]
    n = len(s)
    if n == 0:
        return np.inf
    k = int(np.ceil((n + 1) * (1.0 - beta)))
    if k > n:
        return np.inf
    if k < 1:
        k = 1
    return float(s[k - 1])


def expansion_only(Q):
    """Q+ = max(0, Q); +inf preserved."""
    return max(0.0, Q)


# ------------------------------------------------------------------ §2 bins
TEMP_BIN_EDGES = np.array([-np.inf, -15.0, -10.0, -5.0, 0.0, np.inf])
MONDRIAN_SHRINK_M = 50          # §2 C2b shrinkage constant

# ------------------------------------------------------------------ §3 C4
C4_GAMMA_GRID = [0.0, 0.02, 0.05, 0.1, 0.2, 0.4]
C4_HOLDOUT_FRAC = 0.25          # D_tune inner holdout = last 25%
SIGMA0_FLOOR_MW = 1.0

# ------------------------------------------------------------------ §4 ACI
ACI_ETA = 0.002
ACI_WINDOW_H = 2160
ACI_ALPHA_CLIP = (0.001, 0.5)

# ------------------------------------------------------------------ §5 L3
L3_BIN_MIN_N = 200
L3_LAMBDA_GRID = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]

# ------------------------------------------------------------------ splits (§0)
CAL_TRAIN_DAYS = 92
TUNE_DAYS = 273

HDH_BASE_C = 18.3
SEED = 42

# C0x proportional-expansion baseline (FREEZE J2 frontier comparator;
# factor selected on D_cal, expansion around q_0.5 of the sorted base).
C0X_K_GRID = np.round(np.arange(1.0, 3.0001, 0.05), 2)

# ------------------------------------------------------------------ events (local, [start, end))
NAMED_EVENTS = {
    "2014": dict(name="event_2014_vortex", start="2014-01-06 00:00", end="2014-01-09 00:00"),
    "2018": dict(name="event_2018_snap", start="2017-12-28 00:00", end="2018-01-08 00:00"),
    "2022": dict(name="event_2022_elliott", start="2022-12-23 00:00", end="2022-12-27 00:00"),
}


def rearrange(P):
    """q-hat is DEFINED as the pointwise-sorted base predictions (v2.1 §0)."""
    return np.sort(P, axis=1)


def pinball(y, qhat, tau):
    u = y - qhat
    return np.where(u >= 0, tau * u, (tau - 1.0) * u)


def endpoint_pinball(y, lo, hi, alpha):
    """§7 calibrated-endpoint pinball P_alpha = rho_{a/2}(y-L) + rho_{1-a/2}(y-U)."""
    return pinball(y, lo, alpha / 2.0) + pinball(y, hi, 1.0 - alpha / 2.0)


def winkler(y, lo, hi, alpha):
    w = hi - lo
    return (w + np.where(y < lo, (2.0 / alpha) * (lo - y), 0.0)
              + np.where(y > hi, (2.0 / alpha) * (y - hi), 0.0))


def nest_bounds(bounds):
    """§7 outward nesting across levels: L*_a = min_{b>=a} L_b,
    U*_a = max_{b>=a} U_b. bounds: {alpha: (lo, hi)} -> nested copy."""
    out = {}
    run_lo, run_hi = None, None
    for alpha in sorted(bounds.keys(), reverse=True):  # 0.20 first (narrowest)
        lo, hi = bounds[alpha]
        run_lo = lo.copy() if run_lo is None else np.minimum(run_lo, lo)
        run_hi = hi.copy() if run_hi is None else np.maximum(run_hi, hi)
        out[alpha] = (run_lo.copy(), run_hi.copy())
    return out


def joint_block_indices(n, block=24, B=1000, seed=SEED):
    """§7: ONE set of circular 24h block indices, shared by all methods.
    Concatenate ceil(n/24) blocks, truncate to n."""
    rng = np.random.default_rng(seed)
    nblocks = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(B, nblocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1) % n
    return idx[:, :n]
