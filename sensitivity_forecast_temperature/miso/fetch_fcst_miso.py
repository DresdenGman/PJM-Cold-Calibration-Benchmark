import json, urllib.request, time, sys
import pandas as pd, numpy as np
LATS=[38.5,41.5,44.5]; LONS=[-95.5,-93.0,-90.5,-88.0,-85.5]
PTS=[(a,o) for a in LATS for o in LONS]
lat_s=",".join(str(p[0]) for p in PTS); lon_s=",".join(str(p[1]) for p in PTS)
def get(u):
    for k in range(4):
        try: return json.load(urllib.request.urlopen(u,timeout=120))
        except Exception as e: print('retry',k,str(e)[:80]); time.sleep(10*(k+1))
    raise SystemExit('failed')
for lead in (1,2):
    fr=[]
    for d0,d1 in [("2022-11-28","2022-12-31"),("2023-01-01","2023-03-01")]:
        v=f"temperature_2m_previous_day{lead}"
        r=get("https://previous-runs-api.open-meteo.com/v1/forecast"
              f"?latitude={lat_s}&longitude={lon_s}&start_date={d0}&end_date={d1}&hourly={v}&models=gfs_seamless&timezone=UTC")
        r=r if isinstance(r,list) else [r]
        T=np.array([[np.nan if x is None else x for x in loc['hourly'][v]] for loc in r],float)
        fr.append(pd.DataFrame({'timestamp_utc':pd.to_datetime(r[0]['hourly']['time'],utc=True),'t2m_c':np.nanmean(T,0),'n_points':(~np.isnan(T)).sum(0)}))
        time.sleep(2)
    f=pd.concat(fr).drop_duplicates('timestamp_utc').sort_values('timestamp_utc')
    f.to_csv(f'fcst_gfs_prevday{lead}_miso_footprint_mean.csv',index=False)
    era=pd.read_csv('data_events/weather/w2022_miso.csv'); era['timestamp_utc']=pd.to_datetime(era['timestamp_utc'],utc=True)
    m=f.merge(era[['timestamp_utc','t2m_c']],on='timestamp_utc',suffixes=('_f','_e'))
    m=m[(m.timestamp_utc>='2022-12-01')&(m.timestamp_utc<'2023-03-01')]
    d=m.t2m_c_f-m.t2m_c_e; ev=m[(m.timestamp_utc>='2022-12-23 05:00')&(m.timestamp_utc<'2022-12-27 05:00')]; de=ev.t2m_c_f-ev.t2m_c_e
    print(f"lead {lead}: rows {len(f)} null {int(f.t2m_c.isna().sum())} minpts {int(f.n_points.min())} | eval bias {d.mean():.2f} MAE {d.abs().mean():.2f} | Elliott bias {de.mean():.2f} MAE {de.abs().mean():.2f}")
