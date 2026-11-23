"""v15 (post hoc): chronological calibrator selection. For each event, the calibrator with the largest summed
Winkler improvement over C0 on EARLIER events of the same system is selected (the first event of each system
has none), and assessed on conditions (a)-(d) with (b) at equal headroom (rev_events.csv)."""
import os
import numpy as np, pandas as pd
import a9_common as A
FD = os.path.join(os.path.dirname(A.HERE), "final_data")
V = pd.read_csv(os.path.join(FD, "rev_events.csv")).set_index(["system", "era"]); RP = pd.read_csv(os.path.join(FD, "rev_repair.csv")).set_index(["system", "era"])
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]; rows = []
for s in ["pjm", "miso", "ercot", "spp", "nyiso", "isone"]:
    ev = A.events(s); eras = sorted(ev, key=int); M = {}
    for e in eras:
        R = pd.read_csv(os.path.join(A.HERE, "results", f"a9_{s}_{e}_L1_gefs.csv")); M[e] = R
    def g(e, c, sc): return M[e][(M[e].calibrator == c) & (M[e].scope == sc)].iloc[0]
    for i, e in enumerate(eras):
        past = eras[:i]
        if not past: rows.append(dict(system=s, era=int(e), chat_past=None)); continue
        nm = ev[e]["name"]
        delta = {c: sum(g(k, "C0", ev[k]["name"]).winkler90 - g(k, c, ev[k]["name"]).winkler90 for k in past) for c in CALS}
        c = max(CALS, key=delta.get)
        r, w, p, w1 = g(e, c, nm), g(e, c, "eval_winter"), g(e, c, "placebo"), g(e, "C1", "eval_winter")
        a = 0.85 <= r.cov90 <= 0.95; cc = w.mean_width90 / w1.mean_width90 <= 1.35; d = p.cov90 <= 0.95; b = bool(V.loc[(s, int(e)), f"b_eq_{c}"])
        rows.append(dict(system=s, era=int(e), chat_past=c, cov=r.cov90, a=a, b=b, c=cc, d=d, repaired=a and b and cc and d, gap_c1=RP.loc[(s, int(e)), "gap_c1"]))
T = pd.DataFrame(rows); T.to_csv(os.path.join(A.HERE, "analysis", "rev_pastsel.csv"), index=False)
t = T.dropna(subset=["chat_past"]); big = t.gap_c1 >= 10
print(f"past-only selection: {len(t)} events with an earlier event; repaired {int(t.repaired.astype(bool).astype(int).sum())}; among gap>=10: {int(t[big].repaired.astype(bool).astype(int).sum())} of {int(big.sum())}")
print(t.chat_past.value_counts().to_dict())
