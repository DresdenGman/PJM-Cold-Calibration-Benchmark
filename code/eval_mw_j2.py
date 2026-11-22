"""J2 repair test applied to the Amendment-A2 MW arm: frozen C0/C3 rows,
MW rows for C0x/C1/C2a/C2b/C4, identical selection rules (report.j2_for_cell)."""
import glob
import pandas as pd
import report as RP

frozen = pd.concat([pd.read_csv(f) for f in glob.glob("results/frag_*.csv")
                    if "mw" not in f and "loeo" not in f])
frozen = frozen[frozen.eval_mode == "chronological"]
keep = frozen[frozen.calibrator.isin(["C0", "C3"])]
mw = pd.concat([pd.read_csv(f) for f in glob.glob("results/frag_mw_*.csv")])
mw = mw[mw.calibrator.isin(["C0x", "C1", "C2a", "C2b", "C4"])].copy()
mw["eval_mode"] = "chronological"
df = pd.concat([keep, mw], ignore_index=True)

loeo_sel = {e: [j for j in RP.ERAS if j != e] for e in RP.ERAS}
chrono_sel = {"2014": ["2018", "2022"], "2018": ["2014"],
              "2022": ["2014", "2018"]}
out = ["# J2 repair test on the MW (Amendment A2) arm", ""]
for label, sel in [("LOEO selection (A1, primary)", loeo_sel),
                   ("Chronological-selection variant", chrono_sel)]:
    out.append(f"## {label}")
    verdicts = {}
    for horizon in ["HDA", "H1H"]:
        for learner in ["L1", "L2", "L3"]:
            _, recs, verdict = RP.j2_for_cell(df, horizon, learner, sel)
            verdicts[(horizon, learner)] = verdict
            if horizon == "HDA":
                for era in RP.ERAS:
                    r = recs[era]
                    out.append(
                        f"- HDAx{learner} {era}: chat={r['chat']} "
                        f"cov90={r['cov90']:.3f} a={'Y' if r['a_ok'] else 'N'} "
                        f"frontier={'Y' if r['frontier'] else 'N'} "
                        f"width={100*r['width_infl']:+.1f}% "
                        f"c={'Y' if r['c_ok'] else 'N'} "
                        f"placebo={r['placebo_cov']:.3f} "
                        f"d={'Y' if r['d_ok'] else 'N'}")
    out.append("verdicts: " + "; ".join(
        f"{h}x{l}: {'HOLDS' if v else 'no'}"
        for (h, l), v in verdicts.items()))
    out.append("")
open("results/mw_j2.md", "w").write("\n".join(out))
print("\n".join(out))
