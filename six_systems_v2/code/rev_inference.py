"""v13 revision (exploratory): pooled inference on the event-minus-winter C1 gap with small-cluster
methods. Clusters are distinct continental cold outbreaks: events whose windows lie within 3 days of
each other (transitively) form one cluster. Writes analysis/rev_clusters.csv and analysis/rev_inference.csv."""
import os, itertools
import numpy as np, pandas as pd
from scipy import stats
import a9_common as A
OUT = os.path.join(A.HERE, "analysis"); rng = np.random.default_rng(2026)
FD = os.path.join(os.path.dirname(A.HERE), "final_data")
E = pd.read_csv(os.path.join(FD, "a9_events_L1_gefs.csv")); E["set"] = "primary"
K = pd.read_csv(os.path.join(FD, "a11_events.csv")); K["set"] = "A11"
X = pd.concat([E[["system", "era", "c1_ev", "c1_per", "set"]], K[["system", "era", "c1_ev", "c1_per", "set"]]], ignore_index=True)
X["gap"] = 100 * (X.c1_per - X.c1_ev)
X["start"] = [pd.Timestamp(A.events(s)[str(e)]["start"]) for s, e in zip(X.system, X.era)]
X["end"] = [pd.Timestamp(A.events(s)[str(e)]["end"]) for s, e in zip(X.system, X.era)]
# clusters by window proximity (3-day tolerance), transitive
par = list(range(len(X)))
def f(i):
    while par[i] != i: i = par[i]
    return i
for i, j in itertools.combinations(range(len(X)), 2):
    if X.start[i] <= X.end[j] + pd.Timedelta(days=3) and X.start[j] <= X.end[i] + pd.Timedelta(days=3): par[f(i)] = f(j)
roots = [f(i) for i in range(len(X))]; lab = {r: k for k, r in enumerate(sorted(set(roots), key=lambda r: X.start[[i for i in range(len(X)) if f(i) == r]].min()))}
X["cluster"] = [lab[r] for r in roots]
X["cluster_name"] = X.groupby("cluster").start.transform(lambda s: s.min().strftime("%b %Y"))
X.to_csv(os.path.join(OUT, "rev_clusters.csv"), index=False)
def infer(d, col="gap"):
    v = d[col].values; cl = d.cluster.values; G = len(np.unique(cl)); est = v.mean()
    keys = np.unique(cl); groups = {k: v[cl == k] for k in keys}
    bs = [np.mean(np.concatenate([groups[k] for k in rng.choice(keys, G)])) for _ in range(10000)]
    pb = np.percentile(bs, [2.5, 97.5])
    # CR1 cluster-robust SE for the mean, t with G-1 df
    u = v - est; S = np.array([u[cl == k].sum() for k in keys]); n = len(v)
    se = np.sqrt((G / (G - 1)) * np.sum(S ** 2)) / n; tq = stats.t.ppf(0.975, G - 1); cr1 = (est - tq * se, est + tq * se)
    # wild cluster bootstrap-t (Webb 6-point weights), null imposed: H0 mean = 0
    w6 = np.array([-np.sqrt(1.5), -1, -np.sqrt(0.5), np.sqrt(0.5), 1, np.sqrt(1.5)])
    t0 = est / se; tb = []
    for _ in range(9999):
        wk = dict(zip(keys, rng.choice(w6, G))); vb = np.array([v[i] * wk[cl[i]] for i in range(n)])   # restricted residuals = v under H0
        eb = vb.mean(); ub = vb - eb; Sb = np.array([ub[cl == k].sum() for k in keys]); seb = np.sqrt((G / (G - 1)) * np.sum(Sb ** 2)) / n
        tb.append(eb / seb)
    p_wild = float(np.mean(np.abs(tb) >= abs(t0)))
    # exact (or Monte-Carlo) sign-flip randomisation on cluster sums, H0: symmetric about 0
    sums = np.array([v[cl == k].sum() for k in keys]); obs = sums.sum()
    flips = itertools.product([-1, 1], repeat=G) if G <= 16 else (rng.choice([-1, 1], G) for _ in range(100000))
    sims = np.array([np.dot(s, sums) for s in flips]); tol = 1e-9 * max(1.0, abs(obs)); p1 = float(np.mean(sims >= obs - tol)); p2 = float(np.mean(np.abs(sims) >= abs(obs) - tol))
    cm = d.groupby("cluster")[col].mean(); tcm = stats.ttest_1samp(cm, 0)
    return dict(n=n, G=G, estimate=est, pboot_lo=pb[0], pboot_hi=pb[1], cr1_lo=cr1[0], cr1_hi=cr1[1], p_wild=p_wild,
                p_signflip_1s=p1, p_signflip_2s=p2, cluster_mean_est=cm.mean(), cluster_mean_p2=tcm.pvalue, share_below=float((d.c1_ev < d.c1_per).mean()))
V = pd.read_csv(os.path.join(OUT, "rev_events.csv"))[["system", "era", "pct_C1"]]
X = X.merge(V, on=["system", "era"], how="left"); X["rank_dev"] = 100 * (0.5 - X.pct_C1)   # >0: event coverage ranks below the winter's median window
rows = []
for nm_, d in [("primary13", X[X.set == "primary"]), ("A11", X[X.set == "A11"]), ("all38", X)]:
    r = infer(d.reset_index(drop=True)); r["set"] = nm_; r["quantity"] = "gap"; rows.append(r)
    r = infer(d.reset_index(drop=True), "rank_dev"); r["set"] = nm_; r["quantity"] = "rank_dev"; r["mean_pct"] = float(d.pct_C1.mean()); r["n_below10"] = int((d.pct_C1 < 0.10).sum()); rows.append(r)
# v13b sensitivity (N4): drop ERCOT, drop the two Uri events, cluster by winter instead of outbreak
Xw = X.copy(); Xw["cluster"] = [d.year + (1 if d.month == 12 else 0) for d in Xw.start]   # v14: winter from the event date (PJM/MISO era 2022 = winter 2022-23)
for nm_, d in [("all38_noERCOT", X[X.system != "ercot"]), ("all38_noUri", X[~((X.era == 2021) & X.system.isin(["ercot", "spp"]))]), ("all38_byWinter", Xw)]:
    r = infer(d.reset_index(drop=True)); r["set"] = nm_; r["quantity"] = "gap"; rows.append(r)
    r = infer(d.reset_index(drop=True), "rank_dev"); r["set"] = nm_; r["quantity"] = "rank_dev"; r["mean_pct"] = float(d.pct_C1.mean()); r["n_below10"] = int((d.pct_C1 < 0.10).sum()); rows.append(r)
# v13b factorial with CR1 intervals over the primary outbreaks (N5)
F = pd.read_csv(os.path.join(FD, "a13_events.csv")).merge(X[X.set == "primary"][["system", "era", "cluster"]], on=["system", "era"])
for k in ["SA", "LA", "SW", "LW"]:
    d = F.rename(columns={f"{k}_gap": "gapk"}).dropna(subset=["gapk"])
    d = d.assign(c1_ev=d[f"{k}_ev"], c1_per=d[f"{k}_per"])
    r = infer(d.reset_index(drop=True), "gapk"); r["set"] = f"factorial_{k}"; r["quantity"] = "gap"; rows.append(r)
# v15 (A3): events in the operational-GEFS period only (event start on or after 2020-01-01)
op = X[X.start >= pd.Timestamp("2020-01-01")]
# v15b: rule-defined events only (drop the six report-defined PJM/MISO windows)
rep = {("pjm", 2014), ("pjm", 2018), ("pjm", 2022), ("miso", 2018), ("miso", 2019), ("miso", 2022)}
ruled = X[[(s, int(e)) not in rep for s, e in zip(X.system, X.era)]]
op = pd.concat([op.assign(_k=0)]).drop(columns="_k")
for nm_, d in [("all38_ruleOnly", ruled), ("all38_opGEFS", op), ("all38_opGEFS_noERCOT", op[op.system != "ercot"])]:
    r = infer(d.reset_index(drop=True)); r["set"] = nm_; r["quantity"] = "gap"; r["mean_ev"] = d.c1_ev.mean(); r["mean_per"] = d.c1_per.mean(); rows.append(r)
    r = infer(d.reset_index(drop=True), "rank_dev"); r["set"] = nm_; r["quantity"] = "rank_dev"; r["mean_pct"] = float(d.pct_C1.mean()); r["n_below10"] = int((d.pct_C1 < 0.10).sum()); rows.append(r)
# v14: operator-forecast intervals (A12) with the same cluster-robust methods (primary outbreak clusters)
Op = pd.read_csv(os.path.join(FD, "a12_summary.csv")).merge(X[X.set == "primary"][["system", "era", "cluster"]], on=["system", "era"])
r = infer(Op.rename(columns={"gap": "gapop"}).reset_index(drop=True), "gapop"); r["set"] = "operator12"; r["quantity"] = "gap"; rows.append(r)
r = infer(Op.assign(evpp=100 * Op.c1_ev).reset_index(drop=True), "evpp"); r["set"] = "operator12"; r["quantity"] = "event_cov_pp"; rows.append(r)
R = pd.DataFrame(rows); R.to_csv(os.path.join(OUT, "rev_inference.csv"), index=False)
pd.set_option("display.width", 250); print(R.round(3).to_string())
print(X.groupby(["cluster", "cluster_name"]).agg(n=("gap", "size"), gap=("gap", "mean"), systems=("system", lambda s: ",".join(sorted(set(s))))).round(1).to_string())
