#!/usr/bin/env python3
# 99c — 결핵 신환자 신고(TBNW) 결핵 가설 풀(2026-11-14). 229 시군구 × 2013–2025. 공유 원본 수정 없음.
#  감염병 경로(플레이북 25 3단계·13 §3 항목 0): 한국 결핵 신환자의 다수는 고령층의 잠복결핵 재활성화. 축 =
#   (1) 재활성화·돌봄 공백: 독거노인 가구 비율  (2) 박탈: 의료급여 1종 진료실인원(10만 명당)  (3) 숙주 감수성: 검진 당뇨 의심 비율·현재 흡연율
#   (4) 유입: 인구 천 명당 외국인 주민(고부담국 출신 이주)  (5) 집단 거주·발견: 65세 이상 10만 명당 요양병원  (6) 진단 접근: 10만 명당 종합병원
#  체육·신체활동 변수는 결핵 기전 가설이 없어 넣지 않는다.
#  출처: 기준 SQLite disease_panel *_raw(열마다 비결측이 가장 많은 태그, 세종 보충 포함; 99H_hcuv_build와 같은 규칙) / 외국인 = FBD 정본 통합자료 261030 /
#        80세 이상 비율 = LEPT 풀(INFECT_Estd2 + KOSIS 2025-12) / 민감도 전용: 고위험 음주율·기초생활수급률(2021-23 양쪽 규칙 33칸 정정).
#  2025: region_year 원값 우선(그 열의 2024 region_year 값이 풀 2024 값과 같을 때만, 세종 등 결측 칸은 2024 이월), 그 밖은 2024 이월(LOCF). 규칙표 = EXT_canonical_pool_TBNW_2025rule.csv
#  산출: 02_패널/EXT_canonical_pool_TBNW_261114.csv
import os, sqlite3, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널")
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
ZD = os.path.join(os.path.expandvars("$ST_DATA_ROOT"), "기타/R_Studio/FBD_DATA_ZIP/통합자료_261030")
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
RAW = {"older_single_household_share": "older_single_household_share_raw", "medical_aid1_patients_per_100k": "medical_aid1_patients_per_100k_raw",
       "screening_suspected_diabetes_share": "screening_suspected_diabetes_share_raw", "current_smoking_rate": "current_smoking_rate_raw",
       "ltc_hospitals_per_100k_65": "ltc_hospitals_per_100k_65_raw", "general_hospitals_per_100k": "general_hospitals_per_100k_raw",
       "high_risk_drinking_rate": "high_risk_drinking_rate_raw", "basic_livelihood_rate": "basic_livelihood_rate_raw"}
ALL = pd.read_sql("select tag, year, fbd_region, " + ", ".join(RAW.values()) + " from disease_panel", c); ALL["fbd_region"] = ALL.fbd_region.map(NFC)
out = ALL[ALL.tag == "PERIO"][["year", "fbd_region"]].copy()
for k, col in RAW.items():
    t = "PERIO" if k == "basic_livelihood_rate" else ALL.groupby("tag")[col].apply(lambda s: s.notna().sum()).idxmax()
    v = ALL[ALL.tag == t][["year", "fbd_region", col]].rename(columns={col: k}); out = out.merge(v, on=["year", "fbd_region"], how="left", validate="one_to_one")
    W = ALL[ALL[col].notna()].pivot_table(index=["year", "fbd_region"], columns="tag", values=col); dif = (W.max(1) - W.min(1)).abs()
    print(f"[99c-tbnw] {k}: 태그 {t}, 비결측 {int(out[k].notna().sum())}/3206, 태그 간 최대 차 {dif.max():.3g}")
out = out.sort_values(["fbd_region", "year"]).reset_index(drop=True)
r = out.fbd_region.map(out[out.year.isin([2020, 2024])].groupby("fbd_region").basic_livelihood_rate.mean())
bad = out.year.isin([2021, 2022, 2023]) & ((out.basic_livelihood_rate < 0.2 * r) | (out.basic_livelihood_rate > 5 * r)); assert int(bad.sum()) == 3, int(bad.sum()); print("[99c-tbnw] 수급률 정정 칸(기준 SQLite PERIO = 창원 2021-23만 부풀림, 나머지 30칸은 이미 보간)", sorted(out.loc[bad, "fbd_region"].unique()))
out.loc[bad, "basic_livelihood_rate"] = np.nan; out["basic_livelihood_rate"] = out.groupby("fbd_region").basic_livelihood_rate.transform(lambda s: s.interpolate(limit_area="inside"))
# 외국인 주민(FBD 정본)
C = pd.read_csv(os.path.join(ZD, "01_공변량_229x2011_2024.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str})
K = pd.read_csv(os.path.join(ZD, "00_시군구_229_대응표.csv"), encoding="utf-8-sig", dtype={"sigungu_cd": str}); assert K.sigungu_cd.is_unique and len(K) == 229
K.loc[K.sigungu_cd == "37310", "region"] = "대구시군위군"; K["region"] = K.region.map(NFC)
C = C.drop(columns=["region"]).merge(K[["sigungu_cd", "region"]], on="sigungu_cd", how="left", validate="many_to_one"); assert C.region.notna().all()
fr = "foreign_residents_per_1000_pop" if C["foreign_residents_per_1000_pop"].notna().sum() >= C["foreign_residents_per_1000"].notna().sum() else "foreign_residents_per_1000"
F = pd.DataFrame({"year": C.year, "fbd_region": C.region.map(NFC), "foreign_residents_per1000": C[fr].astype(float)}); F = F[F.year.between(2011, 2024)]
out = out.merge(F, on=["year", "fbd_region"], how="left", validate="one_to_one"); print("[99c-tbnw] 외국인 열", fr, "결측", int(out.foreign_residents_per1000.isna().sum()))
# 세종 2011 등 결측: 지역 안 선형 보간 → 앞뒤 채움(칸 수 기록)
V = [k for k in RAW] + ["foreign_residents_per1000"]
nfill = {}
for k in V:
    n0 = int(out[k].isna().sum()); out[k] = out.groupby("fbd_region")[k].transform(lambda s: s.interpolate(limit_area="inside").bfill().ffill()); nfill[k] = n0
print("[99c-tbnw] 2011-24 결측 채움 칸(보간·앞뒤 채움)", {k: v for k, v in nfill.items() if v})
assert len(out) == 3206 and out.notna().all().all(), out.isna().sum()
# ── 2025 ──
LP = pd.read_csv(os.path.join(PAN, "EXT_canonical_pool_LEPT_261113.csv"), encoding="utf-8-sig"); LP["fbd_region"] = LP.fbd_region.map(NFC)
o25 = out[out.year == 2024].copy(); o25["year"] = 2025; out = pd.concat([out, o25], ignore_index=True)
RYC = {"older_single_household_share": "eloc__DT_1YL12701__독거노인가구비율＜br＞(A÷B×100)", "current_smoking_rate": "eloc__DT_1YL21001E__흡연율",
       "high_risk_drinking_rate": "eloc__DT_1YL20291E__고위험음주율", "foreign_residents_per1000": "eloc__DT_1YL21271__인구천명당외국인수＜br＞(A÷B×1000)",
       "medical_aid1_patients_per_100k": None, "screening_suspected_diabetes_share": None, "ltc_hospitals_per_100k_65": None, "general_hospitals_per_100k": None, "basic_livelihood_rate": None}
rc = {NFC(x): x for x in pd.read_sql("pragma table_info(region_year)", c).name}
rule = []
for k, col in RYC.items():
    m25 = out.year == 2025; n_ry = 0; note = "region_year에 2025 열 없음 → 2024 이월"
    if col is not None and NFC(col) in rc:
        R = pd.read_sql(f'select year, fbd_region, "{rc[NFC(col)]}" as v from region_year where year in (2024, 2025)', c); R["fbd_region"] = R.fbd_region.map(NFC)
        r24 = R[R.year == 2024].set_index("fbd_region").v; p24 = out[out.year == 2024].set_index("fbd_region")[k]
        both = r24.notna() & p24.reindex(r24.index).notna(); agree = float((np.abs(r24[both] - p24.reindex(r24.index)[both]) < 1e-6).mean())
        if agree >= 0.95:
            r25 = R[R.year == 2025].set_index("fbd_region").v; vals = out.loc[m25, "fbd_region"].map(r25)
            n_ry = int(vals.notna().sum()); idx = vals.index[vals.notna()]; out.loc[idx, k] = vals[idx].values
            note = f"2024 일치 {agree:.3f} → region_year 2025 원값 {n_ry}칸, 나머지 {229 - n_ry}칸 2024 이월"
        else: note = f"2024 일치 {agree:.3f}(<0.95, 정의 다름) → 2024 이월"
    rule.append(dict(variable=k, region_year_column=col or "", n_2025_region_year=n_ry, n_2025_locf=229 - n_ry, rule=note)); print("[99c-tbnw] 2025", k, note)
# 80세 이상 비율(2013-25, LEPT 풀 = INFECT_Estd2 + KOSIS 2025-12)
out = out.merge(LP[["year", "fbd_region", "pop80_share"]], on=["year", "fbd_region"], how="left", validate="one_to_one")
rule.append(dict(variable="pop80_share", region_year_column="KOSIS DT_1B04005N 2025-12", n_2025_region_year=229, n_2025_locf=0, rule="2025 KOSIS 실측"))
E = pd.read_csv(os.path.join(PAN, "TBNW_Estd25.csv"), encoding="utf-8-sig"); E["fbd_region"] = E.fbd_region.map(NFC)
out = out[out.year.between(2013, 2025)].merge(E[["year", "fbd_region", "cases"]].rename(columns={"cases": "tbnw_cases"}), on=["year", "fbd_region"], how="left", validate="one_to_one")
assert len(out) == 229 * 13 and out.notna().all().all() and out[out.fbd_region == NFC("세종시세종시")].year.nunique() == 13, out.isna().sum()
for col in V:
    o = out.sort_values(["fbd_region", "year"]); gg = o.groupby("fbd_region")[col]; nb = (gg.shift(1) + gg.shift(-1)) / 2
    b = (nb > 0) & ((o[col] < 0.2 * nb) | (o[col] > 5 * nb)); print(f"[99c-tbnw] 게이트 {col} 무너진 값 의심 칸", int(b.sum()), o.loc[b, ["fbd_region", "year", col]].head(4).values.tolist())
out["foreign_residents_log1p"] = np.log1p(out.foreign_residents_per1000)  # 사전 지정 변환(치우침: 최대 200 이상, 안산·영등포 등)
pd.DataFrame(rule).to_csv(os.path.join(PAN, "EXT_canonical_pool_TBNW_2025rule.csv"), index=False, encoding="utf-8-sig")
out.sort_values(["fbd_region", "year"]).to_csv(os.path.join(PAN, "EXT_canonical_pool_TBNW_261114.csv"), index=False, encoding="utf-8-sig")
print("[99c-tbnw] 저장", out.shape); print(out.drop(columns=["year", "fbd_region"]).describe().T[["mean", "min", "50%", "max"]].round(2).to_string())
lv = out.groupby("fbd_region").mean(numeric_only=True); E2 = E.groupby("fbd_region")[["cases", "E_std"]].sum(); lv["logSIR"] = np.log(E2.cases / E2.E_std)
print("[99c-tbnw] 지역 평균 스피어만 ρ\n", lv.drop(columns=["year", "tbnw_cases"]).corr(method="spearman").round(2).to_string())
