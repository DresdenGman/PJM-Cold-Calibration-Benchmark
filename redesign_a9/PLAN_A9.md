# A9: redesigned benchmark (long histories, winter calibration, forecast weather primary)

Written 2026-11-22 and pushed to the public repository before any A9 data were downloaded
or any A9 model was fitted. Unlike A5–A8, A9 is written after the analyst has seen all
results of the original design and of A5–A8. It responds to an independent mock review
that raised three design objections: (1) the base forecasters are miscalibrated over the
whole winter, not only in events, so a collapse measured against the uncalibrated full-period
coverage is mis-framed; (2) training histories of about two years and a calibration window
in autumn (the last 92 training days) make winter undercoverage close to inevitable;
(3) same-hour reanalysis weather is an oracle and should not be the primary input. A9 fixes
these choices in advance; its criteria decide how the paper reports the result.

## Events and populations
The 13 named events, cold spells and placebo windows of the original design and of A6 are
unchanged. The evaluation period of every era is December–February, including the 2014 era
(December 2013 – February 2014; the original design used calendar 2014).

## Data
- Load: PJM metered load (2014 era, 2010-01-01 to 2014-02-28, from the original modelling
  frame); EIA-930 demand for PJM and MISO from its start (2015-07-01) for all other eras.
- Weather, primary: the day-ahead GEFS control forecast as in A8 (00 UTC run of local date
  d-1, forecast hours 24–54, 2 m temperature and 10 m wind; reforecast to 2019-12-31,
  operational v11 to 2020-09-22, operational v12 after). Missing spans are fetched with the
  A8 fetcher.
- Weather, oracle sensitivity: same-hour ERA5 footprint means (Open-Meteo), as before.

## Training history and splits
- Training history: every hour from the start of the record to 30 November before the
  evaluation winter (2014 era: 2010-01-01 to 2013-11-30). Lengths range from about 2.4 years
  (2018 era) to about 10.4 years (2026 era), and 3.9 years for the 2014 era.
- Calibration set D_cal: every prior winter (December–February, partial winters at the start
  of the record included) inside the training history, with out-of-sample predictions from
  leave-one-winter-out cross-fitting: for each prior winter, the learner is refitted on all
  other training hours and predicts that winter. Pre-event evaluation hours are added to
  D_cal for each event, as before, using the final model.
- Tuning set D_tune (C4 gamma, C6 bandwidth): the same cross-fitted prior-winter rows; the
  inner hold-out is the last 25% of them in time order, as in C4's rule.
- Final model: refitted on the whole training history; it predicts the evaluation winter.
- Arm: day-ahead (H-DA) only; learners L1, L2, L3 with unchanged hyper-parameters.

## Calibrators
C0, C0x, C1, C2a, C2b, C3, C4, C6, C7 as defined before. C5 is not repeated: its spread would
mix 5-member reforecast and 21- or 31-member operational ensembles across the prior winters
of one calibration set. C3 uses a window of the most recent 2,160 scored items instead of
2,160 clock hours, because calibration items now lie in earlier winters.

## Repair test, relative to a marginally recalibrated baseline
For each event, the calibrator selected by the largest summed Winkler improvement over C0 on
all other events of the same system is assessed on four conditions: (a) event cov90 in
[0.85, 0.95]; (b) frontier win against C0x (unchanged rule); (c) full-period mean width at
most 1.35 times that of C1 (the original design used C0); (d) placebo cov90 at most 0.95.

## Diagnostics (all reported)
- Collapse against the calibrated baseline: full-period minus event cov90 for C0 and for C1.
- Location versus spread: event-window mean error of the median forecast, its ratio to the
  mean half-width of the C0 90% interval, and the share of misses above the upper bound.
- Null windows: coverage of every same-length window that starts at 00:00 local inside the
  evaluation winter and does not overlap the event; the event's percentile in that set, and
  for each calibrator the share of windows whose cov90 lies within 0.85–0.95.
- Retrospective contrast on all 13 events: for C1, C2a, C2b and C4, calibration scores pooled
  from the other events' windows of the same system (each normalised by its era's median
  D_cal score) give a leave-one-event-out coverage; gaps are reported with cells whose
  chronological or retrospective interval is infinite in any event hour flagged and excluded
  from the means.

## Pre-specified criteria (L1, GEFS weather)
- G1, collapse against the calibrated baseline: C1 event cov90 at least 10 pp below C1
  full-period cov90 in at least 9 of the 13 events.
- G2, repair: the out-of-event-selected calibrator meets (a)–(d) in at most 4 of 13 events.
- G3, unusual events: C0 event cov90 lies below the 10th percentile of its null windows in at
  least 9 of 13 events.
- G4, retrospective contrast: the mean absolute leave-one-event-out gap of C2a or C2b over
  events with finite intervals is at least 10 pp.
How the paper reports each outcome: if G2 fails (repair succeeds in more than 4 events),
the paper reports that long histories with winter calibration repair event coverage and
changes its conclusions accordingly. If G1 or G3 fails, the collapse claim is restricted to
the events where it holds.
