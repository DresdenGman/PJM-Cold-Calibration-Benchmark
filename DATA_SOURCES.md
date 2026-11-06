# Data sources and rebuild instructions

Every input to this benchmark comes from a public source. This document
states, for each dataset, where it comes from, what was computed from it,
what is redistributed in this repository, and how to rebuild the rest.

## 1. 2018 / 2022 eras — EIA-930 load (redistributed, derived)

- **Source**: U.S. Energy Information Administration, Form EIA-930
  "Hourly Electric Grid Monitor" — the semi-annual `EIA930_BALANCE_*.csv`
  files (https://www.eia.gov/electricity/gridmonitor/), balancing
  authority = PJM.
- **Rebuild**: download the BALANCE files covering Jul 2015 – Feb 2023
  into `data/events/_raw_eia930/` (not redistributed; ~460 MB), then run
  `code/build_data_events.py` (event windows) and
  `code/build_data_spans.py all` (training spans and Dec–Feb evaluation
  windows). The builders filter the PJM rows and emit hourly series on an
  hour-ending UTC grid with columns
  `timestamp_utc_end_of_hour, timestamp_local_end_of_hour, demand_mw,
  demand_forecast_mw, net_generation_mw, total_interchange_mw`.
- **Redistributed**: the derived PJM series in `data/events/load/`
  (event windows, training spans 2016–2017 and 2020–2021, evaluation
  spans).
- **Measurement basis**: EIA-930 demand is not identical to PJM's own
  metered load. Over the evaluation windows it runs +0.73% (2018 era)
  and +0.47% (2022 era) above the metered series; this basis difference
  is carried through the analysis and stated wherever the two bases meet.
  The 2020–2021 training file contains 14 corrupted values; values with
  |demand| > 170,000 MW are set to NaN by rule and logged.

## 2. Weather — ERA5 via the Open-Meteo archive (redistributed, derived)

- **Source**: ERA5 reanalysis (Copernicus Climate Change Service),
  served by the Open-Meteo archive API
  (https://archive-api.open-meteo.com/v1/archive), hourly
  `temperature_2m, dew_point_2m, wind_speed_10m, wind_direction_10m`,
  model `era5`, UTC.
- **Footprint**: 15 grid points spanning 40–42.5°N, −88…−74°W over the
  PJM footprint, combined as an equal-weight mean — the
  `*_footprint_mean.csv` series in `data/events/weather/` (columns
  `timestamp_utc, t2m_c, d2m_c, u10_ms, v10_ms, wind_speed_ms,
  temperature_f, wind_speed_mph, n_points`). The same builders as in §1
  fetch and aggregate them; NWS wind chill is derived downstream in
  `code/prep_data.py` by the standard NWS formula.
- **Note**: ERA5 is retrospective reanalysis. Both forecast horizons in
  the benchmark therefore use *realized* weather; the day-ahead arm is a
  day-ahead information discipline on the load lags with oracle weather,
  and the paper states this wherever the horizon is described.

## 3. 2014 era — PJM metered load + ERA5 (documented, not redistributed)

- **Sources**: PJM's published hourly metered load (PJM Data Miner 2)
  for 2010–2014, and ERA5 weather columns for the same footprint as §2.
- **The assembled table** (`pjm_era5_modeling_table_2010_2014.csv`,
  43,824 strictly hourly rows, 2010–2014) joins the metered load with
  the ERA5-derived columns `temperature_f`, `wind_chill_f`,
  `wind_speed_mph`, `hdh`, `cdh` (heating/cooling degree hours, base
  65 °F) and calendar fields, with `timestamp_utc` / `timestamp_ept`
  stamps. It is **not redistributed** in this repository; rebuild it
  from the two public sources above to this specification and place it
  in `data/era2014/`. `code/prep_data.py` and `code/regen_qr_gbt.py`
  read it from that path.
- Verified reference points for a rebuild: the January 2014 polar-vortex
  peak is 140,510.2 MW at 2014-01-07 18:00 EPT; the 2014 annual peak is
  141,677.9 MW at 2014-06-17 17:00 EPT.

## 4. Official day-ahead forecasts (error benchmark)

- **Source**: PJM's published day-ahead load forecasts (PJM Data
  Miner 2, day-ahead load forecast series), as issued before each event
  day.
- The four event peak errors reported by the benchmark, all
  underestimates: −2,545 MW (−1.81%) for the January 2014 vortex peak,
  −1,909 MW (−1.33%) for 20 February 2015, −5,361 MW (−3.90%) for the
  2017–18 snap peak, and −8,878 MW (−6.59%) for the December 2022
  Elliott peak. 2015 enters the study only through this official-error
  anchor: EIA-930 begins in July 2015 and no 2015 load series is used
  for probabilistic modelling.

## 5. Regenerated 2014 forecasts (redistributed)

`data/regen/` holds the 2014 QR-GBT quantile forecasts regenerated from
the verified modelling table under the recovered original specification
(14 features; `HistGradientBoostingRegressor(loss="quantile")`,
max_iter=300, max_depth=6, seed 42), together with the full metric set.
See `data/regen/README.md` for the specification and the modelling
choices that had to be fixed by decision because the original run did
not document them.
