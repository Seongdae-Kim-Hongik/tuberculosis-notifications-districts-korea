#!/usr/bin/env python3
# 82 — 핵심 보고서(552 포맷: 영문 캡션 볼드 → 표/그림 → 영문 범례 → 한글 요지 1줄 ≤480자; 모든 수치 CSV 연동). 사용: python3 82_core_report.py <TAG> <YYMMDD>
#  입력: 04_분석/<TAG>/panel_*, panel_META_*, panel_INFO_*, sets_*.json, HM_setcompare_*, HM_best_*, results/S1~S9 CSV, 지도 final.shp
#  산출: 04_분석/<TAG>/<날짜>_<TAG>_핵심.docx / .pdf (soffice), figs/ PNG
import sys, os, json, re, subprocess, unicodedata
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; import matplotlib.font_manager as fm
from docx import Document; from docx.shared import Pt, Cm; from docx.enum.text import WD_ALIGN_PARAGRAPH; from docx.oxml.ns import qn; from docx.oxml import OxmlElement
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHP = os.environ.get("ST_SHP", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "boundary", "final.shp"))
SOFFICE = "/opt/homebrew/bin/soffice"
TAG, DATE = sys.argv[1], sys.argv[2]
VER = os.environ.get("ST_VER", "").strip(); SUF = f"_{VER}" if VER else ""   # 버전 분기(ST_VER=v2 → *_v2 입력·results_v2/·figs_v2/·핵심_v2)
OUTD = os.path.join(ROOT, "04_분석", TAG); RES = os.path.join(OUTD, "results" + SUF); FIG = os.path.join(OUTD, "figs" + SUF); os.makedirs(FIG, exist_ok=True)
S = json.load(open(os.path.join(OUTD, f"config_{TAG}{SUF}.json"), encoding="utf-8")); RU = S["rules"]
INFO = json.load(open(os.path.join(OUTD, f"panel_INFO_{TAG}{SUF}.json"), encoding="utf-8"))
DKO, DEN = S.get("disease_ko", TAG), S.get("disease_en", TAG)
rd = lambda f: pd.read_csv(os.path.join(RES, f), encoding="utf-8-sig")
P = pd.read_csv(os.path.join(OUTD, f"panel_{TAG}{SUF}.csv"), encoding="utf-8-sig")
META = pd.read_csv(os.path.join(OUTD, f"panel_META_{TAG}{SUF}.csv"), encoding="utf-8-sig").set_index("variable")
CMP = pd.read_csv(os.path.join(OUTD, f"HM_setcompare_{TAG}{SUF}.csv"), encoding="utf-8-sig")
BEST = dict(l.split("=", 1) for l in open(os.path.join(OUTD, f"HM_best_{TAG}{SUF}.txt"), encoding="utf-8").read().splitlines() if "=" in l)
LK = rd("S1_likelihood.csv"); MAIN = rd("S3_main_IRR.csv"); MFIT = rd("S3_main_fit.csv").iloc[0]; NEG = rd("S3_negcontrol.csv"); HYP = rd("S3_main_hyper.csv"); YE = rd("S3_year_effect.csv")
WIN = rd("S4_window_IRR.csv"); WFIT = rd("S4_window_fit.csv"); INT = rd("S4_interaction.csv"); COV = rd("S5_covid.csv"); RR = rd("S6_spatial_RR.csv"); MOR = rd("S6_moran_year.csv")
MV = rd("S7_multiverse_summary.csv"); RM = rd("S8_residual_moran.csv"); T1 = rd("S9_typeI_IRR.csv") if os.path.exists(os.path.join(RES, "S9_typeI_IRR.csv")) else None
OS = rd("S10_offset_sensitivity_IRR.csv") if os.path.exists(os.path.join(RES, "S10_offset_sensitivity_IRR.csv")) else None
SENS_SETS = INFO.get("sensitivity_sets", [])
NB = rd(f"nb_{TAG}_summary.csv").iloc[0]
FAMN = {"nbinomial": "negative binomial", "poisson": "Poisson"}; MAINFAM = BEST["main_family"]; BESTSET = BEST["best_set"]
FORCED = INFO["forced"]; HYPV = INFO["sets"][BESTSET]
KO = lambda v: META.loc[v, 'label_ko']
VF = lambda v: META.loc[v, 'vif_final']
CV = lambda v: META.loc[v, 'coverage']
NSO = lambda v: int(META.loc[v, 'n_sgg_observed'])
YMN = lambda v: int(META.loc[v, 'obs_year_min'])
YMX = lambda v: int(META.loc[v, 'obs_year_max'])
SAM = lambda v: META.loc[v, 'sgg_all_missing']
lab = lambda v: f"{META.loc[v,'label_en']} ({META.loc[v,'label_ko']})"
def ci(r, k="IRR"): return f"{r[k]:.3f} ({r['lo']:.3f}-{r['hi']:.3f})"
WINS = INFO["windows"]; WN = list(WINS.keys()); WY = {k: f"{v[0]}-{v[1]}" for k, v in WINS.items()}

# ── 폰트 ──
KF = next((f for f in ["AppleGothic", "Nanum Gothic", "Apple SD Gothic Neo"] if f in {x.name for x in fm.fontManager.ttflist}), "DejaVu Sans")
plt.rcParams.update({"font.family": KF, "axes.unicode_minus": False, "font.size": 9})
DOCF = "Nanum Gothic" if "Nanum Gothic" in {x.name for x in fm.fontManager.ttflist} else "AppleGothic"

# ── 그림 1: 연도 추세(전국 조율 + 시군구 분위 띠) ──
if "offset" not in P.columns: P["offset"] = P.population
P["rate"] = P.cases / P.offset * 1e5; OFFC = INFO.get("offset_column", "population"); DENOM = "residents" if OFFC == "population" else f"denominator ({OFFC})"
nat = P.groupby("year")[["cases","offset"]].sum().pipe(lambda g: g.cases / g.offset * 1e5)
q = P.groupby("year").rate.quantile([0.1, 0.25, 0.5, 0.75, 0.9]).unstack()
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.fill_between(q.index, q[0.1], q[0.9], color="#bbbbbb", alpha=0.5, label="District 10th-90th percentile")
ax.fill_between(q.index, q[0.25], q[0.75], color="#777777", alpha=0.5, label="District 25th-75th percentile")
ax.plot(q.index, q[0.5], color="#333333", lw=1, ls="--", label="District median")
ax.plot(nat.index, nat.values, color="black", lw=2, marker="o", ms=3, label="National crude rate")
for wn, (a, b) in WINS.items(): ax.axvspan(a - 0.5, b + 0.5, color="none", ec="#999999", ls=":", lw=0.8)
ax.axvline(INFO["covid_post_from"] - 0.5, color="#555555", lw=0.8, ls="-.")
ax.set_xlabel("Year"); ax.set_ylabel(f"Cases per 100,000 {DENOM}"); ax.set_xticks(list(nat.index)); ax.tick_params(axis="x", labelsize=8); ax.legend(fontsize=7, frameon=False); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); F1 = os.path.join(FIG, "fig1_trend.png"); fig.savefig(F1, dpi=200); plt.close(fig)

# ── 그림 2: 공간 RR 지도 + 초과확률 지도 ──
import geopandas as gpd
G = gpd.read_file(SHP); G["region"] = G["region"].map(lambda s: unicodedata.normalize("NFC", str(s)))
RR["fbd_region"] = RR["fbd_region"].map(lambda s: unicodedata.normalize("NFC", str(s)))
GM = G.merge(RR, left_on="region", right_on="fbd_region", how="left"); assert GM.RR.notna().all()
fig, axs = plt.subplots(1, 2, figsize=(9, 5.2))
vmax = max(abs(np.log(GM.RR.min())), abs(np.log(GM.RR.max())))
GM.plot(column=np.log(GM.RR), cmap="RdBu_r", vmin=-vmax, vmax=vmax, ax=axs[0], edgecolor="white", linewidth=0.15, legend=True, legend_kwds={"shrink": 0.55, "label": "log RR"})
axs[0].set_title("A. Spatial relative risk (BYM2)", fontsize=9, loc="left"); axs[0].axis("off")
cmap = {"hotspot": "#b2182b", "coldspot": "#2166ac", "neutral": "#e6e6e6", "unobserved": "#ffffff"}
GM.plot(color=GM["class"].map(cmap), ax=axs[1], edgecolor="white", linewidth=0.15); axs[1].axis("off")
axs[1].set_title("B. Exceedance P(RR>1): hotspot >0.95, coldspot <0.05", fontsize=9, loc="left")
from matplotlib.patches import Patch
axs[1].legend(handles=[Patch(color=cmap[k], label=f"{k} (n={int((GM['class']==k).sum())})") for k in ["hotspot", "coldspot", "neutral", "unobserved"] if (GM["class"] == k).any()], fontsize=7, frameon=False, loc="lower left")
fig.tight_layout(); F2 = os.path.join(FIG, "fig2_map.png"); fig.savefig(F2, dpi=200); plt.close(fig)

# ── 그림 3: 창별 IRR 포리스트(가설 변수, 라벨 English (한글)) ──
WH = WIN[WIN.role == "hypothesis"].copy(); WH["ord"] = WH['cov'].map({v: i for i, v in enumerate(HYPV)}); WH = WH.sort_values(["ord", "window"])
fig, ax = plt.subplots(figsize=(7.5, 0.55 * len(HYPV) + 1.4))
mk = {WN[0]: "o", WN[1]: "s", WN[2]: "^"}; off = {WN[0]: 0.22, WN[1]: 0, WN[2]: -0.22}
for i, v in enumerate(HYPV):
    for wn in WN:
        r = WH[(WH['cov'] == v) & (WH.window == wn)]
        if r.empty: continue
        r = r.iloc[0]; y = i + off[wn]
        ax.errorbar(r.IRR, y, xerr=[[r.IRR - r.lo], [r.hi - r.IRR]], fmt=mk[wn], color="black" if r.cred else "#888888", ms=4, capsize=2, lw=1, label=f"{wn} ({WY[wn]})" if i == 0 else None)
ax.axvline(1, color="#555555", lw=0.8, ls="--"); ax.set_yticks(range(len(HYPV))); ax.set_yticklabels([lab(v) for v in HYPV], fontsize=8); ax.invert_yaxis()
ax.set_xlabel("IRR per +1 SD (95% CrI)"); ax.legend(fontsize=7, frameon=False, loc="lower right"); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); F3 = os.path.join(FIG, "fig3_window_forest.png"); fig.savefig(F3, dpi=200); plt.close(fig)

# ── docx 헬퍼 ──
doc = Document()
for s in doc.sections: s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(2.0)
st = doc.styles["Normal"]; st.font.name = DOCF; st.font.size = Pt(10); st.element.rPr.rFonts.set(qn("w:eastAsia"), DOCF)
def run(p, t, sz=10, b=False):
    r = p.add_run(t); r.font.size = Pt(sz); r.bold = b; r.font.name = DOCF; r._element.rPr.rFonts.set(qn("w:eastAsia"), DOCF); return r
def para(t, sz=10, b=False, after=3, before=0, align="left"):
    p = doc.add_paragraph(); run(p, t, sz, b); pf = p.paragraph_format; pf.space_after = Pt(after); pf.space_before = Pt(before)
    pf.alignment = {"left": WD_ALIGN_PARAGRAPH.LEFT, "center": WD_ALIGN_PARAGRAPH.CENTER}[align]; return p
def SEC(t): para(t, sz=12, b=True, before=14, after=6)
def CAP(t): p = para(t, sz=10.5, b=True, before=8, after=3); p.paragraph_format.keep_with_next = True
def LEG(t): para(t, sz=8.5, after=3)
def YOJI(t, alt=None):
    t = re.sub(r"\s+", " ", str(t)).strip()
    if len(t) > 480 and alt is not None: t = re.sub(r"\s+", " ", str(alt)).strip(); print(f"[82] 요지 압축형 사용({len(t)}자)")
    if len(t) > 480:  # 3단계 압축: 괄호 안 구간 제거 → 열거 항목 축약(앞 3개 + 외 n개) → 문장 단위 절단
        t2 = re.sub(r"\([^()]*\)", "", t); t2 = re.sub(r"\s+", " ", t2).replace(" ,", ",").strip()
        if len(t2) > 480:
            parts = re.split(r"(?<=[.;])\s", t2); acc = ""
            for p_ in parts:
                if len(acc) + len(p_) + 1 > 470: break
                acc = (acc + " " + p_).strip()
            t2 = acc if acc else t2[:470]
        print(f"[82] 요지 3단계 압축({len(t)}→{len(t2)}자)"); t = t2
    assert len(t) <= 480, f"요지 480자 초과({len(t)}): {t[:60]}"
    para("요지: " + t, sz=9.5, b=False, after=10)
def TBL(hdr, rows, widths, fs=8.0, cat_rows=()):
    t = doc.add_table(rows=1, cols=len(hdr)); t.style = "Table Grid"; t.autofit = False
    def cell(c, v, b=False):
        c.text = ""; p = c.paragraphs[0]; run(p, str(v), fs, b); p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)
    for j, h in enumerate(hdr): cell(t.rows[0].cells[j], h, True)
    for i, r in enumerate(rows):
        cs = t.add_row().cells
        for j, v in enumerate(r): cell(cs[j], v, b=(i in cat_rows))
    for row in t.rows:
        for j, w in enumerate(widths): row.cells[j].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
def FIGI(path, wcm=16.5): doc.add_picture(path, width=Cm(wcm)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
yn = lambda b: "Yes" if bool(b) else "No"

# ── 표지 ──
para(f"{DKO}({DEN}) 시군구 시공간 결정요인 분석 핵심 보고서", sz=14, b=True, after=2)
para(f"Spatio-temporal determinants of {DEN.lower()} across {INFO['n_sgg']} Korean districts, {INFO['years'][0]}-{INFO['years'][1]} (core report, {DATE})", sz=10, after=8)
EXTE = INFO.get("offset_E_column")   # PLAN R10: 외부 E(간접 연령표준화) 사용 여부
if VER: para(f"version {VER}" + ("(간접 연령표준화 기대건수 E 주분석)" if EXTE else "(기전 기반 축소 풀)"), sz=10, after=8)
imp = META[["n_imputed_interp", "n_imputed_sgg_mean", "n_imputed_year_mean"]].sum()
vifd = META[META.vif_dropped == True].index.tolist(); vifo = META[META.vif_over_threshold_retained == True].index.tolist(); lowc = META[META.low_coverage == True].index.tolist()
cover = [
 ("Outcome", f"{S.get('outcome_label_en', S['outcome_column'])} [{S['outcome_column']}]; residents' annual treated-patient counts (NHIS regional statistics)"),
 ("Units", f"{INFO['n_sgg']} districts × {INFO['n_years']} years ({INFO['years'][0]}-{INFO['years'][1]}) = {INFO['n_rows']:,} district-years (dropped {INFO.get('n_dropped_rows',0)} rows with missing outcome/denominator{', excluded years ' + ', '.join(map(str, INFO['exclude_years'])) if INFO.get('exclude_years') else ''}); total cases {INFO['total_cases']:,.0f}; person-years {INFO['total_person_years']:,.0f}; crude rate {INFO['crude_rate_per_100k_overall']:,.1f} per 100,000 {DENOM}"),
 ("Expected counts E", (f"indirect age standardisation: district 10-year age-group population × national age-specific treated-patient rate of the same year (8 age groups), rescaled so that sum(E) = sum(cases) each year [{EXTE}]; sex not standardised (sex ratio kept as forced control), older-adult share dropped from forced controls" if EXTE else f"{OFFC} × national crude rate of the same year (indirect standardisation without age); sum(E) = sum(cases)") + (f"; sensitivity denominator {INFO['offset_sensitivity']} (Table S6)" if INFO.get("offset_sensitivity") else "") + (f"; denominator fallback population×100/(100+sex ratio) used in {INFO['n_offset_fallback']} cells" if INFO.get("n_offset_fallback") else "")),
 ("Forced controls", "; ".join(lab(v) for v in FORCED)),
 ("Hypothesis sets", f"{len([k for k in S['sets'] if k not in SENS_SETS])} pre-specified sets ({', '.join(k for k in S['sets'] if k not in SENS_SETS)})" + (f"; sensitivity-only sets not eligible for selection: {', '.join(SENS_SETS)}" if SENS_SETS else "") + f"; negative controls: {'; '.join(lab(v) for v in INFO['negative_controls']) or 'none'}"),
 ("Likelihood", f"{FAMN[MAINFAM]} chosen by lower WAIC of the forced-only model ({' vs '.join(f'{FAMN[r.family]} {r.WAIC:,.1f}' for r in LK.itertuples())})"),
 ("Random effects", f"BYM2 spatial (queen contiguity, {int(NB.n_regions)} regions, {int(NB.islands_linked)} islands linked to nearest neighbour: {NB.island_regions}; PC priors), RW1 year trend, IID year; Type I space-time IID as sensitivity; INLA single-thread for reproducibility"),
 ("Imputation", f"interior years linearly interpolated within district ({int(imp.n_imputed_interp)} cells), leading/trailing years by district mean ({int(imp.n_imputed_sgg_mean)}), districts with no data by national year mean ({int(imp.n_imputed_year_mean)}); covariates standardised (per 1 SD, pooled)"),
 ("VIF screening", f"threshold {RU['vif_threshold']:g}, action {RU['vif_action']}; removed: {', '.join(vifd) if vifd else 'none'}; retained above threshold: {', '.join(f'{v} ({VF(v):.1f})' for v in vifo) if vifo else 'none'}; final maximum VIF {META.vif_final.max():.2f}"),
 ("Coverage", f"variables with < 70% observed cells before imputation: {', '.join(f'{v} ({100*CV(v):.0f}%, {NSO(v)} districts, {YMN(v)}-{YMX(v)})' for v in lowc) if lowc else 'none'}"),
 ("Selection rules", f"family = lower WAIC of forced-only; set = min WAIC, within waic_tol {RU['waic_tol']:g} fewest hypothesis variables, ties by LCPO; main set mode = {BEST.get('main_set_mode','rule')}; rule-selected set = {BEST.get('rule_best_set','')}; VIF > {RU['vif_threshold']:g} action = {RU['vif_action']}"),
 ("Config", f"{S['source_json']} fixed {S.get('fixed_on','')}; {S.get('note','')[:160]}")]
TBL(["Item", "Specification"], cover, [3.2, 13.3], fs=8)

# ── Table 1 ──
SEC("Table 1. Period characteristics and treated-patient rates")
CAP(f"Table 1. District-year characteristics and {DEN.lower()} treated-patient rate per 100,000 by period")
rows = []; t1 = {}
for wn in WN:
    d = P[P.window == wn]; r = d.cases.sum() / d.offset.sum() * 1e5; dr = d.rate
    t1[wn] = dict(n=len(d), cases=d.cases.sum(), py=d.population.sum(), off=d.offset.sum(), rate=r, med=dr.median(), q1=dr.quantile(.25), q3=dr.quantile(.75), mn=dr.min(), mx=dr.max())
hdr = ["Characteristic"] + [f"{wn} ({WY[wn]})" for wn in WN] + [f"Pooled ({INFO['years'][0]}-{INFO['years'][1]})"]
allr = dict(n=len(P), cases=P.cases.sum(), py=P.population.sum(), off=P.offset.sum(), rate=P.cases.sum() / P.offset.sum() * 1e5, med=P.rate.median(), q1=P.rate.quantile(.25), q3=P.rate.quantile(.75), mn=P.rate.min(), mx=P.rate.max())
cols = [t1[w] for w in WN] + [allr]
rows.append(["District-years, n"] + [f"{c['n']:,}" for c in cols])
rows.append(["Treated patients, n"] + [f"{c['cases']:,.0f}" for c in cols])
rows.append(["Person-years"] + [f"{c['py']:,.0f}" for c in cols])
if OFFC != "population": rows.append([f"Denominator ({OFFC})"] + [f"{c['off']:,.0f}" for c in cols])
rows.append(["Crude rate per 100,000 (national)"] + [f"{c['rate']:,.1f}" for c in cols])
rows.append(["District rate, median (IQR)"] + [f"{c['med']:,.1f} ({c['q1']:,.1f}-{c['q3']:,.1f})" for c in cols])
rows.append(["District rate, min-max"] + [f"{c['mn']:,.1f}-{c['mx']:,.1f}" for c in cols])
cat = [len(rows)]; rows.append(["Covariates, mean (SD), original scale"] + [""] * (len(WN) + 1))
for v in FORCED + HYPV:
    rows.append([lab(v)] + [f"{P[P.window==w][v+'_raw'].mean():,.2f} ({P[P.window==w][v+'_raw'].std():,.2f})" for w in WN] + [f"{P[v+'_raw'].mean():,.2f} ({P[v+'_raw'].std():,.2f})"])
TBL(hdr, rows, [5.2, 2.8, 2.8, 2.8, 2.9], fs=7.5, cat_rows=cat)
LEG(f"Rates are cases per 100,000 {DENOM} (crude). District rate = district-year cases/population × 100,000. Covariates are shown on their original (pre-standardisation) scale after imputation; models use per-1-SD standardised values. Periods are the three non-overlapping windows fixed in the plan.")
w3, w1 = t1[WN[2]], t1[WN[0]]
YOJI(f"{DKO} 진료실인원 조율은 {WY[WN[0]]} {w1['rate']:,.1f}/10만에서 {WY[WN[2]]} {w3['rate']:,.1f}/10만으로 변했고(전체 {allr['rate']:,.1f}/10만, 총 {allr['cases']:,.0f}명·{allr['n']:,} 시군구-연도), 시군구 중앙값은 {w1['med']:,.1f}→{w3['med']:,.1f}, 범위 {w3['mn']:,.1f}-{w3['mx']:,.1f}({WY[WN[2]]}).")

# ── Table 2 ──
SEC("Table 2. Determinants: set comparison and principal model")
CAP("Table 2a. Comparison of pre-specified covariate sets (principal likelihood, same forced controls)")
C = CMP.copy()
if "sensitivity" not in C.columns: C["sensitivity"] = C.set.isin(SENS_SETS)
wmin = C[~C.set.str.startswith("REF_") & ~C.sensitivity].WAIC.min(); C["dWAIC"] = C.WAIC - wmin
rows = [[r.set, f"{int(r.n_hyp)}", f"{r.WAIC:,.1f}", f"{r.dWAIC:+.1f}", f"{r.LCPO:.4f}", f"{int(r.cpo_fail)}", "Selected" if r.set == BESTSET else ("Reference" if r.set.startswith("REF_") else ("Sensitivity (not eligible)" if r.sensitivity else ("Rule-selected (sensitivity)" if r.set == BEST.get("rule_best_set") else "")))] for r in C.sort_values("WAIC").itertuples()]
TBL(["Set", "k", "WAIC", "ΔWAIC", "LCPO", "CPO fail", "Decision"], rows, [4.2, 1.0, 2.4, 1.8, 2.0, 1.6, 3.5], fs=7.5)
LEG("Set composition: " + " | ".join(f"{sn} = {', '.join(META.loc[v, 'label_en'] for v in vs)}" for sn, vs in INFO["sets"].items()) + ".")
LEG(f"All sets include the {len(FORCED)} forced controls. k = number of hypothesis variables. ΔWAIC relative to the lowest WAIC among candidate sets. LCPO = −mean log CPO. Rule: lowest WAIC; sets within {RU.get('waic_tol',4)} WAIC resolved to the fewest hypothesis variables, then lower LCPO when CPO failures < {100*RU.get('cpo_fail_frac',0.05):.0f}% of cells. REF_forced_only is the hypothesis-free baseline, not a candidate.")
cb = C[C.set == BESTSET].iloc[0]; cref = C[C.set == "REF_forced_only"].iloc[0]; rk = C[~C.set.str.startswith("REF_") & ~C.sensitivity].sort_values("WAIC")
_sens_txt = "; ".join(f"민감도 {r.set} WAIC {r.WAIC:,.1f}" for r in C[C.sensitivity].itertuples())
YOJI(f"주 우도는 {FAMN[MAINFAM]}(강제통제만 모형 WAIC {' vs '.join(f'{FAMN[r.family]} {r.WAIC:,.1f}' for r in LK.itertuples())}). 후보 세트 {len(rk)}개 중 WAIC 최소는 {rk.iloc[0].set}({rk.iloc[0].WAIC:,.1f}, 2위 {rk.iloc[1].set}과 차이 {rk.iloc[1].WAIC-rk.iloc[0].WAIC:.1f}); 주모형 세트는 {BESTSET}(WAIC {cb.WAIC:,.1f}, 가설 변수 {int(cb.n_hyp)}개, 기준모형 대비 {cb.WAIC-cref.WAIC:+.1f}, 선정 방식 {BEST.get('main_set_mode','rule')})" + (f"; {_sens_txt}" if _sens_txt else "") + ".", alt=f"주 우도 {FAMN[MAINFAM]}(강제통제만 WAIC {' vs '.join(f'{FAMN[r.family]} {r.WAIC:,.1f}' for r in LK.itertuples())}). 후보 {len(rk)}개 중 WAIC 최소 {rk.iloc[0].set}({rk.iloc[0].WAIC:,.1f}); 주모형 세트 {BESTSET}(WAIC {cb.WAIC:,.1f}, 가설 {int(cb.n_hyp)}개, 기준모형 대비 {cb.WAIC-cref.WAIC:+.1f}, {BEST.get('main_set_mode','rule').split(' ')[0]} 방식)" + (f"; {_sens_txt}" if _sens_txt else "") + ".")

CAP(f"Table 2b. Principal model: IRR per +1 SD for {DEN.lower()} treated patients ({FAMN[MAINFAM]}, BYM2 + RW1 + IID year; set {BESTSET})")
rows = []; cat = []
cat.append(len(rows)); rows.append(["Hypothesis variables", "", "", "", ""])
for r in MAIN[MAIN.role == "hypothesis"].itertuples(): rows.append([lab(r.cov), (META.loc[r.cov, "expected_direction"] if isinstance(META.loc[r.cov, "expected_direction"], str) else "").replace("−", "-"), ci(r._asdict()), f"{r.P_gt1:.3f}", yn(r.cred)])
cat.append(len(rows)); rows.append(["Forced controls", "", "", "", ""])
for r in MAIN[MAIN.role == "forced"].itertuples(): rows.append([lab(r.cov), "", ci(r._asdict()), f"{r.P_gt1:.3f}", yn(r.cred)])
if len(NEG):
    cat.append(len(rows)); rows.append(["Negative controls (added one at a time to the principal model)", "", "", "", ""])
    for r in NEG.itertuples(): rows.append([lab(r.cov), "0", ci(r._asdict()), f"{r.P_gt1:.3f}", yn(r.cred)])
TBL(["Variable (English (한글))", "Expected", "IRR (95% CrI)", "P(IRR>1)", "Credible"], rows, [7.6, 1.5, 3.4, 1.7, 1.6], fs=7.5, cat_rows=cat)
phi = HYP[HYP.hyperpar.str.contains("Phi")].iloc[0]
LEG(f"IRR per 1 SD increase of the standardised covariate, offset log E. Credible = 95% CrI excludes 1. Expected = pre-specified direction. WAIC of this refit {MFIT.WAIC:,.1f} (Table 2a value is from the set-comparison fit; INLA refits of the same model differ by a few WAIC units), DIC {MFIT.DIC:,.1f}, BYM2 mixing parameter phi {phi['mean']:.3f} ({phi['X0.025quant']:.3f}-{phi['X0.975quant']:.3f}). Residual Moran's I of district-mean Pearson residuals {MFIT.resid_moran_I:.3f} (permutation P {MFIT.resid_moran_p:.3f}); observed pooled log-SIR Moran's I {MFIT.obs_moran_I:.3f} (P {MFIT.obs_moran_p:.3f}). Negative-control IRRs are from separate models each adding one control.")
ch = MAIN[(MAIN.role == "hypothesis") & MAIN.cred]; nh = MAIN[(MAIN.role == "hypothesis") & ~MAIN.cred]
ctxt = "; ".join(f"{META.loc[r.cov,'label_ko']} {r.IRR:.3f}({r.lo:.3f}-{r.hi:.3f})" for r in ch.itertuples()) or "없음"
ctxt_s = '; '.join(f"{KO(r.cov)} {r.IRR:.3f}" for r in ch.itertuples()) or '없음'   # 480자 초과 시 압축형(CI는 표에)
negtxt = "; ".join(f"{META.loc[r.cov,'label_ko']} {r.IRR:.3f}({r.lo:.3f}-{r.hi:.3f})" for r in NEG.itertuples()) if len(NEG) else "없음"
YOJI(f"주모형(가설 {len(HYPV)}·강제통제 {len(FORCED)}) credible 가설 변수 {len(ch)}개: {ctxt}; 비credible {len(nh)}개({', '.join(KO(v) for v in nh['cov']) or '없음'}). 음성대조 {negtxt}(credible {int(NEG.cred.sum()) if len(NEG) else 0}개). 잔차 Moran I {MFIT.resid_moran_I:.3f}(P {MFIT.resid_moran_p:.3f}).",
     alt=f"주모형(가설 {len(HYPV)}·강제통제 {len(FORCED)}) credible 가설 변수 {len(ch)}개(IRR; CrI는 표): {ctxt_s}; 비credible {len(nh)}개. 음성대조 credible {int(NEG.cred.sum()) if len(NEG) else 0}/{len(NEG)}({negtxt}). 잔차 Moran I {MFIT.resid_moran_I:.3f}(P {MFIT.resid_moran_p:.3f}).")

# ── Figure 1 ──
SEC("Figure 1. Annual trend")
CAP(f"Figure 1. National crude rate and district distribution of {DEN.lower()} treated patients per 100,000, {INFO['years'][0]}-{INFO['years'][1]}")
FIGI(F1, 15)
LEG("Black line = national crude rate (sum of cases / sum of population). Dark band = district 25th-75th percentile, light band = 10th-90th percentile, dashed = district median. Dotted boxes mark the three analysis windows; dash-dot line marks the first COVID-19 year.")
ymax, ymin = nat.idxmax(), nat.idxmin(); mo = MOR.sort_values("moran_I", ascending=False).iloc[0]
YOJI(f"전국 조율은 {int(nat.index[0])}년 {nat.iloc[0]:,.1f}/10만에서 {int(nat.index[-1])}년 {nat.iloc[-1]:,.1f}/10만(최저 {int(ymin)}년 {nat.min():,.1f}, 최고 {int(ymax)}년 {nat.max():,.1f}); 시군구 10-90분위 폭은 {int(q.index[0])}년 {q[0.9].iloc[0]-q[0.1].iloc[0]:,.1f}에서 {int(q.index[-1])}년 {q[0.9].iloc[-1]-q[0.1].iloc[-1]:,.1f}. 연도별 관측 log SIR Moran I 최대 {mo.moran_I:.3f}({int(mo.year)}년, P {mo.p_perm:.3f}).")

# ── Figure 2 ──
SEC("Figure 2. Spatial relative risk and hotspots")
CAP("Figure 2. District-level spatial relative risk (BYM2 total effect, principal model) and exceedance classification")
FIGI(F2, 16.5)
LEG(f"A: exp of the BYM2 total spatial effect after adjustment for all principal-model covariates and the year effects (diverging scale centred at RR = 1). B: hotspot = P(RR>1) > 0.95, coldspot = P(RR>1) < 0.05. Hotspots n = {int(MFIT.n_hotspot)}, coldspots n = {int(MFIT.n_coldspot)}; RR range {MFIT.RR_min:.3f}-{MFIT.RR_max:.3f}.")
RRo = RR[RR["class"] != "unobserved"] if "class" in RR.columns else RR; top = RRo.sort_values("RR", ascending=False).head(5); bot = RRo.sort_values("RR").head(5)
YOJI(f"공변량·연도 보정 후 공간 RR은 {MFIT.RR_min:.3f}-{MFIT.RR_max:.3f}, 핫스팟 {int(MFIT.n_hotspot)}곳·콜드스팟 {int(MFIT.n_coldspot)}곳({int(MFIT.n_regions)}구 중" + (f", 미관측 {len(INFO.get('unobserved_regions', []))}구 제외" if INFO.get('unobserved_regions') else "") + f"). RR 상위 5: {', '.join(f'{r.fbd_region} {r.RR:.3f}' for r in top.itertuples())}; 하위 5: {', '.join(f'{r.fbd_region} {r.RR:.3f}' for r in bot.itertuples())}.")

# ── Figure 3 ──
SEC("Figure 3. Determinants by window")
CAP(f"Figure 3. Window-specific IRR per +1 SD of hypothesis variables ({', '.join(f'{w} = {WY[w]}' for w in WN)}; separate refits of the principal model)")
FIGI(F3, 15.5)
LEG("Each window is refitted with the same covariates and random-effect structure on that window's district-years. Black markers = 95% CrI excludes 1. Window-by-variable interaction tests (pooled model, reference = first window) are in Table S4.")
wtxt = []
for wn in WN:
    d = WH[WH.window == wn]; cc = d[d.cred]; nn = int(WFIT[WFIT.window == wn].n_obs.iloc[0])
    wtxt.append(f"{WY[wn]}(n={nn:,}) credible {len(cc)}개" + (f"[{'; '.join(f'{KO(r.cov)} {r.IRR:.3f}' for r in cc.itertuples())}]" if len(cc) else ""))
icr = INT[INT.cred]
_wshort = "; ".join(f"{WY[wn]}(n={int(WFIT[WFIT.window == wn].n_obs.iloc[0]):,}) credible {int(WFIT[WFIT.window == wn].n_cred_hyp.iloc[0])}개" for wn in WN)
_allw = [v for v in HYPV if all(bool(WH[(WH['cov'] == v) & (WH.window == wn)].cred.iloc[0]) for wn in WN if not WH[(WH['cov'] == v) & (WH.window == wn)].empty)]
YOJI("창별 재적합: " + "; ".join(wtxt) + f". 창×변수 상호작용 credible {len(icr)}/{len(INT)}" + (f"({'; '.join(f'{KO(r.cov)}×{r.window} {r.IRR_ratio:.3f}' for r in icr.itertuples())})" if len(icr) else "") + ".",
     alt=f"창별 재적합(가설 {len(HYPV)}개): {_wshort}; 세 창 모두 credible {len(_allw)}개({', '.join(KO(v) for v in _allw) or '없음'}). 창×변수 상호작용 credible {len(icr)}/{len(INT)}(수치는 Table S4).")

# ── 보충 ──
SEC("Supplementary analyses")
CAP(f"Table S1. Multiverse robustness: {int(MV.n_specs_total.iloc[0])} random covariate specifications (forced controls fixed, each candidate included with probability 0.5)")
rows = [[lab(r.cov), yn(r.in_main_set), f"{int(r.n_specs)}", f"{100*r.cred_frac:.1f}", f"{100*r.sign_agree:.1f}", f"{r.IRR_median:.3f} ({r.IRR_min:.3f}-{r.IRR_max:.3f})", ("Robust" if r.robust else "Not robust") + (" (provisional, n<50)" if r.provisional else "")] for r in MV.sort_values("cred_frac", ascending=False).itertuples()]
TBL(["Variable", "In main set", "n specs", "Credible %", "Sign agreement %", "IRR median (range)", "Verdict"], rows, [6.3, 1.5, 1.3, 1.5, 1.8, 3.0, 2.4], fs=7.5)
LEG("Credible % = share of specifications in which the 95% CrI excludes 1; sign agreement = share with the same direction as the principal model (or the multiverse median when not in the main set). Robust = credible ≥ 75% and sign agreement ≥ 95%; n < 50 flagged provisional.")
rb = MV[MV.robust]
_mvfull = f"다중우주 {int(MV.n_specs_total.iloc[0])}사양에서 강건 판정 {len(rb)}개" + (f"({'; '.join(f'{KO(r.cov)} credible {100*r.cred_frac:.0f}%·부호 {100*r.sign_agree:.0f}%' for r in rb.itertuples())})" if len(rb) else "") + f"; 주모형 credible 변수의 재현율: " + ("; ".join(f"{KO(r.cov)} {100*MV[MV['cov']==r.cov].cred_frac.iloc[0]:.0f}%(n={int(MV[MV['cov']==r.cov].n_specs.iloc[0])})" for r in ch.itertuples()) or "해당 없음") + "."
_mvshort = f"다중우주 {int(MV.n_specs_total.iloc[0])}사양(변수당 n {int(MV.n_specs.min())}-{int(MV.n_specs.max())})에서 강건 판정 {len(rb)}개: {', '.join(KO(v) for v in rb['cov']) or '없음'}; 주모형 credible {len(ch)}개 중 다중우주 재현율 75% 이상 {sum(MV[MV['cov']==v].cred_frac.iloc[0] >= 0.75 for v in ch['cov'])}개(변수별 수치는 표)."
YOJI(_mvfull, alt=_mvshort)

CAP(f"Table S2. COVID-19 period ({INFO['covid_post_from']}+) main effect and variable × post interactions (pooled principal model)")
rows = [[r.label_en if r.term == "post_main" else lab(r.cov), {"post_main": "Post-period main effect", "var_x_post": "Variable × post (ratio)", "var_pre": "Variable, pre-period"}[r.term], ci(r._asdict()), f"{r.P_gt1:.3f}", yn(r.cred)] for r in COV.itertuples()]
TBL(["Term", "Type", "IRR or ratio (95% CrI)", "P(>1)", "Credible"], rows, [7.3, 3.5, 3.2, 1.3, 1.5], fs=7.5)
LEG(f"Post = indicator for years ≥ {INFO['covid_post_from']} added to the principal model together with variable × post products; ratios > 1 indicate a stronger positive association after {INFO['covid_post_from']}. WAIC {COV.WAIC.iloc[0]:,.1f}.")
pm = COV[COV.term == "post_main"].iloc[0]; cx = COV[(COV.term == "var_x_post") & COV.cred]
YOJI(f"COVID 시기 주효과 IRR {pm.IRR:.3f}({pm.lo:.3f}-{pm.hi:.3f}); 변수×post 상호작용 credible {len(cx)}/{int((COV.term=='var_x_post').sum())}" + (f"({'; '.join(f'{KO(r.cov)} {r.IRR:.3f}' for r in cx.itertuples())})" if len(cx) else "") + ".",
     alt=f"COVID 시기 주효과 IRR {pm.IRR:.3f}({pm.lo:.3f}-{pm.hi:.3f}); 변수×post 상호작용 credible {len(cx)}/{int((COV.term=='var_x_post').sum())}(비율 범위 {COV[COV.term=='var_x_post'].IRR.min():.3f}-{COV[COV.term=='var_x_post'].IRR.max():.3f}; 변수별 수치는 표).")

CAP("Table S3. Likelihood comparison (forced-only model) and Type I space-time interaction sensitivity")
rows = [[f"REF_forced_only · {FAMN[r.family]}", f"{r.WAIC:,.1f}", f"{r.DIC:,.1f}", f"{r.LCPO:.4f}", f"{int(r.cpo_fail)}", "Principal likelihood" if r.family == MAINFAM else ""] for r in LK.itertuples()]
TBL(["Model", "WAIC", "DIC", "LCPO", "CPO fail", "Decision"], rows, [6.5, 2.4, 2.4, 2.0, 1.5, 2.8], fs=7.5)
if T1 is not None:
    rows = []
    for r in MAIN[MAIN.role == "hypothesis"].itertuples():
        t = T1[T1['cov'] == r.cov].iloc[0]; rows.append([lab(r.cov), ci(r._asdict()), yn(r.cred), ci(t), yn(t.cred)])
    TBL(["Variable", "Principal IRR (95% CrI)", "Credible", "Type I IRR (95% CrI)", "Credible"], rows, [6.3, 3.3, 1.5, 3.3, 1.5], fs=7.5)
    LEG(f"Type I = principal model plus an IID district-year interaction term (WAIC {T1.WAIC.iloc[0]:,.1f} vs principal {MFIT.WAIC:,.1f}).")
    same = sum(bool(MAIN[MAIN['cov'] == v].cred.iloc[0]) == bool(T1[T1['cov'] == v].cred.iloc[0]) for v in HYPV)
    YOJI(f"우도: {FAMN[MAINFAM]} WAIC {LK[LK.family==MAINFAM].WAIC.iloc[0]:,.1f} vs {' / '.join(f'{FAMN[r.family]} {r.WAIC:,.1f}' for r in LK[LK.family!=MAINFAM].itertuples())}. Type I 상호작용 추가 시 WAIC {T1.WAIC.iloc[0]:,.1f}, 가설 변수 credible 판정 일치 {same}/{len(HYPV)}.")
else:
    LEG("Type I sensitivity not available."); YOJI(f"우도: {FAMN[MAINFAM]} WAIC {LK[LK.family==MAINFAM].WAIC.iloc[0]:,.1f}.")

CAP(f"Table S4. Window × variable interactions (pooled model, reference window {WN[0]} = {WY[WN[0]]})")
rows = [[lab(r.cov), f"{r.window} ({WY[r.window]})", ci(r._asdict(), "IRR_ratio"), f"{r.P_gt1:.3f}", yn(r.cred)] for r in INT.itertuples()]
TBL(["Variable", "Window", "IRR ratio vs reference (95% CrI)", "P(>1)", "Credible"], rows, [6.5, 3.0, 3.8, 1.5, 1.5], fs=7.5)
LEG(f"Ratios of window-specific IRRs to the reference window from one pooled model with window indicators and products; non-overlapping windows. WAIC {INT.WAIC.iloc[0]:,.1f}.")
YOJI(f"상호작용 {len(INT)}항 중 credible {len(icr)}개; 비율 범위 {INT.IRR_ratio.min():.3f}-{INT.IRR_ratio.max():.3f}.")

CAP("Table S5. Yearly spatial autocorrelation of observed log SIR (Moran's I, 999 permutations) and residual check")
rows = [[f"{int(r.year)}", f"{r.crude_rate_per100k:,.1f}", f"{r.moran_I:.3f}", f"{r.p_perm:.3f}"] for r in MOR.itertuples()] + [[f"Residual (district-mean Pearson)", "", f"{RM[RM.quantity=='pearson_residual_area_mean'].moran_I.iloc[0]:.3f}", f"{RM[RM.quantity=='pearson_residual_area_mean'].p_perm.iloc[0]:.3f}"]]
TBL(["Year", "Crude rate /100k", "Moran's I", "Permutation P"], rows, [4.0, 3.5, 3.0, 3.0], fs=7.5, cat_rows=[len(rows) - 1])
LEG("Observed SIR = cases / E with 0.5 added to cases before the log; queen contiguity weights (row-standardised). The residual row uses district means of Pearson residuals from the principal model.")
YOJI(f"관측 log SIR Moran I는 {MOR.moran_I.min():.3f}({int(MOR.loc[MOR.moran_I.idxmin(),'year'])}년)-{MOR.moran_I.max():.3f}({int(MOR.loc[MOR.moran_I.idxmax(),'year'])}년), 전 연도 P {MOR.p_perm.max():.3f} 이하; 주모형 잔차 Moran I {MFIT.resid_moran_I:.3f}(P {MFIT.resid_moran_p:.3f}).")

if OS is not None:
    PLAB = INFO.get("offset_E_label") or OFFC   # 주분석 E 이름(외부 E면 E_std)
    CAP(f"Table S6. Denominator sensitivity: principal model refitted with E based on {INFO['offset_sensitivity']} instead of {PLAB}")
    rows = []
    for r in MAIN[MAIN.role == "hypothesis"].itertuples():
        t = OS[OS['cov'] == r.cov].iloc[0]; rows.append([lab(r.cov), ci(r._asdict()), yn(r.cred), ci(t), yn(t.cred)])
    TBL(["Variable", f"Principal ({PLAB}) IRR (95% CrI)", "Credible", f"Sensitivity ({INFO['offset_sensitivity']}) IRR (95% CrI)", "Credible"], rows, [5.9, 3.5, 1.5, 3.5, 1.5], fs=7.5)
    LEG(f"Same covariates and random effects; only the offset changes. WAIC {OS.WAIC.iloc[0]:,.1f} (not comparable across offsets).")
    same = sum(bool(MAIN[MAIN['cov'] == v].cred.iloc[0]) == bool(OS[OS['cov'] == v].cred.iloc[0]) for v in HYPV)
    YOJI(f"분모를 {INFO['offset_sensitivity']}로 바꿔도 가설 변수 credible 판정 일치 {same}/{len(HYPV)}.")

# ── 한계 ──
SEC("Analysis limitations")
lim = [
 f"① 종속변수는 진료실인원(의료 이용)이므로 유병의 대리지표이며, 요양기관 밀도를 강제통제했어도 접근성·수진 행태 교란이 남는다.",
 (f"② 기대건수 E는 10세 8구간 간접 연령표준화이며 성은 표준화하지 못했다(성비 강제통제). 전국 연령별 기준율은 298분류 세부 분류 합이라 중복 진단이 포함된 연령 프로파일이다." if EXTE else f"② 기대건수 E는 연령 비표준화(전국 연도별 조율)이고 고령인구비율로만 부분 보정했으므로 연령 구조 잔존 교란이 있다(연령별 E는 2차 과제)."),
 f"③ 공변량 결측 {int(imp.sum())}셀을 대치했다(보간 {int(imp.n_imputed_interp)}·시군구 평균 {int(imp.n_imputed_sgg_mean)}·연도 전국 평균 {int(imp.n_imputed_year_mean)}); 전 연도 결측 시군구: {', '.join(f'{v}={SAM(v)}' for v in META.index if isinstance(META.loc[v,'sgg_all_missing'], str) and META.loc[v,'sgg_all_missing']) or '없음'}.",
 f"④ 생태학적(시군구 집계) 연관으로 개인 수준 인과 해석은 불가하며, KCHS 표준화율은 표본조사 추정치로 측정오차가 있다.",
 f"⑤ 세트 비교는 사전지정 {len(S['sets'])}개 세트에 한정되고, 다중우주는 후보 {len(INFO['candidates'])}개의 부분집합 {int(MV.n_specs_total.iloc[0])}사양으로 모형 불확실성의 일부만 반영한다.",
 f"⑥ 2024년 행정구역 경계로 고정한 229 시군구 패널이며 경계 변경·통합 구는 마스터 키 규칙(boundary_flag)으로 합산되었다.",
 f"⑦ 이웃 구조는 queen 인접이고 섬 {int(NB.islands_linked)}곳은 최근접 1개와 연결했다; 공간 RR과 핫스팟은 이 그래프와 BYM2 PC 사전분포에 조건부이다.",
 f"⑧ 창별 재적합은 창마다 {min(WFIT.n_years)}-{max(WFIT.n_years)}개 연도만 사용하므로 연도 효과 추정이 불안정할 수 있고, COVID 전후 비교는 {INFO['covid_post_from']}년 이후 {int((P.year>=INFO['covid_post_from']).sum()//INFO['n_sgg'])}개 연도에 의존한다.",
]
if vifo: lim.append(f"⑨ VIF가 {RU['vif_threshold']:g}을 넘는 변수({', '.join(META.loc[v,'label_ko'] for v in vifo)})를 사전지정 규칙에 따라 유지했으므로 해당 계수는 공선성으로 불안정할 수 있다(다중우주 재현율로 보완).")
if lowc: lim.append(f"⑩ 관측 비율 70% 미만 변수({', '.join(f'{KO(v)} {100*CV(v):.0f}%' for v in lowc)})는 대치 비중이 커 계수 해석에 주의한다.")
if "PILOT" in S.get("note", "").upper(): lim.append("⑪ 이번 판은 파이프라인 파일럿용 임시 공변량 풀로, 문헌 기반 sets json 교체 후 재실행한 결과로 대체되어야 한다.")
for t in lim: para(t, sz=9, after=2)

# ── α 요약 ──
SEC("α summary")
rbtxt = ", ".join(META.loc[v, "label_ko"] for v in rb['cov']) or "없음"
alpha = [
 f"• 우도 {FAMN[MAINFAM]}; 주모형 세트 {BESTSET}(WAIC {cb.WAIC:,.1f}, 기준모형 대비 {cb.WAIC-cref.WAIC:+.1f}).",
 f"• credible 가설 변수 {len(ch)}개: {ctxt if len(ctxt) <= 300 else ctxt_s}.",
 f"• 다중우주 강건: {rbtxt}; 음성대조 credible {int(NEG.cred.sum()) if len(NEG) else 0}/{len(NEG)}.",
 f"• 공간: 핫스팟 {int(MFIT.n_hotspot)}·콜드스팟 {int(MFIT.n_coldspot)}, RR {MFIT.RR_min:.3f}-{MFIT.RR_max:.3f}, 잔차 Moran I {MFIT.resid_moran_I:.3f}(P {MFIT.resid_moran_p:.3f}).",
 f"• 시기: 창별 credible 수 {', '.join(f'{WY[w]} {int(WFIT[WFIT.window==w].n_cred_hyp.iloc[0])}' for w in WN)}; 상호작용 credible {len(icr)}/{len(INT)}; COVID 주효과 {pm.IRR:.3f}({pm.lo:.3f}-{pm.hi:.3f}).",
]
for t in alpha: para(t, sz=9.5, after=2)

# ── 최종 요지 ──
SEC("최종 요지")
_fin = lambda c: f"{INFO['n_sgg']}개 시군구 {INFO['years'][0]}-{INFO['years'][1]}년 {DKO} 진료실인원({allr['cases']:,.0f}명)을 {FAMN[MAINFAM]} BYM2 시공간 모형으로 분석한 결과, 주모형 세트 {BESTSET}에서 credible 가설 변수는 {len(ch)}개({c}), 다중우주 강건 {len(rb)}개({rbtxt}), 핫스팟 {int(MFIT.n_hotspot)}·콜드스팟 {int(MFIT.n_coldspot)}곳, 창×변수 상호작용 credible {len(icr)}/{len(INT)}, 음성대조 credible {int(NEG.cred.sum()) if len(NEG) else 0}/{len(NEG)}."
YOJI(_fin(ctxt), alt=_fin(ctxt_s))

base = os.path.join(OUTD, f"{DATE}_{TAG}_핵심{SUF}"); doc.save(base + ".docx")
r = subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", OUTD, base + ".docx"], capture_output=True, text=True, timeout=300)
assert os.path.exists(base + ".pdf"), "PDF 변환 실패: " + r.stderr
print(f"[82] {base}.docx / .pdf 생성")
