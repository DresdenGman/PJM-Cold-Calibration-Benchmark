"""A11 populations, fixed before any fitting: for each new system and era, the A6 weather rule
on ERA5 footprint temperature (named event = rule-selected cold spell containing the coldest
evaluation hour), the frozen cold-spell rule and the frozen placebo rule.
Requires the ERA5 frames (build_frames_a9.py SYSTEM ERA era5). Usage: prep_a11.py SYSTEM"""
import os, sys, json
import numpy as np, pandas as pd
import a9_common as A
import exp_common as C
import prep_data as PD
system = sys.argv[1]
out = os.path.join(os.path.dirname(A.HERE), "a11", "populations", system); os.makedirs(out, exist_ok=True)
events, spells, placebos, log = {}, [], [], []
ERAS_RUN = sys.argv[2].split(",") if len(sys.argv) > 2 else A.A11_ERAS
for era in ERAS_RUN:
    df = pd.read_pickle(os.path.join(A.HERE, "frames", f"{system}_{era}_era5.pkl"))
    thr = PD.cold_threshold(df.loc[df["split"] == "train", "t2m_c"])
    sp = PD.cold_spells(df, era, thr); spells.append(sp)
    ev = df[df["split"] == "eval"]; i_min = ev["t2m_c"].idxmin(); t_min = ev.loc[i_min, "ts_local"].tz_localize(None)
    chosen = None
    for _, r in sp.iterrows():
        if pd.Timestamp(r.start_local) <= t_min < pd.Timestamp(r.end_local): chosen = r
    line = f"[{era}] thr={thr:.3f} C; spells={len(sp)}; coldest eval hour {t_min} ({ev.loc[i_min,'t2m_c']:.2f} C)"
    if chosen is None:
        line += " -> no named event"
    else:
        s0 = pd.Timestamp(chosen.start_local).normalize()
        e0 = (pd.Timestamp(chosen.end_local) - pd.Timedelta(minutes=1)).normalize() + pd.Timedelta(days=1)
        events[era] = dict(name=f"event_{era}_{system}", start=s0.strftime("%Y-%m-%d %H:%M"), end=e0.strftime("%Y-%m-%d %H:%M"))
        C.NAMED_EVENTS = dict(events)
        pl = PD.placebo_windows(df, era, thr); placebos.append(pl)
        shed_in = int(df.loc[(df.ts_local.dt.tz_localize(None) >= s0) & (df.ts_local.dt.tz_localize(None) < e0), "shed"].sum())
        line += f" -> event {events[era]['start']}..{events[era]['end']} ({chosen.hours} h spell; flagged shed hours in window: {shed_in}); placebos={len(pl)}"
    print(line, flush=True); log.append(line)
json.dump(events, open(os.path.join(out, "events.json"), "w"), indent=1)
pd.concat(spells).to_csv(os.path.join(out, "cold_spell_events.csv"), index=False)
(pd.concat(placebos) if placebos else pd.DataFrame()).to_csv(os.path.join(out, "placebo_windows.csv"), index=False)
open(os.path.join(out, "prep_log.txt"), "w").write("\n".join(log) + "\n")
w = os.path.join(A.HERE, "work", system); os.makedirs(os.path.join(w, "prepped"), exist_ok=True)
for f in ["cold_spell_events.csv", "placebo_windows.csv"]:
    pd.read_csv(os.path.join(out, f)).to_csv(os.path.join(w, f), index=False)
print("populations saved before any fitting:", out)
