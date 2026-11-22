import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep_data as P
from features import build_h1h_features, build_masked_features
EXP = os.path.dirname(os.path.abspath(__file__))
df = P.era_eia("2022", "train_2020_2021_pjm_load_eia930.csv",
               "eval_2022dec_2023feb_pjm_load_eia930.csv",
               "span2020_2023feb_weather_openmeteo_era5_footprint_mean.csv")
os.makedirs(os.path.join(EXP, "prepped"), exist_ok=True)
df.to_pickle(os.path.join(EXP, "prepped", "era2022.pkl"))
build_h1h_features(df).to_pickle(os.path.join(EXP, "prepped", "era2022_X1.pkl"))
build_masked_features(df, "H1H").to_pickle(os.path.join(EXP, "prepped", "era2022_X1H.pkl"))
build_masked_features(df, "HDA").to_pickle(os.path.join(EXP, "prepped", "era2022_XDA.pkl"))
print(df.shape, df["part"].value_counts().to_dict(), df["split"].value_counts().to_dict())
