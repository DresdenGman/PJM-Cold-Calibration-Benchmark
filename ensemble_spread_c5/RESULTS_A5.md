# A5 results: ensemble-spread calibrator C5

Plan: `PLAN_A5.md` (pushed to GitHub before any GEFS data were downloaded, merge commit
442bae8, 2026-11-22). Analysis: `analyze_c5.py`; full output in `results/analyze_c5_output.txt`.

## Data checks
- 1,245 GEFS 00 UTC cycles fetched (2017-01-01 to 2019-02-27, 2020-12-30 to 2021-12-30,
  2022-11-29 to 2023-02-27); no cycle missing.
- Rerunning C0 and C4 in the same pipeline reproduces the archived rows (max relative
  difference 5.5e-16).
- GEFS ensemble-mean footprint temperature against ERA5: correlation 0.993, mean error
  -0.8 to -1.1 C, MAE 1.2-1.3 C.

## Deviations from the plan
1. One file is absent from the NOAA archive (cycle 2018-10-24, member gep05, forecast hour 24;
   HTTP 404 under both file-name forms). The spread for that forecast hour uses the 20
   remaining members. The cycle lies in the MISO 2019 era's D_cal. The plan did not cover a
   missing member.
2. From 2018-07-27 the archive names forecast hours with two digits (`f24`, not `f024`).
   The fetcher was corrected to accept both forms; the data are unaffected.

## Verdict (H-DA x L1, five events)
| Event | C0 | C4 | C5 | C5 full-period cov90 | C5 width inflation | C5 placebo | spread z: event / D_cal median (C) |
|---|---|---|---|---|---|---|---|
| PJM 2017-18 snap | 0.439 | 0.739 | 0.689 | 0.870 | +71.0% | 0.933 | 0.23 / 0.26 |
| PJM 2022 Elliott | 0.458 | 0.552 | 0.552 | 0.810 | +60.4% | 0.958 | 0.52 / 0.45 |
| MISO 2017-18 snap | 0.140 | 0.621 | 0.458 | 0.743 | +76.1% | 0.899 | 0.36 / 0.30 |
| MISO 2019 vortex | 0.222 | 0.736 | 0.583 | 0.846 | +102.1% | 0.944 | 0.40 / 0.28 |
| MISO 2022 Elliott | 0.281 | 0.385 | 0.354 | 0.803 | +76.2% | 0.958 | 0.46 / 0.54 |

- S1 (C5 above C4 in at least 4 of 5 events): 0 of 5. FAIL.
- S2 ((a) and (c) in at least 3 of 5, (d) in all 5): 0 of 5; (d) fails in two events. FAIL.
- S3 (cell test): fails for every learner in both systems.

No C5 interval is infinite. The hold-out selection often chose the largest spread
coefficient (gamma = 4 per degree C), so C5 does lean on the spread; but the spread inside the events is
close to its calibration-period level (event median 0.23-0.52 C against 0.26-0.54 C). The
ensemble was not unusually uncertain about temperature during these events.

Pre-specified interpretation: the remedy is not supported for these events.

Caveat: the base forecasts use reanalysis temperature, so their residuals contain no
weather-forecast error, the component ensemble spread is designed to track. A forecaster
driven by forecast weather, as in the note that motivated A5, could respond differently.
