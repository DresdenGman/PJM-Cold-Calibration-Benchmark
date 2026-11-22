#!/usr/bin/env python3
"""Figure redesign round (figs_v3) — design-first rebuild.

Reads ONLY the canonical CSVs in ../figs_matlab/data/ (md5-verified
against md5sums.txt at startup; aborts on mismatch). Dumps every
plotted coordinate to plotted_coords.json for the independent
verifier. Design brief: FIG_DESIGN_V2.md.
"""
import csv, hashlib, json, sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent)); import _fonts  # noqa: E402,F401
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

# ---- data discipline: verify hashes before anything is plotted
manifest = {}
for line in (DATA / "md5sums.txt").read_text().splitlines():
    parts = line.split()
    if len(parts) == 2:
        manifest[parts[1].lstrip("*")] = parts[0]
for name, want in manifest.items():
    got = hashlib.md5((DATA / name).read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"MD5 MISMATCH {name}: {got} != {want}")
print("md5: all canonical CSVs verified")

def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))

# ---- identity
VERM = "#D55E00"; SKY = "#56B4E9"; BLUE = "#0072B2"; GREEN = "#009E73"
ORANGE = "#E69F00"; PURPLE = "#CC79A7"; GREY = "#7F7F7F"
INK = "#1A1A1A"; PANEL_EC = "#8FB8D8"; TINT = "#FDF1E7"
GRID = "#D9D9D9"
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Liberation Serif"],
    "mathtext.fontset": "custom",
    "mathtext.rm": "Liberation Serif",
    "mathtext.it": "Liberation Serif:italic",
    "mathtext.bf": "Liberation Serif:bold",
    "axes.edgecolor": INK, "axes.linewidth": 0.8,
    "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.labelsize": 9.5, "axes.titlesize": 9.5,
    "legend.fontsize": 8, "figure.dpi": 300, "savefig.dpi": 300,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.55,
    "xtick.bottom": True, "ytick.left": True, "axes.axisbelow": True,
})
COORDS = {}

def save(fig, name):
    fig.savefig(HERE / f"{name}.pdf")
    fig.savefig(HERE / f"{name}.png", dpi=300)
    plt.close(fig)
    print("wrote", name)

def panel_tag(ax, letter, x=0.012, y=0.965):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=10.5,
            fontweight="bold", va="top", ha="left", zorder=20,
            bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="none"))

# ================================================================
# fig1 / fig7 — collapse as slope rows (099 Fig 3 grammar)
# ================================================================
LEARNERS = [("L1", "L1 · Quantile boosting"), ("L2", "L2 · Linear-leaf boosting"),
            ("L3", "L3 · Location–scale")]
EVENTS = [("2014", "2014 Polar Vortex", "a"), ("2018", "2017–18 Cold Snap", "b"),
          ("2022", "2022 Winter Storm Elliott", "c")]

def collapse_rows(csvname, outname):
    data = rows(csvname)
    lut = {(r["era"], r["learner"]): (float(r["event_cov90"]),
                                       float(r["winter_cov90"]),
                                       int(r["n_event"])) for r in data}
    fig = plt.figure(figsize=(7.2, 4.55))
    # label column + plot column share the y layout
    gs = fig.add_gridspec(1, 2, width_ratios=[0.265, 1], wspace=0.02,
                          left=0.015, right=0.985, top=0.90, bottom=0.16)
    lax = fig.add_subplot(gs[0, 0]); ax = fig.add_subplot(gs[0, 1])
    # y layout: 3 groups; header + 3 rows each; unit = 1 row step
    pos = {}   # (era, learner) -> y
    headers = {}
    y = 0.0
    for era, _name, _tag in EVENTS:
        y -= 1.35
        headers[era] = y
        for learner, _lab in LEARNERS:
            y -= 1.0
            pos[(era, learner)] = y
    ymin, ymax = y - 1.08, 0.55
    for a in (lax, ax):
        a.set_ylim(ymin, ymax)
    lax.axis("off")
    ax.set_xlim(-0.06, 1.10)
    ax.set_yticks([])
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", visible=True)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 0.9, 1.0])
    ax.set_xlabel("Coverage of nominal 90% interval (C0, uncalibrated)")
    ax.axvline(0.90, color=INK, ls=(0, (5, 3)), lw=1.0, zorder=1)
    ax.text(0.90, ymax - 0.42, "nominal 0.90", ha="center", va="top",
            fontsize=7.5, zorder=6,
            bbox=dict(boxstyle="square,pad=0.22", fc="white", ec="none"))
    plotted = []
    for era, name, tag in EVENTS:
        hy = headers[era]
        ax.text(0.008, hy, f"({tag})",
                transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=10.5, fontweight="bold", zorder=7,
                bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="none"))
        lax.text(0.97, hy, name, transform=lax.get_yaxis_transform(),
                 ha="right", va="center", fontsize=9.2, fontweight="bold")
        n = lut[(era, "L1")][2]
        lax.text(0.97, hy - 0.52, f"event n = {n} h",
                 transform=lax.get_yaxis_transform(), ha="right",
                 va="center", fontsize=8, color="#404040")
        if era != "2014":
            ax.axhline(hy + 0.92, color=GRID, lw=0.8, zorder=0)
        for learner, lab in LEARNERS:
            ev, wi, _n = lut[(era, learner)]
            ry = pos[(era, learner)]
            lax.text(0.97, ry, lab, transform=lax.get_yaxis_transform(),
                     ha="right", va="center", fontsize=8.5)
            ax.plot([wi, ev], [ry, ry], color="#BFBFBF", lw=2.4,
                    solid_capstyle="round", zorder=2)
            ax.scatter([wi], [ry], s=70, facecolor=SKY, edgecolor=INK,
                       linewidth=0.7, zorder=4)
            ax.scatter([ev], [ry], s=70, facecolor=VERM, edgecolor=INK,
                       linewidth=0.7, zorder=5)
            ax.annotate(f"{wi:.3f}", (wi, ry), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8, zorder=6,
                        bbox=dict(boxstyle="square,pad=0.12", fc="white",
                                  ec="none"))
            ev_dy = 8 if (learner == "L3" and era != "2022") else -11
            ax.annotate(f"{ev:.3f}", (ev, ry), textcoords="offset points",
                        xytext=(0, ev_dy), ha="center", fontsize=8.5,
                        fontweight="bold", color=VERM, zorder=6,
                        bbox=dict(boxstyle="square,pad=0.12", fc="white",
                                  ec="none"))
            plotted.append({"era": era, "learner": learner,
                            "event": ev, "winter": wi})
    handles = [Line2D([], [], marker="o", ls="none", markerfacecolor=VERM,
                      markeredgecolor=INK, markersize=7,
                      label="Event window"),
               Line2D([], [], marker="o", ls="none", markerfacecolor=SKY,
                      markeredgecolor=INK, markersize=7,
                      label="Full evaluation period")]
    ax.legend(handles=handles, loc="upper center",
              bbox_to_anchor=(0.44, -0.135), ncol=2, frameon=False,
              handletextpad=0.1, columnspacing=1.6)
    COORDS[outname] = plotted
    save(fig, outname)

# ================================================================
# fig2 — transfer gap as position on a common scale
# ================================================================
def transfer_gap():
    data = rows("fig2_transfer_series.csv")
    for r in data:  # identity gate: the CSV gap must be loeo - chron
        assert abs(float(r["gap_pp"]) -
                   (float(r["loeo_cov90"]) - float(r["chron_cov90"])) * 100) < 1e-9
    cals = ["C0x", "C1", "C2a", "C2b", "C4"]
    eras = [("2014", VERM, "o", 0.24), ("2018", BLUE, "^", 0.0),
            ("2022", GREEN, "s", -0.24)]
    titles = [("L1", "L1 quantile boosting", "a"), ("L2", "L2 linear-leaf boosting", "b"),
              ("L3", "L3 location–scale", "c")]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.9), sharex=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.86, bottom=0.24,
                        wspace=0.14)
    plotted = []
    for ax, (learner, title, tag) in zip(axes, titles):
        ax.set_title(title, fontsize=9.5, pad=7)
        ax.set_xlim(-32, 57)
        ax.set_ylim(-0.62, 4.62)
        ax.grid(axis="y", visible=False)
        ax.set_xticks([-25, 0, 25, 50])
        ax.axvline(0, color=INK, lw=1.5, zorder=1)
        for gx in (-25, 25, 50):
            ax.axvline(gx, color=GRID, lw=0.55, zorder=0)
        panel_tag(ax, tag)
        for ci, cal in enumerate(cals):
            ry = 4 - ci
            for era, col, mk, dy in eras:
                r = next(r for r in data if r["learner"] == learner
                         and r["calibrator"] == cal and r["era"] == era)
                gap = float(r["gap_pp"])
                ax.scatter([gap], [ry + dy], s=52, marker=mk, facecolor=col,
                           edgecolor="white", linewidth=0.6, zorder=5)
                if abs(gap) >= 15:
                    lab = f"{gap:+.1f} pp".replace("-", "\u2212")
                    if gap >= 40:  # keep the label inside the panel
                        ax.annotate(lab, (gap, ry + dy),
                                    textcoords="offset points",
                                    xytext=(-7, -3.5), ha="right", fontsize=8,
                                    fontweight="bold", zorder=6)
                    else:  # room toward zero / mid-panel
                        ax.annotate(lab, (gap, ry + dy),
                                    textcoords="offset points", xytext=(7, -3.5),
                                    fontsize=8, fontweight="bold", zorder=6)
                plotted.append({"learner": learner, "calibrator": cal,
                                "era": era, "gap_pp": gap})
        ax.tick_params(labelleft=False)
    axes[0].set_yticks(range(4, -1, -1))
    axes[0].set_yticklabels(cals)
    axes[0].tick_params(labelleft=True)
    fig.text(0.53, 0.085, "Transfer gap (pp): LOEO − chronological "
             "event-window coverage", ha="center", fontsize=9.5)
    handles = [Line2D([], [], marker="o", ls="none", markerfacecolor=VERM,
                      markeredgecolor="white", markersize=7, label="2014"),
               Line2D([], [], marker="^", ls="none", markerfacecolor=BLUE,
                      markeredgecolor="white", markersize=7, label="2018"),
               Line2D([], [], marker="s", ls="none", markerfacecolor=GREEN,
                      markeredgecolor="white", markersize=6.5, label="2022")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.005),
               ncol=3, frameon=False, handletextpad=0.1, columnspacing=1.6)
    COORDS["fig2_transfer_illusion"] = plotted
    save(fig, "fig2_transfer_illusion")

# ================================================================
# fig3 — frontier drawn: Pareto polyline + target band + direct labels
# ================================================================
CAL_STYLE = {  # calibrator -> (colour, marker) — the set's established mapping
    "C0": (INK, "o"), "C0x": (GREY, "x"), "C1": (BLUE, "s"),
    "C2a": (VERM, "^"), "C2b": (ORANGE, "v"), "C3": (GREEN, "D"),
    "C4": (PURPLE, "+"),
}
LBL_OFF = {  # (era, calibrator) -> (dx, dy, ha) direct-label offsets (points)
    ("2014", "C0"): (10, 5, "left"), ("2014", "C0x"): (2, 9, "left"),
    ("2014", "C1"): (-6, -15, "right"), ("2014", "C2a"): (0, 9, "center"),
    ("2014", "C2b"): (0, -16, "center"), ("2014", "C3"): (-9, -2, "right"),
    ("2014", "C4"): (4, 9, "left"),
    ("2018", "C0"): (-4, 9, "right"), ("2018", "C1"): (-9, -3, "right"),
    ("2018", "C3"): (0, 10, "center"), ("2018", "C4"): (6, -14, "left"),
    ("2018", "C0x"): (7, 7, "left"),
    ("2022", "C0"): (-4, 9, "right"), ("2022", "C3"): (0, 10, "center"),
    ("2022", "C0x"): (4, -15, "left"),
}
LBL_LEADER = {  # crowded 2022 cluster: label anchor (data coords) + leader
    ("2022", "C1"): (2600, 0.452), ("2022", "C4"): (9050, 0.545),
    ("2022", "C2b"): (13300, 0.352),
}

def frontier():
    data = rows("fig3_frontier_series.csv")
    eras = [("2014", "2014 Vortex", 72, "a"), ("2018", "2017–18 Snap", 264, "b"),
            ("2022", "2022 Elliott", 96, "c")]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.95), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.87, bottom=0.335,
                        wspace=0.12)
    plotted = {"points": [], "frontier": {}}
    for ax, (era, name, n, tag) in zip(axes, eras):
        ax.set_title(f"{name}  ($n$ = {n} h)", fontsize=9.5, pad=7)
        ax.set_xlim(0, 26314); ax.set_ylim(-0.03, 0.95)
        ax.set_xticks([0, 5000, 10000, 15000, 20000, 25000])
        ax.axhspan(0, 0.05, color=SKY, alpha=0.14, zorder=0)
        ax.axhline(0.05, color=INK, ls=(0, (5, 3)), lw=1.0, zorder=3)
        ax.text(350, 0.068, "nominal upper tail 0.05", fontsize=7.5, zorder=6,
                bbox=dict(boxstyle="square,pad=0.2", fc="white", ec="none"))
        panel_tag(ax, tag)
        pts = []
        for r in data:
            if r["era"] != era:
                continue
            cal = r["calibrator"]
            exc = float(r["exceedance_freq"])
            inf = r["is_inf"] == "1"
            hr = None if inf else float(r["upper_headroom"])
            pts.append((cal, hr, exc, inf))
            plotted["points"].append({"era": era, "calibrator": cal,
                                      "headroom": hr, "exceedance": exc,
                                      "is_inf": inf})
        # Pareto frontier through finite non-dominated points
        finite = [(c, h, e) for c, h, e, i in pts if not i]
        nd = [(c, h, e) for c, h, e in finite
              if not any(h2 <= h and e2 <= e and (h2 < h or e2 < e)
                         for c2, h2, e2 in finite if c2 != c)]
        nd.sort(key=lambda t: t[1])
        plotted["frontier"][era] = [c for c, _h, _e in nd]
        ax.plot([h for _c, h, _e in nd], [e for _c, _h, e in nd],
                color="#595959", lw=1.3, zorder=2)
        for cal, hr, exc, inf in pts:
            col, mk = CAL_STYLE[cal]
            if inf:
                ax.scatter([25850], [exc], s=120, marker=">", facecolor=col,
                           edgecolor="white", linewidth=0.6, zorder=5,
                           clip_on=False)
                ax.annotate(cal, (25850, exc), textcoords="offset points",
                            xytext=(-9, -3.5), ha="right", fontsize=8.5,
                            fontweight="bold", color=col, zorder=6)
                continue
            if mk == "x":
                ax.scatter([hr], [exc], s=64, marker="x", color=col,
                           linewidths=1.4, zorder=5)
            elif mk == "+":
                ax.scatter([hr], [exc], s=110, marker="+", color=col,
                           linewidths=1.5, zorder=5)
            else:
                ax.scatter([hr], [exc], s=68, marker=mk, facecolor=col,
                           edgecolor="white", linewidth=0.6, zorder=5)
            # finite points are identified by the shared marker legend
    axes[0].set_ylabel("Upper exceedance frequency")
    fig.text(0.53, 0.235, "Mean upper headroom (MW)", ha="center",
             fontsize=9.5)
    handles = []
    for cal in ["C0", "C0x", "C1", "C2a", "C2b", "C3", "C4"]:
        col, mk = CAL_STYLE[cal]
        if mk in ("x", "+"):
            handles.append(Line2D([], [], marker=mk, ls="none", color=col,
                                  markersize=7, markeredgewidth=1.5, label=cal))
        else:
            handles.append(Line2D([], [], marker=mk, ls="none",
                                  markerfacecolor=col, markeredgecolor="white",
                                  markersize=7, label=cal))
    handles.append(Line2D([], [], color="#595959", lw=1.3,
                          label="Non-dominated frontier"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.085),
               ncol=8, frameon=False, handletextpad=0.15, columnspacing=1.1)
    fig.text(0.53, 0.018,
             "▶ at right edge: infinite mean headroom (infinite intervals in the coldest temperature bin; "
             "2018: C2a and C2b, 84 of 264 h; 2022: C2a, 53 of 96 h)",
             ha="center", fontsize=7.8, family="STIXGeneral")
    COORDS["fig3_frontier"] = plotted
    save(fig, "fig3_frontier")

# ================================================================
# fig4 — reliability curves + derived C1-C0 gap strips
# ================================================================
def reliability():
    data = rows("fig4_reliability_series.csv")
    eras = [("2014", "2014 era (eval $n$ = 8,760 h)", "a"),
            ("2018", "2018 era (eval $n$ = 2,156 h)", "b"),
            ("2022", "2022 era (eval $n$ = 1,988 h)", "c")]
    fig = plt.figure(figsize=(7.2, 4.9))
    gs = fig.add_gridspec(2, 3, height_ratios=[3.3, 1.0], hspace=0.12,
                          wspace=0.13, left=0.075, right=0.985, top=0.90,
                          bottom=0.175)
    plotted = []
    for ci, (era, title, tag) in enumerate(eras):
        ax = fig.add_subplot(gs[0, ci])
        sx = fig.add_subplot(gs[1, ci], sharex=ax)
        rr = sorted([r for r in data if r["era"] == era],
                    key=lambda r: int(r["bin"]))
        xs = [int(r["bin"]) for r in rr]
        c0 = [float(r["C0"]) for r in rr]; c1 = [float(r["C1"]) for r in rr]
        gaps = [(b - a) * 100 for a, b in zip(c0, c1)]
        ax.set_title(title, fontsize=9.5, pad=7)
        ax.set_ylim(-0.02, 1.06); ax.set_xlim(-0.55, 9.55)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 0.9, 1.0])
        ax.tick_params(labelbottom=False)
        ax.axvspan(-0.55, 2.5, color=SKY, alpha=0.12, zorder=0)
        ax.axhline(0.90, color=INK, ls=(0, (5, 3)), lw=1.0, zorder=1)
        ax.plot(xs, c0, color=VERM, lw=1.5, marker="o", markersize=4.2,
                markerfacecolor=VERM, markeredgecolor="white",
                markeredgewidth=0.5, zorder=4)
        ax.plot(xs, c1, color=BLUE, lw=1.5, marker="s", markersize=4.2,
                markerfacecolor=BLUE, markeredgecolor="white",
                markeredgewidth=0.5, zorder=4)
        panel_tag(ax, tag)
        if ci > 0:
            ax.tick_params(labelleft=False)
        # gap strip
        sx.set_ylim(-3, 42); sx.set_yticks([0, 20, 40])
        sx.axhline(0, color=INK, lw=0.9, zorder=1)
        sx.grid(axis="x", visible=False)
        for x, g in zip(xs, gaps):
            sx.plot([x, x], [0, g], color=VERM, lw=1.1, alpha=0.55, zorder=2)
        sx.scatter(xs, gaps, s=26, facecolor=VERM, edgecolor="white",
                   linewidth=0.5, zorder=4)
        if ci > 0:
            sx.tick_params(labelleft=False)
        labels = [f"[{float(r['edge_lo']):.0f}, {float(r['edge_hi']):.0f})"
                  if int(r["bin"]) % 2 == 0 else "" for r in rr]
        sx.set_xticks(xs); sx.set_xticklabels(labels, fontsize=7.5,
                                             rotation=35, ha="right")
        for x, a, b, g in zip(xs, c0, c1, gaps):
            plotted.append({"era": era, "bin": x, "C0": a, "C1": b,
                            "gap_pp": g})
    fig.axes[0].set_ylabel("Coverage of 90% interval")
    fig.axes[1].set_ylabel("C1 − C0 (pp)", fontsize=8.5)
    fig.text(0.53, 0.055, "Temperature decile (°C)", ha="center",
             fontsize=9.5)
    handles = [Line2D([], [], color=VERM, marker="o", markersize=4.5,
                      label="C0"),
               Line2D([], [], color=BLUE, marker="s", markersize=4.5,
                      label="C1"),
               Line2D([], [], color=INK, lw=1.0, ls=(0, (5, 3)),
                      label="nominal 0.90")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.0),
               ncol=3, frameon=False, handletextpad=0.3, columnspacing=1.6)
    COORDS["fig4_temp_reliability"] = plotted
    save(fig, "fig4_temp_reliability")

# ================================================================
# fig5 — operator peak errors (composition KEPT by design verdict)
# ================================================================
def operator():
    data = rows("fig5_operator_series.csv")
    names = {"E2014": "2014 Polar Vortex", "E2015": "2015 Anchor Day",
             "E2018": "2017–18 Cold Snap", "E2022": "2022 Winter Storm Elliott"}
    order = ["E2014", "E2015", "E2018", "E2022"]
    lut = {r["code"]: r for r in data}
    fig, ax = plt.subplots(figsize=(6.4, 3.3))
    fig.subplots_adjust(left=0.27, right=0.975, top=0.94, bottom=0.24)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(-10000, 150); ax.set_ylim(-0.55, 3.68)
    ax.set_xticks([-10000, -5000, 0])
    ax.set_xlabel("PJM day-ahead forecast error at event peak hour "
                  "(MW; forecast − actual)")
    plotted = []
    for i, code in enumerate(order):
        r = lut[code]
        err = float(r["err"]); ape = float(r["ape"])
        y = 3 - i
        if code == "E2015":
            ax.barh(y, err, height=0.62, facecolor="#BFBFBF",
                    edgecolor=INK, linewidth=0.7, hatch="///", zorder=3)
        else:
            ax.barh(y, err, height=0.62, facecolor=VERM, edgecolor="none",
                    zorder=3)
        lab = f"−{abs(round(err)):,} MW (−{ape:.2f}%)".replace("-", "−")
        if code in ("E2014", "E2015"):  # left of the bar end
            ax.annotate(lab, (err, y), textcoords="offset points",
                        xytext=(-5, -3.5), ha="right", fontsize=8.5, zorder=6)
        else:  # above the bar's left end
            ax.text(err, y + 0.40, lab, ha="left", va="bottom",
                    fontsize=8.5, zorder=6)
        plotted.append({"code": code, "err": err, "ape": ape})
    ax.axvline(0, color=INK, lw=1.5, zorder=4)
    ax.set_yticks([3, 2, 1, 0])
    ax.set_yticklabels([names[c] for c in order], fontsize=9)
    fig.text(0.53, 0.045, "Grey hatched bar: 2015 anchor day — operator "
             "record only (no model run).", ha="center", fontsize=8,
             style="italic", color="#404040")
    COORDS["fig5_operator_peaks"] = plotted
    save(fig, "fig5_operator_peaks")

# ================================================================
# fig6 — event window as stacked lanes (051 Fig 11 grammar)
# ================================================================
def event_series():
    import datetime as dt
    data = rows("fig6_event_series.csv")
    ts = [dt.datetime.fromisoformat(r["ts"]) for r in data]
    y = np.array([float(r["y"]) for r in data])
    c0lo = np.array([float(r["C0_lo"]) for r in data])
    c0hi = np.array([float(r["C0_hi"]) for r in data])
    c3lo = np.array([float(r["C3_lo"]) for r in data])
    c3hi = np.array([float(r["C3_hi"]) for r in data])
    miss0 = (y < c0lo) | (y > c0hi)
    miss3 = (y < c3lo) | (y > c3hi)
    cum0 = np.cumsum(~miss0) / np.arange(1, 73)
    cum3 = np.cumsum(~miss3) / np.arange(1, 73)
    peak_i = int(np.argmax(y))
    fig = plt.figure(figsize=(7.2, 5.5))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.0, 2.05, 2.05],
                          hspace=0.16, left=0.085, right=0.985, top=0.965,
                          bottom=0.115)
    sa = fig.add_subplot(gs[0, 0])
    sb = fig.add_subplot(gs[1, 0], sharex=sa)
    sc = fig.add_subplot(gs[2, 0], sharex=sa)
    # (a) cumulative coverage strip
    sa.plot(ts, cum3, color=GREEN, lw=1.6, zorder=4)
    sa.plot(ts, cum0, color=VERM, lw=1.6, zorder=4)
    sa.axhline(0.90, color=INK, ls=(0, (1.5, 2)), lw=1.0, zorder=1)
    sa.text(ts[36], 0.868, "nominal 0.90", ha="center", va="top",
            fontsize=7.5, zorder=6)
    sa.set_ylim(-0.04, 1.06); sa.set_yticks([0, 0.5, 1.0])
    sa.set_ylabel("Cumulative\ncoverage", fontsize=8.5)
    sa.tick_params(labelbottom=False)
    panel_tag(sa, "a")
    sa.annotate(f"C3 (adaptive) · {int((~miss3).sum())} of 72 h", (ts[-1], cum3[-1]),
                textcoords="offset points", xytext=(-4, 7), ha="right",
                fontsize=8.5, color=GREEN, fontweight="bold", zorder=6)
    sa.annotate(f"C0 · {int((~miss0).sum())} of 72 h", (ts[-1], cum0[-1]),
                textcoords="offset points", xytext=(-4, 6), ha="right",
                fontsize=8.5, color=VERM, fontweight="bold", zorder=6)
    for ax, lo, hi, miss, fillc, edgec, tag, title in [
            (sb, c0lo, c0hi, miss0, VERM, VERM, "b", "C0 band (uncalibrated)"),
            (sc, c3lo, c3hi, miss3, GREEN, GREEN, "c", "C3 band (adaptive conformal)")]:
        ax.fill_between(ts, lo, hi, color=fillc, alpha=0.16, zorder=1)
        ax.plot(ts, lo, color=edgec, lw=0.9,
                ls="--" if tag == "c" else "-", zorder=2)
        ax.plot(ts, hi, color=edgec, lw=0.9,
                ls="--" if tag == "c" else "-", zorder=2)
        ax.plot(ts, y, color=INK, lw=1.3, zorder=3)
        ax.scatter(np.array(ts)[miss], y[miss], s=21, facecolor=edgec,
                   edgecolor="white", linewidth=0.4, zorder=5)
        ax.set_ylim(60000, 150000)
        ax.set_yticks([60000, 80000, 100000, 120000, 140000])
        ax.set_title(title, loc="left", fontsize=9, fontweight="bold",
                     pad=3)
        panel_tag(ax, tag)
        if ax is sb:
            ax.tick_params(labelbottom=False)
            ax.set_ylabel("Load (MW)")
            ax.text(ts[peak_i], 146200, "event peak · 140,510 MW",
                    fontsize=8.5, ha="center", va="center", zorder=6)
    sc.text(dt.datetime(2014, 1, 8, 4), 96000,
            "C3 daily batch\nupdate, 8 Jan", fontsize=7.5,
            color="#33691E", va="center", zorder=6)
    sc.set_xticks([dt.datetime(2014, 1, d) for d in (6, 7, 8, 9)])
    sc.set_xticklabels(["6 Jan", "7 Jan", "8 Jan", "9 Jan"])
    handles = [Line2D([], [], color=INK, lw=1.3, label="Actual load"),
               Line2D([], [], marker="o", ls="none", markerfacecolor=VERM,
                      markeredgecolor="white", markersize=5.5,
                      label="Hour outside C0 band"),
               Line2D([], [], marker="o", ls="none", markerfacecolor=GREEN,
                      markeredgecolor="white", markersize=5.5,
                      label="Hour outside C3 band")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.53, 0.005),
               ncol=3, frameon=False, handletextpad=0.3, columnspacing=1.4)
    COORDS["fig6_event_series"] = {
        "miss0_hours": [int(i) for i in np.where(miss0)[0]],
        "miss3_hours": [int(i) for i in np.where(miss3)[0]],
        "cum0_final": float(cum0[-1]), "cum3_final": float(cum3[-1]),
        "peak_mw": float(y[peak_i]), "peak_hour": peak_i,
    }
    save(fig, "fig6_event_series")

# ================================================================
# fig0 — schematic: fork-centred two-tier flow (087 Fig 2 grammar)
# ================================================================
def schematic():
    S = {r["quantity"]: float(r["value"])
         for r in rows("fig0_schematic_scalars.csv")}
    n_ev, n_ch, n_lo = int(S["n_ev"]), int(S["n_ch"]), int(S["n_lo"])
    tick_ch, tick_lo = int(S["tick_ch"]), int(S["tick_lo"])
    fig = plt.figure(figsize=(7.3, 4.95))
    ax = fig.add_axes([0.004, 0.004, 0.992, 0.992])
    ax.set_xlim(0, 146); ax.set_ylim(0, 100); ax.axis("off")
    MID = "·"

    def panel(x0, x1, y0, y1, num, title):
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor="white",
                               edgecolor=PANEL_EC, lw=0.9, zorder=1))
        ax.add_patch(plt.Circle((x0 + 3.4, y1 - 3.6), 2.55, facecolor=INK,
                                edgecolor="none", zorder=3))
        ax.text(x0 + 3.4, y1 - 3.65, str(num), color="white", fontsize=8.5,
                fontweight="bold", ha="center", va="center", zorder=4)
        ax.text(x0 + 7.2, y1 - 3.65, title, fontsize=9.3, fontweight="bold",
                ha="left", va="center", zorder=4)

    def sbox(x0, x1, y0, y1, text, fs=7.8, fc="white", ec=BLUE, tc=INK,
             bold=False):
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=fc,
                               edgecolor=ec, lw=0.9, zorder=2))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, fontsize=fs,
                    color=tc, ha="center", va="center", zorder=4,
                    fontweight="bold" if bold else "normal")

    def arrow(xa, xb, y, c="#595959"):
        ax.annotate("", xy=(xb, y), xytext=(xa, y),
                    arrowprops=dict(arrowstyle="-|>", color=c, lw=1.1,
                                    shrinkA=0, shrinkB=0), zorder=3)

    # ---------- tier 1: four supply stages
    T1Y0, T1Y1 = 64.0, 97.5
    xs1 = [(1.0, 35.4), (37.6, 72.0), (74.2, 108.6), (110.8, 145.2)]
    for (x0, x1), (num, title) in zip(xs1, [(1, "Data"),
                                            (2, "Chronological splits"),
                                            (3, "Forecasters"),
                                            (4, "Calibrators")]):
        panel(x0, x1, T1Y0, T1Y1, num, title)
    for i in range(3):
        arrow(xs1[i][1] + 0.3, xs1[i + 1][0] - 0.3, 80.5)
    # 1 Data: load glyph + two boxes
    gx = np.linspace(4.2, 31.8, 80)
    prof = (np.sin((gx - 4.2) / 27.6 * 2 * np.pi * 1.6) * 0.38
            + np.exp(-((gx - 15.5) ** 2) / 5.5) * 0.95 + 0.55)
    ax.add_patch(Rectangle((3.2, 78.5), 30.0, 9.6, facecolor="white",
                           edgecolor=BLUE, lw=0.9, zorder=2))
    ax.plot(gx, 79.9 + prof * 3.3, color=BLUE, lw=1.1, zorder=3)
    im = int(np.argmax(prof))
    ax.scatter([gx[im]], [79.9 + prof[im] * 3.3], s=26, facecolor=VERM,
               edgecolor="white", linewidth=0.5, zorder=4)
    ax.text(4.8, 80.3, "PJM hourly load", fontsize=7.4, ha="left",
            va="center", zorder=4)
    sbox(3.2, 18.6, 67.2, 76.8, "ERA5 weather\nreanalysis", 7.6)
    sbox(19.4, 33.2, 67.2, 76.8, "Three eras\n2010–14\n2016–18\n2020–22", 7.3)
    # 2 Splits: split bar + full-width rows
    segs = [(0.58, BLUE, "fit"), (0.24, SKY, "tune"), (0.18, GREY, "cal")]
    bx = 40.2
    for frac, col, lab in segs:
        w = frac * 29.4
        ax.add_patch(Rectangle((bx, 84.6), w, 3.7, facecolor=col,
                               edgecolor="white", lw=0.7, zorder=2))
        ax.text(bx + w / 2, 86.45, lab, fontsize=6.4, fontweight="bold",
                color="white", ha="center", va="center", zorder=4)
        bx += w
    sbox(39.8, 70.0, 78.6, 83.8,
         f"$D_{{\\mathrm{{fit}}}}$ {MID} fit base learners", 7.4)
    sbox(39.8, 70.0, 72.8, 78.0,
         f"$D_{{\\mathrm{{tune}}}}$ {MID} set scaling ($\\sigma$, $\\gamma$)", 7.4)
    sbox(39.8, 70.0, 65.2, 71.8,
         f"$D_{{\\mathrm{{cal}}}}$ {MID} conformal cutoffs,\n"
         "last 92 d + pre-event hours,\nappend-only", 7.2)
    # 3 Forecasters: three boxes + horizon fan (original line breaks)
    sbox(76.2, 91.4, 79.8, 88.8,
         f"L1 {MID} QR-GBT\nquantile\ngradient\nboosting", 7.1)
    sbox(92.2, 107.4, 79.8, 88.8, f"L2 {MID} LightGBM\nlinear tree", 7.3)
    sbox(76.2, 91.4, 66.8, 78.8, "L3\nLocation–scale\nstatistical\nmodel", 7.1)
    ax.add_patch(Rectangle((92.2, 66.8), 15.2, 12.0, facecolor=TINT,
                           edgecolor=VERM, lw=0.9, zorder=2))
    fx = np.linspace(94.2, 105.4, 20)
    for dy in (1.5, 0.0, -1.5):
        ax.plot(fx, 76.4 + dy * (fx - 94.2) / 11.2, color=BLUE, lw=0.9,
                zorder=3)
    ax.add_patch(Polygon([[94.2, 76.4], [105.4, 77.9], [105.4, 74.9]],
                         closed=True, facecolor=SKY, alpha=0.3,
                         edgecolor="none", zorder=2))
    ax.text(99.8, 71.5, "H-DA day-ahead\n(primary)\nH-1H one-hour\n(oracle)",
            fontsize=7.0, ha="center", va="center", zorder=4)
    # 4 Calibrators: six rows (C2 row is two lines)
    cal = [(f"C0 {MID} none", 3.3), (f"C0x {MID} proportional expansion", 3.3),
           (f"C1 {MID} global conformal", 3.3),
           (f"C2a/C2b {MID} Mondrian\ntemperature-stratified", 6.6),
           (f"C3 {MID} adaptive conformal (ACI)", 3.3),
           (f"C4 {MID} temperature-excess scaling", 3.3)]
    yy = 90.3
    for c, h in cal:
        ax.add_patch(Rectangle((113.0, yy - h), 30.0, h, facecolor="white",
                               edgecolor=BLUE, lw=0.8, zorder=2))
        ax.text(128.0, yy - h / 2, c, fontsize=7.1, ha="center", va="center",
                zorder=4)
        yy -= h + 0.38
    # return sweep: calibrators -> evaluation (tier 2)
    ax.plot([128.0, 128.0], [61.5, T1Y0], color="#595959", lw=1.1, zorder=3)
    ax.plot([46.0, 128.0], [61.5, 61.5], color="#595959", lw=1.1, zorder=3)
    ax.annotate("", xy=(46.0, 58.2), xytext=(46.0, 61.5),
                arrowprops=dict(arrowstyle="-|>", color="#595959", lw=1.1),
                zorder=3)
    # ---------- tier 2: evaluation fork + judgements
    panel(1.0, 92.0, 4.0, 58.0, 5, "Evaluation")
    ax.text(46.5, 49.6,
            f"Named events {MID} rule-selected cold spells {MID} placebo windows",
            fontsize=7.8, ha="center", va="center", zorder=4)
    def lane(x0, x1, primary, title, sub, ticks, nh, tcol):
        fc = TINT if primary else "white"
        ec = VERM if primary else GREY
        ls_patch = Rectangle((x0, 12.5), x1 - x0, 33.5, facecolor=fc,
                             edgecolor=ec, lw=1.8 if primary else 1.1,
                             zorder=2)
        if not primary:
            ls_patch.set_linestyle("--")
        ax.add_patch(ls_patch)
        ax.text(x0 + 2.2, 42.6, title, fontsize=8.8, ha="left", va="center",
                zorder=4)
        ax.text(x0 + 2.2, 38.6, sub, fontsize=8.0, ha="left", va="center",
                zorder=4, color=VERM if primary else "#303030",
                fontweight="bold" if primary else "normal")
        for i in range(10):
            fc_i = tcol if i < ticks else "white"
            ax.add_patch(Rectangle((x0 + 2.2 + i * 2.55, 26.5), 2.2, 3.4,
                                   facecolor=fc_i, edgecolor=tcol, lw=0.9,
                                   zorder=3))
        ax.text(x0 + 2.2, 20.6, f"C2a {MID} 2014 {MID} {nh} of {n_ev} h",
                fontsize=7.8, ha="left", va="center", zorder=4,
                color="#303030")
    lane(3.2, 45.4, True, "Strictly chronological", "PRIMARY EVIDENCE",
         tick_ch, n_ch, VERM)
    lane(47.6, 89.8, False, "Retrospective LOEO",
         "leave-one-event-out contrast", tick_lo, n_lo, BLUE)
    ax.text(46.5, 8.2, f"same calibrators {MID} two evaluation designs",
            fontsize=7.4, ha="center", va="center", color="#595959", zorder=4)
    panel(94.2, 145.2, 4.0, 58.0, 6, "Pre-registered judgements")
    arrow(92.3, 93.9, 31.0)
    for (lab, y1) in [(f"J1 {MID} Collapse", 47.5), (f"J2 {MID} Repair", 33.0),
                      (f"J3 {MID} Transfer gap", 18.5)]:
        ax.add_patch(Rectangle((96.4, y1 - 11.5), 46.6, 11.5, facecolor=TINT,
                               edgecolor=VERM, lw=0.9, zorder=2))
        ax.text(119.7, y1 - 5.75, lab, fontsize=8.8, ha="center", va="center",
                zorder=4)
    COORDS["fig0_design_schematic"] = {
        "n_ev": n_ev, "n_ch": n_ch, "n_lo": n_lo,
        "tick_ch": tick_ch, "tick_lo": tick_lo}
    save(fig, "fig0_design_schematic")

if __name__ == "__main__":
    collapse_rows("fig1_collapse_series.csv", "fig1_collapse")
    # fig7 (oracle-arm gap) is drawn by build_fig7_gap.py
    transfer_gap()
    frontier()
    reliability()
    operator()
    event_series()
    # fig0 (evaluation design) is drawn by make_fig_design.py; schematic() is the superseded draft
    (HERE / "plotted_coords.json").write_text(json.dumps(COORDS, indent=1))
    print("coords dumped")
