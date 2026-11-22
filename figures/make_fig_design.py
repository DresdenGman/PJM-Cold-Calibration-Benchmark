"""Figure 2 (evaluation design), vector diagram drawn with matplotlib at Elsevier full width (190 mm).
Replaces the earlier raster schematic. Counts shown are from the results matrices:
C2a, PJM 2014 vortex, day-ahead L1: chronological cov90 0.306 (22 of 72 h), LOEO 0.764 (55 of 72 h)."""
import sys, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__))); import _fonts  # noqa: E402,F401  (Liberation Serif if available)
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif"]})
VER, SKY, GRY, DARK, MID = "#D55E00", "#56B4E9", "#8C8C8C", "#222222", "#555555"
W, H = 190, 86
fig = plt.figure(figsize=(W / 25.4, H / 25.4))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
T, D = 7.0, 6.3   # title / detail font sizes (pt)

def box(x, y, w, h, fc="white", ec=DARK, lw=0.7, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.0", fc=fc, ec=ec, lw=lw, ls=ls))
def t(x, y, s, size=D, weight="normal", color=DARK, ha="center"):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va="center", linespacing=1.15)
def arrow(x0, y0, x1, y1, color=GRY, lw=0.8, ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=6, color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0))
def card(x, y, w, h, title, lines, tcolor=DARK, fc="white", ec=DARK, ls="-", tsize=None):
    box(x, y, w, h, fc=fc, ec=ec, ls=ls)
    n = len(lines); top = y + h - 3.2
    t(x + w / 2, top, title, size=T, weight="bold", color=tcolor)
    for i, s in enumerate(lines):
        t(x + w / 2, top - 3.6 - 3.0 * i, s)

cols = [(2, 27), (32, 27), (62, 29), (94, 29), (126, 62)]
heads = ["1  Data", "2  Chronological splits", "3  Forecasters", "4  Calibrators", "5  Evaluation and pre-specified judgements"]
top, bot = 78, 3
for (x, w), h in zip(cols, heads):
    box(x, bot, w, top - bot, fc="#F6F6F6", ec="#C8C8C8", lw=0.5)
    t(x + w / 2, top + 3.6, h, size=7.6, weight="bold")
for (x0, w0), (x1, _) in zip(cols[:-1], cols[1:]):
    arrow(x0 + w0 + 0.2, 40, x1 - 0.2, 40)

# 1 Data
x, w = cols[0]; cx, cw = x + 2, w - 4
card(cx, 55, cw, 18, "PJM", ["2014, 2017–18, 2022", "+ 2015 operator anchor"])
card(cx, 33, cw, 18, "MISO replication", ["2017–18, 2019, 2022", "plan fixed in advance"], tcolor=VER, ec=VER)
card(cx, 11, cw, 18, "Inputs", ["load: PJM, EIA-930", "weather: ERA5,", "15-point mean"])

# 2 Splits
x, w = cols[1]; cx, cw = x + 2, w - 4
ax.add_patch(Rectangle((cx, 66), cw * 0.55, 5.5, fc="#4C72B0", ec="white", lw=0.5))
ax.add_patch(Rectangle((cx + cw * 0.55, 66), cw * 0.27, 5.5, fc="#9DB4D6", ec="white", lw=0.5))
ax.add_patch(Rectangle((cx + cw * 0.82, 66), cw * 0.18, 5.5, fc=SKY, ec="white", lw=0.5))
t(cx + cw * 0.275, 68.75, "fit", color="white"); t(cx + cw * 0.685, 68.75, "tune"); t(cx + cw * 0.91, 68.75, "cal")
t(x + w / 2, 62.5, "training span, then test winter", size=6.3, color=GRY)
card(cx, 45, cw, 13, "Fit set", ["fit forecasters"])
card(cx, 29, cw, 13, "Tuning set", ["set scale parameters"])
card(cx, 9, cw, 17, "Calibration set", ["conformal cutoffs:", "last 92 days", "+ pre-event hours"])

# 3 Forecasters
x, w = cols[2]; cx, cw = x + 2, w - 4
card(cx, 59, cw, 14, "L1", ["quantile gradient", "boosting (primary)"])
card(cx, 42, cw, 14, "L2", ["linear-leaf boosting", "(can extrapolate)"])
card(cx, 25, cw, 14, "L3", ["location–scale", "statistical model"])
card(cx, 6, cw, 16, "Two horizons", ["H-DA: day-ahead", "(primary)", "H-1H: one-hour oracle"], fc="#FDF1E8", ec=VER)

# 4 Calibrators
x, w = cols[3]; cx, cw = x + 2, w - 4
cal = [("C0", "uncalibrated"), ("C0x", "proportional expansion"), ("C1", "global conformal"),
       ("C2a / C2b", "temperature Mondrian"), ("C3", "adaptive conformal"), ("C4", "temperature-scaled")]
for i, (a, b) in enumerate(cal):
    y = 64 - i * 10.4
    card(cx, y, cw, 9, a, [b])
t(x + w / 2, 6.0, "same calibrators, two designs", size=6.3, color=GRY)

# 5 Evaluation
x, w = cols[4]
def strip(x0, y0, k, col, n=12, s=1.75, g=0.35):
    for i in range(n):
        ax.add_patch(Rectangle((x0 + i * (s + g), y0), s, 2.4, fc=col if i < k else "white", ec=col, lw=0.45))
bw = (w - 7) / 2
bx1, bx2, by, bh = x + 2.5, x + 4.5 + bw, 48, 25
box(bx1, by, bw, bh, fc="#FDF1E8", ec=VER, lw=1.0)
t(bx1 + bw / 2, by + bh - 3.2, "Chronological", size=T, weight="bold", color=VER)
t(bx1 + bw / 2, by + bh - 6.8, "pre-event data only"); t(bx1 + bw / 2, by + bh - 9.8, "primary design")
strip(bx1 + (bw - 12 * 2.1) / 2, by + 9.5, round(22 / 72 * 12), VER)
t(bx1 + bw / 2, by + 6.0, "C2a, PJM 2014 vortex:"); t(bx1 + bw / 2, by + 3.0, "22 of 72 h covered")
box(bx2, by, bw, bh, fc="white", ec=MID, lw=0.9, ls=(0, (3, 2)))
t(bx2 + bw / 2, by + bh - 3.2, "Retrospective LOEO", size=T, weight="bold", color=MID)
t(bx2 + bw / 2, by + bh - 6.8, "pool other events' scores"); t(bx2 + bw / 2, by + bh - 9.8, "retrospective contrast")
strip(bx2 + (bw - 12 * 2.1) / 2, by + 9.5, round(55 / 72 * 12), MID)
t(bx2 + bw / 2, by + 6.0, "C2a, PJM 2014 vortex:"); t(bx2 + bw / 2, by + 3.0, "55 of 72 h covered")
# judgements row
jw = (w - 9) / 3; jy, jh = 21, 15
for i, (a, b1, b2) in enumerate([("J1 Collapse", "event window vs", "full period"), ("J2 Repair", "calibrator chosen", "on other events"), ("J3 Transfer gap", "LOEO minus", "chronological")]):
    jx = x + 2.5 + i * (jw + 2)
    card(jx, jy, jw, jh, a, [b1, b2])
arrow(bx1 + bw * 0.3, by - 0.2, x + 2.5 + jw * 0.5, jy + jh + 0.2, color=VER)
arrow(bx1 + bw * 0.7, by - 0.2, x + 2.5 + jw * 1.5 + 2, jy + jh + 0.2, color=VER)
arrow(bx2 + bw * 0.5, by - 0.2, x + 2.5 + jw * 2.5 + 4, jy + jh + 0.2, color=MID, ls=(0, (3, 2)))
arrow(bx1 + bw * 0.9, by - 0.2, x + 2.5 + jw * 2.5 + 2, jy + jh + 0.2, color=VER)
# MISO note
box(x + 2.5, 6, w - 5, 11, fc="white", ec=VER, lw=0.8)
t(x + w / 2, 14.3, "MISO replication, criteria fixed in advance", size=T, weight="bold", color=VER)
t(x + w / 2, 10.6, "collapse and repair failure replicate;"); t(x + w / 2, 7.9, "the sign of the J3 gap does not")
out = sys.argv[1]
fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=300)
print("saved")
