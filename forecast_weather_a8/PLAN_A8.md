# A8: the benchmark with forecast weather throughout

Written 2026-11-22 and pushed before any forecast-weather data were downloaded.

## Design
Every row of every era (fit, tune, cal and evaluation) gets weather from a day-ahead forecast
instead of same-hour reanalysis: for target local date d, the 00 UTC run of local date d-1,
forecast hours 24–54, linearly interpolated to each hour, bilinearly interpolated to the 15
footprint points and averaged. Variables: 2 m temperature and 10 m wind (u, v); all derived
features (Fahrenheit temperature, wind chill, heating and cooling degree hours, thermal memory)
are rebuilt from them. Load features and their release masks are unchanged. Learners L1–L3 are
refitted on the H-DA arm only (the one-hour oracle arm is not repeated). Calibrators C0–C4 and
C5 (ensemble spread, as in A5) are applied unchanged.

## Sources (fixed in advance)
- 2000–2019: GEFSv12 reforecast on AWS (`noaa-gefs-retrospective`), control member for the
  weather features; control plus four perturbed members (5 in total) for the C5 spread.
- 2020-01-01 to 2020-09-22: operational GEFS v11 (1.0 degree), control member; no C5 spread
  needed in this span (it is fit-only).
- From 2020-09-23: operational GEFS v12 (0.5 degree), control member; all 31 members for the
  C5 spread.
Because member counts differ (5 in reforecast eras, 21 or 31 in operational eras), C5 spread
is compared only within an era.

## Scope
All eras with named events: PJM 2014, 2018, 2019, 2022, 2024–2026; MISO 2018, 2019, 2022,
2024–2026 (the A6 eras only if A6 data are built).

## Pre-specified criteria (L1)
- F1, collapse: event cov90 below full-period cov90 in at least 2/3 of the events.
- F2, repair: as N2 in A6, at most 1/3 of events meet (a), (c) and (d) with the
  out-of-event-selected calibrator.
- F3, ensemble spread with forecast weather: C5 meets (a) and (c) in at least half the events
  it covers, with (d) in all.
Differences from the reanalysis benchmark are reported descriptively.
