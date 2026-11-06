"""Base learners L1 / L2 / L3 (FREEZE §4, METHODS v2.1).

All learners are fit ONLY on D_fit rows (v2.1 §0 three-way split).

L1: sklearn HistGradientBoostingRegressor, quantile loss, max_iter=300,
    max_depth=6, random_state=42 (PHASE2A spec). Quantile grid: 15 values
    (v2.1 §0); the 2014 H-1H reproduction arm uses the native 7.
L2: LightGBM linear_tree=True, 15 quantiles (params logged by caller).
L3: location-scale model per v2.1 §5:
    mu: natural cubic spline in T (knots at D_fit T quantiles
        {5,25,50,75,95}% + observed extremes; linear beyond the boundary
        by construction) + thermal memory M + HDH + intercept +
        167 reference-coded hour-of-week dummies (ref = Monday 00) +
        linear year trend; penalized LS with a second-difference penalty
        on the spline coefficients, lambda by the §5 GCV formula.
    sigma (de-circularized): z_i = log(max(|r_i|, 1 MW)/1 MW) regressed
        by OLS on (1, HDH, (-T-10)+); sigma_hat = 1 MW * exp(a^T h).
    eps: D_fit standardized residuals; per-temperature-bin order
        statistics F_b^{-1}(tau) = eps_(ceil(n_b * tau)); bins merged
        deterministically (coldest under-full group into its warmer
        neighbour; warmest under-full into its colder neighbour) until
        every group has >= 200 points or one group remains.
    L3 uses no load lags -> identical under both horizon masks.
"""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
import lightgbm as lgb

import exp_common as C

# Trimmed from an initial (250 rounds / 31 leaves) default set after timing
# benchmarks on this VM (see RESULTS_RUN1 run log): linear_tree LightGBM at
# the larger setting cost ~9x the CPU for the same matrix slot; the frozen
# spec fixes only linear_tree=True + features/quantiles, not these values.
L2_PARAMS = dict(objective="quantile", linear_tree=True, n_estimators=120,
                 learning_rate=0.1, num_leaves=15, min_data_in_leaf=60,
                 verbosity=-1, seed=C.SEED, n_jobs=4)


def fit_predict_L1(Xtr, ytr, Xall, grid):
    P = np.full((len(Xall), len(grid)), np.nan)
    ok_tr = np.isfinite(Xtr).all(axis=1) & np.isfinite(ytr)
    ok_all = np.isfinite(Xall).all(axis=1)
    for j, tau in enumerate(grid):
        m = HistGradientBoostingRegressor(loss="quantile", quantile=float(tau),
                                          max_iter=300, max_depth=6,
                                          random_state=C.SEED)
        m.fit(Xtr[ok_tr], ytr[ok_tr])
        P[ok_all, j] = m.predict(Xall[ok_all])
    return P


def fit_predict_L2(Xtr, ytr, Xall, grid):
    P = np.full((len(Xall), len(grid)), np.nan)
    ok_tr = np.isfinite(Xtr).all(axis=1) & np.isfinite(ytr)
    ok_all = np.isfinite(Xall).all(axis=1)
    for j, tau in enumerate(grid):
        m = lgb.LGBMRegressor(alpha=float(tau), **L2_PARAMS)
        m.fit(Xtr[ok_tr], ytr[ok_tr])
        P[ok_all, j] = m.predict(Xall[ok_all])
    return P


# --------------------------------------------------------------------- L3
def _natural_spline_basis(T, knots):
    """Hastie natural cubic spline basis: [T, N_1..N_{K-2}],
    d_k(T) = ((T-xi_k)_+^3 - (T-xi_K)_+^3) / (xi_K - xi_k),
    N_k = d_k - d_{K-1}. Linear outside the boundary knots."""
    T = np.asarray(T, dtype=float)
    K = len(knots)
    xiK = knots[-1]

    def d(k, T):
        return (np.clip(T - knots[k], 0, None) ** 3
                - np.clip(T - xiK, 0, None) ** 3) / (xiK - knots[k])

    cols = [T]
    for k in range(K - 2):
        cols.append(d(k, T) - d(K - 2, T))
    return np.column_stack(cols)


def _merge_bins_v21(counts, min_n):
    """§5 deterministic merging. Returns groups as [lo_bin, hi_bin] lists."""
    groups = [[i, i] for i in range(len(counts))]
    cnt = list(counts)
    while len(groups) > 1:
        small = [k for k in range(len(groups)) if cnt[k] < min_n]
        if not small:
            break
        k = small[0]                      # coldest under-full group
        if k == len(groups) - 1:          # warmest group: merge colder-ward
            j = k - 1
        else:                             # merge into warmer neighbour
            j = k + 1
        a, b = min(k, j), max(k, j)
        groups[a][1] = groups[b][1]
        cnt[a] += cnt[b]
        del groups[b], cnt[b]
    return groups


class L3Model:
    def _design(self, df):
        S = _natural_spline_basis(df["t2m_c"].values, self.knots_)
        hour = df["ts_local"].dt.hour.values
        dow = df["ts_local"].dt.dayofweek.values
        how = dow * 24 + hour                       # 0 = Monday 00 (reference)
        D = np.zeros((len(df), 167))
        cols = how - 1
        rows = np.where(cols >= 0)[0]
        D[rows, cols[rows]] = 1.0
        trend = ((df["ts_utc"] - self.t0_).dt.total_seconds()
                 / (365.25 * 86400.0)).values
        X = np.column_stack([np.ones(len(df)), S, df["mem_c"].values,
                             df["hdh_c"].values, trend, D])
        return X

    def fit(self, df_fit):
        y = df_fit["load"].values
        T = df_fit["t2m_c"].values
        qs = np.quantile(T[np.isfinite(T)], [0.05, 0.25, 0.50, 0.75, 0.95])
        self.knots_ = np.unique(np.concatenate(
            [[np.nanmin(T)], qs, [np.nanmax(T)]]))
        self.t0_ = df_fit["ts_utc"].iloc[0]
        X = self._design(df_fit)
        ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
        X, y = X[ok], y[ok]
        T_ok = T[ok]
        n_spline = X.shape[1] - 1 - 3 - 167        # spline block width
        # second-difference penalty on spline coefficients only
        D2 = np.diff(np.eye(n_spline), n=2, axis=0)
        P = np.zeros((D2.shape[0], X.shape[1]))
        P[:, 1:1 + n_spline] = D2
        XtX = X.T @ X
        Xty = X.T @ y
        best = None
        for lam in C.L3_LAMBDA_GRID:
            A = XtX + lam * (P.T @ P) + 1e-8 * np.eye(X.shape[1])
            Ainv = np.linalg.pinv(A)
            beta = Ainv @ Xty
            trH = float(np.trace(X @ Ainv @ X.T))
            rss = float(np.sum((y - X @ beta) ** 2))
            gcv = rss / (len(y) * (1.0 - trH / len(y)) ** 2)
            if best is None or gcv < best[0]:
                best = (gcv, lam, beta)
        self.gcv_, self.lambda_, self.beta_ = best
        resid = y - X @ self.beta_
        # de-circularized scale regression (§5)
        Z = np.column_stack([np.ones(len(y)), df_fit["hdh_c"].values[ok],
                             np.clip(-T_ok - 10.0, 0.0, None)])
        z = np.log(np.maximum(np.abs(resid), 1.0))
        self.scale_beta_, *_ = np.linalg.lstsq(Z, z, rcond=None)
        sigma = np.exp(Z @ self.scale_beta_)
        eps = resid / sigma
        bidx = np.clip(np.searchsorted(C.TEMP_BIN_EDGES, T_ok,
                                       side="right") - 1, 0, 4)
        counts = [int((bidx == k).sum()) for k in range(5)]
        self.bin_groups_ = _merge_bins_v21(counts, C.L3_BIN_MIN_N)
        self.bin_of_ = {}
        for g, (a, b) in enumerate(self.bin_groups_):
            for k in range(a, b + 1):
                self.bin_of_[k] = g
        self.eps_sorted_ = {}
        for g, (a, b) in enumerate(self.bin_groups_):
            pool = np.sort(eps[(bidx >= a) & (bidx <= b)])
            self.eps_sorted_[g] = pool
        return self

    def predict_quantiles(self, df, grid):
        X = self._design(df)
        mu = X @ self.beta_
        Z = np.column_stack([np.ones(len(df)), df["hdh_c"].values,
                             np.clip(-df["t2m_c"].values - 10.0, 0.0, None)])
        sigma = np.exp(Z @ self.scale_beta_)
        bidx = np.clip(np.searchsorted(C.TEMP_BIN_EDGES, df["t2m_c"].values,
                                       side="right") - 1, 0, 4)
        P = np.full((len(df), len(grid)), np.nan)
        for g, pool in self.eps_sorted_.items():
            rows = np.array([self.bin_of_[int(b)] == g for b in bidx])
            if not rows.any():
                continue
            k = np.clip(np.ceil(len(pool) * np.asarray(grid)).astype(int),
                        1, len(pool))
            eq = pool[k - 1]
            P[rows] = mu[rows][:, None] + sigma[rows][:, None] * eq[None, :]
        return P
