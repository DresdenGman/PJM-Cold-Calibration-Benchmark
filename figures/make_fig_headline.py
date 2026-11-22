"""Headline figure: L1 day-ahead (H-DA), chronological, nominal 90% intervals.
Event-window vs full-evaluation-period coverage (C0) and the adaptive conformal
recalibration (C3) for six events in two systems. Values read from the
tidy results matrices; nothing typed by hand."""
import sys, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import _fonts  # noqa: E402,F401  (Liberation Serif if available)
pjm = pd.read_csv(sys.argv[1]); miso = pd.read_csv(sys.argv[2]); out = sys.argv[3]
def g(df, era, cal, scope):
    r = df[(df.era == int(era)) & (df.horizon == "HDA") & (df.learner == "L1") &
           (df.calibrator == cal) & (df.scope == scope) & (df.eval_mode == "chronological")]
    assert len(r) == 1, (era, cal, scope, len(r))
    return float(r.cov90.iloc[0]), int(r.n_inf90.iloc[0])
rows = [("PJM", "2014", "event_2014_vortex", "2014 polar vortex (72 h)"),
        ("PJM", "2018", "event_2018_snap", "2017–18 cold snap (264 h)"),
        ("PJM", "2022", "event_2022_elliott", "2022 Winter Storm Elliott (96 h)"),
        ("MISO", "2018", "event_2018_snap", "2017–18 cold snap (264 h)"),
        ("MISO", "2019", "event_2019_vortex", "2019 polar vortex (72 h)"),
        ("MISO", "2022", "event_2022_elliott", "2022 Winter Storm Elliott (96 h)")]
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif"], "mathtext.fontset": "custom",
                     "mathtext.rm": "Liberation Serif", "mathtext.it": "Liberation Serif:italic", "mathtext.bf": "Liberation Serif:bold",
                     "axes.edgecolor": "#1A1A1A", "axes.linewidth": 0.8, "text.color": "#1A1A1A",
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.labelsize": 9.5, "legend.fontsize": 8})
fig, ax = plt.subplots(figsize=(7.2, 3.9))
VER, SKY, GRY = "#D55E00", "#56B4E9", "#BDBDBD"
ys = [6.4, 5.4, 4.4, 2.6, 1.6, 0.6]
tab = []
for (sysn, era, scope, label), y in zip(rows, ys):
    df = pjm if sysn == "PJM" else miso
    ev, _ = g(df, era, "C0", scope); per, _ = g(df, era, "C0", "eval_winter"); c3, inf3 = g(df, era, "C3", scope)
    tab.append((sysn, era, ev, per, c3, inf3))
    ax.plot([ev, per], [y, y], color=GRY, lw=2.2, zorder=1)
    ax.scatter([per], [y], s=55, color=SKY, edgecolor="#1f3a4d", lw=0.6, zorder=3)
    ax.scatter([ev], [y], s=55, color=VER, edgecolor="#5a2300", lw=0.6, zorder=3)
    ax.scatter([c3], [y], s=40, marker="D", color="white", edgecolor="black", lw=0.9, zorder=4)
    ax.text(ev - 0.012, y - 0.30, f"{ev:.3f}", ha="center", va="top", color=VER, fontsize=8, fontweight="bold")
    ax.text(per, y + 0.22, f"{per:.3f}", ha="center", va="bottom", color="#1f3a4d", fontsize=8)
    ax.text(c3, y + 0.22, f"{c3:.3f}" + ("$^{\\dagger}$" if inf3 else ""), ha="center", va="bottom", fontsize=8)
    ax.text(-0.02, y, label, ha="right", va="center", fontsize=8.5, transform=ax.get_yaxis_transform())
ax.axvline(0.90, color="black", ls=(0, (4, 3)), lw=0.9)
ax.text(0.89, 6.95, "nominal 0.90", ha="right", va="center", fontsize=8)
for yb, name in [(5.4, "PJM"), (1.6, "MISO")]:
    ax.text(-0.42, yb, name, ha="center", va="center", rotation=90, fontsize=10, fontweight="bold",
            transform=ax.get_yaxis_transform())
ax.axhline(3.5, color="#999999", lw=0.6)
ax.set_xlim(0, 1.0); ax.set_ylim(0, 7.4); ax.set_yticks([])
ax.set_xticks([0, 0.25, 0.5, 0.75, 0.9, 1.0]); ax.grid(axis="x", color="#D9D9D9", lw=0.55); ax.set_axisbelow(True)
ax.set_xlabel("Coverage of nominal 90% interval (quantile gradient boosting, day-ahead arm)")
h = [plt.Line2D([], [], ls="", marker="o", color=VER, markeredgecolor="#5a2300", label="Event window, uncalibrated"),
     plt.Line2D([], [], ls="", marker="o", color=SKY, markeredgecolor="#1f3a4d", label="Full evaluation period, uncalibrated"),
     plt.Line2D([], [], ls="", marker="D", color="white", markeredgecolor="black", label="Event window, adaptive conformal (C3)")]
ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.42, -0.16), ncol=3, frameon=False, fontsize=7.8, handletextpad=0.3, columnspacing=1.2)
fig.subplots_adjust(left=0.30, right=0.98, top=0.95, bottom=0.22)
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=200)
pd.DataFrame(tab, columns=["system", "era", "event_cov90_C0", "period_cov90_C0", "event_cov90_C3", "event_inf90_C3"]).to_csv(out + "_data.csv", index=False)
print(pd.DataFrame(tab, columns=["system", "era", "ev", "per", "c3", "inf3"]).to_string())
