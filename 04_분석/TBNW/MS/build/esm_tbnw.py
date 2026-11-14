# esm_tbnw.py — TBNW Thorax Supporting Information(esm_scrt.py 이식, 2026-11-14)(단일 파일: Appendix S1·Table S1-S4·Appendix S2 STROBE) + STROBE 단독 파일(2026-11-14, esm_sknd.py 구조 이식).
#  수치는 결과 CSV에서만. 영국식 철자(TX가 brit 적용), 표 제목 쌍점 금지, 사후 검토는 post hoc 표기, 보충 번호 = 본문 첫 인용 순서(S1 공변량 → S2 우도 → S3 사양 → S4 핫스팟).
import os, re, json, subprocess, pandas as pd
import content_tbnw as C
from build_thorax_tbnw import LABEL, GROUPS, TX, TITLE as DTITLE, foot_row
HERE = os.path.dirname(os.path.abspath(__file__)); MSD = os.path.dirname(HERE); OUT = os.path.join(MSD, "out"); B = os.path.dirname(MSD); RS = os.path.join(B, "results_std3")
N = C.N
from decimal import Decimal, ROUND_HALF_UP
q3 = lambda x: str(Decimal(str(x)).quantize(Decimal("0.001"), ROUND_HALF_UP))
st = lambda t: f"{q3(t[0])} ({q3(t[1])}–{q3(t[2])})"
J = TX(cite="bracket")
def TF(title, header, rows, foot="", fs=8):
    J.page_break(); J.table_fit(title, header, rows, "", fs_max=fs, title_bold=True)
    if foot: foot_row(J, foot, 8, 12)
J.para("<b>Supporting Information</b>"); J.para(f"Supporting information for the manuscript entitled \"{DTITLE}\"")
J.para("Contents. Appendix S1 (supplementary methods and additional results); Table S1 (district characteristics); Table S2 (likelihood comparison); Table S3 (alternative specifications); Table S4 (residual hot spots and cold spots); Appendix S2 (STROBE checklist).")
_MT = pd.read_csv(os.path.join(B, "panel_META_TBNW_std3.csv"), encoding="utf-8-sig").set_index("variable")
gate = open(os.path.join(B, "data_gate_TBNW_std3_261114.txt"), encoding="utf-8").read(); nwarn = int(re.search(r"경고 (\d+)건", gate).group(1))
_vif = _MT.vif_final.dropna().sort_values(ascending=False)
PPC = pd.read_csv(os.path.join(RS, "S42_ppc.csv")).iloc[0].to_dict()
L = pd.read_csv(os.path.join(RS, "S52L_likelihood.csv")).set_index("likelihood")
R25 = N["rule2025"].set_index("variable")
J.page_break(); J.head("Appendix S1. Supplementary methods and additional results", 2)
SM = [("Outcome.", f"Annual new tuberculosis patients (never treated, or treated for less than 1 month) by district of residence for 2013–2025 came from Korean Statistical Information Service table 117N_A00108 of the Korea Disease Control and Prevention Agency, and national new patients by sex and 5-year age group from table 117N_A00102; the 13-year total was {N['cases_total']:,}. "
       "In every year, the sum over the 229 districts equalled the national total. Where a city reported both a city-level row and rows for its general wards (Changwon and Pohang in 2016–2023), the city-level row exceeded the sum of the wards while the provincial and national totals equalled the sum of the wards, so the sum of the wards was used. Sejong, reported only as a provincial-level row, was assigned its district code, and records under former codes (Michuhol-gu, Yeoju, Dangjin, Cheongwon, Gunwi and the Seonsan health centre of Gumi) were mapped to the current districts. "
       "Counts of tuberculosis in foreign nationals are published only nationally (table 117N_A00119) and could not be used at district level. Respiratory tuberculosis deaths (A15–A16) by district came from cause-of-death statistics for 2013–2024."),
      ("Expected cases.", "National new cases by year, sex and age group (5-year groups aggregated to eight 10-year groups, the last 70 years or older; cases of unknown age excluded from the rates) were divided by national populations to give annual sex- and age-specific rates, which were applied to district populations by sex and age group; expected cases were rescaled so that their yearly sum equalled the observed national total. "
       "District populations by sex and age for 2013–2024 came from the notification population file rescaled to the official district totals; for 2025 they came from resident registration for December 2025 matched to districts by a crosswalk in which the December 2024 values were identical to the notification file in all 229 districts. The 2023 age-specific populations of Changwon, which repeated the 2022 values in the source file, were replaced with the official 2023 values (total 1,009,038)."),
      ("Covariates.", "The share of households that are older adults living alone and current smoking came from local statistics and the Korea Community Health Survey; years before 2015 for living alone were interpolated from the 2010 census. Medical Aid type 1 patients, suspected diabetes among national health-screening participants (fasting glucose in the diabetes range without a diagnosis), long-term care hospitals and general hospitals came from National Health Insurance Service statistics. Foreign residents per 1,000 came from local statistics. "
       "Values missing for Sejong in early years were taken from the national district database, which fills them from provincial-level releases. Basic livelihood recipient shares that collapsed in 2021–2023 in Changwon were corrected before use in sensitivity analyses. "
       "For 2025, values published in the national district database were used (living alone, smoking and foreign residents, after confirming that the 2024 values in that database equalled those used for 2013–2024); Medical Aid, suspected diabetes, long-term care and general hospitals were carried forward from 2024, and all models were repeated for 2013–2024."),
      ("Panel checks before modelling.", f"An automated gate run on the analytic panel before any model was fitted reported {nwarn} flags: standardised columns whose yearly means were near 0 (a ratio artefact), the fall in notifications over time, real increases in the share aged 80 years or older, the sex ratio above 100 by definition, the post-2020 indicator (constant by design) and districts with no long-term care or general hospital in any year (true zeros); no flag concerned keys, missing outcome counts or population denominators. "
       f"The highest variance inflation factor was {_vif.iloc[0]:.1f} for the share of older adults living alone, which was retained as pre-specified; models without the share aged 80 years or older are reported in Table S3."),
      ("Models.", f"Software: R 4.6.0 with R-INLA (one thread) and Python 3.9 for data preparation and figures. Fixed effects had normal priors with mean 0 and precision 4 (intercept precision 0.001). The Besag–York–Mollié 2 district effect used penalised-complexity priors (P(σ > 0.5) = 0.01; P(φ < 0.5) = 2/3) on a 593-edge district adjacency graph with island districts linked to the nearest mainland district; the random-walk and independent year effects used penalised-complexity priors (P(σ > 0.5) = 0.01). "
       f"Because seven characteristics have only {N['mv_total']} non-empty subsets, all were fitted instead of a random sample. Kendall's W used annual SIR ranks. Emerging hot spot analysis used annual empirical Bayes SIRs. Five likelihoods and six prior settings gave the same conclusions (Table S2)."),
]
for h, t in SM: J.para(f"<b>{h}</b> {t}")
J.para("<b>Additional results.</b> " + f"Posterior predictive 95% intervals covered {100*PPC['coverage95']:.1f}% of district-years. The post-2020 indicator was not associated with notifications after adjustment ({st(N['covid_main'])}); in the interaction model, the ratio of RRs from 2020 versus before was {st(N['covid'][C.OS])} for living alone and {st(N['covid'][C.FR])} for foreign residents. "
       f"The structured spatial district effect accounted for {100*N['vp']['spatial_structured']:.0f}% of the variance of the linear predictor and the covariates for {100*N['vp']['fixed_covariates']:.0f}%. "
       f"In emerging hot spot analysis, {N['ehsa'].get('Persistent hot', 0)} districts were persistent hot spots, {N['ehsa'].get('Intensifying hot', 0)} intensifying and {N['ehsa'].get('New hot', 0)} new hot spots, and {N['ehsa'].get('Persistent cold', 0)} persistent cold spots. "
       f"For respiratory tuberculosis deaths, the RRs were " + "; ".join(f"{LABEL[v].lower()} {st(N['tbd'][('TBD', v)][:3])}" for v in C.HYP) + ".")
# ── Table S1 ──
DIR = {v: "+" for v in C.HYP}
SRCN = {C.OS: "Local statistics (KOSIS)", C.MA: "National Health Insurance Service", C.DM: "National health screening", C.SM: "Community Health Survey", C.FR: "Local statistics (KOSIS)", C.LTC: "National Health Insurance Service", C.GH: "National Health Insurance Service",
        "urban_population_share": "KOSIS local indicators", "physicians_per_1000": "KOSIS local indicators", "sex_ratio": "KOSIS local indicators", "fiscal_independence": "KOSIS local indicators", "pop80_share": "Resident registration"}
UNIT = {C.OS: "% of households", C.MA: "per 100,000", C.DM: "% of participants", C.SM: "% of adults", C.FR: "log(1 + per 1,000)", C.LTC: "per 100,000 aged ≥ 65", C.GH: "per 100,000",
        "urban_population_share": "%", "physicians_per_1000": "per 1,000", "sex_ratio": "ratio", "fiscal_independence": "%", "pop80_share": "%"}
POOLV = {C.OS: "older_single_household_share", C.MA: "medical_aid1_patients_per_100k", C.DM: "screening_suspected_diabetes_share", C.SM: "current_smoking_rate", C.FR: "foreign_residents_per1000", C.LTC: "ltc_hospitals_per_100k_65", C.GH: "general_hospitals_per_100k",
         "urban_population_share": "urban_population_share", "physicians_per_1000": "physicians_per_1000", "sex_ratio": "sex_ratio", "fiscal_independence": "fiscal_independence", "pop80_share": "pop80_share"}
def y25(v):
    k = POOLV[v]; r = R25.loc[[k]].iloc[0] if k in R25.index else None
    if r is None or pd.isna(r.n_2025_locf): return "Observed"
    return "Carried forward" if int(r.n_2025_locf) >= 228 else ("Observed" if int(r.n_2025_locf) == 0 else f"Observed ({int(r.n_2025_locf)} carried forward)")
rows = []
for g, vs in GROUPS:
    rows.append(["__H__", g])
    for v in vs: rows.append([f"  {LABEL[v].split(' (')[0]}", UNIT[v], SRCN[v], y25(v), ("Forced" if v in C.FORCED else DIR[v])])
TF("Table S1 Source, unit, 2025 values and expected direction of each district characteristic, 229 districts, Republic of Korea, 2013–2025", ["Characteristic", "Unit", "Source", "2025 values", "Direction"], rows,
   "KOSIS, Korean Statistical Information Service; ratio, men per 100 women; forced, in every model. Expected directions were set before any covariate model was fitted. "
   "Carried forward, 2025 value set to the district's 2024 value because the 2025 figure was not yet published. Negative control exposures (separate model): hit-and-run collisions, a traffic-culture index and fires per 10,000 residents.")
# ── Table S2 우도 ──
LN = [("poisson", "Poisson"), ("nbinomial", "Negative binomial"), ("zeroinflatedpoisson1", "Zero-inflated Poisson"), ("zeroinflatednbinomial1", "Zero-inflated negative binomial"), ("poisson+obs_iid", "Poisson with observation-level effect")]
rows = [[lab, f"{L.loc[k,'WAIC']:.1f}", f"{L.loc[k,'DIC']:.1f}", f"{L.loc[k,'neg_logscore']:.1f}", "–" if pd.isna(L.loc[k, "zero_prob"]) else f"{L.loc[k,'zero_prob']:.4f}", "–" if pd.isna(L.loc[k, "size"]) else f"{L.loc[k,'size']:.1f}", "–" if pd.isna(L.loc[k, "expected_zeros"]) else f"{L.loc[k,'expected_zeros']:.0f}"] for k, lab in LN]
TF(f"Table S2 Likelihood comparison for notified new tuberculosis with the principal model specification, {N['n_rows']:,} district-years, Republic of Korea, 2013–2025", ["Likelihood", "WAIC", "DIC", "−Σ log CPO", "Zero probability", "Size", "Expected zeros"], rows,
   f"WAIC, widely applicable information criterion; DIC, deviance information criterion; CPO, conditional predictive ordinate; size, negative binomial size parameter; –, not applicable. Observed district-years with no case: {N['zeros']}. "
   "Expected zeros are the sum of posterior-mean probabilities of a zero count. The principal model used the negative binomial likelihood, chosen before covariates were added by the pre-specified comparison with Poisson. The rate ratios of the seven characteristics were the same to the second decimal under all five likelihoods.", fs=8)
# ── Table S3 사양 ──
NAMES = [("principal", "Principal model"), ("KH_typeI", "Knorr-Held type I"), ("KH_typeII", "Knorr-Held type II"), ("KH_typeIII", "Knorr-Held type III"), ("KH_typeIV", "Knorr-Held type IV"),
         ("icar_besag", "ICAR district effect"), ("iid_only", "IID district effect"), ("no_spatial", "No district effect"), ("knn3", "3 nearest neighbours"), ("knn4", "4 nearest neighbours"), ("knn5", "5 nearest neighbours"),
         ("pc_phi_flat", "Flat prior on mixing"), ("pc_relaxA", "Relaxed priors A"), ("pc_relaxB", "Relaxed priors B"),
         ("B3_smooth_forced", "Smoothed forced controls"), ("C1_poisson_lognormal", "Poisson, observation effect"), ("C2_rw2_year", "RW2 year effect"), ("C3_ar1_year", "AR1 year effect"), ("C4_sido_year_iid", "Province-by-year effect"), ("D1_spatial_plus", "Spatial+-type"),
         ("E0_nolag_from2012", "No lag, from 2012"), ("E1_lag1", "Lag 1 year"), ("E2_lag2", "Lag 2 years"), ("H4_odd_years", "Odd years only"), ("H4_even_years", "Even years only"),
         ("y24", "2013–2024 only"), ("f15", "2015–2025 only"), ("sc", "Crude expected cases"), ("s2", "Share aged 80+ omitted"), ("s577", "Queen graph, 577 edges"),
         ("bw_twoway", "Within-district component"), ("H1_nco_TRANS", "Transport-injury deaths (comparison)"), ("H1_nco_GCA", "Gastric cancer patients (comparison)")]
SS = {**N["s43"], **N["s41"]}; WA = {**N["s43_waic"], **N["s41_waic"]}
SS.update({("f15", c): t for c, t in N["f15"].items()}); WA["f15"] = float(pd.read_csv(os.path.join(RS, "S52S_from2015.csv")).WAIC.iloc[0])
for v in ("s577", "s2", "sc", "y24"): SS.update({(v, c): t for c, t in N["sens"][v].items()}); WA[v] = float(pd.read_csv(os.path.join(B, f"results_{v}", "S3_main_fit.csv")).WAIC.iloc[0])
WA["principal"] = N["waic_main"]; SS.update({("principal", c): (r["IRR"], r["lo"], r["hi"], r["cred"]) for c, r in N["main"].items()})
V5 = (C.OS, C.SM, C.GH, C.DM, C.FR)
for v in V5:
    if v + "__within" in N["bw"]: SS[("bw_twoway", v)] = N["bw"][v + "__within"]
def cell(a, v): t = SS.get((a, v)); return "–" if t is None else st(t)
HN = {C.OS: "Living alone", C.SM: "Smoking", C.GH: "General hospitals", C.DM: "Suspected diabetes", C.FR: "Foreign residents"}
rows = [[lab, f"{WA[a]:.0f}" if a in WA and not a.startswith(("H1_", "bw_")) else "–"] + [cell(a, v) for v in V5] for a, lab in NAMES]
LO = N["leaveout"]
TF("Table S3 Rate ratios per 1 standard deviation across alternative specifications and comparison outcomes, 229 districts, Republic of Korea, 2013–2025", ["Specification", "WAIC"] + [HN[v] for v in V5], rows,
   "Values are rate ratios (95% credible intervals) per 1 standard deviation; –, not estimated. Three planned alternatives were identical to the principal model in these data (no lag from 2013, because 2013 is the first year; extreme-value refilling, because no value met the rule; survey 3-year averages, which apply only to survey variables not in this set) and are not shown or counted. For the within-district row, values are the within-district components (between-district components: "
   + "; ".join(f"{HN[v].lower()} {st(N['bw'][v + '__between'])}" for v in V5 if v + '__between' in N['bw']) + "; foreign residents, not robust, were not decomposed" + "). For the Spatial+-type model, rate ratios are per 1 standard deviation of the residualised covariate. "
   "Comparison outcomes (2013–2024) were fitted with the same covariates and model. WAIC is not comparable across outcomes, numbers of years or expected-case definitions; ICAR, intrinsic conditional autoregressive; IID, independent and identically distributed; RW2, second-order random walk; AR1, first-order autoregressive. "
   f"Omitting each province, living alone, smoking, general hospitals and suspected diabetes were credible with the same sign in {', '.join(str(LO[('province', v)][1]) for v in V5[:4])} of {LO[('province', C.OS)][0]} fits; omitting each year, in {', '.join(str(LO[('year', v)][1]) for v in V5[:4])} of {LO[('year', C.OS)][0]}.", fs=7)
# ── Table S4 핫·콜드 ──
EN = {"서울시": "Seoul", "부산시": "Busan", "대구시": "Daegu", "인천시": "Incheon", "광주시": "Gwangju", "대전시": "Daejeon", "울산시": "Ulsan", "세종시": "Sejong", "경기도": "Gyeonggi-do", "강원도": "Gangwon-do", "충청북도": "Chungcheongbuk-do",
      "충청남도": "Chungcheongnam-do", "전라북도": "Jeollabuk-do", "전라남도": "Jeollanam-do", "경상북도": "Gyeongsangbuk-do", "경상남도": "Gyeongsangnam-do", "제주도": "Jeju"}
ROM = json.load(open(os.path.join(HERE, "district_romanization_all.json"), encoding="utf-8"))
S6 = N["s6"].copy(); S6["sido"] = S6.fbd_region.str.extract(r"^(\S+?(?:도|시))")[0]
rows = []
for cls, lab in (("hotspot", "Hot spots"), ("coldspot", "Cold spots")):
    q = S6[S6["class"] == cls].sort_values(["sido", "RR"], ascending=[True, cls != "hotspot"]); rows.append(["__H__", f"{lab} ({len(q)})"])
    for r in q.itertuples(): rows.append([f"  {EN[r.sido]}", ROM[r.fbd_region], f"{r.RR:.2f} ({r.lo:.2f}–{r.hi:.2f})", (">0.999" if r.P_gt1 > 0.9995 else ("<0.001" if r.P_gt1 < 0.0005 else f"{r.P_gt1:.3f}")), f"{r.SIR_obs:.2f}"])
TF("Table S4 Residual hot spots and cold spots of notified new tuberculosis, 229 districts, Republic of Korea, 2013–2025", ["Province", "District", "Residual spatial RR (95% CrI)", "P(RR > 1)", "Observed SIR"], rows,
   "RR, rate ratio from the district effect of the principal model; CrI, credible interval; SIR, standardised incidence ratio over 13 years. Hot spots: posterior probability of RR > 1 above 0.95; cold spots: below 0.05. Exploratory; not adjusted for multiple comparisons.", fs=7)
assert not any(isinstance(r[1], str) and re.search(r"[가-힣]", r[1]) for r in rows if r[0] != "__H__"), "untranslated district name"
# ── STROBE ──
MH = [x[0] for x in C.METHODS]; RH = [x[0] for x in C.RESULTS]
CK = [("Title and abstract", "1", "Title page; Abstract"), ("Background/rationale", "2", "Introduction"), ("Objectives", "3", "Introduction, final paragraph"),
      ("Study design", "4", f"Methods, {MH[0]}"), ("Setting", "5", f"Methods, {MH[0]}"), ("Participants", "6", f"Methods, {MH[0]} (all notified cases; ecological)"),
      ("Variables", "7", f"Methods, {MH[1]}; {MH[2]}; Table S1"), ("Data sources/measurement", "8", "Methods; Appendix S1"),
      ("Bias", "9", f"Methods, {MH[1]}; {MH[3]}; Table S3"), ("Study size", "10", f"Methods, {MH[0]} (all 229 districts)"), ("Quantitative variables", "11", f"Methods, {MH[2]}"),
      ("Statistical methods", "12", f"Methods, {MH[3]}; Appendix S1; Table S2"), ("Participants (flow)", "13", "Not applicable (aggregate district data; no exclusions)"),
      ("Descriptive data", "14", f"Results, {RH[0]}; Table 1"), ("Outcome data", "15", f"Results, {RH[0]}; Table 1; Figure 1"),
      ("Main results", "16", f"Results, {RH[1]}; {RH[2]}; Table 2; Figures 2–3"), ("Other analyses", "17", f"Results, {RH[2]}; Tables S2–S4"),
      ("Key results", "18", "Discussion, Main findings"), ("Limitations", "19", "Discussion, Strengths and limitations"), ("Interpretation", "20", "Discussion"), ("Generalisability", "21", "Discussion, Implications"),
      ("Other information (funding, code)", "22", "Funding; Data availability statement")]
J.page_break()
J.table_fit("Appendix S2 STROBE checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], "", fs_max=8, title_bold=True)
foot_row(J, "STROBE, Strengthening the Reporting of Observational Studies in Epidemiology.", 8, 12)
ps = os.path.join(OUT, "Supporting_Information_Thorax_TBNW.docx"); J.doc_title = "Supporting Information"; J.save(ps)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_tbnw_esm", "--convert-to", "pdf", "--outdir", OUT, ps], check=True, capture_output=True)
print("saved", os.path.basename(ps))
K = TX(cite="bracket"); K.para("<b>STROBE checklist</b>"); K.para(f"Manuscript \"{DTITLE}\"")
K.table_fit("STROBE checklist for this ecological study", ["Item", "No.", "Where reported"], [[a, b, c] for a, b, c in CK], "", fs_max=9, title_bold=True)
foot_row(K, "Section names refer to the main manuscript and the Supporting Information.", 8, 12)
pk = os.path.join(OUT, "STROBE_Checklist_Thorax_TBNW.docx"); K.doc_title = "STROBE checklist"; K.save(pk)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_tbnw_esm", "--convert-to", "pdf", "--outdir", OUT, pk], check=True, capture_output=True)
print("saved", os.path.basename(pk))
