# RESULTS — Run 1 (frozen protocol v2)

**spec version: METHODS_FORMULAS v2.1 + Freeze Amendment A1**

Matrix: 3 eras × 2 horizons (H-DA primary, H-1H) × 3 learners (L1 QR-GBT / L2 LightGBM linear_tree / L3 location-scale) × calibrators C0, C0x, C1, C2a, C2b, C3, C4 under the v2.1 three-way split (D_fit / D_tune / D_cal) and chronological discipline; plus retrospective LOEO-transfer rows for J3. Full tidy results: `results/results_matrix.csv`; per-τ base pinball: `results/pinball_by_tau.csv`.

## Populations

- era 2014: named event `event_2014_vortex` (n=72 valid h); cold spells: 8 spells / 491 h (event-macro and hour-pooled both reported); placebo windows: 3.
- era 2018: named event `event_2018_snap` (n=264 valid h); cold spells: 1 spells / 303 h (event-macro and hour-pooled both reported); placebo windows: 3.
- era 2022: named event `event_2022_elliott` (n=96 valid h); cold spells: 2 spells / 110 h (event-macro and hour-pooled both reported); placebo windows: 3.

## J1 — coverage collapse at C0, and is it one model's artifact?

Event-window cov90 vs same-era eval-winter cov90 at C0 (uncalibrated, sorted base quantiles); gap = winter − event. Frozen bar: L1 gap ≥ 10pp in all three events + same-direction replication by L2 or L3 (operationalized: ≥5pp in ≥2 events).

| horizon | learner | 2014 ev (winter) gap | 2018 ev (winter) gap | 2022 ev (winter) gap |
|---|---|---|---|---|
| HDA | L1 | 0.125 (0.657) +53.2pp | 0.439 (0.583) +14.3pp | 0.458 (0.550) +9.2pp |
| HDA | L2 | 0.333 (0.924) +59.0pp | 0.818 (0.976) +15.8pp | 0.667 (0.982) +31.6pp |
| HDA | L3 | 0.792 (0.637) -15.5pp | 0.492 (0.691) +19.9pp | 0.688 (0.942) +25.5pp |
| H1H | L1 | 0.611 (0.811) +20.0pp | 0.602 (0.719) +11.7pp | 0.562 (0.693) +13.1pp |
| H1H | L2 | 0.333 (0.924) +59.0pp | 0.818 (0.976) +15.8pp | 0.667 (0.982) +31.6pp |
| H1H | L3 | 0.792 (0.637) -15.5pp | 0.492 (0.691) +19.9pp | 0.688 (0.942) +25.5pp |

**J1 verdict (H-DA): DOES NOT HOLD as written** — L1 ≥10pp in all three events: NO (2014: +53.2pp, 2018: +14.3pp, 2022: +9.2pp); L2/L3 best replication per event: 2014: +59.0pp, 2018: +19.9pp, 2022: +31.6pp (≥5pp in ≥2 events: YES).

## Joint block bootstrap — cov90 resampling ranges (H-DA × L1)

v2.1 §7: the SAME circular 24h block indices are applied to every method's frozen (y, L, U) tuples; no refitting, no ACI replay. Descriptive ranges, not confidence intervals.

### event_2014_vortex (n=72)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.125 | 0.000–0.333 | +0.0pp … +0.0pp | 0 |
| C0x | 0.208 | 0.000–0.500 | +0.0pp … +20.9pp | 0 |
| C1 | 0.222 | 0.000–0.528 | +0.0pp … +25.0pp | 0 |
| C2a | 0.306 | 0.028–0.653 | +2.8pp … +36.1pp | 0 |
| C2b | 0.264 | 0.000–0.611 | +0.0pp … +29.2pp | 0 |
| C3 | 0.583 | 0.181–0.973 | +15.3pp … +77.8pp | 0 |
| C4 | 0.250 | 0.000–0.583 | +0.0pp … +30.6pp | 0 |

### event_2018_snap (n=264)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.439 | 0.246–0.640 | +0.0pp … +0.0pp | 0 |
| C0x | 0.841 | 0.727–0.943 | +25.8pp … +54.6pp | 0 |
| C1 | 0.670 | 0.455–0.875 | +13.6pp … +34.1pp | 0 |
| C2a | 0.848 | 0.723–0.951 | +26.9pp … +54.9pp | 84 |
| C2b | 0.792 | 0.651–0.909 | +21.6pp … +49.6pp | 84 |
| C3 | 0.701 | 0.473–0.894 | +15.9pp … +37.1pp | 0 |
| C4 | 0.739 | 0.534–0.913 | +19.3pp … +42.1pp | 0 |

### event_2022_elliott (n=96)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.458 | 0.104–0.792 | +0.0pp … +0.0pp | 0 |
| C0x | 0.615 | 0.208–0.969 | +3.1pp … +29.2pp | 0 |
| C1 | 0.562 | 0.146–0.938 | +0.0pp … +20.8pp | 0 |
| C2a | 1.000 | 1.000–1.000 | +20.8pp … +89.6pp | 53 |
| C2b | 0.562 | 0.146–0.938 | +0.0pp … +20.8pp | 0 |
| C3 | 0.615 | 0.208–0.969 | +3.1pp … +29.2pp | 0 |
| C4 | 0.552 | 0.146–0.917 | +0.0pp … +18.8pp | 0 |

## J2 — repair under Amendment A1 leave-one-event-out selection

Δ_{c,e} = event Winkler90(C0) − Winkler90(c) (MW; positive = improvement). For event e the calibrator ĉ_{−e} is selected on the OTHER two events only, then judged on e: (a) cov90 within ±5pp of nominal; (b) frontier win vs C0x on e; (c) era eval-winter width inflation ≤ 35%; (d) era placebo cov90 ≤ 0.95.

### LOEO selection (Amendment A1, primary)

| cell | event | ĉ | cov90 (a) | frontier (b) | width infl (c) | placebo cov (d) |
|---|---|---|---|---|---|---|
| HDA×L1 | 2014 | C0x | 0.208 ✗ | ✓ | +115.0% ✗ | 0.903 ✓ |
| HDA×L1 | 2018 | C3 | 0.701 ✗ | ✓ | +103.9% ✗ | 0.919 ✓ |
| HDA×L1 | 2022 | C3 | 0.615 ✗ | ✗ | +inf% ✗ | 0.943 ✓ |
| HDA×L2 | 2014 | C0x | 0.333 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2018 | C2b | 0.905 ✓ | ✗ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2022 | C0x | 0.667 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L3 | 2014 | C3 | 0.958 ✗ | ✗ | +44.1% ✗ | 0.935 ✓ |
| HDA×L3 | 2018 | C1 | 0.530 ✗ | ✗ | +0.0% ✓ | 0.826 ✓ |
| HDA×L3 | 2022 | C3 | 0.688 ✗ | ✓ | +inf% ✗ | 0.882 ✓ |
| H1H×L1 | 2014 | C0x | 0.764 ✗ | ✓ | +35.0% ✗ | 0.954 ✗ |
| H1H×L1 | 2018 | C0x | 0.848 ✗ | ✓ | +70.0% ✗ | 0.919 ✓ |
| H1H×L1 | 2022 | C0x | 0.708 ✗ | ✓ | +50.1% ✗ | 0.880 ✓ |
| H1H×L2 | 2014 | C0x | 0.333 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2018 | C3 | 0.818 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2022 | C3 | 0.667 ✗ | ✓ | +inf% ✗ | 1.000 ✗ |
| H1H×L3 | 2014 | C3 | 0.958 ✗ | ✗ | +41.7% ✗ | 0.921 ✓ |
| H1H×L3 | 2018 | C1 | 0.530 ✗ | ✗ | +0.0% ✓ | 0.826 ✓ |
| H1H×L3 | 2022 | C3 | 0.688 ✗ | ✓ | +inf% ✗ | 0.882 ✓ |

Cell verdicts (a≥2/3, b≥2/3, all c, all d): HDA×L1: no; HDA×L2: no; HDA×L3: no; H1H×L1: no; H1H×L2: no; H1H×L3: no

### Chronological-selection variant (2014's variant uses later events and is retrospective by construction)

| cell | event | ĉ | cov90 (a) | frontier (b) | width infl (c) | placebo cov (d) |
|---|---|---|---|---|---|---|
| HDA×L1 | 2014 | C0x | 0.208 ✗ | ✓ | +115.0% ✗ | 0.903 ✓ |
| HDA×L1 | 2018 | C2a | 0.848 ✗ | ✗ | +inf% ✗ | 0.907 ✓ |
| HDA×L1 | 2022 | C3 | 0.615 ✗ | ✗ | +inf% ✗ | 0.943 ✓ |
| HDA×L2 | 2014 | C0x | 0.333 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2018 | C2a | 0.905 ✓ | ✗ | +inf% ✗ | 1.000 ✗ |
| HDA×L2 | 2022 | C0x | 0.667 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L3 | 2014 | C3 | 0.958 ✗ | ✗ | +44.1% ✗ | 0.935 ✓ |
| HDA×L3 | 2018 | C1 | 0.530 ✗ | ✗ | +0.0% ✓ | 0.826 ✓ |
| HDA×L3 | 2022 | C3 | 0.688 ✗ | ✓ | +inf% ✗ | 0.882 ✓ |
| H1H×L1 | 2014 | C0x | 0.764 ✗ | ✓ | +35.0% ✗ | 0.954 ✗ |
| H1H×L1 | 2018 | C4 | 0.780 ✗ | ✓ | +55.1% ✗ | 0.918 ✓ |
| H1H×L1 | 2022 | C0x | 0.708 ✗ | ✓ | +50.1% ✗ | 0.880 ✓ |
| H1H×L2 | 2014 | C0x | 0.333 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2018 | C2a | 0.905 ✓ | ✗ | +inf% ✗ | 1.000 ✗ |
| H1H×L2 | 2022 | C3 | 0.667 ✗ | ✓ | +inf% ✗ | 1.000 ✗ |
| H1H×L3 | 2014 | C3 | 0.958 ✗ | ✗ | +41.7% ✗ | 0.921 ✓ |
| H1H×L3 | 2018 | C1 | 0.530 ✗ | ✗ | +0.0% ✓ | 0.826 ✓ |
| H1H×L3 | 2022 | C3 | 0.688 ✗ | ✓ | +inf% ✗ | 0.882 ✓ |

Cell verdicts (a≥2/3, b≥2/3, all c, all d): HDA×L1: no; HDA×L2: no; HDA×L3: no; H1H×L1: no; H1H×L2: no; H1H×L3: no

## J3 — retrospective LOEO transfer minus chronological (cov90 gap, pp)

Positive = retrospective event-pooling flatters the calibrator relative to what chronological calibration delivered. C3: no LOEO variant (online method) → n/a. C4 LOEO is skipped for the H1H×L1 cell (mixed 7/15 quantile grids across eras).

| horizon | learner | calibrator | 2014 | 2018 | 2022 | mean |
|---|---|---|---|---|---|---|
| HDA | L1 | C0x | -1.4pp | -3.4pp | +1.0pp | -1.3pp |
| HDA | L1 | C1 | -5.6pp | -0.8pp | +3.1pp | -1.1pp |
| HDA | L1 | C2a | +45.8pp | +15.2pp | -26.0pp | +11.6pp |
| HDA | L1 | C2b | +50.0pp | +4.2pp | +9.4pp | +21.2pp |
| HDA | L1 | C4 | -2.8pp | -2.7pp | +8.3pp | +1.0pp |
| HDA | L2 | C0x | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L2 | C1 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L2 | C2a | +37.5pp | +3.8pp | -26.0pp | +5.1pp |
| HDA | L2 | C2b | +48.6pp | -8.7pp | +0.0pp | +13.3pp |
| HDA | L2 | C4 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L3 | C0x | -13.9pp | -3.4pp | +6.2pp | -3.7pp |
| HDA | L3 | C1 | -8.3pp | -3.8pp | +7.3pp | -1.6pp |
| HDA | L3 | C2a | +6.9pp | -19.3pp | +2.1pp | -3.4pp |
| HDA | L3 | C2b | +11.1pp | -19.7pp | +26.0pp | +5.8pp |
| HDA | L3 | C4 | -5.6pp | -3.0pp | +2.1pp | -2.2pp |
| H1H | L1 | C0x | +6.9pp | -8.7pp | +0.0pp | -0.6pp |
| H1H | L1 | C1 | +13.9pp | -9.1pp | +0.0pp | +1.6pp |
| H1H | L1 | C2a | +22.2pp | -12.9pp | -33.3pp | -8.0pp |
| H1H | L1 | C2b | +22.2pp | -12.1pp | -1.0pp | +3.0pp |
| H1H | L2 | C0x | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L2 | C1 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L2 | C2a | +37.5pp | +3.8pp | -26.0pp | +5.1pp |
| H1H | L2 | C2b | +48.6pp | -8.7pp | +0.0pp | +13.3pp |
| H1H | L2 | C4 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L3 | C0x | -13.9pp | -3.4pp | +6.2pp | -3.7pp |
| H1H | L3 | C1 | -8.3pp | -3.8pp | +7.3pp | -1.6pp |
| H1H | L3 | C2a | +6.9pp | -19.3pp | +2.1pp | -3.4pp |
| H1H | L3 | C2b | +11.1pp | -19.7pp | +26.0pp | +5.8pp |
| H1H | L3 | C4 | -5.6pp | -3.0pp | +2.1pp | -2.2pp |

**J3 reading:** the gaps above ARE the result (no pass/fail in the frozen protocol). Systematically positive gaps = the retrospective transfer evaluation overstates deliverable coverage — the R6 'transfer illusion' configuration if the chronological arm simultaneously fails J2.

## Deviations, operationalizations, hard blockers

- Named-event windows are the the Phase 1 audit-registered windows (2014: Jan 6–8, 72h; 2018: Dec 28–Jan 7, 264h; 2022: Dec 23–26, 96h), not the shorthand dates in the original brief; the onset scope follows v2.1 §4 (first min(72h, event length) hours).
- Reproduction arm (L1, 2014, H-1H): native Phase 2a features and the native 7-quantile set per the v2.1 §0 exception, but fitted on D_fit (2010–2012) under the global three-way split (Phase 2a itself trained on 2010–2013); α=0.20/0.05 endpoints use the §0 outward bracketing grid pair.
- Release-mask as-of semantics (v2.1 §8): lag features are nominal-anchored with a ≤48h scan-back to a finite released label. Consequence: 2022 eval rows are valid only from Dec 8 in both arms (168 rows dropped per arm) because lag_168h's nominal source falls in the Jan–Nov 2022 load gap; the Elliott window is fully covered. (The initially briefed '~Dec 2' assumed only a 38h history requirement, which the 168h features override.)
- ACI: the §1 expansion-only rule (Q+ = max(0, Q)) is applied to ACI cutoffs as well; error updates are applied at issuance points using labels with a_i < s, in target-hour order.
- C4 LOEO: gamma search on pooled other-era D_tune uses one pooled sigma0 (approximation, flagged in code); C4 LOEO is not run for H1H×L1 (mixed 7/15 quantile grids). LOEO score pooling normalizes each era's scores by its median CQR score at α=0.10 (v2.1 does not specify cross-era pooling mechanics).
- The 2018/2022 eval spans contribute 2,156 of 2,160 hours (4 boundary hours fall outside the weather span; Phase 2b §5.3 join note).
- J1's replication bar (≥5pp) and J2's frontier interpolation rule are operationalizations, flagged where used. C0x's expansion factor is selected on D_cal (v2.1 does not redefine C0x; it is retained as the FREEZE J2 frontier comparator).
- No component was infeasible: sklearn/LightGBM/scipy were already present in the aideml venv; no data column was missing (EIA-era wind chill is derived by the standard NWS formula, documented in prep_data.py).
- C3 in era 2022: D_cal_train is Oct–Dec 2021, so at the Dec 2022 stream start every seed score lies outside ACI's 2160h clock window (v2.1 §4); the first issued intervals are +inf by the §0 n=0 rule (11 infinite winter intervals at H-1H, 25 at H-DA, identical across learners) until in-stream scores accumulate. This is the frozen rule applied across the declared data gap, not an implementation defect.
- Placebo window 2022_P1 (Dec 1–4) contains zero feature-valid rows for L1/L2 (it sits inside the Dec 1–7 masked-history gap); it contributes NaN per-window rows, is excluded from the placebo macro average, and the pooled placebo scope still has 192 valid hours from P2/P3.
- Runtime engineering (no spec impact): L2 LightGBM defaults were trimmed after timing benchmarks (250 rounds/31 leaves -> 120 rounds/15 leaves, lr 0.1; linear_tree=True, features and quantile grid unchanged — the frozen spec fixes only those). Jobs were run sequentially with capped passive-wait threads after parallel launches collapsed into OpenMP thread thrash on this 4-core VM; every cell was then completed with exit 0.

## Run facts

- `job_2014_H1H_L1.log`: C4 sigma0=552.1 MW; gammas={0.2: (0.4, 0.0), 0.1: (0.2, 0.4), 0.05: (0.4, 0.0), 0.02: (0.2, 0.0)}
- `job_2014_H1H_L1.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2014_H1H_L2.log`: C4 sigma0=11831.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2014_H1H_L2.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2014_HDA_L1.log`: C4 sigma0=2903.6 MW; gammas={0.2: (0.02, 0.4), 0.1: (0.05, 0.02), 0.05: (0.4, 0.0), 0.02: (0.4, 0.05)}
- `job_2014_HDA_L1.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2014_HDA_L2.log`: C4 sigma0=11832.3 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2014_HDA_L2.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2014_L3.log`: C4 sigma0=4797.2 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.02), 0.05: (0.0, 0.4), 0.02: (0.0, 0.4)}
- `job_2014_L3.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2014_L3.log`: C4 sigma0=4797.2 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.02), 0.05: (0.0, 0.4), 0.02: (0.0, 0.4)}
- `job_2014_L3.log`: first valid eval row: 2014-01-01 00:00:00-05:00 (8760 of 8760 eval rows)
- `job_2018_H1H_L1.log`: C4 sigma0=1559.5 MW; gammas={0.2: (0.0, 0.4), 0.1: (0.0, 0.4), 0.05: (0.0, 0.05), 0.02: (0.02, 0.0)}
- `job_2018_H1H_L1.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_H1H_L2.log`: C4 sigma0=9532.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2018_H1H_L2.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_HDA_L1.log`: C4 sigma0=2287.2 MW; gammas={0.2: (0.0, 0.2), 0.1: (0.02, 0.2), 0.05: (0.05, 0.4), 0.02: (0.1, 0.0)}
- `job_2018_HDA_L1.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_HDA_L2.log`: C4 sigma0=9531.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2018_HDA_L2.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_L3.log`: C4 sigma0=3500.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.02, 0.0)}
- `job_2018_L3.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_L3.log`: C4 sigma0=3500.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.02, 0.0)}
- `job_2018_L3.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2022_H1H_L1.log`: C4 sigma0=1498.0 MW; gammas={0.2: (0.0, 0.2), 0.1: (0.0, 0.2), 0.05: (0.0, 0.4), 0.02: (0.02, 0.4)}
- `job_2022_H1H_L1.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_H1H_L2.log`: C4 sigma0=11291.0 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_H1H_L2.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_HDA_L1.log`: C4 sigma0=2434.7 MW; gammas={0.2: (0.0, 0.1), 0.1: (0.0, 0.02), 0.05: (0.02, 0.02), 0.02: (0.4, 0.2)}
- `job_2022_HDA_L1.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_HDA_L2.log`: C4 sigma0=11291.7 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_HDA_L2.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_L3.log`: C4 sigma0=3438.6 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.1)}
- `job_2022_L3.log`: first valid eval row: 2022-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2022_L3.log`: C4 sigma0=3438.6 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.1)}
- `job_2022_L3.log`: first valid eval row: 2022-11-30 23:00:00-05:00 (2156 of 2156 eval rows)

