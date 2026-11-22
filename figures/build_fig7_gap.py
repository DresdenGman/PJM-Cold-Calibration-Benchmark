#!/usr/bin/env python3
"""fig7 redesign (user-approved 2026-11-07): gap-type design.
Plots ONLY the event-minus-winter gap in C0 cov90 on the H-1H arm,
one dot per (event, learner), from the canonical CSV (md5-checked).
Replaces the slope version so fig7 no longer duplicates fig1's form."""
import csv, hashlib, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent)); import _fonts  # noqa: E402,F401
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
manifest = {}
for line in (DATA / "md5sums.txt").read_text().splitlines():
    p = line.split()
    if len(p) == 2:
        manifest[p[1].lstrip("*")] = p[0]
got = hashlib.md5((DATA / "fig7_oracle_series.csv").read_bytes()).hexdigest()
if got != manifest["fig7_oracle_series.csv"]:
    sys.exit("MD5 MISMATCH fig7 csv")
print("md5 ok")

with open(DATA / "fig7_oracle_series.csv", newline="") as f:
    rows = list(csv.DictReader(f))

VERM = "#D55E00"; BLUE = "#0072B2"; GREEN = "#009E73"
INK = "#1A1A1A"; GRID = "#D9D9D9"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Liberation Serif"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Serif",
    "mathtext.it": "Liberation Serif:italic",
    "axes.edgecolor": INK, "axes.linewidth": 0.8,
    "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 8.5, "ytick.labelsize": 9,
    "axes.labelsize": 9.5, "figure.dpi": 300, "savefig.dpi": 300,
})

EVENTS = [("2014", "2014 Polar Vortex", VERM), ("2018", "2017–18 Cold Snap", BLUE),
          ("2022", "2022 Winter Storm Elliott", GREEN)]
LEARNERS = ["L1", "L2", "L3"]

gaps = {}
for r in rows:
    gaps[(r["era"], r["learner"])] = (float(r["winter_cov90"]) - float(r["event_cov90"])) * 100.0
for k, v in sorted(gaps.items()):
    print(k, f"{v:+.2f} pp")

# layout: 9 data rows + 3 group headers, top group = 2014
fig, ax = plt.subplots(figsize=(7.4, 3.9))
y = 0
yticks, ylabels = [], []
for era, name, color in EVENTS:
    n = next(int(float(r["n_event"])) for r in rows if r["era"] == era)
    ax.text(-29, y + 0.62, f"{name}  (event $n$ = {n} h)", fontsize=9.5,
            fontweight="bold", color=INK, va="center", ha="left", zorder=6,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
    for ln in LEARNERS:
        g = gaps[(era, ln)]
        ax.plot([0, g], [y, y], color=color, lw=1.1, alpha=0.55, zorder=2)
        ax.plot([g], [y], marker="o", ms=6.5, color=color, zorder=3,
                markeredgecolor="white", markeredgewidth=0.7)
        lab_x = g + (2.2 if g >= 0 else -2.2)
        ax.text(lab_x, y, f"{g:+.1f}".replace("-", "\u2212"), fontsize=8.5, color=INK,
                va="center", ha="left" if g >= 0 else "right")
        yticks.append(y); ylabels.append(ln)
        y -= 1
    y -= 0.55

ax.axvline(0, color=INK, lw=1.4, zorder=1)
ax.set_yticks(yticks); ax.set_yticklabels(ylabels)
ax.set_xlim(-30, 72); ax.set_ylim(y + 0.45, 1.25)
ax.set_xlabel("Collapse gap (pp): full-period minus event-window coverage of nominal 90% interval (C0), one-hour oracle arm")
ax.grid(axis="x", color=GRID, lw=0.55); ax.set_axisbelow(True)
for s in ["top", "right", "left"]:
    ax.spines[s].set_visible(False)
ax.tick_params(length=0)
fig.tight_layout()
fig.savefig(HERE / "fig7_oracle_collapse.pdf")
fig.savefig(HERE / "fig7_oracle_collapse.png", dpi=300)
print("wrote fig7_oracle_collapse (gap design)")
