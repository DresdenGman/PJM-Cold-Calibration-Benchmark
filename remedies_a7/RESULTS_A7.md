# A7 results: temperature-weighted conformal (C6) and conditional GPD tails (C7)

Plan: `PLAN_A7.md` (merged 8719926, before any A7 interval was computed). Full output:
`results/analyze_a7_output.txt`. C0 and C4 rerun in the same pipeline reproduce the archived
rows (max difference 5.5e-16). No C7 fit failed (no fallback to C1).

- C6: (a) and (c) together in 0/13 events (L1); (d) in all; above C4 in 11/13, mostly through
  infinite intervals (up to 64 h of an event). NOT SUPPORTED.
- C7: (a) and (c) together in 0/13 (L1); (d) in all; widens full-period intervals by 33–86%.
  NOT SUPPORTED. For L3 (not the pre-specified learner), C7 meets (a) and (c) in 3 events.

Scripts were run in the development layout (`pjm02/experiments`, `miso/experiments`, `a6/<system>/experiments`, `a8/<system>/experiments`); paths inside them refer to that layout. The experiment code itself is the unchanged code in `code/` and `replication_miso/code`.
