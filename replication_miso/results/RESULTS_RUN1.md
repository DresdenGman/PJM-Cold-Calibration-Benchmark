# RESULTS — Run 1 (frozen protocol v2)

**spec version: METHODS_FORMULAS v2.1 + Freeze Amendment A1**

Matrix: 3 eras × 2 horizons (H-DA primary, H-1H) × 3 learners (L1 QR-GBT / L2 LightGBM linear_tree / L3 location-scale) × calibrators C0, C0x, C1, C2a, C2b, C3, C4 under the v2.1 three-way split (D_fit / D_tune / D_cal) and chronological discipline; plus retrospective LOEO-transfer rows for J3. Full tidy results: `results/results_matrix.csv`; per-τ base pinball: `results/pinball_by_tau.csv`.

## Populations

- era 2018: named event `event_2018_snap` (n=264 valid h); cold spells: 3 spells / 296 h (event-macro and hour-pooled both reported); placebo windows: 3.
- era 2019: named event `event_2019_vortex` (n=72 valid h); cold spells: 1 spells / 66 h (event-macro and hour-pooled both reported); placebo windows: 3.
- era 2022: named event `event_2022_elliott` (n=96 valid h); cold spells: 1 spells / 52 h (event-macro and hour-pooled both reported); placebo windows: 3.

## J1 — coverage collapse at C0, and is it one model's artifact?

Event-window cov90 vs same-era eval-winter cov90 at C0 (uncalibrated, sorted base quantiles); gap = winter − event. Frozen bar: L1 gap ≥ 10pp in all three events + same-direction replication by L2 or L3 (operationalized: ≥5pp in ≥2 events).

| horizon | learner | 2018 ev (winter) gap | 2019 ev (winter) gap | 2022 ev (winter) gap |
|---|---|---|---|---|
| HDA | L1 | 0.140 (0.499) +35.8pp | 0.222 (0.546) +32.4pp | 0.281 (0.544) +26.3pp |
| HDA | L2 | 0.951 (0.990) +4.0pp | 0.931 (0.996) +6.6pp | 0.833 (0.992) +15.9pp |
| HDA | L3 | 0.572 (0.721) +14.9pp | 0.986 (0.747) -23.9pp | 0.885 (0.942) +5.7pp |
| H1H | L1 | 0.473 (0.602) +12.9pp | 0.222 (0.630) +40.8pp | 0.365 (0.628) +26.3pp |
| H1H | L2 | 0.951 (0.990) +4.0pp | 0.931 (0.996) +6.6pp | 0.833 (0.992) +15.9pp |
| H1H | L3 | 0.572 (0.721) +14.9pp | 0.986 (0.747) -23.9pp | 0.885 (0.942) +5.7pp |

**J1 verdict (H-DA): HOLDS** — L1 ≥10pp in all three events: YES (2018: +35.8pp, 2019: +32.4pp, 2022: +26.3pp); L2/L3 best replication per event: 2018: +14.9pp, 2019: +6.6pp, 2022: +15.9pp (≥5pp in ≥2 events: YES).

## Joint block bootstrap — cov90 resampling ranges (H-DA × L1)

v2.1 §7: the SAME circular 24h block indices are applied to every method's frozen (y, L, U) tuples; no refitting, no ACI replay. Descriptive ranges, not confidence intervals.

### event_2018_snap (n=264)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.140 | 0.027–0.288 | +0.0pp … +0.0pp | 0 |
| C0x | 0.542 | 0.326–0.746 | +23.5pp … +55.3pp | 0 |
| C1 | 0.330 | 0.155–0.511 | +10.6pp … +26.9pp | 0 |
| C2a | 0.568 | 0.345–0.769 | +25.8pp … +58.0pp | 0 |
| C2b | 0.413 | 0.235–0.598 | +15.9pp … +38.3pp | 0 |
| C3 | 0.735 | 0.519–0.920 | +40.2pp … +78.4pp | 0 |
| C4 | 0.621 | 0.398–0.814 | +31.1pp … +64.0pp | 0 |

### event_2019_vortex (n=72)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.222 | 0.014–0.459 | +0.0pp … +0.0pp | 0 |
| C0x | 0.583 | 0.181–0.986 | +8.3pp … +65.3pp | 0 |
| C1 | 0.403 | 0.111–0.694 | +6.9pp … +29.2pp | 0 |
| C2a | 0.681 | 0.402–0.917 | +31.9pp … +59.7pp | 0 |
| C2b | 0.542 | 0.291–0.792 | +23.6pp … +40.3pp | 0 |
| C3 | 0.750 | 0.417–1.000 | +34.7pp … +69.4pp | 0 |
| C4 | 0.736 | 0.431–1.000 | +36.1pp … +69.4pp | 0 |

### event_2022_elliott (n=96)

| calibrator | cov90 | boot 2.5–97.5% | Δcov90 vs C0 range | infinite intervals |
|---|---|---|---|---|
| C0 | 0.281 | 0.010–0.625 | +0.0pp … +0.0pp | 0 |
| C0x | 0.521 | 0.156–0.896 | +7.3pp … +44.8pp | 0 |
| C1 | 0.375 | 0.052–0.750 | +1.0pp … +19.8pp | 0 |
| C2a | 0.760 | 0.552–0.948 | +17.7pp … +80.2pp | 39 |
| C2b | 0.729 | 0.510–0.938 | +14.6pp … +78.1pp | 39 |
| C3 | 0.740 | 0.375–1.000 | +17.7pp … +72.9pp | 24 |
| C4 | 0.385 | 0.052–0.760 | +1.0pp … +21.9pp | 0 |

## J2 — repair under Amendment A1 leave-one-event-out selection

Δ_{c,e} = event Winkler90(C0) − Winkler90(c) (MW; positive = improvement). For event e the calibrator ĉ_{−e} is selected on the OTHER two events only, then judged on e: (a) cov90 within ±5pp of nominal; (b) frontier win vs C0x on e; (c) era eval-winter width inflation ≤ 35%; (d) era placebo cov90 ≤ 0.95.

### LOEO selection (Amendment A1, primary)

| cell | event | ĉ | cov90 (a) | frontier (b) | width infl (c) | placebo cov (d) |
|---|---|---|---|---|---|---|
| HDA×L1 | 2018 | C4 | 0.621 ✗ | ✗ | +113.9% ✗ | 0.957 ✗ |
| HDA×L1 | 2019 | C4 | 0.736 ✗ | ✗ | +137.5% ✗ | 0.968 ✗ |
| HDA×L1 | 2022 | C4 | 0.385 ✗ | ✓ | +79.7% ✗ | 0.932 ✓ |
| HDA×L2 | 2018 | C0x | 0.951 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2019 | C0x | 0.931 ✓ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2022 | C0x | 0.833 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L3 | 2018 | C1 | 0.652 ✗ | ✗ | +13.4% ✓ | 0.902 ✓ |
| HDA×L3 | 2019 | C3 | 1.000 ✗ | ✓ | +29.1% ✓ | 0.861 ✓ |
| HDA×L3 | 2022 | C2b | 0.958 ✗ | ✗ | +1.3% ✓ | 0.868 ✓ |
| H1H×L1 | 2018 | C3 | 0.860 ✓ | ✓ | +109.7% ✗ | 0.920 ✓ |
| H1H×L1 | 2019 | C3 | 0.722 ✗ | ✗ | +119.1% ✗ | 0.926 ✓ |
| H1H×L1 | 2022 | C4 | 0.396 ✗ | ✗ | +37.5% ✗ | 0.818 ✓ |
| H1H×L2 | 2018 | C0x | 0.951 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2019 | C0x | 0.931 ✓ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2022 | C0x | 0.833 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L3 | 2018 | C1 | 0.652 ✗ | ✗ | +13.4% ✓ | 0.902 ✓ |
| H1H×L3 | 2019 | C3 | 1.000 ✗ | ✓ | +25.3% ✓ | 0.875 ✓ |
| H1H×L3 | 2022 | C3 | 0.885 ✓ | ✓ | +inf% ✗ | 0.865 ✓ |

Cell verdicts (a≥2/3, b≥2/3, all c, all d): HDA×L1: no; HDA×L2: no; HDA×L3: no; H1H×L1: no; H1H×L2: no; H1H×L3: no

### Chronological-selection variant (2014's variant uses later events and is retrospective by construction)

| cell | event | ĉ | cov90 (a) | frontier (b) | width infl (c) | placebo cov (d) |
|---|---|---|---|---|---|---|
| HDA×L1 | 2018 | C4 | 0.621 ✗ | ✗ | +113.9% ✗ | 0.957 ✗ |
| HDA×L1 | 2019 | C3 | 0.750 ✗ | ✗ | +173.0% ✗ | 0.986 ✗ |
| HDA×L1 | 2022 | C4 | 0.385 ✗ | ✓ | +79.7% ✗ | 0.932 ✓ |
| HDA×L2 | 2018 | C0x | 0.951 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2019 | C0x | 0.931 ✓ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L2 | 2022 | C0x | 0.833 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| HDA×L3 | 2018 | C1 | 0.652 ✗ | ✗ | +13.4% ✓ | 0.902 ✓ |
| HDA×L3 | 2019 | C2a | 1.000 ✗ | ✓ | +inf% ✗ | 0.838 ✓ |
| HDA×L3 | 2022 | C2b | 0.958 ✗ | ✗ | +1.3% ✓ | 0.868 ✓ |
| H1H×L1 | 2018 | C3 | 0.860 ✓ | ✓ | +109.7% ✗ | 0.920 ✓ |
| H1H×L1 | 2019 | C0x | 0.431 ✗ | ✓ | +75.0% ✗ | 0.903 ✓ |
| H1H×L1 | 2022 | C4 | 0.396 ✗ | ✗ | +37.5% ✗ | 0.818 ✓ |
| H1H×L2 | 2018 | C0x | 0.951 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2019 | C0x | 0.931 ✓ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L2 | 2022 | C0x | 0.833 ✗ | ✓ | +0.0% ✓ | 1.000 ✗ |
| H1H×L3 | 2018 | C1 | 0.652 ✗ | ✗ | +13.4% ✓ | 0.902 ✓ |
| H1H×L3 | 2019 | C3 | 1.000 ✗ | ✓ | +25.3% ✓ | 0.875 ✓ |
| H1H×L3 | 2022 | C3 | 0.885 ✓ | ✓ | +inf% ✗ | 0.865 ✓ |

Cell verdicts (a≥2/3, b≥2/3, all c, all d): HDA×L1: no; HDA×L2: no; HDA×L3: no; H1H×L1: no; H1H×L2: no; H1H×L3: no

## J3 — retrospective LOEO transfer minus chronological (cov90 gap, pp)

Positive = retrospective event-pooling flatters the calibrator relative to what chronological calibration delivered. C3: no LOEO variant (online method) → n/a. C4 LOEO is skipped for the H1H×L1 cell (mixed 7/15 quantile grids across eras).

| horizon | learner | calibrator | 2018 | 2019 | 2022 | mean |
|---|---|---|---|---|---|---|
| HDA | L1 | C0x | +6.4pp | -4.2pp | +4.2pp | +2.1pp |
| HDA | L1 | C1 | +1.1pp | -4.2pp | +8.3pp | +1.8pp |
| HDA | L1 | C2a | +9.5pp | +1.4pp | -22.9pp | -4.0pp |
| HDA | L1 | C2b | +11.7pp | -6.9pp | -20.8pp | -5.3pp |
| HDA | L1 | C4 | -25.4pp | -37.5pp | +7.3pp | -18.5pp |
| HDA | L2 | C0x | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L2 | C1 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L2 | C2a | +0.0pp | +0.0pp | -16.7pp | -5.6pp |
| HDA | L2 | C2b | +0.0pp | +0.0pp | -16.7pp | -5.6pp |
| HDA | L2 | C4 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| HDA | L3 | C0x | -9.5pp | -1.4pp | +11.5pp | +0.2pp |
| HDA | L3 | C1 | -6.1pp | -1.4pp | +8.3pp | +0.3pp |
| HDA | L3 | C2a | -26.1pp | +0.0pp | +4.2pp | -7.3pp |
| HDA | L3 | C2b | -16.3pp | +0.0pp | +4.2pp | -4.0pp |
| HDA | L3 | C4 | -14.0pp | +0.0pp | +4.2pp | -3.3pp |
| H1H | L1 | C0x | -1.5pp | -1.4pp | +6.2pp | +1.1pp |
| H1H | L1 | C1 | -0.8pp | -1.4pp | +2.1pp | -0.0pp |
| H1H | L1 | C2a | +3.0pp | +5.6pp | -17.7pp | -3.0pp |
| H1H | L1 | C2b | +3.4pp | +1.4pp | -13.5pp | -2.9pp |
| H1H | L1 | C4 | -9.1pp | -29.2pp | +15.6pp | -7.5pp |
| H1H | L2 | C0x | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L2 | C1 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L2 | C2a | +0.0pp | +0.0pp | -16.7pp | -5.6pp |
| H1H | L2 | C2b | +0.0pp | +0.0pp | -16.7pp | -5.6pp |
| H1H | L2 | C4 | +0.0pp | +0.0pp | +0.0pp | +0.0pp |
| H1H | L3 | C0x | -9.5pp | -1.4pp | +11.5pp | +0.2pp |
| H1H | L3 | C1 | -6.1pp | -1.4pp | +8.3pp | +0.3pp |
| H1H | L3 | C2a | -26.1pp | +0.0pp | +4.2pp | -7.3pp |
| H1H | L3 | C2b | -16.3pp | +0.0pp | +4.2pp | -4.0pp |
| H1H | L3 | C4 | -14.0pp | +0.0pp | +4.2pp | -3.3pp |

**J3 reading:** the gaps above ARE the result (no pass/fail in the frozen protocol). Systematically positive gaps = the retrospective transfer evaluation overstates deliverable coverage — the R6 'transfer illusion' configuration if the chronological arm simultaneously fails J2.

## Deviations, operationalizations, hard blockers

- Named-event windows are the PHASE1_AUDIT-registered windows (2014: Jan 6–8, 72h; 2018: Dec 28–Jan 7, 264h; 2022: Dec 23–26, 96h), not the shorthand dates in the original brief; the onset scope follows v2.1 §4 (first min(72h, event length) hours).
- Reproduction arm (L1, 2014, H-1H): native PHASE2A features and the native 7-quantile set per the v2.1 §0 exception, but fitted on D_fit (2010–2012) under the global three-way split (PHASE2A itself trained on 2010–2013); α=0.20/0.05 endpoints use the §0 outward bracketing grid pair.
- Release-mask as-of semantics (v2.1 §8): lag features are nominal-anchored with a ≤48h scan-back to a finite released label. Consequence: 2022 eval rows are valid only from Dec 8 in both arms (168 rows dropped per arm) because lag_168h's nominal source falls in the Jan–Nov 2022 load gap; the Elliott window is fully covered. (The initially briefed '~Dec 2' assumed only a 38h history requirement, which the 168h features override.)
- ACI: the §1 expansion-only rule (Q+ = max(0, Q)) is applied to ACI cutoffs as well; error updates are applied at issuance points using labels with a_i < s, in target-hour order.
- C4 LOEO: gamma search on pooled other-era D_tune uses one pooled sigma0 (approximation, flagged in code); C4 LOEO is not run for H1H×L1 (mixed 7/15 quantile grids). LOEO score pooling normalizes each era's scores by its median CQR score at α=0.10 (v2.1 does not specify cross-era pooling mechanics).
- The 2018/2022 eval spans contribute 2,156 of 2,160 hours (4 boundary hours fall outside the weather span; PHASE2B §5.3 join note).
- J1's replication bar (≥5pp) and J2's frontier interpolation rule are operationalizations, flagged where used. C0x's expansion factor is selected on D_cal (v2.1 does not redefine C0x; it is retained as the FREEZE J2 frontier comparator).
- No component was infeasible: sklearn/LightGBM/scipy were already present in the aideml venv; no data column was missing (EIA-era wind chill is derived by the standard NWS formula, documented in prep_data.py).
- C3 in era 2022: D_cal_train is Oct–Dec 2021, so at the Dec 2022 stream start every seed score lies outside ACI's 2160h clock window (v2.1 §4); the first issued intervals are +inf by the §0 n=0 rule (11 infinite winter intervals at H-1H, 25 at H-DA, identical across learners) until in-stream scores accumulate. This is the frozen rule applied across the declared data gap, not an implementation defect.
- Placebo window 2022_P1 (Dec 1–4) contains zero feature-valid rows for L1/L2 (it sits inside the Dec 1–7 masked-history gap); it contributes NaN per-window rows, is excluded from the placebo macro average, and the pooled placebo scope still has 192 valid hours from P2/P3.
- Runtime engineering (no spec impact): L2 LightGBM defaults were trimmed after timing benchmarks (250 rounds/31 leaves -> 120 rounds/15 leaves, lr 0.1; linear_tree=True, features and quantile grid unchanged — the frozen spec fixes only those). Jobs were run sequentially with capped passive-wait threads after parallel launches collapsed into OpenMP thread thrash on this 4-core VM; every cell was then completed with exit 0.

## Run facts

- `job_2018_H1H_L1.log`: C4 sigma0=976.8 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.02, 0.02), 0.05: (0.02, 0.05), 0.02: (0.02, 0.02)}
- `job_2018_H1H_L1.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_H1H_L2.log`: C4 sigma0=7031.0 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2018_H1H_L2.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_HDA_L1.log`: C4 sigma0=1484.5 MW; gammas={0.2: (0.02, 0.0), 0.1: (0.05, 0.05), 0.05: (0.1, 0.2), 0.02: (0.1, 0.4)}
- `job_2018_HDA_L1.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_HDA_L2.log`: C4 sigma0=7030.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2018_HDA_L2.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_L3.log`: C4 sigma0=2253.6 MW; gammas={0.2: (0.0, 0.4), 0.1: (0.4, 0.1), 0.05: (0.4, 0.05), 0.02: (0.4, 0.4)}
- `job_2018_L3.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2018_L3.log`: C4 sigma0=2253.6 MW; gammas={0.2: (0.0, 0.4), 0.1: (0.4, 0.1), 0.05: (0.4, 0.05), 0.02: (0.4, 0.4)}
- `job_2018_L3.log`: first valid eval row: 2017-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_H1H_L1.log`: C4 sigma0=1059.0 MW; gammas={0.2: (0.1, 0.0), 0.1: (0.1, 0.0), 0.05: (0.1, 0.0), 0.02: (0.05, 0.0)}
- `job_2019_H1H_L1.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_H1H_L2.log`: C4 sigma0=7545.8 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2019_H1H_L2.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_HDA_L1.log`: C4 sigma0=1518.1 MW; gammas={0.2: (0.05, 0.0), 0.1: (0.05, 0.0), 0.05: (0.05, 0.0), 0.02: (0.05, 0.0)}
- `job_2019_HDA_L1.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_HDA_L2.log`: C4 sigma0=7547.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2019_HDA_L2.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_L3.log`: C4 sigma0=2469.1 MW; gammas={0.2: (0.0, 0.4), 0.1: (0.4, 0.4), 0.05: (0.4, 0.4), 0.02: (0.4, 0.4)}
- `job_2019_L3.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2019_L3.log`: C4 sigma0=2469.1 MW; gammas={0.2: (0.0, 0.4), 0.1: (0.4, 0.4), 0.05: (0.4, 0.4), 0.02: (0.4, 0.4)}
- `job_2019_L3.log`: first valid eval row: 2018-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2022_H1H_L1.log`: C4 sigma0=1110.5 MW; gammas={0.2: (0.0, 0.05), 0.1: (0.0, 0.0), 0.05: (0.0, 0.02), 0.02: (0.0, 0.2)}
- `job_2022_H1H_L1.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_H1H_L2.log`: C4 sigma0=7527.5 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_H1H_L2.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_HDA_L1.log`: C4 sigma0=1920.8 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.02), 0.02: (0.0, 0.05)}
- `job_2022_HDA_L1.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_HDA_L2.log`: C4 sigma0=7527.7 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_HDA_L2.log`: first valid eval row: 2022-12-07 23:00:00-05:00 (1988 of 2156 eval rows)
- `job_2022_L3.log`: C4 sigma0=2480.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_L3.log`: first valid eval row: 2022-11-30 23:00:00-05:00 (2156 of 2156 eval rows)
- `job_2022_L3.log`: C4 sigma0=2480.4 MW; gammas={0.2: (0.0, 0.0), 0.1: (0.0, 0.0), 0.05: (0.0, 0.0), 0.02: (0.0, 0.0)}
- `job_2022_L3.log`: first valid eval row: 2022-11-30 23:00:00-05:00 (2156 of 2156 eval rows)

