"""v12 figures from the result files. Usage: make_figs.py WORKDIR"""
import sys, os
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.stats import norm
W = sys.argv[1]; D = f"{W}/final_data"; O = f"{W}/paper12/v12/figs"
sys.path.insert(0, f"{W}/paper12"); sys.argv = [sys.argv[0], W]
from make_tables import nm, SYS
EV, WI, INK, MUTED = "#D55E00", "#0072B2", "#1f1f1f", "#8a8a8a"
plt.rcParams.update({"font.family": "serif", "font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK, "pdf.fonttype": 42})
def dots(ax, df, title):
    df = df.assign(_g=df.c1_per - df.c1_ev).sort_values("_g", ascending=False)
    y = np.arange(len(df))[::-1]
    for yi, r in zip(y, df.itertuples()):
        ax.plot([r.c1_ev, r.c1_per], [yi, yi], color="#cfcfcf", lw=1.2, zorder=1)
    ax.scatter(df.c1_per, y, s=30, facecolor="white", edgecolor=WI, lw=1.4, marker="s", zorder=3, label="Evaluation winter")
    ax.scatter(df.c1_ev, y, s=34, color=EV, edgecolor="white", lw=0.8, zorder=4, label="Event window")
    ax.axvline(0.9, ls="--", color=MUTED, lw=0.8); ax.set_yticks(y)
    ax.set_yticklabels([f"{SYS[r.system]} {nm(r.system, r.era)}" for r in df.itertuples()])
    ax.set_xlim(-0.02, 1.02); ax.set_xlabel("C1 coverage of nominal 90% interval"); ax.set_title(title, loc="left", fontsize=9)
    ax.grid(axis="x", color="#ececec", lw=0.6); ax.set_axisbelow(True)
    for yi, r in zip(y, df.itertuples()):
        ax.text(1.03, yi, (lambda v: "0" if abs(v) < 0.5 else f"{v:+.0f}")(100 * (r.c1_per - r.c1_ev)), va="center", ha="left", fontsize=6.5, color=MUTED, transform=ax.get_yaxis_transform())
    ax.text(1.03, len(df) - 0.3, "gap", va="bottom", ha="left", fontsize=6.5, color=MUTED, transform=ax.get_yaxis_transform())
E = pd.read_csv(f"{D}/a9_events_L1_gefs.csv"); A = pd.read_csv(f"{D}/a11_events.csv")
fig, ax = plt.subplots(1, 2, figsize=(7.4, 5.6), gridspec_kw=dict(width_ratios=[1, 1], wspace=1.05))
dots(ax[0], E, "(a) PJM and MISO, 13 events"); dots(ax[1], A, f"(b) Four further systems, {len(A)} events")
ax[0].legend(loc="lower left", frameon=False, fontsize=7.5)
fig.savefig(f"{O}/fig1_headline.pdf", bbox_inches="tight"); plt.close(fig)
# fig3 decomposition (v13)
DC = pd.read_csv(f"{D}/rev_decomp.csv"); dg = DC[DC.gap_c1 >= 10]
fig, ax = plt.subplots(1, 2, figsize=(7.0, 3.2), gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.35))
cols = ["c1_ev", "c1_rescaled_only", "c1_recentred", "c1_recentred_rescaled"]; labs = ["As issued", "Rescaled\nonly", "Recentred\nonly", "Recentred\nand rescaled"]
xs = np.arange(len(cols))
for r in dg.itertuples():
    el = (r.era == 2022 and r.system in ("pjm", "miso")) or (r.era == 2023 and r.system in ("ercot", "spp"))
    ax[0].plot(xs, [getattr(r, c) for c in cols], color=EV if el else "#c9c9c9", lw=1.3 if el else 0.7, zorder=3 if el else 1, alpha=1 if el else 0.9)
ax[0].plot(xs, [dg[c].mean() for c in cols], color=INK, lw=2, marker="o", ms=5, zorder=4, label=f"Mean of {len(dg)} events")
ax[0].axhline(0.9, ls="--", color=MUTED, lw=0.8); ax[0].axhline(dg.c1_per.mean(), ls=":", color=WI, lw=1, label="Mean winter coverage")
ax[0].plot([], [], color=EV, lw=1.3, label="Elliott (Dec 2022)")
ax[0].set_xticks(xs); ax[0].set_xticklabels(labs, fontsize=7.5); ax[0].set_ylim(-0.02, 1.03); ax[0].set_ylabel("C1 event coverage")
ax[0].set_title("(a) Events with a gap of at least 10 pp", loc="left", fontsize=9); ax[0].legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
for s_, mk in [("pjm", "o"), ("miso", "D"), ("ercot", "s"), ("spp", "^"), ("nyiso", "v"), ("isone", "P")]:
    x = DC[DC.system == s_]; ax[1].scatter(x.c1_ev, x.c1_recentred, marker=mk, s=24, color=WI if s_ in ("pjm", "miso") else "#8c8c8c", edgecolor="white", lw=0.6, label=SYS[s_], zorder=3)
ax[1].plot([0, 1], [0, 1], color="#d0d0d0", lw=0.8); ax[1].axhline(0.9, ls="--", color=MUTED, lw=0.7)
ax[1].set_xlim(-0.03, 1.03); ax[1].set_ylim(-0.03, 1.03); ax[1].set_xlabel("C1 event coverage, as issued"); ax[1].set_ylabel("C1 event coverage, recentred")
ax[1].set_title("(b) All 38 events", loc="left", fontsize=9); ax[1].legend(frameon=False, fontsize=6.5, loc="lower right", ncol=2)
for a in ax: a.grid(color="#ececec", lw=0.6); a.set_axisbelow(True)
fig.savefig(f"{O}/fig3_mechanism.pdf", bbox_inches="tight"); plt.close(fig)
# fig4 operator vs model, all six systems (SPP 2026 hollow: reporting break, excluded from pooled results)
Q = pd.concat([pd.read_csv(f"{D}/a12_summary.csv"), pd.read_csv(f"{D}/a14_summary.csv")], ignore_index=True)
PAL = {"pjm": ("#2f6db5", "o"), "miso": ("#e08a2e", "D"), "ercot": ("#c0392b", "s"), "spp": ("#6b8e23", "^"), "nyiso": ("#7b4fa0", "v"), "isone": ("#3a9a9a", "P")}
fig, ax = plt.subplots(figsize=(4.4, 4.0))
for s, (col, mk) in PAL.items():
    x = Q[Q.system == s]; brk = (x.system == "spp") & (x.era == 2026)
    ax.scatter(x[~brk].c1_ev, x[~brk].model_c1_ev, marker=mk, s=34, color=col, edgecolor="white", lw=0.7, zorder=3, label=SYS[s])
    if brk.any(): ax.scatter(x[brk].c1_ev, x[brk].model_c1_ev, marker=mk, s=34, facecolor="none", edgecolor=col, lw=1.0, zorder=3)
ax.plot([0, 1.02], [0, 1.02], color="#d0d0d0", lw=0.8); ax.axvline(0.9, ls="--", color=MUTED, lw=0.7); ax.axhline(0.9, ls="--", color=MUTED, lw=0.7)
ax.set_xlim(-0.02, 1.03); ax.set_ylim(-0.02, 1.03); ax.set_xlabel("C1 event coverage, operator forecast"); ax.set_ylabel("C1 event coverage, L1")
ax.grid(color="#ececec", lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=6, handletextpad=0.2, columnspacing=0.8); fig.savefig(f"{O}/fig4_operator.pdf", bbox_inches="tight"); plt.close(fig)
# fig5 PJM 2014 hourly
z = np.load(f"{D}/tuples_pjm_2014_L1_gefs.npz"); y, q, lo, hi = z["y"] / 1e3, z["q50"] / 1e3, z["C1_lo"] / 1e3, z["C1_hi"] / 1e3
h = np.arange(len(y)); fig, ax = plt.subplots(figsize=(6.6, 3.0))
ax.fill_between(h, lo, hi, color=WI, alpha=0.18, lw=0, label="C1 90% interval")
sh = np.where(y > hi, y - hi, 0); ax.bar(h[sh > 0], sh[sh > 0], bottom=hi[sh > 0], width=0.8, color=EV, alpha=0.55, lw=0, label="Shortfall of upper bound")
ax.plot(h, q, color=WI, lw=1.4, label="Median forecast"); ax.plot(h, y, color=INK, lw=1.6, label="Load")
ax.set_xticks([0, 24, 48, 71]); ax.set_xticklabels(["Jan 6", "Jan 7", "Jan 8", ""]); ax.set_ylabel("GW")
ax.legend(frameon=False, fontsize=7, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12)); ax.grid(axis="y", color="#ececec", lw=0.6); ax.set_axisbelow(True)
fig.savefig(f"{O}/fig5_series.pdf", bbox_inches="tight"); plt.close(fig)
print("figs written")
