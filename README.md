# PJM Cold-Spell Calibration Benchmark

**When Cold-Spell Calibration Fails to Transfer: A PJM Benchmark of Probabilistic Load Forecasting Across Four Extreme-Cold Events**

This repository contains the code, pre-registration, derived data and full
results for a benchmark study of probabilistic load forecasting under
extreme cold. It asks a narrow question: can calibration learned from
historically available cold-weather observations be transferred to a
subsequent extreme-cold event, under evaluation rules that respect what
was knowable at the time?

The benchmark covers four PJM extreme-cold events — the January 2014
polar vortex, February 2015 (an official-forecast error anchor only), the
December 2017 – January 2018 cold snap, and Winter Storm Elliott in
December 2022. Three structurally different forecasters (a quantile
gradient-boosting model, an extrapolating linear-tree LightGBM, and a
statistical location–scale model) are combined with five conformal-style
calibrators (global split conformal, temperature-stratified Mondrian in
guarantee-preserving and shrinkage variants, adaptive conformal inference,
and a temperature-excess scaled variant, plus uncalibrated and
proportionally expanded baselines), at a day-ahead issuance horizon
(primary) and a one-hour oracle horizon (reference). Every method is
judged twice: under strictly chronological evaluation, and under
retrospective leave-one-event-out (LOEO) transfer.

The design — event definitions, data splits, calibrator formulas and the
three judgements below — was frozen in writing before any result was
computed (see `preregistration/`).

## Headline findings

- **J1 — collapse.** Uncalibrated 90% prediction intervals collapse
  inside the events: at the day-ahead horizon the quantile-boosting model
  covered 12.5% of polar-vortex hours against 65.7% over the full 2014
  evaluation period (gap +53.2 pp), with gaps of +14.3 pp (2018 snap) and
  +9.2 pp (Elliott). The strictest pre-registered form of J1 (a gap of
  ≥10 pp in all three modelled events) narrowly missed on Elliott; the
  collapse itself replicates in the extrapolating learner (+59.0 /
  +15.8 / +31.6 pp), so it is not one model's artifact.
- **J2 — repair fails.** No calibrator, selected using only the other
  events, restored event-window 90% coverage to within ±5 pp of nominal
  in at least two of the three events while respecting the width and
  placebo conditions: 0 of 18 horizon × learner cells passed. The
  strongest single repair (adaptive conformal on the 2014 vortex) reached
  0.583 — still far from 0.90.
- **J3 — transfer illusion.** Retrospective LOEO evaluation flatters the
  temperature-stratified Mondrian calibrators: relative to chronological
  evaluation it overstates their mean event coverage by +11.6 pp (C2a)
  and +21.2 pp (C2b) on the day-ahead quantile-boosting arm — exactly the
  pre-registered "transfer illusion" configuration — while global and
  scaled conformal show gaps near zero.
- **The operator's own record.** PJM's day-ahead forecasts underestimated
  the peak of all four events: −2,545 MW (−1.8%) in January 2014,
  −1,909 MW (−1.3%) in February 2015, −5,361 MW (−3.9%) in the 2017–18
  snap, and −8,878 MW (−6.6%) during Elliott.

## Repository layout

| Path | Contents |
|---|---|
| `preregistration/` | The frozen protocol (FREEZE_PROTOCOL v2 + Amendment A1) and the formula specification (METHODS_FORMULAS v2.1) that the code implements. |
| `code/` | The full experiment pipeline: data builders, preparation, learners, calibrators, fit jobs, LOEO transfer, reporting; the Run-1 report (`RESULTS_RUN1.md`); and the tidy result tables in `code/results/` (`results_matrix.csv`, `pinball_by_tau.csv`, per-cell fragments). |
| `data/events/` | Derived hourly PJM load series (from EIA-930) and ERA5 footprint-mean weather series (from the Open-Meteo archive) for the 2018/2022 eras. |
| `data/regen/` | Regenerated 2014 QR-GBT quantile forecasts for the full test year 2014, with their metric set. |
| `data/era2014/` | Placeholder and instructions for the assembled 2014 modelling table, which is not redistributed (see `DATA_SOURCES.md`). |
| `DATA_SOURCES.md` | Provenance of every dataset and how to rebuild each one from the public sources. |

## Reproducing the results

Requirements: Python 3.11+ with `numpy`, `pandas`, `scikit-learn`,
`lightgbm` and `scipy` (see `requirements.txt`). The reference run used
scikit-learn 1.5.0, pandas 2.1.4 and numpy 1.26.2; the seed is fixed
(42) throughout.

```bash
pip install -r requirements.txt

# 1. Data (2018/2022 derived series are already in data/events/;
#    to rebuild them from the raw sources, see DATA_SOURCES.md)
python code/build_data_events.py    # event windows (needs data/events/_raw_eia930/)
python code/build_data_spans.py all # training spans + evaluation windows

# 2. Build the 2014 modelling table per DATA_SOURCES.md and place it in
#    data/era2014/ (required for the 2014 era and for step 3)

# 3. Optional: regenerate the 2014 QR-GBT forecasts (data/regen/)
python code/regen_qr_gbt.py

# 4. Prepare era frames, fit all cells, run LOEO transfer, write the report
python code/prep_data.py
bash   code/run_seq.sh              # or code/run_all.sh for the parallel driver
#    (run_seq.sh calls code/job_fit.py per cell, then code/phase2_loeo.py
#     and code/report.py, regenerating code/results/*.csv and the report)
```

## Data

All inputs come from public sources: PJM metered load and PJM published
day-ahead load forecasts, the U.S. EIA Form 930 hourly balancing-authority
files, and ERA5 reanalysis served by the Open-Meteo archive. The derived
series computed from them are included under the repository license;
the assembled 2014 modelling table is documented but not redistributed.
Full details, including known measurement-basis differences (EIA-930
demand vs PJM metered load), are in `DATA_SOURCES.md`.

## Citation

If you use this benchmark, please cite the software using `CITATION.cff`
in this repository. Archived releases are deposited on Zenodo.

## License

MIT — see `LICENSE`. Input data remain under their original terms
(EIA-930: U.S. government public data; ERA5: Copernicus / CC BY 4.0;
PJM data: PJM's published data terms).

## Contact

Dresden Goehner, Independent Researcher, Jurupa Valley, CA, USA —
dresdengoehner@outlook.com
