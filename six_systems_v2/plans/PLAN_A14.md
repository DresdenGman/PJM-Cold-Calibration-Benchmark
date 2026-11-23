# A14: operator-forecast intervals in all six systems

Written 2026-11-23 before any A14 interval was computed; local SHA-256 fingerprint, published with the
final repository upload. Written after all A9-A13 results, the v13/v14 revision analyses and three
external assessments (which suggested this extension) were known. The EIA-930 files, which contain the
"Demand Forecast (MW)" column for every balancing authority, were already on disk.

## Question
Does the event-window coverage gap of conformal intervals around the balancing authorities' own
day-ahead demand forecasts, found for PJM and MISO in A12, also hold in ERCOT, SPP, NYISO and ISO-NE?

## Design
A12 unchanged: base quantiles all equal to the EIA-930 day-ahead demand forecast, calibrators C1, C2a,
C2b, C3, C4, C6, C7 under the A9 design (prior-winter calibration set from 2015-07-01, pre-event hours
added), A11 events, populations, evaluation winters and GEFS temperatures. Rows with a missing, non-positive
or glitch-flagged forecast are excluded; shed hours (ERCOT, SPP, 14-20 Feb 2021) are excluded as in A11.

## Pre-specified criteria (new systems only)
- P1: C1 event cov90 at least 10 pp below C1 winter cov90 in at least half of the A11 events with a forecast.
- P2: the calibrator with the largest summed Winkler improvement over C1 on the other events of the same
  system meets (a), (c) and (d) together in at most a third of those events.

## Reported (descriptive)
- All events with an operator forecast (PJM, MISO and the four new systems): mean C1 event and winter cov90
  and the gap, with CR1 intervals, wild cluster bootstrap and sign-flip tests over cold-outbreak clusters;
  the same without ERCOT.
- Event-window point accuracy: mean absolute error of the operator forecast and of the L1 median, per event.
- Agreement between operator-based and L1-based C1 event coverage (Spearman).
