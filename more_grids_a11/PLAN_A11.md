# A11: four further balancing authorities

Written 2026-11-22 and pushed before any A11 load, weather or forecast data were downloaded
for these systems.

## Systems and footprints (15 points each: 3 latitudes x 5 longitudes)
- ERCOT (EIA-930 BA `ERCO`): lat 29.5, 31.0, 32.5; lon -98.5, -97.5, -96.5, -95.5, -94.5.
- SPP (`SWPP`): lat 35.5, 37.5, 39.5; lon -99.5, -98.0, -96.5, -95.0, -93.5.
- NYISO (`NYIS`): lat 40.75, 42.0, 43.0; lon -79.0, -77.0, -75.5, -74.5, -73.75.
- ISO-NE (`ISNE`): lat 41.5, 42.5, 43.5; lon -73.0, -72.0, -71.0, -70.5, -70.0.

## Design
The A9 design (long histories from 2015-07-01, leave-one-winter-out cross-fitted calibration
on prior winters, GEFS day-ahead control forecasts at the footprint points, day-ahead arm),
learner L1 only, calibrators C0, C0x, C1, C2a, C2b, C3, C4, C6, C7. Evaluation winters
2017-18 to 2025-26 (eras named by the January year, 2018–2026). In each winter the named
event is the A6 weather rule's cold spell containing the coldest footprint hour; cold spells
and placebo windows follow the frozen rules. Winters with no qualifying spell have no event.

## Load shedding
All hours from 14 to 20 February 2021 (local dates) are flagged as affected by firm load
shedding for ERCOT, SPP and MISO, a window that covers the days of firm load shed documented
in the FERC-NERC-Regional Entity staff report on the February 2021 cold weather outages. In
the primary analysis these hours are excluded from fitting, calibration and scoring. A
secondary analysis treats them as censored: true demand is at least the recorded load. A
flagged hour is certainly uncovered when the recorded load exceeds the upper endpoint and is
undetermined otherwise (it is never certainly covered). Event coverage is then reported as an
interval: the lower bound counts every undetermined flagged hour as uncovered, the upper bound
counts it as covered.

## Pre-specified criteria (L1)
- K1: across all A11 events, C1 event cov90 is at least 10 pp below C1 full-period cov90 in at
  least half of them.
- K2: the out-of-event-selected calibrator (selection over the other events of the same system)
  meets repair conditions (a)–(d) in at most a third of the events.
- K3: pooled over the 13 A9 events and the A11 events, the share of events in which no
  calibrator meets (a)–(d) is reported, with the distinct weather events listed.
All results are reported whatever the outcome.
