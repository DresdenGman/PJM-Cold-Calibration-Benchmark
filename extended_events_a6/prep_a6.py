"""A6 prep (run inside a6/<system>/experiments): build era frames for the new eras with the
frozen era_eia builder, then apply the frozen cold-spell rule, the A6 event rule and the
frozen placebo rule, all before any fitting. Usage: prep_a6.py SYSTEM ERA [ERA ...]"""
import os, sys, json
import numpy as np, pandas as pd
EXP = os.getcwd(); sys.path.insert(0, EXP)
import exp_common as C
import prep_data as PD
from features import build_h1h_features, build_masked_features

system, eras = sys.argv[1], sys.argv[2:]
events, spells_all, placebos_all, log = {}, [], [], []
for era in eras:
    df = PD.era_eia(era, f"train_{era}_{system}_load_eia930.csv", f"eval_{era}_{system}_load_eia930.csv",
                    f"w{era}_{system}.csv")
    thr = PD.cold_threshold(df.loc[df["split"] == "train", "t2m_c"])
    sp = PD.cold_spells(df, era, thr)
    ev = df[df["split"] == "eval"]
    i_min = ev["t2m_c"].idxmin(); t_min = ev.loc[i_min, "ts_local"].tz_localize(None)
    chosen = None
    for _, r in sp.iterrows():
        if pd.Timestamp(r.start_local) <= t_min < pd.Timestamp(r.end_local):
            chosen = r
    line = f"[{era}] thr={thr:.3f} C; spells={len(sp)}; coldest eval hour {t_min} ({ev.loc[i_min,'t2m_c']:.2f} C)"
    if chosen is None:
        line += " -> not inside a rule-selected spell: no named event"
    else:
        s = pd.Timestamp(chosen.start_local).normalize()
        e = (pd.Timestamp(chosen.end_local) - pd.Timedelta(minutes=1)).normalize() + pd.Timedelta(days=1)
        events[era] = dict(name=f"event_{era}_a6", start=s.strftime("%Y-%m-%d %H:%M"), end=e.strftime("%Y-%m-%d %H:%M"))
        line += f" -> event {events[era]} (spell {chosen.spell_id}, {chosen.hours} h)"
    print(line); log.append(line)
    spells_all.append(sp)
    C.NAMED_EVENTS.update(events)
    if era in events:
        pl = PD.placebo_windows(df, era, thr); placebos_all.append(pl)
        print(f"[{era}] placebo windows = {len(pl)}")
    df.to_pickle(os.path.join(EXP, "prepped", f"era{era}.pkl"))
    build_h1h_features(df).to_pickle(os.path.join(EXP, "prepped", f"era{era}_X1.pkl"))
    build_masked_features(df, "H1H").to_pickle(os.path.join(EXP, "prepped", f"era{era}_X1H.pkl"))
    build_masked_features(df, "HDA").to_pickle(os.path.join(EXP, "prepped", f"era{era}_XDA.pkl"))
    for part in ["fit", "tune", "cal", "eval"]:
        m = (df["part"] == part).values
        print(f"[{era}] {part}: rows={int(m.sum())} load NaN={int(df.loc[m,'load'].isna().sum())} T NaN={int(df.loc[m,'t2m_c'].isna().sum())}")
json.dump(events, open(os.path.join(EXP, "events_a6.json"), "w"), indent=1)
pd.concat(spells_all).to_csv(os.path.join(EXP, "cold_spell_events.csv"), index=False)
(pd.concat(placebos_all) if placebos_all else pd.DataFrame()).to_csv(os.path.join(EXP, "placebo_windows.csv"), index=False)
open(os.path.join(EXP, "logs", "prep_a6_log.txt"), "w").write("\n".join(log) + "\n")
print("saved events_a6.json, cold_spell_events.csv, placebo_windows.csv BEFORE any fitting")
