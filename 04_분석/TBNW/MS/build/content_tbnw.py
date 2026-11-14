# content_tbnw.py — TBNW Thorax 원저의 제목·Methods·Results 문장(수치는 numbers_tbnw에서만, 2026-11-14, content_scrt.py 구조 이식).
#  Thorax 규정(MS/00_Thorax_투고규정_261114.md): 본문 ≤3,500, 초록 ≤250(Background/Methods/Results/Conclusions), 참고문헌 ≤40, 제목 ≤20단어, Key messages, STROBE, 인과 표현 금지.
#  단독 저자 → 1인칭 금지. 결과 절에 해석 금지. 제목·소제목 쌍점 금지.
from numbers_tbnw import load, HYP, FORCED, P80, OS, MA, DM, SM, FR, LTC, GH
N = load()
def tci(t): return f"RR {t[0]:.3f}, 95% CrI {t[1]:.3f}–{t[2]:.3f}"
def ci(v): r = N["main"][v]; return tci((r["IRR"], r["lo"], r["hi"]))
def sh(t): return f"{t[0]:.3f} ({t[1]:.3f}–{t[2]:.3f})"
M = N["main"]; T1 = N["T1"]
S43 = lambda a, v: N["s43"][(a, v)]
S41 = lambda a, v: N["s41"][(a, v)]
BW = lambda k: N["bw"][k]
NCO = lambda o, v: N["nco"][(o, v)]
SEN = lambda s, v: N["sens"][s][v]
WIN = lambda v, w: N["win"][(v, w)]
KH = ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV"); BEST_KH = min(KH, key=lambda a: N["s43_waic"][a])
EN = {"서울시": "Seoul", "경기도": "Gyeonggi-do", "충청남도": "Chungcheongnam-do", "충청북도": "Chungcheongbuk-do", "부산시": "Busan", "전라남도": "Jeollanam-do", "전라북도": "Jeollabuk-do",
      "광주시": "Gwangju", "경상남도": "Gyeongsangnam-do", "경상북도": "Gyeongsangbuk-do", "강원도": "Gangwon-do", "인천시": "Incheon", "대전시": "Daejeon", "울산시": "Ulsan", "대구시": "Daegu",
      "세종시": "Sejong", "제주도": "Jeju"}
def sidos(d, k=4): return ", ".join(f"{EN[a]} ({b})" for a, b in list(d.items())[:k])
TITLE = "As tuberculosis declined in Korea, its district geography concentrated rather than flattened"
RUNNING = "Where tuberculosis remains in Korea"
KEYWORDS = "tuberculosis; epidemiology; notification; small-area analysis; older adults; smoking; Republic of Korea"
assert len(TITLE.split()) <= 20 and ":" not in TITLE and "229" not in TITLE
SUP = {"methods": "Appendix S1", "covariates": "Table S1", "lik": "Table S2", "specs": "Table S3", "hot": "Table S4", "strobe": "Appendix S2"}
sup = lambda k: SUP[k]
RET = N["ret"]
MVN = lambda v: f"{round(N['mv'][v]['cred_frac']*N['mv'][v]['n_specs'])}/{N['mv'][v]['n_specs']}"
A0 = lambda y: N["asr"][(y, "Both")]
GAP = N["gap"]

METHODS = [
("Study design and data",
 f"This ecological study covered all {N['n_districts']} districts (urban wards, cities and counties) of the Republic of Korea, harmonised to 2024 boundaries, from 2013 to 2025 ({N['n_rows']:,} district-years), and is reported according to the STROBE statement [@vonelm2007strengthening] ({sup('strobe')}). "
 "Tuberculosis is a notifiable disease in Korea, and the national tuberculosis surveillance system collects notifications from all medical institutions [@lew2006an]; the Korea Disease Control and Prevention Agency publishes annual counts of new cases (people never treated or treated for less than 1 month, regardless of nationality) by district of residence from 2013 and nationally by sex and age group [@web:kdca2026tb]; new cases exclude retreatment cases, so they are fewer than all notified cases. "
 "Counts for 2026 were excluded because the year was incomplete. Resident populations by sex and age came from resident registration [@web:mois2026population]. Districts were joined across sources by administrative code only; where a city reported both the city and its wards, the sum of the wards was used because it matched the provincial and national totals, and Sejong, which is published only as a provincial-level unit, was included in every year. "
 "Only published aggregate statistics were used. The Institutional Review Board of Hongik University approved the study (7002340-202511-HR-012) and its continuing review (7002340-202611-HR-040) and waived informed consent."),
("Outcome and expected cases",
 "The outcome was the annual number of notified new tuberculosis cases by district of residence. Expected cases were obtained by indirect standardisation, applying national new-case rates by year, sex and eight age groups (10-year groups to 70 years or older) to each district population, and the ratio of observed to expected cases is the standardised incidence ratio (SIR) [@inskip1983methods]. "
 f"Respiratory tuberculosis deaths (ICD-10 A15–A16) by district of residence for 2013–2024, standardised in the same way, served as an auxiliary outcome ({sup('methods')})."),
("District characteristics",
 f"Seven characteristics were fixed before any covariate model was fitted, each hypothesised to be positively associated with notifications ({sup('covariates')}). "
 "The share of households that are older adults living alone was included as a marker of older populations with less household support, among whom reactivation and delayed care-seeking are plausible [@carauxpaz2021tuberculosis; @nordholm2022social]; its values before 2015 were interpolated from the 2010 census. Deprivation was represented by Medical Aid type 1 patients per 100,000 residents, the means-tested public coverage for the poorest households [@choi2023lower; @nguipdopdjomo2020smallarea]; "
 "host susceptibility by the share of national health-screening participants with suspected diabetes and the current smoking rate from the Korea Community Health Survey [@jeon2008diabetes; @yoo2021diabetes; @jee2009smoking]; migration from higher-burden countries by foreign residents per 1,000 residents (log scale) [@lee2024incidence]; "
 "congregate care by long-term care hospitals per 100,000 residents aged 65 years or older [@seto2017mycobacterium]; and diagnostic access by general hospitals per 100,000 residents. "
 "Five controls were forced into every model: urban population share, physicians per 1,000 residents, sex ratio, fiscal autonomy and the population share aged 80 years or older. "
 "Medical Aid, suspected diabetes, long-term care hospitals and general hospitals for 2025 were carried forward from 2024, and all models were repeated for 2013–2024. "
 "Three negative control exposures with no plausible association with tuberculosis (hit-and-run collisions, a traffic-culture index and fires) were fitted in a separate model [@lipsitch2010negative]. All characteristics were standardised to mean 0 and standard deviation (SD) 1. The aim was to describe associations, not to estimate causal effects."),
("Statistical analysis",
 f"Five likelihoods were compared with the forced controls and the same random effects ({sup('lik')}). The principal model was negative binomial, chosen by the pre-specified rule of a lower widely applicable information criterion (WAIC) than Poisson in models with the forced controls only ({N['waic_nb']:,.1f} versus {N['waic_pois']:,.1f}), "
 "with an offset of log expected cases, a Besag–York–Mollié 2 district effect with penalised-complexity priors [@besag1991bayesian; @riebler2016an; @simpson2017penalising] and random-walk and independent year effects, fitted by integrated nested Laplace approximation in R 4.6.0 [@rue2009approximate]. "
 "Rate ratios (RRs) per 1 SD are reported with 95% credible intervals (CrIs), and an association was called credible when its interval excluded 1. "
 "Residual hot spots and cold spots were districts whose posterior probability of a residual spatial RR above 1 exceeded 0.95 or fell below 0.05. Persistence of district rankings was measured by Kendall's W over annual SIRs, relative concentration by the ratio of the 90th to the 10th percentile of annual empirical Bayes (smoothed) SIRs, and spatial autocorrelation by Moran's I of annual log SIRs.",
 f"Robustness was assessed in all {N['mv_total']} models formed by the non-empty subsets of the seven characteristics (an operational criterion set in advance: credible in at least 75% of the models containing the characteristic with at least 95% sign agreement) [@steegen2016increasing]; four Knorr-Held space–time interactions [@knorrheld2000bayesian]; refits in 2013–2015, 2016–2019 and 2020–2025; between-district and within-district components entered together; "
 f"{len(N['alt_valid'])} alternative fits of likelihood, temporal structure, one- and two-year lags, spatial confounding [@dupont2022spatial] and odd or even years; omission of each province and each year; a different adjacency graph; omission of the share aged 80 years or older; crude expected cases; restriction to 2013–2024; and restriction to 2015–2025, when the living-alone share was observed annually ({sup('specs')}). "
 "Transport-injury deaths and patients treated for gastric cancer, which share the rural and socioeconomic gradients of Korean districts but not the pathogen, were fitted with the same model as exploratory comparison outcomes for 2013–2024, and E-values were computed for the point estimates and the credible limits closer to 1 [@vanderweele2017sensitivity]."),
]

hot = sidos(N["hot_by_sido"], 5); cold = sidos(N["cold_by_sido"], 3)
AK = N["altk"]; NA = len(N["alt_valid"]); F15 = N["f15"]
RESULTS = [
("Notifications",
 f"From 2013 to 2025, {N['cases_total']:,} new tuberculosis cases were notified. Annual counts fell from {N['n_y'][2013]:,} to {N['n_y'][2025]:,} ({100*(1-N['n_y'][2025]/N['n_y'][2013]):.0f}% fewer), and the age-standardised rate fell from {A0(2013):.1f} to {A0(2025):.1f} per 100,000 ({100*(1-A0(2025)/A0(2013)):.0f}% lower; Figure 1). "
 f"The share of cases aged 65 years or older rose from {N['pct65'][2013]:.1f}% to {N['pct65'][2025]:.1f}% and the share aged 80 years or older from {N['pct80'][2013]:.1f}% to {N['pct80'][2025]:.1f}%. "
 f"Men accounted for {N['cases_sex']['Men']:,} cases ({100-N['pct_women']:.0f}%), and rates were highest at 70 years or older ({N['agerate'][('Men', '70세 이상')]:.1f} per 100,000 person-years in men and {N['agerate'][('Women', '70세 이상')]:.1f} in women; Table 1). Every district notified at least one case in every year."),
("Geography",
 f"Annual district SIRs were spatially clustered in every year (Moran's I {N['moran_y'][2013]:.2f} in 2013, {N['moran_year'][0]:.2f}–{N['moran_year'][1]:.2f} across years and {N['moran_y'][2025]:.2f} in 2025; pooled {N['moran_pooled']:.2f}). "
 f"The ratio of the 90th to the 10th percentile of annual smoothed district SIRs was {GAP[2013]['ratio']:.2f} in 2013 and {GAP[2025]['ratio']:.2f} in 2025, the highest of the 13 years, and district rankings were persistent (Kendall's W {N['kendall']['2013-2025']:.2f}). "
 f"After adjustment, {N['n_hot']} districts had residual hot spots, most in {hot}, and {N['n_cold']} had residual cold spots, most in {cold} (Figure 2; {sup('hot')}); hot spots included inner-city wards of Seoul and Daegu and counties of eastern Gangwon-do, inland Gyeongsangbuk-do and south-western Jeollanam-do. "
 f"The structured spatial share of the district effect was {N['phi'][0]:.2f} (95% CrI {N['phi'][1]:.2f}–{N['phi'][2]:.2f}), and the residual Moran's I was {N['moran_resid']:.3f}."),
("District characteristics",
 f"In the principal model, the share of older adults living alone ({ci(OS)}), current smoking ({ci(SM)}), general hospitals ({ci(GH)}) and screening-measured suspected diabetes ({ci(DM)}) were associated with more notifications (Table 2); one SD corresponded to {N['sd'][OS]:.1f} percentage points of households and {N['sd'][SM]:.1f} percentage points of current smoking. "
 f"The four met the multiverse criterion (credible in {MVN(OS)}, {MVN(SM)}, {MVN(GH)} and {MVN(DM)} of the models containing them) and were credible with the same sign in {AK[OS]}, {AK[SM]}, {AK[GH]} and {AK[DM]} of {NA} alternative fits ({sup('specs')}). "
 f"Foreign residents ({ci(FR)}), Medical Aid patients ({ci(MA)}) and long-term care hospitals ({ci(LTC)}) were not credible. Of the negative control exposures, hit-and-run collisions showed a small inverse association ({sh(N['negctl']['hit_and_run_rate'][:3])}) and the other two none.",
 f"In the best-fitting space–time model (Knorr-Held type II; WAIC {N['s43_waic']['KH_typeII']:,.0f} versus {N['waic_main']:,.0f}), living alone ({sh(S43('KH_typeII', OS))}), smoking ({sh(S43('KH_typeII', SM))}), general hospitals ({sh(S43('KH_typeII', GH))}) and foreign residents ({sh(S43('KH_typeII', FR))}) were credible and suspected diabetes ({sh(S43('KH_typeII', DM))}) was not; living alone and smoking were credible in all four space–time models. "
 f"The living-alone association arose from its between-district component ({sh(BW(OS + '__between'))}), not from within-district change ({sh(BW(OS + '__within'))}), whereas smoking was associated through both ({sh(BW(SM + '__between'))} and {sh(BW(SM + '__within'))}). "
 f"In the Spatial+-type model the living-alone association was smaller ({sh(S41('D1_spatial_plus', OS))}). "
 f"For the comparison outcomes, the 95% CrIs for living alone and smoking included 1 (transport-injury deaths {sh(NCO('TRANS', OS))} and {sh(NCO('TRANS', SM))}; gastric cancer {sh(NCO('GCA', OS))} and {sh(NCO('GCA', SM))}), whereas foreign residents were associated with transport-injury deaths ({sh(NCO('TRANS', FR))}) and general hospitals inversely with gastric cancer ({sh(NCO('GCA', GH))}).",
 f"By period, the living-alone association was {sh(WIN(OS, 'W1_2013-15')[:3])} in 2013–2015, {sh(WIN(OS, 'W2_2016-19')[:3])} in 2016–2019 and {sh(WIN(OS, 'W3_2020-25')[:3])} in 2020–2025, and in 2015–2025, without interpolated years, it was {sh(F15[OS][:3])}; smoking ({sh(F15[SM][:3])}), general hospitals ({sh(F15[GH][:3])}) and foreign residents ({sh(F15[FR][:3])}) were credible in 2015–2025. "
 f"Foreign residents were credible in all three periods, and Medical Aid patients in 2020–2025 only ({sh(WIN(MA, 'W3_2020-25')[:3])}). "
 f"Without the share aged 80 years or older the living-alone association was {sh(SEN('s2', OS))}, with crude expected cases {sh(SEN('sc', OS))}, with a different adjacency graph {sh(SEN('s577', OS))} and in 2013–2024 {sh(SEN('y24', OS))}. "
 f"E-values were {N['evalue'][OS]['E_point']:.2f} (credible limit {N['evalue'][OS]['E_limit']:.2f}) for living alone and {N['evalue'][SM]['E_point']:.2f} ({N['evalue'][SM]['E_limit']:.2f}) for smoking. "
 f"For respiratory tuberculosis deaths ({N['tbd_cases']:,} deaths, 2013–2024), smoking ({sh(N['tbd'][('TBD', SM)][:3])}) was credible and living alone ({sh(N['tbd'][('TBD', OS)][:3])}) was not."),
]
