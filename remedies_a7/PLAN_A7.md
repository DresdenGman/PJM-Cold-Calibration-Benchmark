# A7: two further remedy families (weighted conformal, conditional extreme-value tails)

Written 2026-11-22 and pushed before any A7 interval was computed.

## Calibrators
- C6, temperature-weighted conformal (covariate-shift weighting in the spirit of Tibshirani
  et al., 2019): two-sided CQR scores on D_cal are weighted by
  w_i = exp(-(T_i - T_t)^2 / (2 h^2)), where T is footprint temperature; the cutoff is the
  weighted (1 - alpha) quantile with the test point's own weight placed at +infinity, so the
  cutoff is infinite when the weighted support is too thin. h is chosen from {1, 2, 4, 8} C on
  the D_tune inner hold-out by C4's rule (coverage closest to nominal, then the narrower interval,
  then the larger h).
- C7, conditional generalised Pareto tails (in the spirit of Browell and Fasiolo, 2021):
  separately for each side, the side score s (exceedance of the base interval endpoint) on D_cal
  above its empirical 0.8 quantile u is modelled as generalised Pareto with constant shape xi
  and log-scale linear in heating degree hours, fitted by maximum likelihood; the cutoff
  solves P(s > q | x) = alpha / 2 using the empirical exceedance rate of u. Expansion-only,
  as for the other calibrators. If the fit fails to converge, C7 falls back to C1 for that
  calibration set; fallbacks are counted.

## Scope
All modelled events (6 original + up to 7 from A6), H-DA arm, L1–L3, chronological
evaluation, reanalysis weather, archived base predictions.

## Pre-specified criteria (L1)
For each of C6 and C7: the remedy is supported if repair conditions (a) and (c) hold together
in at least half of the events and (d) holds in all of them. Also reported: the number of
events in which each beats C4 on event cov90.
