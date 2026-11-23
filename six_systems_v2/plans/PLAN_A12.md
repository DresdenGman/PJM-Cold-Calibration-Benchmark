# A12: intervals around the operators' own day-ahead forecasts

Written 2026-11-23 before any A12 interval was computed. Kept locally with a SHA-256
fingerprint and published with the final repository upload (no external timestamp; the user
asked for a single final upload). Written after A9 and A10 results were known.

## Question
Are the event-window failures specific to the study's forecasters? A12 replaces the model's
quantiles by the balancing authority's own day-ahead demand forecast from EIA-930
("Demand Forecast (MW)") and applies the same calibration layer.

## Design
- Systems and events: PJM and MISO, the 12 named events from 2015 on (the 2014 era has no
  EIA-930 forecast). A9 populations and evaluation winters.
- Point forecast: the EIA-930 demand forecast for the hour. Its issuance time is not documented
  by EIA; this is stated as a limitation.
- Calibration set: every prior winter in the record from 2015-07-01 (the operator forecast is
  out of sample by construction, so no cross-fitting), plus pre-event evaluation hours, as in A9.
- Intervals: all base quantiles set to the operator forecast, so the CQR score is the absolute
  error; calibrators C1, C2a, C2b, C3 (item window), C4, C6, C7 as in A9 (C0 and C0x are
  undefined for a point forecast). Temperatures are the GEFS forecast footprint means of A9.
- Rows with a missing or flagged-glitch operator forecast are excluded from calibration and
  scoring; counts are reported.

## Pre-specified criteria
- O1: C1 event cov90 is at least 10 pp below C1 full-period cov90 in at least half of the
  12 events.
- O2: the calibrator with the largest summed Winkler improvement over C1 on the other events
  of the same system meets (a) cov90 in [0.85, 0.95], (c) full-period width at most 1.35 times
  C1's, and (d) placebo cov90 at most 0.95 together in at most a third of the events.
- O3 (descriptive): event-level agreement between the A9 model-based and the A12
  operator-based C1 event coverage (Spearman correlation and paired differences).
