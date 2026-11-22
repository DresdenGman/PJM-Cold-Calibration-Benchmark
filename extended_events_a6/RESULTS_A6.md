# A6 results: seven further events

Plan: `PLAN_A6.md` (merged 8719926, before any new load data were downloaded). Populations
(event windows, cold spells, placebos): `populations/` (merged afc3b62, before any fitting).
Full output: `results/analyze_a6_output.txt`; summary: `a6_summary.csv`.

- N1 PASS: event cov90 below full-period cov90 in 7/7 new events, by >= 10 pp in 5/7
  (exceptions PJM 2019, +2.7 pp; MISO 2026, +2.8 pp).
- N2 PASS: out-of-event-selected calibrator meets (a), (c), (d) together in 0/7 new events.
- N3: all 13 events below; seven distinct weather events, one-sided sign test p = 0.0078.
  On the one-hour oracle arm, 12 of 13 (MISO 2026 is not).
- No calibrator (C0x, C1–C7) meets (a), (c) and (d) together in any of the 13 events (L1, H-DA).

Scripts were run in the development layout (`pjm02/experiments`, `miso/experiments`, `a6/<system>/experiments`, `a8/<system>/experiments`); paths inside them refer to that layout. The experiment code itself is the unchanged code in `code/` and `replication_miso/code`.
