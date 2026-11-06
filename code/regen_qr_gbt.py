#!/usr/bin/env python3
"""
Regeneration of the 2014 QR-GBT quantile forecasts (the original
Task07B run).

Spec (recovered from the Task07A/Task07B modelling reports):
  - Data: pjm_era5_modeling_table_2010_2014.csv (43,824 rows)
  - Features (14): hour, day_of_week, month, is_weekend,
                   load_lag_1h, load_lag_24h, load_lag_168h,
                   rolling_mean_24h, rolling_mean_168h,
                   temperature_f, wind_chill_f, wind_speed_mph, hdh, cdh
  - First 168 rows dropped (lag/rolling warm-up) -> 43,656 rows
  - Train 2010-2013 (34,896), Test 2014 (8,760)
  - Model: sklearn HistGradientBoostingRegressor(loss='quantile'),
           max_iter=300, max_depth=6, random_state=42, other params default
  - Quantiles: 0.01, 0.05, 0.10, 0.50, 0.90, 0.95, 0.99
  - Post-hoc monotone rearrangement (row-wise sort) applied for headline metrics
Undocumented choices made here (recorded in data/regen/README.md):
  - rolling_mean_24h/168h = mean of the *previous* 24/168 hourly loads
    (rolling(k).mean().shift(1)); Task07A states rolling means use only
    past timestamps ("operationally available").
  - day_of_week: Monday=0 from EPT wall clock; hour/month from EPT wall clock.
"""
import json
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import sklearn

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJ, "data", "era2014",
                   "pjm_era5_modeling_table_2010_2014.csv")
OUT = os.path.join(PROJ, "data", "regen")

QUANTILES = [0.01, 0.05, 0.10, 0.50, 0.90, 0.95, 0.99]
QCOLS = [f"q{int(round(q*100)):02d}" for q in QUANTILES]

# ---------------------------------------------------------------- data
df = pd.read_csv(SRC)
df["ts_utc"] = pd.to_datetime(df["timestamp_utc"], format="%m/%d/%Y %I:%M:%S %p")
df["ts_ept"] = pd.to_datetime(df["timestamp_ept"], format="%m/%d/%Y %I:%M:%S %p")
df = df.sort_values("ts_utc").reset_index(drop=True)
diffs = df["ts_utc"].diff().dropna().unique()
assert len(diffs) == 1 and diffs[0] == pd.Timedelta(hours=1), f"non-hourly gaps: {diffs}"
print(f"loaded {len(df)} rows, strictly hourly in UTC")

load = df["actual_load_mw"]
feat = pd.DataFrame(index=df.index)
feat["hour"] = df["ts_ept"].dt.hour
feat["day_of_week"] = df["ts_ept"].dt.dayofweek
feat["month"] = df["ts_ept"].dt.month
feat["is_weekend"] = (feat["day_of_week"] >= 5).astype(int)
feat["load_lag_1h"] = load.shift(1)
feat["load_lag_24h"] = load.shift(24)
feat["load_lag_168h"] = load.shift(168)
feat["rolling_mean_24h"] = load.rolling(24).mean().shift(1)
feat["rolling_mean_168h"] = load.rolling(168).mean().shift(1)
for c in ["temperature_f", "wind_chill_f", "wind_speed_mph", "hdh", "cdh"]:
    feat[c] = df[c]
FEATURES = list(feat.columns)
assert len(FEATURES) == 14, FEATURES

feat["actual_load_mw"] = load.values
feat["ts_utc"] = df["ts_utc"].values
feat["ts_ept"] = df["ts_ept"].values
feat["source_year"] = df["source_year"].values
feat = feat.dropna().reset_index(drop=True)
print(f"after warm-up drop: {len(feat)} rows (expect 43,656)")

train = feat[feat["source_year"] <= 2013]
test = feat[feat["source_year"] == 2014].reset_index(drop=True)
print(f"train {len(train)} (expect 34,896) | test {len(test)} (expect 8,760)")
assert len(train) == 34896 and len(test) == 8760

# ---------------------------------------------------------------- models
preds_raw = {}
for q, qc in zip(QUANTILES, QCOLS):
    m = HistGradientBoostingRegressor(
        loss="quantile", quantile=q, max_iter=300, max_depth=6, random_state=42)
    m.fit(train[FEATURES], train["actual_load_mw"])
    preds_raw[qc] = m.predict(test[FEATURES])
    print(f"trained q={q}: n_iter={m.n_iter_}")

P = pd.DataFrame(preds_raw)
cross_rows = (np.diff(P.values, axis=1) < 0).any(axis=1)
crossing_rate = float(cross_rows.mean())
print(f"raw crossing rate: {crossing_rate:.4f} ({int(cross_rows.sum())}/{len(P)} rows)")

P_mono = pd.DataFrame(np.sort(P.values, axis=1), columns=QCOLS)

out = pd.DataFrame({
    "timestamp_utc": test["ts_utc"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    "timestamp_ept": test["ts_ept"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    "actual_load_mw": test["actual_load_mw"].values,
})
for qc in QCOLS:
    out[qc + "_raw"] = P[qc].values
    out[qc + "_mono"] = P_mono[qc].values
out.to_csv(OUT + "/quantile_predictions_2014_regen.csv", index=False)
print("saved quantile_predictions_2014_regen.csv")

# ---------------------------------------------------------------- metrics
def pinball(y, yhat, q):
    d = y - yhat
    return np.where(d >= 0, q * d, (q - 1) * d)

def winkler90(y, lo, hi, alpha=0.10):
    w = hi - lo
    return (w + np.where(y < lo, (2 / alpha) * (lo - y), 0.0)
              + np.where(y > hi, (2 / alpha) * (y - hi), 0.0))

def window_metrics(d, Pq, label):
    y = d["actual_load_mw"].values
    pb = np.mean([pinball(y, Pq[qc].values, q).mean()
                  for q, qc in zip(QUANTILES, QCOLS)])
    pb_by_q = {qc: float(pinball(y, Pq[qc].values, q).mean())
               for q, qc in zip(QUANTILES, QCOLS)}
    cov90 = float(((y >= Pq["q05"].values) & (y <= Pq["q95"].values)).mean() * 100)
    cov98 = float(((y >= Pq["q01"].values) & (y <= Pq["q99"].values)).mean() * 100)
    return {
        "window": label, "n": int(len(d)),
        "q50_mae": float(np.abs(y - Pq["q50"].values).mean()),
        "q50_rmse": float(np.sqrt(((y - Pq["q50"].values) ** 2).mean())),
        "q50_bias": float((y - Pq["q50"].values).mean() * -1),  # pred - actual
        "mean_pinball": float(pb), "pinball_by_quantile": pb_by_q,
        "pi90_coverage_pct": cov90, "pi98_coverage_pct": cov98,
        "winkler90": float(winkler90(y, Pq["q05"].values, Pq["q95"].values).mean()),
    }

ept = test["ts_ept"]
masks = {
    "Full-year_2014": np.ones(len(test), dtype=bool),
    "Jan_6-8_2014": ((ept >= "2014-01-06") & (ept < "2014-01-09")).values,
    "Jun_16-18_2014": ((ept >= "2014-06-16") & (ept < "2014-06-19")).values,
}
top1_thr = test["actual_load_mw"].quantile(0.99)
masks["Top_1pct_load"] = (test["actual_load_mw"] >= top1_thr).values

results = {"spec": {
    "sklearn_version": sklearn.__version__,
    "model": "HistGradientBoostingRegressor(loss='quantile', max_iter=300, max_depth=6, random_state=42, defaults otherwise)",
    "features": FEATURES, "quantiles": QUANTILES,
    "crossing_rate_raw": crossing_rate,
    "top1_threshold_mw": float(top1_thr),
}, "windows_mono": [], "windows_raw": []}

for label, mask in masks.items():
    d = test[mask].reset_index(drop=True)
    results["windows_mono"].append(window_metrics(d, P_mono[mask].reset_index(drop=True), label))
    results["windows_raw"].append(window_metrics(d, P[mask].reset_index(drop=True), label))
    wm = results["windows_mono"][-1]
    print(f"{label}: n={wm['n']} q50MAE={wm['q50_mae']:.1f} pinball={wm['mean_pinball']:.1f} "
          f"cov90={wm['pi90_coverage_pct']:.1f}% cov98={wm['pi98_coverage_pct']:.1f}% wink90={wm['winkler90']:.0f}")

# calibration by quantile (full-year + vortex), mono assignment
cal = {}
for label, mask in [("full", masks["Full-year_2014"]), ("vortex", masks["Jan_6-8_2014"])]:
    y = test["actual_load_mw"].values[mask]
    cal[label] = {qc: float((y <= P_mono.values[mask][:, i]).mean() * 100)
                  for i, qc in enumerate(QCOLS)}
results["calibration_empirical_coverage_pct"] = cal

# peak hour: Jan 7 18:00 EPT
pk = test[(ept.dt.month == 1) & (ept.dt.day == 7) & (ept.dt.hour == 18)]
assert len(pk) == 1
i = pk.index[0]
results["peak_hour"] = {
    "timestamp_ept": "2014-01-07 18:00", "actual_mw": float(test.loc[i, "actual_load_mw"]),
    "raw": {qc: float(P.loc[i, qc]) for qc in QCOLS},
    "mono": {qc: float(P_mono.loc[i, qc]) for qc in QCOLS},
}
print("peak hour:", json.dumps(results["peak_hour"], indent=1))

with open(OUT + "/metrics_regen.json", "w") as f:
    json.dump(results, f, indent=2)
print("saved metrics_regen.json")
