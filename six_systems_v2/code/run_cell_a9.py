"""A9: one cell (system, era, learner, weather). Leave-one-winter-out cross-fitted predictions
for prior winters (D_cal = D_tune), final model on the whole training history for the evaluation
winter, then calibrators C0 C0x C1 C2a C2b C3 C4 C6 C7 under the job_fit discipline.
Usage: run_cell_a9.py SYSTEM ERA LEARNER WEATHER [fit-only]"""
import os, sys, time, json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import a9_common as A
system, era, learner, weather = sys.argv[1:5]
import a9_job
C, CAL, JF, F7, JobA9 = a9_job.setup(system)
import learners as LRN
from features import build_masked_features
t0 = time.time()
df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{system}_{era}_{weather}.pkl"))
DESIGN = os.environ.get("DESIGN", "")                   # A13: "" (A9), "D1" long+autumn, "D2" short+winter
# v13 revision: "D1b" long+autumn with the final model fitted on all history (calibration and tuning rows predicted by a
# model fitted without the last 365 training days); "D3" the same rule on the short (D2) history.
if DESIGN in ("D2", "D3"):
    e0 = pd.Timestamp(A.eval_span(system, era)[0]); start = pd.Timestamp(f"{e0.year - 1}-01-01", tz="America/New_York")
    df = df[df["ts_local"] >= start].reset_index(drop=True)
if DESIGN in ("D1", "D1b", "D3"):
    tr = np.where((df["split"] == "train").values)[0]; tloc = df["ts_local"].iloc[tr]
    end = tloc.max().normalize(); cal_start = end - pd.Timedelta(days=91); tune_start = cal_start - pd.Timedelta(days=273)
    part = np.array(df["part"].values, dtype=object)
    part[tr] = np.where(tloc >= cal_start, "cal", np.where(tloc >= tune_start, "tune", "fit"))
    df["part"] = part
df["dT24"] = df["t2m_c"] - df["t2m_c"].shift(24)       # A10: forecast 24 h temperature change
X = build_masked_features(df, "HDA").values
if learner == "L1h":                                    # A10: holiday-aware L1
    from pandas.tseries.holiday import USFederalHolidayCalendar
    dloc = df["ts_local"].dt.tz_localize(None).dt.normalize()
    hol = USFederalHolidayCalendar().holidays(start=dloc.min(), end=dloc.max())
    is_hol = dloc.isin(hol).values.astype(float)
    md = df["ts_local"].dt.month.values * 100 + df["ts_local"].dt.day.values
    season = ((md >= 1224) | (md <= 101)).astype(float)
    X = np.column_stack([X, is_hol, season])
y = df["load"].values; grid = C.QUANTILES
train = (df["split"] == "train").values
winters = sorted(int(w) for w in df.loc[df.part == "cal", "winter"].unique())
def fit_predict(mask, rows):
    if learner == "L3":
        m = LRN.L3Model().fit(df[mask]); return m.predict_quantiles(df.iloc[rows], grid)
    fn = LRN.fit_predict_L1 if learner in ("L1", "L1h") else LRN.fit_predict_L2
    return fn(X[mask], y[mask], X[rows], grid)
pred_path = os.path.join(A.HERE, os.environ.get("PRED_DIR", "preds"), f"{system}_{era}_{learner}_{weather}" + (f"_{DESIGN}" if DESIGN else "") + ".npz")
if os.path.exists(pred_path):
    P_raw = np.load(pred_path)["P_raw"]; log = ["predictions reused"]
else:
    P_raw = np.full((len(df), len(grid)), np.nan)
    if DESIGN == "D1":                                     # original split rule on the long history: fit on D_fit only
        P_raw[:] = fit_predict((df["part"] == "fit").values, np.arange(len(df))); winters = []
    elif DESIGN in ("D1b", "D3"):                          # final model on all history; last 365 training days cross-fitted
        P_raw[:] = fit_predict(train, np.arange(len(df)))
        hold = train & np.isin(df["part"].values, ["tune", "cal"])
        P_raw[hold] = fit_predict(train & ~hold, np.where(hold)[0]); winters = []
    else:
        P_raw[:] = fit_predict(train, np.arange(len(df)))  # final model, all rows
    log = [f"final fit {time.time()-t0:.0f}s; winters={winters}"]
    for w in winters:                                      # leave-one-winter-out cross-fitting
        hold = (df["winter"].values == w) & train
        P_raw[hold] = fit_predict(train & ~hold, np.where(hold)[0])
    log.append(f"cross-fit done {time.time()-t0:.0f}s")
    np.savez_compressed(pred_path, P_raw=P_raw)
if len(sys.argv) > 5 and sys.argv[5] == "fit-only":
    print("fit-only", system, era, learner, weather, round(time.time() - t0), flush=True); sys.exit(0)
job = JobA9(era, "HDA", learner, df, P_raw, grid, log.append)
rows, _ = job.run()
rows.insert(0, "system", system); rows.insert(1, "weather", weather)
tag = "a10" if os.environ.get("A10") else (f"a13{DESIGN}" if DESIGN else "a9")
rows.to_csv(os.path.join(A.HERE, "results", f"{tag}_{system}_{era}_{learner}_{weather}.csv"), index=False)
meta = dict(system=system, era=era, learner=learner, weather=weather, winters=winters, n_train=int(train.sum()),
            c7_fallbacks=F7.FALLBACKS["C7"], seconds=round(time.time() - t0), log=log)
json.dump(meta, open(os.path.join(A.HERE, "results", f"{tag}_{system}_{era}_{learner}_{weather}.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in meta.items() if k != "log"}), flush=True)
