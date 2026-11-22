# Amendment A4 — second-system replication on MISO

The frozen PJM protocol (METHODS_FORMULAS v2.1 + Amendment A1) applied unchanged to the
MISO balancing authority across three cold events: the 2017–18 cold snap, the January 2019
polar vortex and Winter Storm Elliott (2022).

| File | Content |
|---|---|
| `PRESPEC_A4_MISO.md`, `.sha256` | Replication plan and criteria R1–R3, written and fingerprinted before any MISO data were downloaded (local timestamp only; no external timestamp). |
| `POPULATIONS.sha256` | Fingerprint of the cold-spell and placebo files, recorded before any model was fitted. |
| `RESULTS_A4_MISO.md` | Results against R1–R3 and the deviations log. |
| `results/` | Full results matrix, per-cell fragments, report (`RESULTS_RUN1.md`), cold spells and placebo windows. |
| `data/load/` | Derived MISO hourly demand series from EIA-930 (training and evaluation spans). |
| `data/weather/` | ERA5 (Open-Meteo archive) equal-weight means over a 15-point MISO footprint grid. |
| `code/` | `build_miso.py` (data builder) and the four pipeline files that differ from `code/` only in era/event definitions. |

## Verdict (fixed criteria)
- **R1 collapse — replicates.** Day-ahead L1 event cov90 0.140 / 0.222 / 0.281 against full-period 0.499 / 0.546 / 0.544.
- **R2 repair fails — replicates.** 0 of 6 learner × horizon cells pass under both selection rules.
- **R3 transfer illusion — does not replicate.** Mean LOEO − chronological gaps: C1 +1.8, C2a −4.0, C2b −5.3 pp.

## Reproduce
1. Put the EIA-930 six-month BALANCE files for 2016-01 → 2019-06 and 2020-01 → 2023-06 in a folder
   (2022 Jan–Jun is not used, mirroring the PJM design) and run
   `python code/build_miso.py <raw_folder>` from a copy of this directory laid out as
   `<root>/build_miso.py`, `<root>/data_events/{load,weather}` (the builder writes there).
2. Copy the repository's `code/` to `<root>/experiments/`, overwrite it with the four files in
   `replication_miso/code/`, then run `prep_data.py`, the 15 `job_fit.py` cells (eras 2018, 2019, 2022),
   `phase2_loeo.py` and `report.py`.

The PJM 2022 L1 and L2 day-ahead cells were re-run with scikit-learn 1.8.0 and LightGBM 4.7.0 and
reproduce the archived v1.0.0 results exactly.
