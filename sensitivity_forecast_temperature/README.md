# Amendment A3 — forecast temperature in place of reanalysis (post hoc)

Added after the primary results; not part of the frozen protocol. For the 2022 era of both PJM and
MISO, the temperature of every evaluation hour (Dec 2022 – Feb 2023) is replaced by an archived
GFS day-ahead forecast (Open-Meteo previous-runs archive, `temperature_2m_previous_day1` and
`_previous_day2`, model `gfs_seamless`) averaged over the same 15 footprint points. Wind stays
ERA5 because no wind forecasts are archived for this period. Forecasters, calibration windows,
event, cold-spell and placebo windows are unchanged; derived heating, wind-chill and
thermal-memory features are rebuilt.

| File | Content |
|---|---|
| `fetch_fcst.py` | Fetch PJM-footprint forecasts. (`miso/fetch_fcst_miso.py` for MISO.) |
| `build_fcst_variants.py` | Swap forecast temperature into the 2022 evaluation rows and rebuild features. |
| `rebuild_2022_baseline.py` | Rebuild the 2022 PJM era from the released derived data (reproduces v1.0.0 exactly). |
| `pjm/`, `miso/` | Forecast series and result fragments (`exp_base`/`experiments` = ERA5; `exp_fcst1`/`exp_fcst2` = 1-/2-day lead). |

Result: uncalibrated L1 event cov90 is unchanged (PJM 0.458, MISO 0.281) at both leads.
Limitations: one event, one forecast model, temperature only, no refitting on forecast inputs.
