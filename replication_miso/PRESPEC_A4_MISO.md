# Amendment A4 — second-system replication (MISO): pre-specification

Written before any MISO load, weather or model result was downloaded or inspected.
Purpose: apply the frozen PJM protocol (METHODS_FORMULAS v2.1 + Amendment A1) unchanged
to a second balancing authority, as announced in the PJM paper's limitations.
This file is a working record kept by the author's assistant; it has no external
timestamp (see the SHA-256 and local time recorded at the end).

## System
- MISO (EIA-930 balancing authority code "MISO").
- Chosen over ERCOT because Winter Storm Uri (Feb 2021) involved ~20 GW of firm load
  shed in ERCOT, so EIA-930 "demand" there is served load, not demand.

## Eras, spans and named events (local = America/New_York, as in the PJM code)
| era  | training span           | evaluation span          | named event window [start, end) | hours |
|------|-------------------------|--------------------------|---------------------------------|-------|
| 2018 | 2016-01-01 … 2017-11-30 | 2017-12-01 … 2018-02-28  | 2017-12-28 00:00 → 2018-01-08 00:00 | 264 |
| 2019 | 2017-01-01 … 2018-11-30 | 2018-12-01 … 2019-02-28  | 2019-01-29 00:00 → 2019-02-01 00:00 | 72  |
| 2022 | 2020-01-01 … 2021-12-31 | 2022-12-01 … 2023-02-28  | 2022-12-23 00:00 → 2022-12-27 00:00 | 96  |
- 2018 and 2022 windows are identical to the PJM benchmark (same continental cold events).
- 2019 is the January 2019 polar vortex, the most widely reported MISO cold-weather emergency
  of the period; its 72-hour window is fixed here before looking at MISO data. Documentation
  of the MISO emergency declarations must be cited before submission.
- Same split rule as PJM: D_cal = last 92 training days, D_tune = 273 days before, D_fit = rest.

## Data
- Load: EIA-930 six-month BALANCE files, rows with Balancing Authority == "MISO",
  column "Demand (MW)", same window/convention code as build_data_spans.py.
  Glitch rule (replaces PJM's 170,000 MW rule, scaled to MISO): |value| > 150,000 MW -> NaN,
  logged, never dropped (MISO's all-time peak is about 127 GW). No other cleaning.
- Operator anchor: EIA-930 "Demand Forecast (MW)" for MISO, error at each event's peak hour
  (forecast − actual). Vintage/issuance time of this field is not documented by EIA-930
  and will be stated as such.
- Weather: ERA5 via the Open-Meteo archive, same variables and code as PJM, equal-weight mean
  of a 15-point grid over MISO's northern, heating-sensitive footprint:
  latitudes {38.5, 41.5, 44.5} °N × longitudes {−95.5, −93.0, −90.5, −88.0, −85.5} °E.
  MISO South (Arkansas, Louisiana, Mississippi, East Texas) is not covered; stated as a limitation.

## Models, calibrators, populations
- L1, L2, L3, C0–C4, the order-statistic operator, the issuance horizons (H-DA primary,
  H-1H oracle), cold-spell rule (below the era's 2nd training percentile for ≥24 h, merge gaps
  ≤12 h), placebo rule and all metrics: identical code to the PJM run.
- Cold spells and placebo windows are generated and saved before any model is fitted.
- Known environment differences: scikit-learn 1.8.0 (PJM reference 1.5.0), LightGBM version as
  installed; the PJM 2022 cell was re-run in this environment and reproduced bit-for-bit.

## Judgements (same as PJM) and replication criteria fixed now
- J1, J2 (leave-one-event-out selection over the other two MISO events; (a),(b) on ≥2 of 3
  events, (c),(d) on all), J3 (transfer gap): identical definitions and thresholds.
- R1 collapse replicates: on H-DA × L1, event cov90 is at least 10 pp below the same era's
  full-period cov90 in at least 2 of the 3 MISO events.
- R2 repair fails: 0 of 6 learner × horizon cells pass J2 under leave-one-event-out selection.
- R3 transfer illusion replicates: on H-DA × L1 the mean (LOEO − chronological) cov90 gap is
  ≥ +5 pp for C2a or C2b, while for C1 it lies within ±5 pp.
- Every result is reported whether or not it replicates. Any change made after data are seen
  is listed in a deviations section of the results file.

## Not run in A4
- The prior-winter calibration sensitivity (A2) and the forecast-temperature arm (A3).
