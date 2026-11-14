#!/usr/bin/env python3
# 80_v25 — , 열마다 기록. 나머지는 80_v와 동일)
# 80_v — (사본 2026-10-19: sets json extra_columns 로 02_패널 파일 열 병합; 나머지 원본과 동일) 질환 패널 생성 (시군구×연도, 2011~2024). 사용: python3 80_build_disease_panel.py <TAG>
#  입력: 02_패널/MASTER_시군구_연도_wide.parquet, 04_분석/<TAG>/sets_<TAG>.json(+hypothesis_table_<TAG>.csv) → _st_config.load_config 로 정규화, 지도 final.shp(면적)
#  처리: outcome·population·forced·세트·음성대조 변수 추출 → transform(per100k/per1k/pct_of_pop/pct_of_area/log/log1p/none)
#        → 결측 대치(시군구 내 앞뒤 연도 선형 보간 → 시군구 평균 → 연도 전국 평균; 건수 기록) → z 표준화(전체 풀링, per 1 SD)
#        → VIF>임계 처리(rules.vif_action: drop = 후보만 반복 제거 / report = 유지·기록) → E = population × 전국 연도별 조율
#  외부 E(PLAN R10): sets json "offset_E_column"(예 E_std) → 02_패널/<TAG>_Estd.csv 병합해 E 대체(crude는 E_crude), "offset_E_sensitivity_column" → E_sens(81 S10)
#  산출: 04_분석/<TAG>/config_<TAG>.json, panel_<TAG>.csv, panel_META_<TAG>.csv, panel_INFO_<TAG>.json  (ST_VER=v2 → sets_<TAG>_v2.json 입력, 모든 산출에 _v2 접미)
import sys, os, json, unicodedata
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _st_config import load_config, ROOT, NFC, SUF   # SUF: ST_VER 버전 접미(""=v1, "_v2")
SHP = os.environ.get("ST_SHP", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "boundary", "final.shp"))
TAG = sys.argv[1]; OUT = os.path.join(ROOT, "04_분석", TAG)
C = load_config(TAG); RU = C["rules"]; Y0, Y1 = RU["years"]
FORCED, CAND, NEG, V = C["forced"], C["candidates"], C["negative_controls"], C["vars"]
SENSV = C.get("sensitivity_only_vars", []); ALLV = FORCED + CAND + SENSV + NEG
OFFC = C.get("offset_column", "population"); OFFS = C.get("offset_sensitivity"); EXCL = C.get("exclude_years", [])

M = pd.read_parquet(os.path.join(ROOT, "02_패널", "MASTER_시군구_연도_wide.parquet"))
M.columns = [NFC(c) for c in M.columns]
# ── (_v 사본, 2026-10-19 R14) 외부 공변량 병합: sets json "extra_columns" = {"<마스터식 열 이름>": ["<02_패널 파일>", "<원본 열>"]} → M 에 (year, fbd_region) 병합 ──
_EXT = json.load(open(os.path.join(OUT, f"sets_{TAG}{SUF}.json"), encoding="utf-8")).get("extra_columns") or {}
for _nc, (_f, _c) in _EXT.items():
    _X = pd.read_csv(os.path.join(ROOT, "02_패널", _f), encoding="utf-8-sig")[["year", "fbd_region", _c]].rename(columns={_c: NFC(_nc)}); _X["fbd_region"] = _X.fbd_region.map(NFC)
    _n = len(M); M["fbd_region"] = M.fbd_region.map(NFC); M = M.merge(_X, on=["year", "fbd_region"], how="left", validate="many_to_one"); assert len(M) == _n
    print(f"[80v] 외부 열 병합 {NFC(_nc)} ← 02_패널/{_f}:{_c} (2011-24 비결측 {int(M.loc[(M.year >= 2011) & (M.year <= 2024), NFC(_nc)].notna().sum())}행)")
# ── (2026-11-04) 인구 교정: sets json "population_override" = [{"year":Y,"fbd_region":R,"population":N,"source":"..."}] → M.population 대체(원 값 출력) ──
for _o in (json.load(open(os.path.join(OUT, f"sets_{TAG}{SUF}.json"), encoding="utf-8")).get("population_override") or []):
    _m = (M.year == int(_o["year"])) & (M.fbd_region.map(NFC) == NFC(_o["fbd_region"])); assert _m.sum() == 1, _o
    print(f"[80v] 인구 교정 {_o['year']} {_o['fbd_region']}: {M.loc[_m, 'population'].iloc[0]:,.0f} → {_o['population']:,} ({_o.get('source','')})"); M.loc[_m, "population"] = float(_o["population"])
# ── (80_v25, 2026-11-13) 2025년 행: population·마스터 열 채움 ──
if Y1 >= 2025:
    import sqlite3
    _DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
    _con = sqlite3.connect(f"file:{_DB}?mode=ro", uri=True); _rc = [NFC(c) for c in pd.read_sql("pragma table_info(region_year)", _con).name]
    M["fbd_region"] = M.fbd_region.map(NFC); _m25 = M.year == 2025; assert _m25.sum() == 229
    _need = ["population"] + [V[k]["column"] for k in ALLV]
    _q = [c for c in _need if c in _rc]
    _R = pd.read_sql("select fbd_region, " + ", ".join(f'"{c}"' for c in _q) + " from region_year where year=2025", _con); _R.columns = ["fbd_region"] + _q; _R["fbd_region"] = _R.fbd_region.map(NFC)
    _R = _R.set_index("fbd_region"); _P24 = M[M.year == 2024].set_index("fbd_region")
    for _c in _need:
        _cur = M.loc[_m25, _c].values.astype(float) if _c in M.columns else np.full(229, np.nan)
        _reg = M.loc[_m25, "fbd_region"]
        _ry = _reg.map(_R[_c]).values.astype(float) if _c in _R.columns else np.full(229, np.nan)
        _lo = _reg.map(_P24[_c]).values.astype(float)
        _n_cur = int(np.isfinite(_cur).sum()); _fill = np.where(np.isfinite(_cur), _cur, _ry); _n_ry = int(np.isfinite(_fill).sum()) - _n_cur
        _same = int(np.isclose(_fill[np.isfinite(_fill)], _lo[np.isfinite(_fill)]).sum()) if np.isfinite(_fill).any() else 0
        _fill2 = np.where(np.isfinite(_fill), _fill, _lo); _n_lo = int(np.isfinite(_fill2).sum()) - int(np.isfinite(_fill).sum())
        M.loc[_m25, _c] = _fill2
        print(f"[80v25] 2025 {_c[:60]}: 마스터 {_n_cur} + region_year {_n_ry} (그중 2024와 같은 값 {_same}) + LOCF {_n_lo} = {int(np.isfinite(_fill2).sum())}")
    assert M.loc[_m25, "population"].gt(0).all()
OUTC = C["outcome_column"]; assert OUTC in M.columns, f"outcome 없음: {OUTC}"
for k in ALLV: assert V[k]["column"] in M.columns, f"마스터에 없는 열: {V[k]['column']} ({k})"
D = M[(M.year >= Y0) & (M.year <= Y1)].sort_values(["key", "year"]).reset_index(drop=True)
assert D.groupby("year").key.nunique().nunique() == 1, "연도별 시군구 수 불일치"
# ── 분모(offset): population 또는 json 지정 열(METS 수검자수·BRCA 여자 인구). 결측 시 BRCA형 fallback(인구×100/(100+성비)) ──
assert OFFC in M.columns, f"offset 열 없음: {OFFC}"
D["offset"] = D[OFFC].astype(float); n_off_fb = 0; n_off_fb2 = 0
if OFFC != "population" and D["offset"].isna().any():
    if C.get("offset_fallback") == "population_by_sex_ratio":   # BRCA json fallback 1: 인구×100/(100+성비)
        sr = D["eloc__DT_1YL20701__남녀성비＜br＞(A÷B×100)"].astype(float); fb = D.population * 100 / (100 + sr)
        m_ = D["offset"].isna() & fb.notna(); n_off_fb = int(m_.sum()); D.loc[m_, "offset"] = fb[m_]
    if D["offset"].isna().any() and not OFFC.startswith("chk__"):   # fallback 2(주민등록 계·여 결측 시군구, 예 세종): 인구 × 그해 전국 (분모/인구) 비율
        ratio = D.groupby("year").apply(lambda d: d["offset"].sum() / d.loc[d["offset"].notna(), "population"].sum())
        m_ = D["offset"].isna(); n_off_fb2 = int(m_.sum()); D.loc[m_, "offset"] = (D.population * D.year.map(ratio))[m_]
# ── 분석 행: outcome·offset 결측 행 및 제외 연도 제거(기록) ──
drop_mask = D[OUTC].isna() | D["offset"].isna() | (D["offset"] <= 0) | D.year.isin(EXCL)
DROPPED = D.loc[drop_mask, ["year", "key"]]; D = D[~drop_mask].reset_index(drop=True)
YOBS = sorted(D.year.unique()); assert len(YOBS) >= 3, "분석 가능한 연도 부족"
for _nc in _EXT: assert D[NFC(_nc)].notna().all(), f"외부 열 결측: {_nc} {int(D[NFC(_nc)].isna().sum())}행"

import geopandas as gpd
G = gpd.read_file(SHP); G["region"] = G["region"].map(NFC); D["fbd_region"] = D["fbd_region"].map(NFC)
area = G.set_index("region").geometry.area
assert set(D.fbd_region.unique()) <= set(area.index), "지도에 없는 fbd_region: " + str(set(D.fbd_region.unique()) - set(area.index))
UNOBS = sorted(set(area.index) - set(D.fbd_region.unique()))   # outcome/분모 전 연도 결측으로 빠진 시군구(예: METS 세종) — 그래프에는 남고 모형에서는 미관측
D["area_m2"] = D.fbd_region.map(area).values

out = D[["year", "key", "sido_std", "sigungu", "fbd_region", "population", "area_m2", "offset"]].copy()
out["cases"] = D[OUTC].values
assert out.cases.notna().all() and out.population.notna().all() and (out.population > 0).all()
# E = offset × 전국 연도별 조율(간접표준화; offset=population이면 PLAN §0 그대로)
nat = out.groupby("year").agg(cases=("cases", "sum"), off=("offset", "sum"), pop=("population", "sum")); nat["rate"] = nat.cases / nat["off"]; nat["rate_pop"] = nat.cases / nat["pop"]
out["E"] = out.offset * out.year.map(nat.rate); assert abs(out.E.sum() - out.cases.sum()) < 1e-6 * out.cases.sum()
# ── 외부 E(PLAN R10, 예 간접 연령표준화 E_std): sets json "offset_E_column" 이 있으면 02_패널/<TAG>_Estd.csv(또는 "offset_E_file")를 병합해 E 로 사용 ──
#    crude E 는 E_crude 로 보존; "offset_E_sensitivity_column"(예 E_std_nondem) → E_sens(81 S10 분모 민감도). 분석 행 기준으로 연도별 ΣE=Σcases 재척도(간접 표준화 유지).
EXTC = C.get("offset_E_column"); EXTS = C.get("offset_E_sensitivity_column"); EXT_INFO = {}
if EXTC:
    assert not OFFS, "offset_sensitivity 와 offset_E_sensitivity_column 동시 지정 불가"
    ef = os.path.join(ROOT, "02_패널", C.get("offset_E_file") or f"{TAG}_Estd.csv"); assert os.path.exists(ef), f"외부 E 파일 없음: {ef}"
    XE = pd.read_csv(ef, encoding="utf-8-sig"); XE["fbd_region"] = XE.fbd_region.map(NFC)
    cols = [EXTC] + ([EXTS] if EXTS else []); assert all(c in XE.columns for c in cols), f"외부 E 열 없음: {cols}"
    mg = out[["year", "fbd_region"]].merge(XE[["year", "fbd_region"] + cols], on=["year", "fbd_region"], how="left", validate="one_to_one")
    assert mg[cols].notna().all().all() and (mg[cols] > 0).all().all(), f"외부 E 결측/0: {int(mg[cols].isna().any(axis=1).sum())}행"
    out["E_crude"] = out.E
    rs = lambda v: v * out.groupby("year").cases.transform("sum") / v.groupby(out.year).transform("sum")
    out["E"] = rs(pd.Series(mg[EXTC].values, index=out.index)).values; assert abs(out.E.sum() - out.cases.sum()) < 1e-6 * out.cases.sum()
    if EXTS: out["E_sens"] = rs(pd.Series(mg[EXTS].values, index=out.index)).values; OFFS = C.get("offset_E_label_sensitivity") or EXTS
    EXT_INFO = dict(offset_E_column=EXTC, offset_E_file=os.path.basename(ef), offset_E_sensitivity_column=EXTS, offset_E_label=C.get("offset_E_label") or EXTC,
                    E_over_Ecrude=dict((k, round(float(v), 4)) for k, v in (out.E / out.E_crude).describe()[["min", "50%", "max"]].items()))
    print(f"[80] 외부 E 사용: {EXTC} ({os.path.basename(ef)}); crude E → E_crude 보존; 민감도 E_sens = {EXTS}; E/E_crude {EXT_INFO['E_over_Ecrude']}")
out["SIR"] = out.cases / out.E
if OFFS and not EXTC:   # 분모 민감도(METS: population) → E_sens
    assert OFFS in M.columns or OFFS == "population"; os_ = D[OFFS].astype(float) if OFFS != "population" else D.population.astype(float)
    assert os_.notna().all() and (os_ > 0).all(), f"offset_sensitivity {OFFS} 결측"
    ns = out.assign(o=os_.values).groupby("year").agg(c=("cases", "sum"), o=("o", "sum")); out["E_sens"] = os_.values * out.year.map(ns.c / ns.o)
# 창: 사전지정 창을 관측 연도에 맞춰 자르고 이름을 실제 범위로(예: METS 2013~)
W = {}
for wn, (a, b) in RU["windows"].items():
    yy = [y for y in YOBS if a <= y <= b]
    if not yy: print(f"[80] 창 {wn} 에 관측 연도 없음 → 제외"); continue
    nm = f"{wn.split('_')[0]}_{min(yy)}-{str(max(yy))[2:]}" if (min(yy) != a or max(yy) != b) else wn; W[nm] = [int(min(yy)), int(max(yy))]
out["window"] = ""
for wn, (a, b) in W.items(): out.loc[(out.year >= a) & (out.year <= b), "window"] = wn
assert (out.window != "").all(), "창에 속하지 않는 연도 존재"
out["post"] = (out.year >= RU["covid_post_from"]).astype(int)

def transform(raw, tr, pop, area):
    if tr == "none": return raw
    if tr == "per100k": return raw / pop * 1e5
    if tr == "per100k_log1p": return np.log1p((raw / pop * 1e5).clip(lower=0))
    if tr == "per1k": return raw / pop * 1e3
    if tr == "pct_of_pop": return raw / pop * 100
    if tr == "pct_of_area": return raw / area * 100
    if tr == "log": return np.log(raw.where(raw > 0))
    if tr == "log1p": return np.log1p(raw.clip(lower=0))
    raise ValueError(tr)

meta = []
for k in ALLV:
    src, tr = V[k]["column"], V[k]["transform"]
    raw = D[src].astype(float); x = transform(raw, tr, D.population, D.area_m2)
    tmp = pd.DataFrame({"key": D.key, "year": D.year, "x": x.values})
    tmp["x1"] = tmp.groupby("key")["x"].transform(lambda s: s.interpolate(method="linear", limit_area="inside"))
    n_interp = int(tmp.x.isna().sum() - tmp.x1.isna().sum())
    tmp["x2"] = tmp.x1.fillna(tmp.groupby("key")["x1"].transform("mean")); n_sgg = int(tmp.x1.isna().sum() - tmp.x2.isna().sum())
    tmp["x3"] = tmp.x2.fillna(tmp.groupby("year")["x2"].transform("mean")); n_year = int(tmp.x2.isna().sum() - tmp.x3.isna().sum())
    assert tmp.x3.notna().all(), f"{k}: 대치 후에도 결측"
    out[k + "_raw"] = tmp.x3.values; mu, sd = float(tmp.x3.mean()), float(tmp.x3.std(ddof=0)); assert sd > 0, f"{k}: SD=0"
    out[k] = (tmp.x3.values - mu) / sd
    yrs = tmp[tmp.x.notna()].year
    meta.append(dict(variable=k, source_column=src, transform=tr, label_en=V[k]["label_en"], label_ko=V[k]["label_ko"], role=V[k]["role"], expected_direction=V[k]["expected_direction"],
                     n_obs=len(tmp), n_missing_raw=int(raw.isna().sum()), n_missing_after_transform=int(x.isna().sum()), coverage=round(float(x.notna().mean()), 3),
                     obs_year_min=int(yrs.min()) if len(yrs) else None, obs_year_max=int(yrs.max()) if len(yrs) else None, n_sgg_observed=int(tmp[tmp.x.notna()].key.nunique()),
                     n_imputed_interp=n_interp, n_imputed_sgg_mean=n_sgg, n_imputed_year_mean=n_year, mean=mu, sd=sd, min=float(tmp.x3.min()), median=float(tmp.x3.median()), max=float(tmp.x3.max()),
                     sgg_all_missing=";".join(sorted(tmp.loc[tmp.x2.isna(), "key"].unique().tolist()))))
META = pd.DataFrame(meta); META["low_coverage"] = META.coverage < 0.7

def vif_table(cols):
    np.seterr(all="ignore"); X = np.column_stack([np.ones(len(out)), out[cols].values.astype(np.float64)]); vifs = {}
    for j, c in enumerate(cols):
        y = X[:, j + 1]; Xo = np.delete(X, j + 1, axis=1); beta, *_ = np.linalg.lstsq(Xo, y, rcond=None)
        r2 = 1 - ((y - Xo @ beta) ** 2).sum() / ((y - y.mean()) ** 2).sum(); vifs[c] = 1 / max(1 - r2, 1e-12)
    return pd.Series(vifs)
keep = FORCED + CAND; dropped = []; TH = RU["vif_threshold"]   # 민감도 전용 변수(S1b 비만율)는 VIF 제거 루프 밖, 값만 기록
if RU["vif_action"] == "drop":
    while True:
        vt = vif_table(keep); cand = vt[(vt > TH) & (~vt.index.isin(FORCED))]
        if cand.empty: break
        dv = cand.idxmax(); dropped.append((dv, float(cand.max()))); keep.remove(dv)
vt0 = vif_table(FORCED + CAND + SENSV); vt_final = pd.concat([vif_table(keep), vif_table(keep + SENSV)[SENSV]]) if SENSV else vif_table(keep)
META["vif_initial"] = META.variable.map(vt0).round(2); META["vif_final"] = META.variable.map(vt_final).round(2)
META["vif_dropped"] = META.variable.isin([d for d, _ in dropped]); META["vif_at_drop"] = META.variable.map(dict(dropped)).round(2)
META["vif_over_threshold_retained"] = (RU["vif_action"] == "report") & (META.vif_final > TH)
if (vt_final[FORCED] > TH).any(): print("★경고: 강제통제 VIF>임계 잔존:", vt_final[FORCED][vt_final[FORCED] > TH].round(1).to_dict())

out.to_csv(os.path.join(OUT, f"panel_{TAG}{SUF}.csv"), index=False, encoding="utf-8-sig")
META.to_csv(os.path.join(OUT, f"panel_META_{TAG}{SUF}.csv"), index=False, encoding="utf-8-sig")
C["sets_after_vif"] = {k: [v for v in vs if v not in [d for d, _ in dropped]] for k, vs in C["sets"].items()}
json.dump(C, open(os.path.join(OUT, f"config_{TAG}{SUF}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
info = dict(tag=TAG, outcome_column=OUTC, unobserved_regions=UNOBS, n_regions_map=int(len(area)), offset_column=OFFC, offset_sensitivity=OFFS, n_offset_fallback=n_off_fb, n_offset_fallback_national_ratio=n_off_fb2, exclude_years=EXCL,
            years=[int(min(YOBS)), int(max(YOBS))], years_prespecified=[int(Y0), int(Y1)], years_observed=[int(y) for y in YOBS],
            n_dropped_rows=int(len(DROPPED)), dropped_by_year={int(y): int(n) for y, n in DROPPED.groupby("year").size().items()}, dropped_sgg=sorted(DROPPED.key.unique().tolist())[:30],
            n_rows=int(len(out)), n_sgg=int(out.key.nunique()), n_years=int(out.year.nunique()),
            total_cases=float(out.cases.sum()), total_E=float(out.E.sum()), total_person_years=float(out.population.sum()), total_offset=float(out.offset.sum()), crude_rate_per_100k_overall=float(out.cases.sum() / out.offset.sum() * 1e5),
            national_rate_by_year={int(y): float(r * 1e5) for y, r in nat.rate.items()}, forced=FORCED, candidates=CAND, sensitivity_only_vars=SENSV, sensitivity_sets=C.get("sensitivity_sets", []), negative_controls=NEG, vif_dropped=[d for d, _ in dropped],
            vif_action=RU["vif_action"], vif_threshold=TH, vif_over_threshold=[v for v in keep if vt_final[v] > TH], sets=C["sets_after_vif"],
            n_imputed_total=int(META[["n_imputed_interp", "n_imputed_sgg_mean", "n_imputed_year_mean"]].sum().sum()), low_coverage=META.variable[META.low_coverage].tolist(), windows=W, covid_post_from=RU["covid_post_from"], **EXT_INFO)
json.dump(info, open(os.path.join(OUT, f"panel_INFO_{TAG}{SUF}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"[80] {TAG}{SUF}: rows {len(out)} · sgg {out.key.nunique()} · years {min(YOBS)}-{max(YOBS)} (dropped rows {len(DROPPED)}, offset {OFFC}, fallback {n_off_fb}+{n_off_fb2}) · cases {out.cases.sum():,.0f} · E check ok · imputed {info['n_imputed_total']} · VIF action {RU['vif_action']} dropped {dropped} over-threshold {info['vif_over_threshold']}")
print(META[["variable", "role", "coverage", "n_sgg_observed", "n_imputed_interp", "n_imputed_sgg_mean", "n_imputed_year_mean", "vif_final", "sgg_all_missing"]].to_string())
