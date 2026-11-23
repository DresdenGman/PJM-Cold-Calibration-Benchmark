"""All v12 tables from the result files (written to v12/tab_*.tex). Usage: make_tables.py WORKDIR"""
import sys, os, json, glob
import numpy as np, pandas as pd
W = sys.argv[1]; D = f"{W}/final_data"; T = f"{W}/paper12/v12"; R = f"{W}/repo"
sys.path.insert(0, f"{W}/a9"); import a9_common as A
NAME = {2014: "2014 vortex", 2018: "2017--18 snap", 2019: "2019 vortex", 2020: "2019--20", 2021: "2021 Uri", 2022: "2022 Elliott", 2023: "2023 cold", 2024: "2024 cold", 2025: "2025 cold", 2026: "2026 cold"}
SYS = {"pjm": "PJM", "miso": "MISO", "ercot": "ERCOT", "spp": "SPP", "nyiso": "NYISO", "isone": "ISO-NE"}
def nm(s, e):
    if s in ("ercot", "spp", "nyiso", "isone"):          # A11 windows are rule-selected: name them by date
        a = pd.Timestamp(A.events(s)[str(e)]["start"]); lab = f"{a.strftime('%b')} {a.year}"
        if s in ("ercot", "spp") and int(e) == 2021: lab += " (Uri)"
        if a.year == 2022 and a.month == 12: lab += " (Elliott)"
        return lab
    return NAME[int(e)]
def win(s, e):
    ev = A.events(s)[str(e)]; a = pd.Timestamp(ev["start"]); b = pd.Timestamp(ev["end"]) - pd.Timedelta(days=1)
    if a.year != b.year: return f"{a.strftime('%b')} {a.day}, {a.year}--{b.strftime('%b')} {b.day}, {b.year}"
    if a.month != b.month: return f"{a.strftime('%b')} {a.day}--{b.strftime('%b')} {b.day}, {b.year}"
    return f"{a.strftime('%b')} {a.day}--{b.day}, {b.year}"
f3 = lambda x: f"{x:.3f}"
# ---- Table: design factorial (A13), C1 event / period cov90 per event
F = pd.read_csv(f"{D}/a13_events.csv"); rows = []
c = lambda r, k: "--" if pd.isna(getattr(r, f"{k}_ev")) else f"{getattr(r, k + '_ev'):.2f} / {getattr(r, k + '_per'):.2f}"
for r in F.itertuples():
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)} & " + " & ".join(c(r, k) for k in ["SA", "LA", "SW", "LW"]) + " \\\\")
open(f"{T}/tab_design_rows.tex", "w").write("\n".join(rows) + "\n")
# ---- Table: calibrators x 13 events (A9, GEFS, L1)
E = pd.read_csv(f"{D}/a9_events_L1_gefs.csv"); cals = ["C0", "C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
rows = []
for r in E.itertuples():
    cells = []
    for c in cals:
        v = getattr(r, f"ev_{c}"); i = getattr(r, f"inf_{c}")
        cells.append(f"{v:.2f}" + (f"$^{{{i}}}$" if i else ""))
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)} & " + " & ".join(cells) + " \\\\")
open(f"{T}/tab_cal_rows.tex", "w").write("\n".join(rows) + "\n")
# ---- Table: events (13 + 24)
rows = []
for r in E.itertuples():
    src = "report" if (r.system, str(r.era)) in [("pjm", "2014"), ("pjm", "2018"), ("pjm", "2022"), ("miso", "2018"), ("miso", "2019"), ("miso", "2022")] else "rule"
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)} & {win(r.system, r.era)} & {src} \\\\")
A11 = pd.read_csv(f"{D}/a11_events.csv")
for r in A11.itertuples():
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)} & {win(r.system, r.era)} & rule \\\\")
open(f"{T}/tab_events_rows.tex", "w").write("\n".join(rows) + "\n"); open(f"{T}/stab_events_rows.tex", "w").write("\n".join(rows) + "\n")   # Table S1
# ---- Table: A11 per event
rows = [f"{SYS[r.system]} & {nm(r.system, r.era)} & {int(r.n)} & {r.c0_ev:.2f} & {r.c1_ev:.2f} & {r.c1_per:.2f} & ${r.gap_c1:+.1f}$ & {r.chat} {r.chat_cov:.2f} \\\\" for r in A11.itertuples()]
open(f"{T}/tab_a11_rows.tex", "w").write("\n".join(rows) + "\n")
# ---- Table: operator (A12)
O = pd.read_csv(f"{D}/a12_summary.csv")
rows = [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.c1_ev:.2f} & {r.c1_per:.2f} & ${r.gap:+.1f}$ & {r.model_c1_ev:.2f} & {r.chat} {r.chat_cov:.2f} \\\\" for r in O.itertuples()]
open(f"{T}/tab_op_rows.tex", "w").write("\n".join(rows) + "\n")
# ---- Table: shortfall (A9, GEFS, L1): C0, C1, best finite calibrator
OPS = pd.read_csv(f"{D}/ops_a9_gefs.csv"); rows = []; srows = []
for (s, e), g in OPS.groupby(["system", "era"], sort=False):
    g = g.set_index("calibrator")
    fin = g[(g.inf_hours == 0) & (~g.index.isin(["C0", "C1"]))]
    b = fin.sort_values("shortfall_mwh").index[0]
    rows.append(f"{SYS[s]} & {nm(s, e)} & {int(g.loc['C1','exceed_hours'])}/{int(g.loc['C1','hours'])} & {g.loc['C1','max_shortfall_mw']/1000:.1f} & {g.loc['C1','max_shortfall_pct_peak']:.1f} & {g.loc['C1','shortfall_mwh']/1000:.0f} \\\\")
    srows.append(f"{SYS[s]} & {nm(s, e)} & {b} & {g.loc[b,'max_shortfall_mw']/1000:.1f} & {g.loc[b,'shortfall_mwh']/1000:.0f} & {g.loc[b,'extra_headroom_mw']/1000:.1f} \\\\")
order = {("pjm", 2014): 0}
open(f"{T}/tab_ops_rows.tex", "w").write("\n".join(rows) + "\n"); open(f"{T}/stab_ops_rows.tex", "w").write("\n".join(srows) + "\n")
print("tables written")
# ================= supplement tables =================
yn = lambda b: "yes" if b else "no"
def w(name, rows): open(f"{T}/{name}", "w").write("\n".join(rows) + "\n")
E5 = pd.read_csv(f"{D}/a9_events_L1_era5.csv")
w("stab_era5_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.c0_ev:.2f} & {r.c0_per:.2f} & {r.c1_ev:.2f} & {r.c1_per:.2f} & ${r.gap_c1:+.1f}$ & {r.chat} {r.chat_cov:.2f} \\\\" for r in E5.itertuples()])
w("stab_repair_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.chat} & {r.chat_cov:.2f} & {r.chat_wr:.2f} & {r.chat_plac:.2f} & {yn(r.a)} & {yn(r.b)} & {yn(r.c)} & {yn(r.d)} & {r.any_pass if isinstance(r.any_pass, str) else '--'} \\\\" for r in E.itertuples()])
NW = pd.read_csv(f"{D}/a9_null_L1_gefs.csv"); L = pd.read_csv(f"{D}/rev_loeo.csv")   # v13: corrected normaliser
m = NW.merge(L, on=["system", "era"])
g = lambda r, c: f"${getattr(r, 'gap_' + c):+.1f}$" + ("" if getattr(r, "finite_" + c) else "$^{\\infty}$")
w("stab_null_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & {int(r.n_windows)} & {r.pct_C0:.2f} & " + " & ".join(g(r, c) for c in ["C1", "C2a", "C2b", "C4"]) + " \\\\" for r in m.itertuples()])
MC = pd.read_csv(f"{D}/mechanism_L1_gefs.csv")
w("stab_mech_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.mean_err/1000:+.1f} & {r.mean_half/1000:.1f} & ${r.bias_ratio:+.2f}$ & {r.share_above:.2f} & {r.pred_c0_ev:.2f} & {r.c0_ev:.2f} & {r.share_below_p01:.2f} \\\\" for r in MC.itertuples()])
L23 = pd.read_csv(f"{D}/a9_L23_summary.csv"); G = L23[L23.weather == "gefs"]
rows = []
for r in E.itertuples():
    x2 = G[(G.learner == "L2") & (G.system == r.system) & (G.era == r.era)].iloc[0]; x3 = G[(G.learner == "L3") & (G.system == r.system) & (G.era == r.era)].iloc[0]
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.c1_ev:.2f} / {r.c1_per:.2f} & {x2.c1_ev:.2f} / {x2.c1_per:.2f} & {x3.c1_ev:.2f} / {x3.c1_per:.2f} \\\\")
w("stab_learners_rows.tex", rows)
H1 = pd.read_csv(f"{D}/a10_H1.csv"); H2 = pd.read_csv(f"{D}/a10_H2.csv")
rows = []
for (s, e), gg in H1.groupby(["system", "era"], sort=False):
    a_, b_ = gg[gg.cal == "C8a"].iloc[0], gg[gg.cal == "C8b"].iloc[0]
    rows.append(f"{SYS[s]} & {nm(s, e)} & {a_.ev:.2f} & {a_.wr:.2f} & {a_.plac:.2f} & {b_.ev:.2f} & {b_.wr:.2f} & {b_.plac:.2f} \\\\")
w("stab_h1_rows.tex", rows)
w("stab_h2_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & ${r.bias_L1:+.2f}$ & ${r.bias_L1h:+.2f}$ & {r.c1ev_L1:.2f} & {r.c1ev_L1h:.2f} & {r.c1per_L1:.2f} & {r.c1per_L1h:.2f} \\\\" for r in H2.itertuples()])
w("stab_op_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & " + " & ".join(f"{getattr(r, 'ev_' + c):.2f}" for c in ["C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]) + " \\\\" for r in O.itertuples()])
RP = pd.read_csv(f"{D}/rev_repair.csv"); DC = pd.read_csv(f"{D}/rev_decomp.csv")
yn2 = lambda b: "yes" if b else "no"
w("stab_repair38_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & ${r.gap_c1:+.1f}$ & {r.chat} & {r.chat_cov:.2f} & {yn2(r.a)} & {yn2(r.b_eq)} & {yn2(r.c)} & {yn2(r.d)} & {r.ok_chat:.2f} & {r.any_pass_eq if isinstance(r.any_pass_eq, str) else '--'} \\\\" for r in RP.itertuples()])
w("stab_decomp_rows.tex", [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.c1_ev:.2f} & {r.c1_recentred:.2f} & {r.c1_rescaled_only:.2f} & {r.c1_recentred_rescaled:.2f} & {r.c1_per:.2f} & {r.disp_ratio:.2f} & {r.pct_C1:.2f} \\\\" for r in DC.itertuples()])
CLU = pd.read_csv(f"{D}/rev_clusters.csv")
cl = CLU.groupby(["cluster", "cluster_name"]).agg(n=("gap", "size"), gap=("gap", "mean"), systems=("system", lambda x: ", ".join(SYS[v] for v in sorted(set(x), key=list(SYS).index)))).reset_index()
w("stab_clusters_rows.tex", [f"{int(r.cluster)+1} & {r.cluster_name} & {r.systems} & {int(r.n)} & ${r.gap:+.1f}$ \\\\" for r in cl.itertuples()])
TG = pd.read_csv(f"{D}/rev_trigger.csv"); rows = []
for (sy, er), g in TG.groupby(["system", "era"], sort=False):
    g = g.set_index("variant"); f = lambda v, c, fmt="{:.2f}": (fmt.format(g.loc[v, c]) if (v in g.index and bool(g.loc[v, "available"])) else "--")
    rows.append(f"{SYS[sy]} & {nm(sy, er)} & {f('C1','event_cov')} & {f('loeo_all','event_cov')} & {f('loeo_all','width_ratio')} & {f('past_only','event_cov')} & {f('past_only','width_ratio')} & {f('triggered','event_cov')} & {f('triggered','width_ratio')} & {f('triggered','placebo_cov')} & " + ("yes" if ("triggered" in g.index and bool(g.loc["triggered", "available"]) and bool(g.loc["triggered", "repaired"])) else ("--" if not ("triggered" in g.index and bool(g.loc["triggered", "available"])) else "no")) + " \\\\")
w("stab_trigger_rows.tex", rows)
print("supplement tables written")
# ---- v15: base forecasts side by side (L1 vs operator), per system; operator per event; upper tail and recentring
SH = pd.read_csv(f"{D}/rev_shift.csv"); OPA = pd.concat([pd.read_csv(f"{D}/a12_summary.csv"), pd.read_csv(f"{D}/a14_summary.csv")], ignore_index=True)
OPA["brk"] = (OPA.system == "spp") & (OPA.era == 2026); MA = pd.read_csv(f"{D}/rev_mae.csv")
rows = []
for s in ["pjm", "miso", "ercot", "spp", "nyiso", "isone"]:
    l = SH[SH.system == s]; o = OPA[(OPA.system == s) & ~OPA.brk]; m = MA[MA.system == s]
    rows.append(f"{SYS[s]} & {len(l)} & {l.event_cov_C1.mean():.2f} & {l.winter_cov_C1.mean():.2f} & {100*(l.winter_cov_C1-l.event_cov_C1).mean():.1f} & "
                f"{len(o)} & {o.c1_ev.mean():.2f} & {o.c1_per.mean():.2f} & {o.gap.mean():.1f} & {(m.winter_mae_l1/m.winter_mae_op).median():.2f} & {(m.event_mae_l1/m.event_mae_op).median():.2f} \\\\")
w("tab_base_rows.tex", rows)
MA2 = MA.set_index(["system", "era"]); rows = []
for r in OPA.sort_values(["system", "era"], key=lambda c: c.map({s: i for i, s in enumerate(SYS)}) if c.name == "system" else c).itertuples():
    k = (r.system, int(r.era)); mr = MA2.loc[k] if k in MA2.index else None
    ma = "--" if mr is None else f"{mr.event_mae_op/1000:.2f} & {mr.event_mae_l1/1000:.2f}"
    if mr is None: ma = "-- & --"
    rows.append(f"{SYS[r.system]} & {nm(r.system, r.era)}{'$^\\dagger$' if r.brk else ''} & {r.c1_ev:.2f} & {r.c1_per:.2f} & {r.gap:.1f} & {r.chat} & {r.chat_cov:.2f} & {'yes' if r.repaired else 'no'} & {ma} \\\\")
w("stab_op36_rows.tex", rows)
rows = [f"{SYS[r.system]} & {nm(r.system, r.era)} & {r.event_cov_C1:.2f} & {100*r.event_upx_C1:.0f} & {100*r.winter_upx_C1:.1f} & {r.event_cov_C9:.2f} & {100*r.event_upx_C9:.0f} & {r.winter_cov_C9:.2f} & {r.placebo_cov_C9:.2f} \\\\" for r in SH.itertuples()]
w("stab_shift_rows.tex", rows)
