"""v13 revision summary (exploratory): repair test with the equal-headroom frontier condition and
null-window attainability; coverage decomposition; corrected LOEO. Reads analysis/rev_events.csv,
analysis/rev_loeo_{pjm,miso}.csv and the A9/A11 event summaries. Writes analysis/rev_*.csv."""
import os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
import a9_common as A
AN = os.path.join(A.HERE, "analysis"); FD = os.path.join(os.path.dirname(A.HERE), "final_data")
S = pd.concat([pd.read_csv(os.path.join(FD, "a9_events_L1_gefs.csv")).assign(set="primary"),
               pd.read_csv(os.path.join(FD, "a11_events.csv")).assign(set="A11")], ignore_index=True)
V = pd.read_csv(os.path.join(AN, "rev_events.csv"))
X = S.merge(V, on=["system", "era"], suffixes=("", "_rev"), how="left"); assert X.c1_recentred.notna().all(), X[X.c1_recentred.isna()][["system", "era"]]
assert (np.abs(X.c1_ev - X.c1_ev_rev) < 1e-9).all(), "C1 event coverage mismatch"
assert (np.abs(X.c0x_check) < 1e-9).all(), "C0x reconstruction mismatch"
X["gap_c1"] = 100 * (X.c1_per - X.c1_ev)
CALS0 = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
for i, r in X.iterrows():   # width ratio and placebo coverage from the raw matrices, same rule for all 38 events
    M = pd.read_csv(os.path.join(A.HERE, "results", f"a9_{r.system}_{r.era}_L1_gefs.csv"))
    w1 = M[(M.calibrator == "C1") & (M.scope == "eval_winter")].mean_width90.iloc[0]
    for c in CALS0:
        X.loc[i, f"wr_{c}"] = M[(M.calibrator == c) & (M.scope == "eval_winter")].mean_width90.iloc[0] / w1
        X.loc[i, f"pl_{c}"] = M[(M.calibrator == c) & (M.scope == "placebo")].cov90.iloc[0]
        X.loc[i, f"ev_{c}"] = M[(M.calibrator == c) & (M.scope == A.events(r.system)[str(r.era)]["name"])].cov90.iloc[0]
CALS = ["C0x", "C1", "C2a", "C2b", "C3", "C4", "C6", "C7"]
def cond(r, c):   # conditions (a), (c), (d) from the released matrices, (b) at equal headroom
    a = 0.85 <= r[f"ev_{c}"] <= 0.95; cc = r[f"wr_{c}"] <= 1.35; d = r[f"pl_{c}"] <= 0.95; b = bool(r[f"b_eq_{c}"])
    return a, b, cc, d
rows = []
for _, r in X.iterrows():
    a, b, c, d = cond(r, r.chat); anyp = [c_ for c_ in CALS if all(cond(r, c_))]
    rows.append(dict(system=r.system, era=r.era, set=r.set, gap_c1=r.gap_c1, chat=r.chat, chat_cov=r.chat_cov,
                     a=a, b_eq=b, c=c, d=d, repaired_eq=a and b and c and d, any_pass_eq=",".join(anyp), ok_chat=r.ok_chat, ok_C1=r.ok_C1,
                     repaired_v12=bool(r.repaired)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(AN, "rev_repair.csv"), index=False)
big = R.gap_c1 >= 10
print("REPAIR (equal-headroom b): selected calibrator repairs", int(R.repaired_eq.sum()), "of", len(R),
      "| primary", int(R[R.set == "primary"].repaired_eq.sum()), "| A11", int(R[R.set == "A11"].repaired_eq.sum()),
      "| among gap>=10:", int(R[big].repaired_eq.sum()), "of", int(big.sum()))
print("   repaired events:", R[R.repaired_eq][["system", "era", "chat", "chat_cov", "gap_c1"]].to_string(index=False))
print("   no calibrator passes (eq-b):", int((R.any_pass_eq == "").sum()), "of", len(R), "| among gap>=10:", int((R[big].any_pass_eq == "").sum()))
print("   condition (a) met by selected:", int(R.a.sum()), "expected under null-window attainability:", round(R.ok_chat.sum(), 1),
      "| mean ok_C1", round(R.ok_C1.mean(), 2), "| among gap>=10: (a) met", int(R[big].a.sum()), "expected", round(R[big].ok_chat.sum(), 1))
# decomposition
D = X[["system", "era", "set", "n", "c1_ev", "c1_per", "c1_recentred", "c1_recentred_rescaled", "c1_rescaled_only", "disp_ratio", "mean_err",
       "share_below_train_min", "share_below_train_p01", "pct_C1", "gap_c1"]].copy()
D.to_csv(os.path.join(AN, "rev_decomp.csv"), index=False)
for nm_, d in [("all", D), ("gap>=10", D[D.gap_c1 >= 10])]:
    print(f"DECOMP {nm_} (n={len(d)}): C1 {d.c1_ev.mean():.3f} | recentred {d.c1_recentred.mean():.3f} | rescaled only {d.c1_rescaled_only.mean():.3f} | both {d.c1_recentred_rescaled.mean():.3f} | winter {d.c1_per.mean():.3f}; disp ratio median {d.disp_ratio.median():.2f}")
short = D.c1_per - D.c1_ev; loc = D.c1_recentred - D.c1_ev
print("   share of the event shortfall (winter - event) removed by recentring, events with gap>=10:", round((loc[D.gap_c1 >= 10]).sum() / short[D.gap_c1 >= 10].sum(), 2))
X["babs"] = np.abs(X.mean_err)
for col in ["share_below_train_min", "share_below_train_p01"]:
    r1 = spearmanr(X[col], X.c1_ev); r2 = spearmanr(X[col], X.mean_err / X.mean_err.abs().max())
    print(f"SUPPORT {col}: rho with C1 event cov {r1.correlation:.2f} (p {r1.pvalue:.3f}); with mean error {r2.correlation:.2f} (p {r2.pvalue:.3f}); events with any hour below: {(X[col] > 0).sum()}")
print("NULL ranks: mean percentile of C1 event coverage among null windows", round(D.pct_C1.mean(), 3), "| below 10th pct:", int((D.pct_C1 < 0.10).sum()), "of", len(D))
# LOEO
L = pd.concat([pd.read_csv(os.path.join(AN, f"rev_loeo_{s}.csv")) for s in ["pjm", "miso"]], ignore_index=True)
L.to_csv(os.path.join(AN, "rev_loeo.csv"), index=False)
for c in ["C1", "C2a", "C2b", "C4"]:
    f = L[L[f"finite_{c}"]]
    print(f"LOEO {c}: finite n={len(f)} mean gap {f[f'gap_{c}'].mean():+.1f} pp, mean |gap| {f[f'gap_{c}'].abs().mean():.1f}, positive in {int((f[f'gap_{c}'] > 0).sum())}")
