# data/regen — Regenerated 2014 QR-GBT forecasts

Regeneration of the 2014 QR-GBT quantile forecasts from the verified
modelling table (see `DATA_SOURCES.md` §3), under the recovered original
specification. This regeneration stands in for the original run's
prediction file, which does not survive.

## Files

| File | Content |
|---|---|
| `quantile_predictions_2014_regen.csv` | 8,760 rows (test year 2014): `timestamp_utc`, `timestamp_ept`, `actual_load_mw`, and for each of q01/q05/q10/q50/q90/q95/q99 the **raw** model output (`*_raw`) and the **monotone-rearranged** value (`*_mono`, row-wise sort of the 7 quantiles) |
| `metrics_regen.json` | Full metric set: per-window metrics for raw and mono assignments, per-quantile empirical calibration, peak-hour quantiles, crossing rate, exact spec |
| `../../code/regen_qr_gbt.py` | The exact script that produced the two files above |

## Exact spec used

Recovered from the original Task07A baseline modelling report and the
Task07B quantile forecasting report:

- **Data**: `pjm_era5_modeling_table_2010_2014.csv` (43,824 rows), sorted
  by UTC timestamp (verified strictly hourly in UTC), features built on
  the full series, first 168 warm-up rows dropped → 43,656 rows.
- **Split**: train = source years 2010–2013 (34,896 rows); test = 2014
  (8,760 rows).
- **Features (14)**: `hour`, `day_of_week`, `month`, `is_weekend` (EPT
  wall clock, Monday=0); `load_lag_1h`, `load_lag_24h`, `load_lag_168h`;
  `rolling_mean_24h`, `rolling_mean_168h`; `temperature_f`,
  `wind_chill_f`, `wind_speed_mph`, `hdh`, `cdh` (ERA5-derived columns
  as shipped in the table; retrospective reanalysis).
- **Model**: `sklearn.ensemble.HistGradientBoostingRegressor(loss="quantile",
  quantile=q, max_iter=300, max_depth=6, random_state=42)`, all other
  parameters at sklearn defaults; one model per quantile. All 7 fits ran
  the full 300 iterations (early stopping did not trigger).
- **Quantiles**: 0.01, 0.05, 0.10, 0.50, 0.90, 0.95, 0.99.
- **Intervals**: 90% PI = [q05, q95]; 98% PI = [q01, q99].
- **Headline metrics** are computed on the **monotone-rearranged**
  quantiles, matching the original run's stated convention.
- **Environment**: Python 3.11+, scikit-learn 1.5.0, pandas 2.1.4,
  numpy 1.26.2.

Headline check values (monotone-rearranged): full-year 90% interval
coverage 86.3%; polar-vortex window (Jan 6–8, 2014) 68.1%; full-year 98%
coverage 96.9%; vortex-window 98% coverage 84.7%; raw quantile crossing
rate 65.2% (5,708 / 8,760 rows).

## Choices NOT documented in the surviving sources (decisions, recorded)

1. **Rolling-mean alignment**: `rolling_mean_24h/168h` = mean of the
   *previous* 24/168 hourly loads (`rolling(k).mean().shift(1)`), i.e.
   only past timestamps, per the Task07A "operationally available"
   statement. The exact window edges are not documented; this is the
   most likely source of the residual deltas vs. the original run.
2. **Top-1% window**: hours with 2014 actual load ≥ the 99th percentile
   of 2014 actuals → n = 88. The original file has n = 87 (threshold
   unstated).
3. Pinball "mean" = average over the 7 fitted quantiles, matching the
   original `quantile_metrics.csv` construction (verified numerically
   consistent).
