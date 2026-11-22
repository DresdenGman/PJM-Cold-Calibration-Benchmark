# Amendments to the frozen protocol

| ID | Type | Content | Status |
|---|---|---|---|
| A1 | Formula review | LOEO calibrator selection rule and formula fixes (see FREEZE_PROTOCOL.md, METHODS_FORMULAS v2.1) | in v1.0.0 |
| A2 | Labelled sensitivity | Prior-winter calibration history (`code/job_mw.py`, results `code/results/frag_mw_*`, `mw_summary.md`) | added in v1.1.0 |
| A3 | Post-hoc sensitivity | Forecast temperature for the 2022 era, PJM and MISO (`sensitivity_forecast_temperature/`) | added in v1.1.0 |
| A4 | Pre-specified replication | MISO replication with criteria R1–R3 fixed before data access (`replication_miso/`) | added in v1.1.0 |
| A5 | Pre-specified test | Ensemble-spread calibrator C5 on archived GEFS, criteria S1–S3 fixed before data access (`ensemble_spread_c5/PLAN_A5.md`) | plan published 2026-11-22 (merge 442bae8); results in `ensemble_spread_c5/RESULTS_A5.md`: S1–S3 fail |
| A6 | Pre-specified extension | Seven additional cold events (PJM 2019; PJM and MISO 2024–2026), windows by weather rule, criteria N1–N3 (`extended_events_a6/PLAN_A6.md`) | plan published 2026-11-22 (8719926), populations before fitting (afc3b62); N1–N2 pass (`RESULTS_A6.md`) |
| A7 | Pre-specified test | Weighted conformal (C6) and conditional GPD tails (C7) (`remedies_a7/PLAN_A7.md`) | plan published 2026-11-22 (8719926); neither supported (`RESULTS_A7.md`) |
| A8 | Pre-specified test | Benchmark refitted on day-ahead forecast weather (GEFS reforecast and operational), criteria F1–F3 (`forecast_weather_a8/PLAN_A8.md`) | plan published 2026-11-22 (8719926); F1–F2 pass, F3 fails (`RESULTS_A8.md`) |

None of the protocol files, nor the A4 plan, carries an external timestamp. The A4 plan was
fingerprinted (SHA-256, local time) before any MISO data were downloaded, and the MISO population
files before any model was fitted (`replication_miso/*.sha256`); A2–A4 were first published
together in release v1.1.0.

A5–A8 differ: their plans were pushed to the public GitHub repository before any GEFS data were
downloaded, so the commit timestamp is external.
