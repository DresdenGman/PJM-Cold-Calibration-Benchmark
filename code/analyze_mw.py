"""Three-way comparison: frozen chronological vs MW (A2) vs LOEO.
Event scopes, cov90 + n_inf90 + mean_width90. Writes results/mw_summary.md"""
import glob
import pandas as pd

R = "experiments/results"
def load(pat, mode):
    d = pd.concat([pd.read_csv(f) for f in glob.glob(f"{R}/{pat}")])
    return d[d.eval_mode == mode]
chro = load("frag_*.csv", "chronological")
chro = chro[~chro.index.isin([])]
mw = pd.concat([pd.read_csv(f) for f in glob.glob(f"{R}/frag_mw_*.csv")])
loeo = load("frag_loeo_*.csv", "loeo_transfer")
lines = ["# MW sensitivity (Amendment A2) — event-window cov90", ""]
for hz in ["HDA", "H1H"]:
    lines.append(f"## {hz}")
    for era, ev in [(2014, "event_2014_vortex"), (2018, "event_2018_snap"),
                    (2022, "event_2022_elliott")]:
        lines.append(f"### era {era}")
        lines.append("| learner | cal | frozen | MW | LOEO | MW n_inf | frozen n_inf | MW width | frozen width |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for lr in ["L1", "L2", "L3"]:
            for cal in ["C1", "C2a", "C2b", "C0x", "C4"]:
                def get(d, mode_col=None):
                    s = d[(d.era == era) & (d.horizon == hz) & (d.learner == lr)
                          & (d.calibrator == cal) & (d.scope == ev)]
                    return s.iloc[0] if len(s) else None
                f, m, l = get(chro), get(mw), get(loeo)
                if f is None or m is None:
                    continue
                lv = f"{l.cov90:.3f}" if l is not None else "—"
                lines.append(
                    f"| {lr} | {cal} | {f.cov90:.3f} | {m.cov90:.3f} | "
                    f"{lv} | {int(m.n_inf90)} | {int(f.n_inf90)} | "
                    f"{m.mean_width90:,.0f} | {f.mean_width90:,.0f} |")
        lines.append("")
open(f"{R}/mw_summary.md", "w").write("\n".join(lines))
print("wrote", f"{R}/mw_summary.md")
