import json, urllib.request, time
import pandas as pd, numpy as np
LATS=[40.0,41.25,42.5]; LONS=[-88.0,-84.5,-81.0,-77.5,-74.0]
PTS=[(a,o) for a in LATS for o in LONS]
lat_s=",".join(str(p[0]) for p in PTS); lon_s=",".join(str(p[1]) for p in PTS)
def get(u):
    for k in range(4):
        try: return json.load(urllib.request.urlopen(u,timeout=120))
        except Exception as e:
            print('retry',k,str(e)[:80]); time.sleep(5*(k+1))
    raise SystemExit('failed '+u)
out={}
for lead in (1,2):
    frames=[]
    for d0,d1 in [("2022-11-28","2022-12-31"),("2023-01-01","2023-02-28"),("2023-03-01","2023-03-01")]:
        u=("https://previous-runs-api.open-meteo.com/v1/forecast"
           f"?latitude={lat_s}&longitude={lon_s}&start_date={d0}&end_date={d1}"
           f"&hourly=temperature_2m_previous_day{lead},wind_speed_10m_previous_day{lead}"
           "&models=gfs_seamless&timezone=UTC&wind_speed_unit=ms")
        r=get(u); r=r if isinstance(r,list) else [r]
        T=np.array([[np.nan if v is None else v for v in x['hourly'][f'temperature_2m_previous_day{lead}']] for x in r],float)
        W=np.array([[np.nan if v is None else v for v in x['hourly'][f'wind_speed_10m_previous_day{lead}']] for x in r],float)
        ts=pd.to_datetime(r[0]['hourly']['time'],utc=True)
        frames.append(pd.DataFrame({'timestamp_utc':ts,'t2m_c':np.nanmean(T,axis=0),'wind_speed_ms':np.nanmean(W,axis=0),'n_points':(~np.isnan(T)).sum(axis=0)}))
        time.sleep(1)
    f=pd.concat(frames).drop_duplicates('timestamp_utc').sort_values('timestamp_utc')
    f['temperature_f']=f['t2m_c']*9/5+32; f['wind_speed_mph']=f['wind_speed_ms']*2.23694
    f.to_csv(f'fcst_gfs_prevday{lead}_footprint_mean.csv',index=False)
    print('lead',lead,len(f),'rows; null T',int(f['t2m_c'].isna().sum()),'min n_points',int(f['n_points'].min()))
# compare with ERA5 footprint series on the same hours
era=pd.read_csv('data_events/weather/span2020_2023feb_weather_openmeteo_era5_footprint_mean.csv'); era['timestamp_utc']=pd.to_datetime(era['timestamp_utc'],utc=True)
for lead in (1,2):
    f=pd.read_csv(f'fcst_gfs_prevday{lead}_footprint_mean.csv'); f['timestamp_utc']=pd.to_datetime(f['timestamp_utc'],utc=True)
    m=f.merge(era,on='timestamp_utc',suffixes=('_f','_e')); m=m[(m.timestamp_utc>='2022-12-01')&(m.timestamp_utc<'2023-03-01')]
    dT=m.t2m_c_f-m.t2m_c_e; dW=m.wind_speed_ms_f-m.wind_speed_ms_e
    print(f'lead {lead}: T bias {dT.mean():.2f} C, MAE {dT.abs().mean():.2f}, RMSE {np.sqrt((dT**2).mean()):.2f}; wind bias {dW.mean():.2f} m/s MAE {dW.abs().mean():.2f}; n={len(m)}')
    ev=m[(m.timestamp_utc>='2022-12-23')&(m.timestamp_utc<'2022-12-27')]; d=ev.t2m_c_f-ev.t2m_c_e
    print(f'   Elliott window: T bias {d.mean():.2f}, MAE {d.abs().mean():.2f}, min ERA5 {ev.t2m_c_e.min():.1f} vs fcst {ev.t2m_c_f.min():.1f}')
