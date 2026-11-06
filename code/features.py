"""Feature builders.

Native H-1H frame (build_h1h_features): the PHASE2A reproduction spec —
14 features, load lags 1/24/168h and trailing rolling means from realized
loads. Used ONLY by the L1 2014 H-1H reproduction arm (v2.1 §0 exception).

Masked frames (build_masked_features): v2.1 §8 release-mask construction.
A label for hour starting at grid position p becomes available at
a = p + 2 grid steps (hour end + 1h). For a target row with issuance grid
position s_pos, usable labels are those with position <= avail = s_pos - 3.
  - H-1H arm: s_pos = the target row itself (issuance at target hour).
  - H-DA arm: s_pos = issuance instant (target local date - 1 day) 10:00
    local (zoneinfo/DST via the frame's tz-aware local timestamps).
Load-derived features take as-of values under the mask:
  - lag_k: load at nominal position (i - k), capped at avail; if that
    label is missing/NaN, scan back to the most recent finite label,
    at most 48h back, else the feature is NaN (row invalid, counted).
  - rolling_k: mean of finite loads over the trailing k hours ending at
    min(i - 1, avail); NaN if the window holds no finite load.
Calendar and (oracle) weather features are at the target hour.
"""
import numpy as np
import pandas as pd
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

LOAD_FEATURES = ["load_lag_1h", "load_lag_24h", "load_lag_168h",
                 "rolling_mean_24h", "rolling_mean_168h"]
FEATURES_14 = ["hour", "day_of_week", "month", "is_weekend",
               "load_lag_1h", "load_lag_24h", "load_lag_168h",
               "rolling_mean_24h", "rolling_mean_168h",
               "temperature_f", "wind_chill_f", "wind_speed_mph", "hdh", "cdh"]
TZ = ZoneInfo("America/New_York")
ASOF_MAX_BACK = 48              # §8: no available obs within 48h -> invalid


def build_h1h_features(df):
    """Native PHASE2A features (reproduction arm only)."""
    load = df["load"]
    F = pd.DataFrame(index=df.index)
    loc = df["ts_local"]
    F["hour"] = loc.dt.hour
    F["day_of_week"] = loc.dt.dayofweek
    F["month"] = loc.dt.month
    F["is_weekend"] = (F["day_of_week"] >= 5).astype(int)
    F["load_lag_1h"] = load.shift(1)
    F["load_lag_24h"] = load.shift(24)
    F["load_lag_168h"] = load.shift(168)
    F["rolling_mean_24h"] = load.rolling(24).mean().shift(1)
    F["rolling_mean_168h"] = load.rolling(168).mean().shift(1)
    F["temperature_f"] = df["temp_f"]
    F["wind_chill_f"] = df["wind_chill_f"]
    F["wind_speed_mph"] = df["wind_mph"]
    F["hdh"] = df["hdh_f"]
    F["cdh"] = df["cdh_f"]
    return F[FEATURES_14]


def _issuance_positions(df):
    """Grid position of the H-DA issuance instant for every row (or -1)."""
    utc_ns = df["ts_utc"].values.astype("datetime64[ns]").astype(np.int64)
    pos_of = {int(v): i for i, v in enumerate(utc_ns)}
    out = np.full(len(df), -1, dtype=int)
    cache = {}
    for i, d in enumerate(df["ts_local"].dt.date):
        if d not in cache:
            c_local = datetime.combine(d - timedelta(days=1), time(10, 0),
                                       tzinfo=TZ)
            cache[d] = pos_of.get(int(pd.Timestamp(c_local)
                                      .tz_convert("UTC").value), -1)
        out[i] = cache[d]
    return out


def build_masked_features(df, arm):
    """arm in {'H1H', 'HDA'}: §8 release-masked 14-feature frame."""
    n = len(df)
    load = df["load"].values.astype(float)
    finite = np.isfinite(load)
    idx = np.arange(n)
    # last finite load position <= p
    lastfin = np.where(finite, idx, -1)
    np.maximum.accumulate(lastfin, out=lastfin)
    csum = np.concatenate([[0.0], np.cumsum(np.where(finite, load, 0.0))])
    ccnt = np.concatenate([[0], np.cumsum(finite.astype(int))])

    if arm == "H1H":
        s_pos = idx.copy()
    else:
        s_pos = _issuance_positions(df)
    avail = s_pos - 3

    def asof(nominal):
        p0 = np.minimum(nominal, avail)
        out = np.full(n, np.nan)
        ok = p0 >= 0
        src = np.where(ok, lastfin[np.clip(p0, 0, n - 1)], -1)
        good = ok & (src >= 0) & ((p0 - src) <= ASOF_MAX_BACK)
        out[good] = load[src[good]]
        return out

    def rolling(k):
        end = np.minimum(idx - 1, avail)
        start = end - k + 1
        out = np.full(n, np.nan)
        ok = end >= 0
        e = np.clip(end, 0, n - 1)
        s0 = np.clip(start, 0, n - 1)   # partial window at grid start: use
        cnt = ccnt[e + 1] - ccnt[s0]    # the available observations in it
        tot = csum[e + 1] - csum[s0]
        good = ok & (cnt > 0)
        out[good] = tot[good] / cnt[good]
        return out

    F = pd.DataFrame(index=df.index)
    loc = df["ts_local"]
    F["hour"] = loc.dt.hour
    F["day_of_week"] = loc.dt.dayofweek
    F["month"] = loc.dt.month
    F["is_weekend"] = (F["day_of_week"] >= 5).astype(int)
    F["load_lag_1h"] = asof(idx - 1)
    F["load_lag_24h"] = asof(idx - 24)
    F["load_lag_168h"] = asof(idx - 168)
    F["rolling_mean_24h"] = rolling(24)
    F["rolling_mean_168h"] = rolling(168)
    F["temperature_f"] = df["temp_f"]
    F["wind_chill_f"] = df["wind_chill_f"]
    F["wind_speed_mph"] = df["wind_mph"]
    F["hdh"] = df["hdh_f"]
    F["cdh"] = df["cdh_f"]
    return F[FEATURES_14]
