# A13: which part of the redesign matters (2 x 2 factorial)

Written 2026-11-23 before any A13 model was fitted; kept locally with a SHA-256 fingerprint
and published with the final repository upload (no external timestamp). Written after the
A9-A12 results were known.

A9 changed two things at once: the training history (about two years -> everything since
2015-07-01, or 2010-01-01 for PJM 2014) and the calibration set (the last 92 training days,
i.e. autumn -> leave-one-winter-out cross-fitted prior winters). A13 separates them.

Cells (L1, GEFS day-ahead weather, H-DA, A9 events and populations, all A9 calibrators):
- D1, long history + autumn calibration: the A9 frame; within the training history the last
  92 days are D_cal, the 273 days before them D_tune, the rest D_fit; the learner is fitted
  on D_fit only (the original split rule applied to the long history). No cross-fitting.
- D2, short history + winter calibration: the A9 frame truncated to start on 1 January of the
  year before the evaluation December (about 23 months of training); D_cal = D_tune = the
  prior winters inside that span with leave-one-winter-out cross-fitting, final model on the
  whole truncated history (the A9 rule applied to the short history).
- Reference corners: the original design (short + autumn; frozen-protocol results with
  reanalysis weather, and A8's forecast-weather refit where available) and A9 (long + winter).

Reported: mean event and full-period C1 cov90 and their gap for each design, per event and
pooled with the cluster bootstrap over weather events; the share of events with a C1 gap of at
least 10 pp. No pass/fail criteria: A13 is descriptive attribution.
