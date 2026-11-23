# A13 addendum (v13 revision): cleaner corners of the 2 x 2 factorial

Written 2026-11-23 after an independent pre-submission review of v12 pointed out two confounds,
and before any of the cells below was run. Local SHA-256 fingerprint; published with the final
repository upload (no external timestamp). All A9-A13 results were known when this was written.

Confounds in the v12 factorial:
1. D1 (long + autumn) fitted the learner on D_fit only, withholding the last 365 training days,
   whereas A9 (long + winter) trains on everything. The calibration-season factor therefore also
   changed the recency of the training data.
2. The short + autumn corner came from a different pipeline (the A8 refit of the original design),
   with calendar-2014 evaluation for the 2014 era.

New cells (L1, GEFS day-ahead weather, A9 frames, events and populations, all A9 calibrators):
- D1b, long history + autumn calibration: last 92 training days = D_cal, the 273 days before =
  D_tune (the original split rule); the final model is fitted on ALL training rows; the D_cal and
  D_tune rows are predicted by a model fitted on the training rows without those 365 days.
- D3, short history + autumn calibration: the D2 truncation (start 1 January of the year before
  the evaluation December), then the D1b rule.
The factorial reported in the revised paper is D3 / D1b / D2 / A9. The v12 cells (A8 corner, D1)
are kept as sensitivity results. Reported: the same descriptive quantities as A13. No criteria.
