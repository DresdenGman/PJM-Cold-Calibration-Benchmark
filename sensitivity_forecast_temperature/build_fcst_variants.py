"""Swap forecast temperature into the EVAL rows of the 2022 frame, rebuild the
derived weather columns, thermal memory and release-masked features, then
job_fit.py is run unchanged. Wind stays ERA5 (no wind forecasts in the archive
for this period). Run from a copy of the experiments directory.
Usage: python3 build_fcst_variants.py <experiments_dir_copy> <lead 1|2> <fcst_csv>
"""
import os, sys, numpy as np, pandas as pd
d, lead, fcst = sys.argv[1], int(sys.argv[2]), sys.argv[3]
sys.path.insert(0, d)
import prep_data as P
from features import build_h1h_features, build_masked_features
df = pd.read_pickle(f"{d}/prepped/era2022.pkl")
f = pd.read_csv(fcst); f['timestamp_utc'] = pd.to_datetime(f['timestamp_utc'], utc=True)
f = f.set_index('timestamp_utc')
ev = (df['split'] == 'eval').values
newT = f['t2m_c'].reindex(df.loc[ev, 'ts_utc']).values
assert np.isfinite(newT).all()
df.loc[ev, 't2m_c'] = newT
df.loc[ev, 'temp_f'] = newT * 9 / 5 + 32
df['wind_chill_f'] = P.nws_wind_chill_f(df['temp_f'], df['wind_mph'])
df['hdh_f'] = np.clip(65.0 - df['temp_f'], 0.0, None)
df['cdh_f'] = np.clip(df['temp_f'] - 65.0, 0.0, None)
df = df.drop(columns=['hdh_c', 'mem_c', 'n_missing_T', 'era', 'part'])
df = P.finalize(df, "2022")
df.to_pickle(f"{d}/prepped/era2022.pkl")
build_h1h_features(df).to_pickle(f"{d}/prepped/era2022_X1.pkl")
build_masked_features(df, "H1H").to_pickle(f"{d}/prepped/era2022_X1H.pkl")
build_masked_features(df, "HDA").to_pickle(f"{d}/prepped/era2022_XDA.pkl")
print("swapped", int(ev.sum()), "eval rows with forecast temperature")
