"""A6: score the new events against N1-N3 (PLAN_A6.md). H-DA x L1, chronological."""
import os, glob, json, math
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.dirname(HERE)
OLD = {"PJM": (f"{O}/pjm02/experiments/results/results_matrix.csv",
               {2014: "event_2014_vortex", 2018: "event_2018_snap", 2022: "event_2022_elliott"}),
       "MISO": (f"{O}/miso/experiments/results/results_matrix.csv",
                {2018: "event_2018_snap", 2019: "event_2019_vortex", 2022: "event_2022_elliott"})}
NEWDIR = {"PJM": f"{HERE}/pjm/experiments", "MISO": f"{HERE}/miso/experiments"}
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4"]
frames, events, newev = {}, {}, {}
for s in ["PJM", "MISO"]:
    old = pd.read_csv(OLD[s][0]); old = old[old.eval_mode == "chronological"]
    new = pd.concat([pd.read_csv(f) for f in glob.glob(f"{NEWDIR[s]}/results/frag_*.csv")])
    new.to_csv(f"{NEWDIR[s]}/results/results_matrix_a6.csv", index=False)
    frames[s] = pd.concat([old, new], ignore_index=True)
    ne = json.load(open(f"{NEWDIR[s]}/events_a6.json"))
    events[s] = dict(OLD[s][1]); events[s].update({int(k): v["name"] for k, v in ne.items()})
    newev[s] = sorted(int(k) for k in ne)

def g(df, era, cal, scope, h="HDA", L="L1"):
    r = df[(df.era == era) & (df.horizon == h) & (df.learner == L) & (df.calibrator == cal) & (df.scope == scope)]
    assert len(r) == 1, (era, cal, scope, len(r)); return r.iloc[0]

rows = []
for s in ["PJM", "MISO"]:
    df = frames[s]; E = events[s]
    delta = {c: {e: g(df, e, "C0", E[e]).winkler90 - g(df, e, c, E[e]).winkler90 for e in E} for c in CALS}
    for e in sorted(E):
        ev, per = g(df, e, "C0", E[e]), g(df, e, "C0", "eval_winter")
        others = [k for k in E if k != e]
        chat = max(CALS, key=lambda c: sum(delta[c][k] for k in others))
        rc = g(df, e, chat, E[e]); wc = g(df, e, chat, "eval_winter"); pl = g(df, e, chat, "placebo")
        winfl = wc.mean_width90 / per.mean_width90 - 1
        rows.append(dict(system=s, era=e, new=e in newev[s], event=E[e], n=int(ev.n), event_cov90=ev.cov90,
                         period_cov90=per.cov90, gap_pp=100 * (per.cov90 - ev.cov90),
                         event_cov98=ev.cov98, c3=g(df, e, "C3", E[e]).cov90, chat=chat, chat_cov90=rc.cov90,
                         width_infl=winfl, placebo=pl.cov90, a=bool(0.85 <= rc.cov90 <= 0.95),
                         c=bool(winfl <= 0.35), d=bool(pl.cov90 <= 0.95)))
R = pd.DataFrame(rows); pd.set_option("display.width", 220)
print(R.round(3).to_string(index=False))
N = R[R.new]
below = int((N.event_cov90 < N.period_cov90).sum()); big = int((N.gap_pp >= 10).sum())
print(f"\nN1: below in {below}/{len(N)} (need >=5), >=10pp in {big}/{len(N)} (need >=4) -> {'PASS' if below >= 5 and big >= 4 else 'FAIL'}")
rep = int((N.a & N.c & N.d).sum())
print(f"N2: repair (a)&(c)&(d) with out-of-event selection in {rep}/{len(N)} new events (pass if <=2) -> {'PASS' if rep <= 2 else 'FAIL'}")
allb = int((R.event_cov90 < R.period_cov90).sum())
# distinct weather events: 2014, 2018, 2019, 2022, 2024, 2025, 2026 -> event counts as below if all its systems are below
wx = R.groupby("era").apply(lambda x: bool((x.event_cov90 < x.period_cov90).all()))
k = int(wx.sum()); n = len(wx)
from math import comb
p = sum(comb(n, j) for j in range(k, n + 1)) / 2 ** n
print(f"N3: all events below in {allb}/{len(R)}; distinct weather events below in all systems {k}/{n}; one-sided sign test p = {p:.4f}")
R.to_csv(f"{HERE}/a6_summary.csv", index=False)
