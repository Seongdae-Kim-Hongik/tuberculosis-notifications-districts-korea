# numbers_tbnw.py — TBNW(결핵 신환자 신고) Thorax 원고의 모든 수치를 결과 CSV에서 읽는다(2026-11-14, numbers_scrt.py 이식). 손입력 금지, assert로 정합 확인.
import os, glob, numpy as np, pandas as pd
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3"); DESC = os.path.join(B, "results_desc")
ROOT = os.path.dirname(os.path.dirname(B)); PAN = os.path.join(ROOT, "02_패널")
SHP = os.environ.get("ST_SHP", os.path.expandvars("$ST_DATA_ROOT") + "/기타/R_Studio/FBD_DATA_ZIP/final.shp")
WIN = [("W1_2013-15", 2013, 2015), ("W2_2016-19", 2016, 2019), ("W3_2020-25", 2020, 2025)]
rd = lambda f, d=RS, **k: pd.read_csv(os.path.join(d, f), encoding="utf-8-sig", **k)
OS, MA, DM, SM, FR, LTC, GH = ("older_single_household_share", "medical_aid1_patients_per_100k", "screening_suspected_diabetes_share", "current_smoking_rate", "foreign_residents_per_1000", "ltc_hospitals_per_100k_65", "general_hospitals_per_100k")
HYP = [OS, MA, DM, SM, FR, LTC, GH]
FORCED = ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"]
P80 = "pop80_share"

def load():
    N = {}
    P = pd.read_csv(os.path.join(B, "panel_TBNW_std3.csv")); N["n_rows"], N["n_districts"] = len(P), P.fbd_region.nunique(); assert (N["n_rows"], N["n_districts"]) == (2977, 229)
    N["cases_total"] = int(P.cases.sum()); assert N["cases_total"] == 310743
    N["zeros"] = int((P.cases == 0).sum())
    yc = P.groupby("year").cases.sum().astype(int); N["n_y"] = yc.to_dict(); assert N["n_y"][2013] == 36089 and N["n_y"][2025] == 13713
    N["peak_year"] = int(yc.idxmax()); N["peak_n"] = int(yc.max())
    D = rd("S52D_national.csv", DESC); N["asr"] = {(r.year, r.sex): r.asr_2020 for r in D.itertuples()}; N["crude"] = {(r.year, r.sex): r.crude for r in D.itertuples()}
    N["cases_sex"] = D[D.sex != "Both"].groupby("sex").cases.sum().to_dict(); assert sum(N["cases_sex"].values()) == N["cases_total"]
    N["pct_women"] = 100 * N["cases_sex"]["Women"] / N["cases_total"]
    AR = rd("S52D_agerate.csv", DESC); N["agerate"] = {(r.sex, r.age): r.rate_per100k_py for r in AR.itertuples()}
    AG = AR.groupby("age").cases.sum(); N["pct70"] = 100 * AG["70세 이상"] / AG.sum()
    OSH = rd("S52D_oldshare.csv", DESC).set_index("year"); N["pct65"] = OSH.pct65.to_dict(); N["pct80"] = OSH.pct80.to_dict()
    TBD = rd("S52T_tbd_aux.csv"); N["tbd"] = {(r.outcome[:4].strip(), r.variable): (r.IRR, r.lo, r.hi, bool(r.credible)) for r in TBD.itertuples()}; N["tbd_cases"] = int(TBD[TBD.outcome.str.startswith("TBD")].cases.iloc[0])
    T1 = {}
    for wn, a, b in WIN + [("ALL", 2013, 2025)]:
        q = P[P.year.between(a, b)]; sir = q.groupby("fbd_region").apply(lambda d: d.cases.sum() / d.E.sum(), include_groups=False)
        T1[wn] = dict(n=len(q), cases=int(q.cases.sum()), zeros=int((q.cases == 0).sum()), p10=sir.quantile(.1), med=sir.median(), p90=sir.quantile(.9),
                      cov={v: (q[f"{v}_raw"].mean(), q[f"{v}_raw"].std()) for v in HYP + FORCED})
    N["T1"] = T1
    lk = rd("S1_likelihood.csv"); lk = lk[lk.set == "REF_forced_only"].set_index("family").WAIC; N["waic_pois"], N["waic_nb"] = lk["poisson"], lk["nbinomial"]; assert N["waic_nb"] < N["waic_pois"]
    hb = open(os.path.join(B, "HM_best_TBNW_std3.txt")).read(); N["waic_forced"] = float(hb.split("ref_forced_only_WAIC=")[1].split()[0]); N["waic_main"] = float(hb.split("S1_narrative_full(")[1].split(",")[0])
    s6m = rd("S6_moran_year.csv"); N["moran_year"] = (s6m.moran_I.min(), s6m.moran_I.max()); N["moran_y"] = s6m.set_index("year").moran_I.to_dict()
    r8 = rd("S8_residual_moran.csv").set_index("quantity"); N["moran_pooled"] = r8.loc["observed_logSIR_pooled", "moran_I"]
    N["moran_resid"], N["moran_resid_p"] = r8.loc["pearson_residual_area_mean", "moran_I"], r8.loc["pearson_residual_area_mean", "p_perm"]
    h = rd("S3_main_hyper.csv"); ph = h[h.hyperpar.str.startswith("Phi")].iloc[0]; N["phi"] = (ph["mean"], ph["X0.025quant"], ph["X0.975quant"])
    s6 = rd("S6_spatial_RR.csv"); N["s6"] = s6; N["rr_min"], N["rr_max"] = s6.RR.min(), s6.RR.max()
    N["n_hot"], N["n_cold"] = int((s6["class"] == "hotspot").sum()), int((s6["class"] == "coldspot").sum())
    sido = s6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
    N["hot_by_sido"] = s6[s6["class"] == "hotspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    N["cold_by_sido"] = s6[s6["class"] == "coldspot"].groupby(sido).size().sort_values(ascending=False).to_dict()
    gun = s6.fbd_region.str.endswith("군"); N["hot_gun"] = int((gun & (s6["class"] == "hotspot")).sum()); N["n_gun"] = int(gun.sum())
    pe = rd("S12_persistence.csv").set_index("set"); N["kendall"] = pe.kendall_W.to_dict()
    N["ehsa"] = rd("S11_ehsa_summary.csv").set_index("category").n.to_dict()
    vp = rd("S42_variance_partition.csv").set_index("component"); N["vp"] = vp.share_of_linear_predictor_var.to_dict()
    d = P.groupby("fbd_region").agg(c=("cases", "sum"), e=("E", "sum")).reset_index(); d["sir"] = d.c / d.e
    N["sir_p90p10"] = d.sir.quantile(.9) / d.sir.quantile(.1)
    w = P.groupby(["fbd_region", "window"]).agg(c=("cases", "sum"), e=("E", "sum")).reset_index(); w["sir"] = w.c / w.e
    pw = w.pivot(index="fbd_region", columns="window", values="sir").corr(method="spearman"); N["rho_win"] = (pw.values[np.triu_indices(3, 1)].min(), pw.values[np.triu_indices(3, 1)].max())
    m3 = rd("S3_main_IRR.csv").set_index("cov"); N["main"] = m3[["IRR", "lo", "hi", "cred", "role"]].to_dict("index")
    N["n_hyp"] = int((m3.role == "hypothesis").sum()); assert N["n_hyp"] == 7 and set(m3.index[m3.role == "hypothesis"]) == set(HYP)
    N["cred_hyp"] = sorted(v for v in HYP if N["main"][v]["cred"])
    s7 = rd("S7_multiverse_summary.csv").set_index("cov"); N["mv"] = s7[["n_specs", "cred_frac", "sign_agree", "robust"]].to_dict("index"); N["robust"] = sorted(s7.index[s7.robust])
    N["mv_total"] = int(s7.n_specs_total.iloc[0])
    nc = rd("S3_negcontrol.csv").set_index("cov"); N["negctl"] = {v: (r.IRR, r.lo, r.hi, bool(r.cred)) for v, r in nc.iterrows()}
    wi = rd("S4_window_IRR.csv"); N["win"] = {(r.cov, r.window): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in wi.itertuples()}
    S43 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S43_part_*.csv"))]); N["s43"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S43.itertuples()}
    N["s43_waic"] = S43.groupby("analysis").WAIC.first().to_dict()
    T9 = rd("S9_typeI_IRR.csv"); N["s43"].update({("KH_typeI", r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in T9.itertuples()}); N["s43_waic"]["KH_typeI"] = float(T9.WAIC.iloc[0])
    S41 = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(RS, "S41_part_*.csv"))]); N["s41"] = {(r.analysis, r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41.itertuples()}
    N["s41_waic"] = S41.groupby("analysis").WAIC.first().to_dict()
    N["alt"] = sorted({a for a in S41.analysis.unique() if not a.startswith(("F1_", "F2_", "G2_", "H1_", "bw_"))})
    ret = rd("S41_retention_by_cov.csv").set_index("cov"); N["ret"] = {v: (int(ret.loc[v, "kept"]), int(ret.loc[v, "n_specs"])) for v in ret.index}
    N["bw"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis == "bw_twoway"].itertuples()}
    N["nco"] = {(r.analysis.replace("H1_nco_", ""), r.cov): (r.IRR, r.lo, r.hi, bool(r.cred)) for r in S41[S41.analysis.str.startswith("H1_nco_")].itertuples()}
    lo = rd("S41_leaveout_ranges.csv"); N["leaveout"] = {(r.set, r.cov): (r.n, r.n_cred_same_sign) for r in lo.itertuples() if not str(r.cov).startswith("__")}
    N["evalue"] = rd("S41_evalues.csv").set_index("cov").to_dict("index")
    F15 = rd("S52S_from2015.csv"); N["f15"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in F15.itertuples()}
    NOOP = ("E0_nolag_from2013", "F3_extreme_R7", "G1_kchs_ma3")   # 주모형과 같은 입력(2013 시작=무지연, 극단값 0건, KCHS 3년 평균 비적용 변수) → 대안 분모에서 제외(11/14 review)
    N["noop"] = list(NOOP); N["alt_valid"] = [a for a in N["alt"] if a not in NOOP]
    N["altk"] = {v: sum(1 for a in N["alt_valid"] if N["s41"][(a, v)][3] and (N["s41"][(a, v)][0] > 1) == (N["main"][v]["IRR"] > 1)) for v in HYP}
    N["sens"] = {}
    for v in ("s577", "s2", "sc", "y24"):
        m = pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_IRR.csv")).set_index("cov"); N["sens"][v] = {c: (m.loc[c, "IRR"], m.loc[c, "lo"], m.loc[c, "hi"], bool(m.loc[c, "cred"])) for c in m.index}
    cv = rd("S5_covid.csv"); N["covid_main"] = tuple(cv[cv.term == "post_main"][["IRR", "lo", "hi", "cred"]].iloc[0])
    eb = rd("S12c_yearly_EB_SIR.csv"); g = eb.groupby("year").ebSIR; gap = pd.DataFrame({"p10": g.quantile(.1), "p90": g.quantile(.9)}); gap["ratio"] = gap.p90 / gap.p10; N["gap"] = gap.to_dict("index")
    N["sd"] = {v: P[f"{v}_raw"].std() for v in HYP}
    cv = rd("S5_covid.csv"); cv = cv[cv.term == "var_x_post"]; N["covid"] = {r.cov: (r.IRR, r.lo, r.hi, bool(r.cred)) for r in cv.itertuples()}
    R25 = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_TBNW_2025rule.csv"), encoding="utf-8-sig"); N["rule2025"] = R25
    return N

if __name__ == "__main__":
    N = load()
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in N.items() if not isinstance(v, (dict, list, pd.DataFrame, tuple))})
    for k in ("phi", "moran_year", "covid_main", "rho_win", "robust", "cred_hyp"): print(k, N[k])
    print("hot", N["hot_by_sido"]); print("cold", N["cold_by_sido"]); print("kendall", N["kendall"]); print("bw", {k: tuple(round(x, 3) for x in v[:3]) + (v[3],) for k, v in N["bw"].items()})
    print("mv", {k: (round(v["cred_frac"], 2), v["robust"]) for k, v in N["mv"].items()}); print("ret", N["ret"]); print("evalue", N["evalue"]); print("waicKH", N["s43_waic"])
