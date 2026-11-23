# A10: rapid-onset calibration and a holiday-aware forecaster

Written 2026-11-22 and pushed before any A10 interval was computed or any A10 model fitted.
A10 is written after the A9 results were known. A9 showed that, under the redesigned
benchmark, the remaining unrepaired events include both Winter Storm Elliott windows, which
combine a rapid temperature drop with the Christmas holiday, and that their errors are partly
negative (MISO load below the forecast). A10 tests two remedies aimed at those features. Its
results are exploratory: the remedies were chosen after seeing which events fail.

## Design
A9 design throughout (long histories, leave-one-winter-out cross-fitted calibration on prior
winters, GEFS day-ahead weather, day-ahead arm, the same 13 events and populations).

## Remedies
- C8a / C8b, rapid-onset Mondrian: as C2a / C2b, but the strata are the forecast 24-hour
  temperature change dT_t = T_t - T_(t-24) (footprint forecast temperature from the frame),
  with bins (-inf, -8], (-8, -4], (-4, 0], (0, inf) degrees C. C8a keeps the bin cutoff no smaller than the
  global one; C8b uses the C2b shrinkage (m = 50).
- L1h, holiday-aware forecaster: L1 with two added features, a US federal holiday indicator
  (pandas USFederalHolidayCalendar, observed dates) and a 24 December – 1 January season
  indicator. Refitted with the A9 design; all A9 calibrators plus C8a/C8b applied.

## Pre-specified criteria
- H1: in the seven A9 events whose C1 event coverage is at least 10 pp below its full-period
  coverage (PJM 2014, 2018, 2022; MISO 2018, 2022, 2025, 2026), C8a or C8b with L1 meets repair
  conditions (a), (c) and (d) in at least three.
- H2: L1h raises C1 event cov90 by at least 10 pp at both Elliott events (PJM and MISO 2022)
  and reduces the absolute event bias ratio at both, while C1 full-period cov90 changes by at
  most 2 pp in every era.
All results are reported whatever the outcome.
