"""Headline figure: L1 day-ahead (H-DA), chronological, nominal 90% intervals.
Event-window vs full-evaluation-period coverage (C0) and the adaptive conformal
recalibration (C3) for the 13 modelled events in two systems (6 original + 7 from
amendment A6). Values read from the tidy results matrices; nothing typed by hand.
Usage: make_fig_headline.py PJM_MATRIX MISO_MATRIX PJM_A6_MATRIX MISO_A6_MATRIX OUT"""
import sys, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import _fonts  # noqa: E402,F401
pjm = pd.concat([pd.read_csv(sys.argv[1]), pd.read_csv(sys.argv[3])])
miso = pd.concat([pd.read_csv(sys.argv[2]), pd.read_csv(sys.argv[4])]); out = sys.argv[5]
def g(df, era, cal, scope):
    r = df[(df.era == int(era)) & (df.horizon == "HDA") & (df.learner == "L1") &
           (df.calibrator == cal) & (df.scope == scope) & (df.eval_mode == "chronological")]
    assert len(r) == 1, (era, cal, scope, len(r))
    return float(r.cov90.iloc[0]), int(r.n_inf90.iloc[0]), int(r.n.iloc[0])
rows = [("PJM", "2014", "event_2014_vortex", "Jan 2014 polar vortex", False),
        ("PJM", "2018", "event_2018_snap", "2017–18 cold snap", False),
        ("PJM", "2019", "event_2019_a6", "Jan 2019 polar vortex", True),
        ("PJM", "2022", "event_2022_elliott", "Dec 2022 Winter Storm Elliott", False),
        ("PJM", "2024", "event_2024_a6", "Jan 2024 cold", True),
        ("PJM", "2025", "event_2025_a6", "Jan 2025 cold", True),
        ("PJM", "2026", "event_2026_a6", "Jan 2026 cold", True),
        ("MISO", "2018", "event_2018_snap", "2017–18 cold snap", False),
        ("MISO", "2019", "event_2019_vortex", "Jan 2019 polar vortex", False),
        ("MISO", "2022", "event_2022_elliott", "Dec 2022 Winter Storm Elliott", False),
        ("MISO", "2024", "event_2024_a6", "Jan 2024 cold", True),
        ("MISO", "2025", "event_2025_a6", "Jan 2025 cold", True),
        ("MISO", "2026", "event_2026_a6", "Jan 2026 cold", True)]
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif"], "mathtext.fontset": "custom",
                     "mathtext.rm": "Liberation Serif", "mathtext.it": "Liberation Serif:italic", "mathtext.bf": "Liberation Serif:bold",
                     "axes.edgecolor": "#1A1A1A", "axes.linewidth": 0.8, "text.color": "#1A1A1A",
                     "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.labelsize": 9.5, "legend.fontsize": 8})
fig, ax = plt.subplots(figsize=(7.2, 6.0))
VER, SKY, GRY = "#D55E00", "#56B4E9", "#BDBDBD"
ys = [14.2 - k for k in range(7)] + [6.0 - k for k in range(6)]
tab = []
for (sysn, era, scope, label, new), y in zip(rows, ys):
    df = pjm if sysn == "PJM" else miso
    ev, _, n = g(df, era, "C0", scope); per, _, _ = g(df, era, "C0", "eval_winter"); c3, inf3, _ = g(df, era, "C3", scope)
    tab.append((sysn, era, n, ev, per, c3, inf3))
    ax.plot([ev, per], [y, y], color=GRY, lw=2.0, zorder=1)
    ax.scatter([per], [y], s=42, color=SKY, edgecolor="#1f3a4d", lw=0.6, zorder=3)
    ax.scatter([ev], [y], s=42, color=VER, edgecolor="#5a2300", lw=0.6, zorder=3)
    ax.scatter([c3], [y], s=30, marker="D", color="white", edgecolor="black", lw=0.9, zorder=4)
    ax.text(min(ev, per) - 0.018, y, f"{ev:.3f}", ha="right", va="center", color=VER, fontsize=7.5, fontweight="bold")
    ax.text(c3, y + 0.30, f"{c3:.3f}" + ("$^{\\dagger}$" if inf3 else ""), ha="center", va="bottom", fontsize=7)
    lab = f"{label} ({n} h)" + ("$^{*}$" if new else "")
    ax.text(-0.02, y, lab, ha="right", va="center", fontsize=8, transform=ax.get_yaxis_transform())
ax.axvline(0.90, color="black", ls=(0, (4, 3)), lw=0.9)
ax.text(0.89, 15.0, "nominal 0.90", ha="right", va="center", fontsize=8)
for yb, name in [(11.2, "PJM"), (3.5, "MISO")]:
    ax.text(-0.53, yb, name, ha="center", va="center", rotation=90, fontsize=10, fontweight="bold",
            transform=ax.get_yaxis_transform())
ax.axhline(7.1, color="#999999", lw=0.6)
ax.set_xlim(0, 1.05); ax.set_ylim(0.3, 15.5); ax.set_yticks([])
ax.set_xticks([0, 0.25, 0.5, 0.75, 0.9, 1.0]); ax.grid(axis="x", color="#D9D9D9", lw=0.55); ax.set_axisbelow(True)
ax.set_xlabel("Coverage of nominal 90% interval (quantile gradient boosting, day-ahead arm)")
h = [plt.Line2D([], [], ls="", marker="o", color=VER, markeredgecolor="#5a2300", label="Event window, uncalibrated"),
     plt.Line2D([], [], ls="", marker="o", color=SKY, markeredgecolor="#1f3a4d", label="Full evaluation period, uncalibrated"),
     plt.Line2D([], [], ls="", marker="D", color="white", markeredgecolor="black", label="Event window, adaptive conformal (C3)")]
ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.36, -0.09), ncol=3, frameon=False, fontsize=7.8, handletextpad=0.3, columnspacing=1.2)
fig.subplots_adjust(left=0.37, right=0.985, top=0.97, bottom=0.14)
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=200)
pd.DataFrame(tab, columns=["system", "era", "event_hours", "event_cov90_C0", "period_cov90_C0", "event_cov90_C3", "event_inf90_C3"]).to_csv(out + "_data.csv", index=False)
print(pd.DataFrame(tab, columns=["system", "era", "n", "ev", "per", "c3", "inf3"]).to_string())
