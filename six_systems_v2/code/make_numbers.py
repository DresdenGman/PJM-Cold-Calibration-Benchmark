"""Every number quoted in the v12 text, computed from the result files and written as LaTeX
macros (numbers.tex). Usage: make_numbers.py WORKDIR"""
import sys, os, json, glob, re
import numpy as np, pandas as pd
W = sys.argv[1]; D = f"{W}/final_data"; OUT = f"{W}/paper12/v12/numbers.tex"
M = {}
def put(k, v, fmt="{:.3f}"):
    assert re.fullmatch(r"[A-Za-z]+", k), k
    M[k] = fmt.format(v) if not isinstance(v, str) else v
pct = lambda x: "{:.1f}".format(100 * x)
E = pd.read_csv(f"{D}/a9_events_L1_gefs.csv"); E5 = pd.read_csv(f"{D}/a9_events_L1_era5.csv")
X = pd.read_csv(f"{D}/old_vs_new.csv")
for k in ["old_c0_ev", "old_c0_per", "old_c1_ev", "old_c1_per", "new_c0_ev", "new_c0_per", "new_c1_ev", "new_c1_per"]:
    put("mean" + "".join(w.capitalize() for w in k.replace("c0", "czero").replace("c1", "cone").split("_")), X[k].mean())
put("meanOldGapCone", 100 * (X.old_c1_per - X.old_c1_ev).mean(), "{:.1f}"); put("meanNewGapCone", 100 * (X.new_c1_per - X.new_c1_ev).mean(), "{:.1f}")
put("nOldGapTen", int(((X.old_c1_per - X.old_c1_ev) >= 0.10).sum()), "{:d}"); put("nNewGapTen", int(((X.new_c1_per - X.new_c1_ev) >= 0.10).sum()), "{:d}")
P = pd.read_csv(f"{D}/pooled.csv").set_index("quantity")
for q, k in [("model C1 gap (pp)", "poolGap"), ("model C1 event cov", "poolEv"), ("operator C1 gap (pp)", "poolOpGap"), ("operator C1 event cov", "poolOpEv")]:
    f = "{:.1f}" if "gap" in q else "{:.2f}"
    put(k, P.loc[q, "estimate"], f); put(k + "Lo", P.loc[q, "ci_lo"], f); put(k + "Hi", P.loc[q, "ci_hi"], f)
# G criteria
put("nRepairedNine", int(E.repaired.sum()), "{:d}"); put("nAnyPassNine", int((E.any_pass.fillna("") != "").sum()), "{:d}")
put("ERAmeanConeEv", E5.c1_ev.mean()); put("ERAmeanConePer", E5.c1_per.mean())
L = pd.read_csv(f"{D}/a9_loeo_L1_gefs.csv")
for c in ["C2a", "C2b"]:
    f = L[L[f"finite_{c}"]]; put(f"loeoAbs{c.replace('C2', 'Two')}", f[f"gap_{c}"].abs().mean(), "{:.1f}"); put(f"loeoMean{c.replace('C2', 'Two')}", f[f"gap_{c}"].mean(), "{:.1f}")
NW = pd.read_csv(f"{D}/a9_null_L1_gefs.csv"); put("nNullTen", int((NW.pct_C0 < 0.10).sum()), "{:d}")
B = pd.read_csv(f"{D}/a9_bias_L1_gefs.csv").set_index(["system", "era"])
put("biasPJMfourteen", B.loc[("pjm", 2014), "bias_ratio"], "{:.2f}"); put("abovePJMfourteen", 100 * B.loc[("pjm", 2014), "share_above"], "{:.0f}")
put("biasPJMElliott", B.loc[("pjm", 2022), "bias_ratio"], "{:.2f}"); put("biasMISOElliott", B.loc[("miso", 2022), "bias_ratio"], "{:.2f}")
MC = pd.read_csv(f"{D}/mechanism_L1_gefs.csv")
from scipy.stats import spearmanr
r = spearmanr(MC.pred_c0_ev, MC.c0_ev); put("shiftRho", r.correlation, "{:.2f}"); put("shiftP", r.pvalue, "{:.2f}"); put("shiftMAE", np.abs(MC.pred_c0_ev - MC.c0_ev).mean(), "{:.2f}")
r2 = spearmanr(MC.share_below_p01, MC.c1_ev); put("supportRho", r2.correlation, "{:.2f}"); put("supportP", r2.pvalue, "{:.2f}")
L23 = pd.read_csv(f"{D}/a9_L23_summary.csv"); g = L23[L23.weather == "gefs"]
for Lr, k in [("L2", "Ltwo"), ("L3", "Lthree")]:
    x = g[g.learner == Lr]; put(f"{k}Ev", x.c1_ev.mean()); put(f"{k}Per", x.c1_per.mean()); put(f"n{k}GapTen", int(((x.c1_per - x.c1_ev) >= 0.10).sum()), "{:d}")
H2 = pd.read_csv(f"{D}/a10_H2.csv").set_index(["system", "era"])
put("holMISOgain", H2.loc[("miso", 2022), "d_c1ev"], "{:.1f}"); put("holPJMgain", H2.loc[("pjm", 2022), "d_c1ev"], "{:.1f}")
put("holMISObiasBefore", abs(H2.loc[("miso", 2022), "bias_L1"]), "{:.2f}"); put("holMISObiasAfter", abs(H2.loc[("miso", 2022), "bias_L1h"]), "{:.2f}")
put("holMaxPer", H2.d_c1per.abs().max(), "{:.1f}")
O = pd.read_csv(f"{D}/a12_summary.csv"); put("nOpGapTen", int((O.gap >= 10).sum()), "{:d}"); put("nOp", len(O), "{:d}"); put("nOpRepaired", int(O.repaired.sum()), "{:d}")
r3 = spearmanr(O.c1_ev, O.model_c1_ev); put("opRho", r3.correlation, "{:.2f}")
put("nOpRepGapTen", int(((O.gap >= 10) & O.repaired).sum()), "{:d}"); put("opRepMaxGap", O[O.repaired].gap.max(), "{:.1f}")
put("opPJMElliottCfour", O[(O.system == "pjm") & (O.era == 2022)].ev_C4.iloc[0])
A11 = pd.read_csv(f"{D}/a11_events.csv"); put("nAeleven", len(A11), "{:d}"); put("nAelevenGapTen", int((A11.gap_c1 >= 10).sum()), "{:d}")
put("nAelevenRepaired", int(A11.repaired.sum()), "{:d}"); put("nAelevenNoPass", int((A11.any_pass.fillna("") == "").sum()), "{:d}")
for s in ["ercot", "spp", "nyiso", "isone"]:
    x = A11[A11.system == s]; put(f"{s}Ev", x.c1_ev.mean()); put(f"{s}Per", x.c1_per.mean()); put(f"n{s}", len(x), "{:d}")
CB = pd.read_csv(f"{D}/a11_censored.csv"); er = CB[(CB.system == "ercot") & (CB.calibrator == "C1")].iloc[0]
put("uriERCOTlo", er.cov_lower, "{:.2f}"); put("uriERCOThi", er.cov_upper, "{:.2f}"); put("uriERCOTpre", int(er.unflagged_hours), "{:d}")
OPS = pd.read_csv(f"{D}/ops_a9_gefs.csv")
def sh(s, e, c, col): return OPS[(OPS.system == s) & (OPS.era == e) & (OPS.calibrator == c)][col].iloc[0]
put("shortPJMfourteenGW", sh("pjm", 2014, "C1", "max_shortfall_mw") / 1000, "{:.1f}"); put("shortPJMfourteenPct", sh("pjm", 2014, "C1", "max_shortfall_pct_peak"), "{:.0f}")
put("shortPJMElliottGW", sh("pjm", 2022, "C1", "max_shortfall_mw") / 1000, "{:.1f}"); put("shortPJMElliottPct", sh("pjm", 2022, "C1", "max_shortfall_pct_peak"), "{:.1f}")
put("shortMISOeighteenGW", sh("miso", 2018, "C1", "max_shortfall_mw") / 1000, "{:.1f}")

# ---- added for v12: counts, ranges, A13 factorial, ERA5 arm, legacy constants
put("nConeBelow", int((E.c1_ev < E.c1_per).sum()), "{:d}"); put("nCzeroBelow", int((E.c0_ev < E.c0_per).sum()), "{:d}")
put("coneEvMin", E.c1_ev.min(), "{:.2f}"); put("coneEvMax", E.c1_ev.max(), "{:.2f}")
put("conePerMin", E.c1_per.min(), "{:.2f}"); put("conePerMax", E.c1_per.max(), "{:.2f}")
put("nOverTen", int(((E.c1_per - E.c1_ev) <= -0.07).sum()), "{:d}")
put("nAelevenBelow", int((A11.c1_ev < A11.c1_per).sum()), "{:d}")
put("nAllEvents", len(E) + len(A11), "{:d}"); put("nAllNoPass", int((E.any_pass.fillna("") == "").sum()) + int((A11.any_pass.fillna("") == "").sum()), "{:d}")
put("nNineNoPass", int((E.any_pass.fillna("") == "").sum()), "{:d}")
put("aelevenEvMin", A11.c1_ev.min(), "{:.2f}"); put("aelevenEvMax", A11.c1_ev.max(), "{:.2f}")
put("meanAelevenGap", A11.gap_c1.mean(), "{:.1f}")
L5 = pd.read_csv(f"{D}/a9_loeo_L1_era5.csv")
for c in ["C2a", "C2b"]:
    f = L5[L5[f"finite_{c}"]]; put(f"eraLoeoAbs{c.replace('C2', 'Two')}", f[f"gap_{c}"].abs().mean(), "{:.1f}")
put("loeoMeanCone", L["gap_C1"].mean(), "{:.1f}"); put("nLoeoNeg", int((L[L.finite_C2b].gap_C2b < 0).sum()), "{:d}"); put("nLoeoFin", int(L.finite_C2b.sum()), "{:d}")
S13 = pd.read_csv(f"{D}/a13_summary.csv")
NM = {"SA": "SA", "LA": "LA", "SW": "SW", "LW": "LW"}
for _, r in S13.iterrows():
    k = r.design + {"ev": "Ev", "per": "Per", "gap": "Gap", "n_gap10": "NGapTen"}[r.quantity]
    if r.quantity == "n_gap10": put(k, int(r.estimate), "{:d}"); put(r.design + "N", int(r.n), "{:d}"); continue
    f = "{:.1f}" if r.quantity == "gap" else "{:.2f}"
    put(k, r.estimate, f); put(k + "Lo", r.ci_lo, f); put(k + "Hi", r.ci_hi, f)
for k, q in [("LWGap", "model C1 gap (pp)"), ("LWEv", "model C1 event cov")]:   # same quantity as the pooled A9 estimate
    f = "{:.1f}" if "Gap" in k else "{:.2f}"; put(k, P.loc[q, "estimate"], f); put(k + "Lo", P.loc[q, "ci_lo"], f); put(k + "Hi", P.loc[q, "ci_hi"], f)
r4 = spearmanr(MC.n_cal_colder_than_ev_median, MC.c1_ev); put("nColderRho", r4.correlation, "{:.2f}")
r5 = spearmanr(MC.excess_min, MC.c1_ev); put("excessRho", r5.correlation, "{:.2f}")
sm = A11.groupby("system").c1_per.mean(); put("aelevenSysPerMin", sm.min(), "{:.2f}"); put("aelevenSysPerMax", sm.max(), "{:.2f}")

# ---- v13 revision analyses (exploratory)
RI = pd.read_csv(f"{D}/rev_inference.csv").set_index(["set", "quantity"])
for st, k in [("all38", "all"), ("primary13", "prim"), ("A11", "ael")]:
    r = RI.loc[(st, "gap")]
    put(k + "GapEst", r.estimate, "{:.1f}"); put(k + "GapLo", r.cr1_lo, "{:.1f}"); put(k + "GapHi", r.cr1_hi, "{:.1f}")
    put(k + "PwildGap", r.p_wild, "{:.3f}"); put(k + "PflipGap", r.p_signflip_2s, "{:.3f}"); put(k + "G", int(r.G), "{:d}")
    q = RI.loc[(st, "rank_dev")]; put(k + "MeanPct", q.mean_pct, "{:.2f}"); put(k + "NBelowTen", int(q.n_below10), "{:d}")
    put(k + "PflipRank", q.p_signflip_2s, "{:.3f}")
put("nAllClusters", int(RI.loc[("all38", "gap")].G), "{:d}")
put("primPbootLo", RI.loc[("primary13", "gap")].pboot_lo, "{:.1f}"); put("primPbootHi", RI.loc[("primary13", "gap")].pboot_hi, "{:.1f}")
RP = pd.read_csv(f"{D}/rev_repair.csv"); big = RP.gap_c1 >= 10
put("nRepEq", int(RP.repaired_eq.sum()), "{:d}"); put("nRepEqPrim", int(RP[RP.set == "primary"].repaired_eq.sum()), "{:d}")
put("nRepEqAel", int(RP[RP.set == "A11"].repaired_eq.sum()), "{:d}")
put("nGapTenAll", int(big.sum()), "{:d}"); put("nRepEqGapTen", int(RP[big].repaired_eq.sum()), "{:d}")
put("nNoPassEq", int((RP.any_pass_eq.fillna("") == "").sum()), "{:d}"); put("nNoPassEqGapTen", int((RP[big].any_pass_eq.fillna("") == "").sum()), "{:d}")
put("nAmet", int(RP.a.sum()), "{:d}"); put("nAexp", RP.ok_chat.sum(), "{:.1f}")
put("nAmetGapTen", int(RP[big].a.sum()), "{:d}"); put("nAexpGapTen", RP[big].ok_chat.sum(), "{:.1f}")
put("okConeMean", RP.ok_C1.mean(), "{:.2f}"); put("okConeMin", RP.ok_C1.min(), "{:.2f}"); put("okConeMax", RP.ok_C1.max(), "{:.2f}")
put("nRepVtwelve", int(RP.repaired_v12.sum()), "{:d}")
DC = pd.read_csv(f"{D}/rev_decomp.csv"); dg = DC[DC.gap_c1 >= 10]
put("decEv", dg.c1_ev.mean(), "{:.2f}"); put("decRec", dg.c1_recentred.mean(), "{:.2f}"); put("decScale", dg.c1_rescaled_only.mean(), "{:.2f}")
put("decBoth", dg.c1_recentred_rescaled.mean(), "{:.2f}"); put("decPer", dg.c1_per.mean(), "{:.2f}")
put("decRecShare", 100 * (dg.c1_recentred - dg.c1_ev).sum() / (dg.c1_per - dg.c1_ev).sum(), "{:.0f}")
put("decDisp", dg.disp_ratio.median(), "{:.2f}")
put("decAllEv", DC.c1_ev.mean(), "{:.2f}"); put("allMeanEv", DC.c1_ev.mean(), "{:.2f}"); put("allMeanPer", DC.c1_per.mean(), "{:.2f}"); put("nAllBelow", int((DC.c1_ev < DC.c1_per).sum()), "{:d}"); put("decAllRec", DC.c1_recentred.mean(), "{:.2f}"); put("decAllBoth", DC.c1_recentred_rescaled.mean(), "{:.2f}")
rs = spearmanr(DC.share_below_train_min, DC.c1_ev); put("fsupRho", rs.correlation, "{:.2f}"); put("fsupP", rs.pvalue, "{:.2f}")
put("nFsup", int((DC.share_below_train_min > 0).sum()), "{:d}")
u = DC[(DC.system == "ercot") & (DC.era == 2021)].iloc[0]; put("uriRec", u.c1_recentred, "{:.2f}")
el = DC[(DC.system == "pjm") & (DC.era == 2022)].iloc[0]; put("pjmElliottRec", el.c1_recentred, "{:.2f}"); put("pjmElliottDisp", el.disp_ratio, "{:.2f}")
LV = pd.read_csv(f"{D}/rev_loeo.csv")
for c, k in [("C1", "Cone"), ("C2a", "Twoa"), ("C2b", "Twob"), ("C4", "Cfour")]:
    f = LV[LV[f"finite_{c}"]]; put("rloeoMean" + k, f[f"gap_{c}"].mean(), "{:.1f}"); put("rloeoAbs" + k, f[f"gap_{c}"].abs().mean(), "{:.1f}")
    put("rloeoPos" + k, int((f[f"gap_{c}"] > 0).sum()), "{:d}"); put("rloeoN" + k, len(f), "{:d}")
put("nConeNearNominal", int(((E.c1_per >= 0.85) & (E.c1_per <= 0.95)).sum()), "{:d}")
V = pd.read_csv(f"{D}/rev_events.csv"); hw = E.merge(V[["system", "era", "n"]], on=["system", "era"])
put("hwGap", 100 * np.average(hw.c1_per - hw.c1_ev, weights=hw.n), "{:.1f}")
H2 = pd.read_csv(f"{D}/a10_H2.csv"); put("nHolWorse", int((H2.d_c1ev <= -5).sum()), "{:d}"); put("holWorstDrop", -H2.d_c1ev.min(), "{:.1f}")

# ---- v13b: sensitivity, factorial CR1 intervals, Shapley split of the oracle decomposition
for st, k in [("all38_noERCOT", "noErcot"), ("all38_noUri", "noUri"), ("all38_byWinter", "byWinter")]:
    r = RI.loc[(st, "gap")]; put(k + "Gap", r.estimate, "{:.1f}"); put(k + "Lo", r.cr1_lo, "{:.1f}"); put(k + "Hi", r.cr1_hi, "{:.1f}")
    put(k + "P", r.p_signflip_2s, "{:.3f}"); put(k + "G", int(r.G), "{:d}")
for k in ["SA", "LA", "SW", "LW"]:   # Table 3 intervals: CR1 over the seven primary outbreaks (replaces the percentile bootstrap)
    r = RI.loc[(f"factorial_{k}", "gap")]; put(k + "GapLo", r.cr1_lo, "{:.1f}"); put(k + "GapHi", r.cr1_hi, "{:.1f}"); put(k + "GapP", r.p_signflip_2s, "{:.2f}")
put("SAGapExact", RI.loc[("factorial_SA", "gap")].estimate, "{:.2f}"); put("SWGapExact", RI.loc[("factorial_SW", "gap")].estimate, "{:.2f}")
put("allPrank", RI.loc[("all38", "rank_dev")].p_signflip_2s, "{:.1e}")
loc = 0.5 * ((dg.c1_recentred - dg.c1_ev) + (dg.c1_recentred_rescaled - dg.c1_rescaled_only))
dis = 0.5 * ((dg.c1_rescaled_only - dg.c1_ev) + (dg.c1_recentred_rescaled - dg.c1_recentred))
put("shapLoc", 100 * loc.sum() / (loc + dis).sum(), "{:.0f}"); put("shapDisp", 100 * dis.sum() / (loc + dis).sum(), "{:.0f}")
put("nLocDom", int((loc > dis).sum()), "{:d}"); put("nRecLower", int((dg.c1_recentred < dg.c1_ev).sum()), "{:d}")
put("dispFirstShare", 100 * (dg.c1_rescaled_only - dg.c1_ev).sum() / (dg.c1_per - dg.c1_ev).sum(), "{:.0f}")
pp_ = RP[big].ok_chat.values; dd = np.array([1.0])
for q_ in pp_: dd = np.convolve(dd, [1 - q_, q_])
put("pAmetGapTen", dd[:int(RP[big].a.sum()) + 1].sum(), "{:.2f}")

# ---- v13b: event-stratum calibration (post hoc): LOEO-all, past-only, forecast-triggered past-only
TG = pd.read_csv(f"{D}/rev_trigger.csv").merge(RP[["system", "era", "gap_c1"]], on=["system", "era"])
TG = TG[TG.available == True]
tr = TG[TG.variant == "triggered"]; keys = tr.set_index(["system", "era"]).index
sub = lambda v: TG[(TG.variant == v) & TG.set_index(["system", "era"]).index.isin(keys)]
c1s, pos, lall = sub("C1"), sub("past_only"), TG[TG.variant == "loeo_all"]
put("nTrig", len(tr), "{:d}"); put("nTrigBig", int((tr.gap_c1 >= 10).sum()), "{:d}")
for nm_, d in [("Cone", c1s), ("Past", pos), ("Trig", tr)]:
    put(f"trg{nm_}Ev", d.event_cov.mean(), "{:.2f}"); put(f"trg{nm_}Win", d.winter_cov.mean(), "{:.2f}"); put(f"trg{nm_}Wr", d.width_ratio.median(), "{:.2f}")
    put(f"trg{nm_}Pl", d.placebo_cov.mean(), "{:.2f}"); b = d[d.gap_c1 >= 10]; put(f"trg{nm_}BigEv", b.event_cov.mean(), "{:.2f}")
    put(f"trg{nm_}BigEightFive", int((b.event_cov >= 0.85).sum()), "{:d}"); put(f"trg{nm_}Rep", int(d.repaired.sum()), "{:d}"); put(f"trg{nm_}BigRep", int(b.repaired.sum()), "{:d}")
put("trgPastWrMin", pos.width_ratio.min(), "{:.2f}"); put("trgPastWrMax", pos.width_ratio.max(), "{:.2f}")
for _nm, _d in [("trgCone", c1s), ("trgPast", pos)]:
    put(_nm + "Over", int((_d.event_cov > 0.95).sum()), "{:d}"); put(_nm + "Under", int((_d.event_cov < 0.85).sum()), "{:d}"); put(_nm + "Out", int(((_d.event_cov < 0.85) | (_d.event_cov > 0.95)).sum()), "{:d}")
put("trgTrigWrMax", tr.width_ratio.max(), "{:.2f}"); put("trgOver", int((tr.event_cov > 0.95).sum()), "{:d}"); put("trgUnder", int((tr.event_cov < 0.85).sum()), "{:d}"); put("trgOutBand", int(((tr.event_cov < 0.85) | (tr.event_cov > 0.95)).sum()), "{:d}")
put("trgShareWin", 100 * tr.trig_share_winter.median(), "{:.0f}"); put("trgShareEv", 100 * tr.trig_share_event.median(), "{:.0f}")
put("trgBigUnder", int(((tr.gap_c1 >= 10) & (tr.event_cov < 0.85)).sum()), "{:d}")
put("loeoAllEv", lall.event_cov.mean(), "{:.2f}"); put("loeoAllWr", lall.width_ratio.median(), "{:.2f}"); put("loeoAllWin", lall.winter_cov.mean(), "{:.2f}")
put("loeoAllWrMin", lall.width_ratio.min(), "{:.2f}"); put("loeoAllWrMax", lall.width_ratio.max(), "{:.2f}"); put("nLoeoAll", len(lall), "{:d}")
put("nLoeoAllFailC", int((lall.width_ratio > 1.35).sum()), "{:d}")

# ---- v14 final-check fixes
r = RI.loc[("operator12", "gap")]; put("opGapEst", r.estimate, "{:.1f}"); put("opGapLo", r.cr1_lo, "{:.1f}"); put("opGapHi", r.cr1_hi, "{:.1f}"); put("opGapP", r.p_signflip_2s, "{:.2f}")
r = RI.loc[("operator12", "event_cov_pp")]; put("opEvEst", r.estimate / 100, "{:.2f}"); put("opEvLo", r.cr1_lo / 100, "{:.2f}"); put("opEvHi", r.cr1_hi / 100, "{:.2f}")
dgx = dg[dg.system != "ercot"]
locx = 0.5 * ((dgx.c1_recentred - dgx.c1_ev) + (dgx.c1_recentred_rescaled - dgx.c1_rescaled_only)); disx = 0.5 * ((dgx.c1_rescaled_only - dgx.c1_ev) + (dgx.c1_recentred_rescaled - dgx.c1_recentred))
put("shapLocNoErcot", 100 * locx.sum() / (locx + disx).sum(), "{:.0f}"); put("nDispDom", int((dis >= loc).sum()), "{:d}")
hw38 = DC.drop(columns=["n"]).merge(V[["system", "era", "n"]], on=["system", "era"])
put("hwGapAll", 100 * np.average(hw38.c1_per - hw38.c1_ev, weights=hw38["n"]), "{:.1f}")
c1all = TG[TG.variant == "C1"].set_index(["system", "era"]).event_cov; la = lall.set_index(["system", "era"])
put("loeoAllGain", 100 * (la.event_cov - c1all.reindex(la.index)).mean(), "{:.1f}")
prim = la[la.index.get_level_values(0).isin(["pjm", "miso"])]; put("loeoPrimWr", prim.width_ratio.median(), "{:.2f}")
ps = pos.set_index(["system", "era"]); put("pastGain", 100 * (ps.event_cov - c1all.reindex(ps.index)).mean(), "{:.1f}")

# ---- v15 (package A): operator forecasts in six systems (A14), operational-GEFS subset, recentring, upper tail,
#      chronological selection, point accuracy
A14 = pd.read_csv(f"{D}/a14_summary.csv"); A14x = A14[~((A14.system == "spp") & (A14.era == 2026))]
put("nOpNew", len(A14x), "{:d}"); put("nOpNewGapTen", int((A14x.gap >= 10).sum()), "{:d}"); put("nOpNewRep", int(A14x.repaired.sum()), "{:d}")
_o36 = pd.concat([pd.read_csv(f"{D}/a12_summary.csv"), A14x]); put("opAllRho", spearmanr(_o36.c1_ev, _o36.model_c1_ev).correlation, "{:.2f}"); put("opWithSppNGapTen", int((A14.gap >= 10).sum()), "{:d}"); put("opWithSppNRep", int(A14.repaired.sum()), "{:d}"); put("nOpNewAll", len(A14), "{:d}")
put("opNewRho", spearmanr(A14x.c1_ev, A14x.model_c1_ev).correlation, "{:.2f}")
AP = pd.read_csv(f"{D}/a14_pooled.csv").set_index("set")
for st, k in [("operator_all", "opAll"), ("operator_noERCOT", "opNoErcot"), ("operator_with_spp2026", "opWithSpp")]:
    r = AP.loc[st]; put(k + "N", int(r.n), "{:d}"); put(k + "G", int(r.G), "{:d}"); put(k + "Gap", r.est, "{:.1f}"); put(k + "Lo", r.lo, "{:.1f}"); put(k + "Hi", r.hi, "{:.1f}")
    put(k + "P", r.p_flip, "{:.3f}"); put(k + "Ev", r.mean_ev, "{:.2f}"); put(k + "Per", r.mean_per, "{:.2f}"); put(k + "GapTen", int(r.n_gap10), "{:d}"); put(k + "RepBig", int(r.n_rep_gap10), "{:d}")
r = RI.loc[("all38_opGEFS", "gap")]; put("ogN", int(r.n), "{:d}"); put("ogG", int(r.G), "{:d}"); put("ogGap", r.estimate, "{:.1f}"); put("ogLo", r.cr1_lo, "{:.1f}"); put("ogHi", r.cr1_hi, "{:.1f}"); put("ogP", r.p_signflip_2s, "{:.3f}")
r = RI.loc[("all38_opGEFS_noERCOT", "gap")]; put("ogxGap", r.estimate, "{:.1f}"); put("ogxLo", r.cr1_lo, "{:.1f}"); put("ogxHi", r.cr1_hi, "{:.1f}")
SH = pd.read_csv(f"{D}/rev_shift.csv"); sb = SH[SH.gap_c1 >= 10]
put("upxEv", 100 * SH.event_upx_C1.mean(), "{:.0f}"); put("upxWin", 100 * SH.winter_upx_C1.mean(), "{:.1f}"); put("upxEvBig", 100 * sb.event_upx_C1.mean(), "{:.0f}")
put("cnEv", SH.event_cov_C9.mean(), "{:.2f}"); put("cnEvBig", sb.event_cov_C9.mean(), "{:.2f}"); put("cnUpxEv", 100 * SH.event_upx_C9.mean(), "{:.0f}"); put("cnUpxWin", 100 * SH.winter_upx_C9.mean(), "{:.1f}")
put("cnWin", SH.winter_cov_C9.mean(), "{:.2f}"); put("cnPl", SH.placebo_cov_C9.mean(), "{:.2f}"); put("cnBetter", int((SH.event_cov_C9 > SH.event_cov_C1).sum()), "{:d}"); put("cnWorse", int((SH.event_cov_C9 < SH.event_cov_C1).sum()), "{:d}")
put("coneWinPl", SH.placebo_cov_C1.mean(), "{:.2f}")
PS = pd.read_csv(f"{D}/rev_pastsel.csv").dropna(subset=["chat_past"]); pb = PS[PS.gap_c1 >= 10]
put("psN", len(PS), "{:d}"); put("psRep", int((PS.repaired.astype(str) == "True").sum()), "{:d}"); put("psBigN", len(pb), "{:d}"); put("psBigRep", int((pb.repaired.astype(str) == "True").sum()), "{:d}")
r = RI.loc[("all38_ruleOnly", "gap")]; put("allMeanPctPct", 100 * RI.loc[("all38", "rank_dev")].mean_pct, "{:.0f}"); put("ruleN", int(r.n), "{:d}"); put("ruleG", int(r.G), "{:d}"); put("ruleGap", r.estimate, "{:.1f}"); put("ruleLo", r.cr1_lo, "{:.1f}"); put("ruleHi", r.cr1_hi, "{:.1f}")
_m = SH.merge(OPA36 := pd.concat([pd.read_csv(f"{D}/a12_summary.csv"), pd.read_csv(f"{D}/a14_summary.csv")]).query("not (system == 'spp' and era == 2026)")[["system", "era"]], on=["system", "era"])
put("matchedLoneGap", 100 * (_m.winter_cov_C1 - _m.event_cov_C1).mean(), "{:.1f}")
put("winInBand", int(((SH.winter_cov_C1 >= 0.85) & (SH.winter_cov_C1 <= 0.95)).sum()), "{:d}"); put("lowxEv", 100 * (1 - SH.event_cov_C1 - SH.event_upx_C1).mean(), "{:.1f}"); put("lowxWin", 100 * (1 - SH.winter_cov_C1 - SH.winter_upx_C1).mean(), "{:.1f}")
put("upShareMiss", 100 * SH.event_upx_C1.sum() / (1 - SH.event_cov_C1).sum(), "{:.0f}")
MA = pd.read_csv(f"{D}/rev_mae.csv")
put("maeN", len(MA), "{:d}"); put("maeRatioEv", (MA.event_mae_l1 / MA.event_mae_op).median(), "{:.2f}"); put("maeRatioWin", (MA.winter_mae_l1 / MA.winter_mae_op).median(), "{:.2f}")
put("maeLoneWorse", int((MA.winter_mae_l1 > MA.winter_mae_op).sum()), "{:d}")
# legacy constants from the original design (frozen-protocol results, v11 Table 4): PJM mean LOEO gaps
put("oldLoeoTwoa", "+11.6"); put("oldLoeoTwob", "+21.2")
put("nOpBelow", int((O.c1_ev < O.c1_per).sum()), "{:d}")
import re as _re
_used = set()
for _f in ["paper.tex", "supplement.tex"]:
    _p = os.path.join(os.path.dirname(OUT), _f)
    if os.path.exists(_p): _used |= set(_re.findall(r"\\([A-Za-z]+)", open(_p).read()))
if _used and not os.environ.get("NOPRUNE"): M = {k: v for k, v in M.items() if k in _used}
with open(OUT, "w") as f:
    f.write("% generated by make_numbers.py from the result files; do not edit by hand\n")
    for k, v in M.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(M), "macros"); print("\n".join(f"{k} = {v}" for k, v in M.items()))
