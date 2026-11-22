# A8 results: benchmark refitted on day-ahead forecast weather

Plan: `PLAN_A8.md` (merged 8719926, before any forecast data were downloaded). Full output:
`results/analyze_a8_output.txt`; summary: `a8_summary.csv`; frame diagnostics:
`results/<system>/a8_frame_<era>.json`. Extracted GEFS values at the 30 footprint points:
`data/gefs_ctl_footprint_points.csv.gz` (5,232 control runs, T2m and 10 m wind) and
`data/gefs_ens_footprint_points.csv.gz` (3,104 runs, T2m of all members used for spread).
No run is missing. Forecast footprint temperature against ERA5: MAE 1.17–1.83 C,
correlation 0.987–0.994.

- F1 PASS (exactly): collapse in 9/13 events (threshold 9). Not in PJM 2019, 2022, 2024 and
  MISO 2026, where event coverage rises and full-period coverage falls.
- F2 PASS: repair (a), (c), (d) with out-of-event selection in 0/13.
- F3 FAIL: C5 with forecast weather meets (a) and (c) in 0/13; it beats C4 in 5/13.
- Event cov90, forecast minus reanalysis: mean +1.1 pp, range -11.1 to +15.9 pp.
- C0 and C4 rerun in the C5 pipeline reproduce the A8 rows exactly.

Scripts were run in the development layout (`pjm02/experiments`, `miso/experiments`, `a6/<system>/experiments`, `a8/<system>/experiments`); paths inside them refer to that layout. The experiment code itself is the unchanged code in `code/` and `replication_miso/code`.
