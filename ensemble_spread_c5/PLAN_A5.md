# A5: pre-specified test of an ensemble-spread calibrator (C5)

Written on 2026-11-22, before any GEFS data were downloaded and before any C5 interval was
computed. This plan is committed and pushed to the public repository before the analysis
starts, which gives it the external (GitHub) timestamp that A1–A4 lack.

## Question
Our calibrators condition on temperature (C2a/C2b, C4) and on past scores (C3). A related note
(Guerra Filho, 2026) reports that scaling interval width by the spread of an ensemble weather
forecast restores event-day coverage. A5 tests that idea inside this benchmark, under the same
chronological discipline, using the archived NOAA GEFS ensemble.

## Data
- Source: NOAA Global Ensemble Forecast System archive on AWS (`noaa-gefs-pds`), 2 m
  temperature (TMP:2 m above ground). GEFS v11 (1.0 degree `pgrb2a`, control + 20 members) for the
  2018 and 2019 eras; GEFS v12 (0.5 degree `pgrb2ap5`, control + 30 members) for the 2022 era. Each era
  uses a single GEFS version.
- Issuance: for target local date d, the 00 UTC cycle of local date d-1 (available about
  05:30 UTC on d-1, before the H-DA issuance time of 10:00 EPT on d-1). Forecast hours 24–54,
  every 6 h.
- Spatial: bilinear interpolation of each member to the 15 footprint points of the system
  (PJM: LATS 40.0/41.25/42.5 x LONS -88.0/-84.5/-81.0/-77.5/-74.0; MISO: LATS 38.5/41.5/44.5 x
  LONS -95.5/-93.0/-90.5/-88.0/-85.5), then the equal-weight footprint mean per member.
- Spread z_t (degrees C): sample standard deviation (ddof = 1) across members of the
  footprint-mean temperature, linearly interpolated in time to each hourly target timestamp.
- Missing cycle: use the 00 UTC cycle of d-2 (forecast hours shifted by +24) once; otherwise z_t
  is missing. The archive begins on 2017-01-01, so D_tune rows of the 2018 era before that date
  have no z_t.
- No data from the 2014 era (no archive), so the 2014 vortex is not tested.

## C5 definition
C5 is C4 with heating degree hours replaced by the ensemble spread:
scale s_t = sigma0 * (1 + gamma * z_t), with sigma0 exactly as C4 (median absolute deviation from
the median forecast on D_tune). gamma is chosen from {0, 0.1, 0.25, 0.5, 1, 2, 4} per degree C, separately
for each alpha level and each side, on the D_tune inner hold-out (last 25%) with C4's objective
(side exceedance rate closest to alpha/2; ties to the smaller added margin, then the smaller gamma).
Cutoffs use the order-statistic operator on D_cal (including pre-event evaluation hours), are
expansion-only, and infinite cutoffs are kept. Rows with missing z_t are left out of tuning and
calibration scores. At evaluation a row with missing z_t uses the median z_t of D_cal; such rows
are counted and reported.

## Scope
H-DA arm; learners L1, L2, L3; PJM eras 2018 and 2022; MISO eras 2018, 2019 and 2022.
Chronological evaluation only. Base forecasts are the archived predictions (ERA5 inputs); no
learner is refitted. Scopes as in the frozen protocol (event, onset, full evaluation period,
rule-selected cold spells, placebo windows). C0 and C4 are recomputed in the same run and must
reproduce the archived rows exactly.

## Pre-specified criteria (primary: H-DA x L1, five events)
- S1, information: C5 event cov90 exceeds C4 event cov90 in at least 4 of the 5 events.
- S2, repair: C5 meets condition (a) of the repair test (event cov90 within 0.85–0.95) and
  condition (c) (full-period width inflation over C0 at most 35%) in at least 3 of the 5
  events, and condition (d) (placebo cov90 at most 0.95) in all 5.
- S3, cell test: treating C5 as the calibrator under test in each system, conditions (a) and
  (b) (frontier win against C0x, as coded in `report.frontier_win`) hold in at least 2 of the
  system's events (PJM: 2 of 2; MISO: 2 of 3), and (c) and (d) in all of them.

Interpretation fixed in advance: if S2 holds, ensemble spread carries event information that
the tested calibrators lack and partly repairs coverage; if S2 fails, the remedy is not
supported for these events. All results are reported whatever the outcome, including L2 and L3
and a diagnostic of z_t inside each event against its D_cal median.
