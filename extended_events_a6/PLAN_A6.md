# A6: seven additional cold events (PJM 2019; PJM and MISO 2024, 2025, 2026)

Written 2026-11-22 and pushed to the public repository before any load data for the new
eras were downloaded and before any model was fitted on them. The analyst has read public
operator summaries of these winters (dates of peaks and alerts) but has not seen the EIA-930
series for the new eras.

## Eras
Each new era follows the template of the existing EIA-930 eras: training spans the 23 months
from 1 January two years before to 30 November of the year before the evaluation winter;
evaluation is December–February. Splits, features, learners (L1–L3), horizons, calibrators
(C0–C4) and all code are unchanged.

| System | Era | Training | Evaluation |
|---|---|---|---|
| PJM | 2019 | 2017-01-01 to 2018-11-30 | 2018-12-01 to 2019-02-28 |
| PJM, MISO | 2024 | 2022-01-01 to 2023-11-30 | 2023-12-01 to 2024-02-29 |
| PJM, MISO | 2025 | 2023-01-01 to 2024-11-30 | 2024-12-01 to 2025-02-28 |
| PJM, MISO | 2026 | 2024-01-01 to 2025-11-30 | 2025-12-01 to 2026-02-28 |

Data: EIA-930 demand for the PJM and MISO balancing authorities (six-month files from
eia.gov), ERA5 footprint means from Open-Meteo for the same 15 points per system, built with
the existing builders. Cleaning as in the existing builders, nothing more.

## Named event windows, fixed by a weather rule
Unlike the original events, which were taken from operator and regulator reports, each new
named event is defined mechanically: it is the rule-selected cold spell (frozen rule: footprint
temperature below the 2nd percentile of the era's training temperature for at least 24 h, gaps
of up to 12 h merged) that contains the lowest footprint-mean temperature of the evaluation
winter. The window runs from 00:00 local on the spell's first day to 00:00 local after its last
day. If no spell qualifies, the era has no named event and is reported through its cold spells
only. Placebo windows follow the frozen placebo rule.

## Pre-specified criteria (H-DA arm, L1, chronological evaluation)
- N1, collapse: event cov90 below full-period cov90 in at least 5 of the new events, and by at
  least 10 pp in at least 4.
- N2, repair: for each new event, the calibrator selected by the largest Winkler improvement
  over C0 on all other events of the same system (old and new) meets repair conditions (a),
  (c) and (d) together in at most 2 of the new events.
- N3, pooled description: across all 13 modelled events, the number with event coverage
  below full-period coverage, and a one-sided sign test over distinct weather events.

All results are reported whatever the outcome. The transfer-gap judgement J3 is not
recomputed for the new events.
