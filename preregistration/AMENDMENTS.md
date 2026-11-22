# Amendments to the frozen protocol

| ID | Type | Content | Status |
|---|---|---|---|
| A1 | Formula review | LOEO calibrator selection rule and formula fixes (see FREEZE_PROTOCOL.md, METHODS_FORMULAS v2.1) | in v1.0.0 |
| A2 | Labelled sensitivity | Prior-winter calibration history (`code/job_mw.py`, results `code/results/frag_mw_*`, `mw_summary.md`) | added in v1.1.0 |
| A3 | Post-hoc sensitivity | Forecast temperature for the 2022 era, PJM and MISO (`sensitivity_forecast_temperature/`) | added in v1.1.0 |
| A4 | Pre-specified replication | MISO replication with criteria R1–R3 fixed before data access (`replication_miso/`) | added in v1.1.0 |
| A5 | Pre-specified test | Ensemble-spread calibrator C5 on archived GEFS, criteria S1–S3 fixed before data access (`ensemble_spread_c5/PLAN_A5.md`) | plan published 2026-11-22 (merge 442bae8); results in `ensemble_spread_c5/RESULTS_A5.md`: S1–S3 fail |

None of the protocol files, nor the A4 plan, carries an external timestamp. The A4 plan was
fingerprinted (SHA-256, local time) before any MISO data were downloaded, and the MISO population
files before any model was fitted (`replication_miso/*.sha256`); A2–A4 were first published
together in release v1.1.0.

A5 differs: its plan was pushed to the public GitHub repository before any GEFS data were
downloaded, so the commit timestamp is external.
