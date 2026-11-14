#!/usr/bin/env python3
# 52E — 결핵 신환자 신고(TBNW): 2013–2025 성×8연령 간접표준화 E (2026-11-14). 99R_next5e_E(TBNW 블록)+51E(2025 구성) 결합, 공유 원본 수정 없음.
#  분자: 02_패널/next5e_TBNW_counts_2013_2025.csv(KOSIS 177 DT_117N_A00108 시군구 신환자, C1 코드 결합, 세종 29→29010, 창원·포항 2016-23 구 합).
#  인구 2013–2024: 질병청 age_final 성×8연령 구성 → 기준 SQLite disease_panel(PERIO) population으로 재척도(창원 2023 1,009,038 단언).
#  인구 2025: KOSIS DT_1B04005N 2025-12 성×5세 → 8구간, 시군구 대응 = 51E 값 일치 대응표(LEPT_kosis_crosswalk_2025.csv), 총인구 = 기준 SQLite region_year 2025.
#  율: 전국 신환자 성×5세(DT_117N_A00102, 미상 제외) → 8구간 ÷ 같은 인구 합. 연도별 ΣE = Σcases.
#  산출: 02_패널/TBNW_Estd25.csv, 02_패널/TBNW_national_rates_2013_2025.csv
import os, json, re, sqlite3, unicodedata
import numpy as np, pandas as pd
NFC = lambda s: unicodedata.normalize("NFC", str(s))
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널"); SRC = os.path.join(ROOT, "00_원천")
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
PQ = os.path.expandvars("$ST_DATA_ROOT") + "/G.Downloads/Foodborn Disease 5/질병관리청데이터_v2026/age_final.parquet"
KD = os.path.join(SRC, "D_KOSIS_인구2025")
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
base = pd.read_sql("select year, fbd_region, sigungu_cd, population from disease_panel where tag='PERIO'", con)
base["fbd_region"] = base.fbd_region.map(NFC); base["sigungu_cd"] = base.sigungu_cd.astype(str); assert len(base) == 3206
ry = pd.read_sql("select year, fbd_region, population from region_year where year=2025", con); ry["fbd_region"] = ry.fbd_region.map(NFC)
cd = base.drop_duplicates("fbd_region").set_index("fbd_region").sigungu_cd; assert len(ry) == 229 and set(ry.fbd_region) == set(cd.index) and ry.population.gt(0).all()
ry["sigungu_cd"] = ry.fbd_region.map(cd); base = pd.concat([base, ry[base.columns]], ignore_index=True); base = base[base.year.between(2013, 2025)]
AG = ["0~9세", "10~19세", "20~29세", "30~39세", "40~49세", "50~59세", "60~69세", "70세 이상"]
A = pd.read_parquet(PQ); A = A[A.year.between(2013, 2024)].copy(); A["sigungu_cd"] = A.sigungu_cd.astype(str)
P = A[(A.disease == "수두") & (A.age != "연령미상")].groupby(["year", "sigungu_cd", "sex", "age"], as_index=False).population.first()
assert set(P.age) == set(AG)
CW = pd.read_csv(os.path.join(PAN, "LEPT_kosis_crosswalk_2025.csv"), dtype=str, encoding="utf-8-sig"); assert len(CW) == 229
K = pd.read_csv(os.path.join(KD, "DT_1B04005N_202512.csv"), dtype=str, encoding="utf-8-sig"); K = K[(K.C1.str.len() == 5) & (K.C2 != "0")].copy()
lo = K.C2_NM.str.extract(r"^(\d+)")[0].astype(int); K["age"] = [AG[min(v // 10, 7)] for v in lo]; K["sex"] = K.ITM_ID.map({"T3": "남", "T4": "여"}); K["v"] = pd.to_numeric(K.DT)
K = K[K.sex.notna()].groupby(["C1", "C1_NM", "sex", "age"], as_index=False).v.sum()
P25 = K.merge(CW, left_on=["C1", "C1_NM"], right_on=["kosis_C1", "kosis_C1_NM"])[["sigungu_cd", "sex", "age", "v"]].rename(columns={"v": "population"}); P25["year"] = 2025
assert P25.sigungu_cd.nunique() == 229 and len(P25) == 229 * 16
P = pd.concat([P, P25[P.columns]], ignore_index=True)
r = base.set_index(["year", "sigungu_cd"]).population / P.groupby(["year", "sigungu_cd"]).population.sum()
print("[52E] 기준 인구/구성 인구 비 연도별 중앙", r.groupby(level=0).median().round(4).to_dict())
P = P.merge(r.rename("adj").reset_index(), on=["year", "sigungu_cd"]); P["pop"] = P.population * P.adj
c23 = P[(P.year == 2023) & (P.sigungu_cd == cd[NFC("경상남도창원시")])]["pop"].sum(); assert abs(c23 - 1009038) < 2, c23
# 전국 성×연령 율
N = pd.DataFrame(json.load(open(os.path.join(SRC, "D_KDCA_결핵", "DT_117N_A00102.json"), encoding="utf-8")))
N = N[(N.ITM_NM == "신환자수") & N.C2_NM.isin(["남자", "여자"]) & ~N.C1_NM.isin(["계", "미상"])].copy(); N["DT"] = pd.to_numeric(N.DT, errors="coerce"); N["year"] = N.PRD_DE.astype(int)
N = N[N.year.between(2013, 2025)]
N["age"] = [AG[min(int(re.match(r"(\d+)", a).group(1)) // 10, 7)] for a in N.C1_NM]; N["sex"] = N.C2_NM.map({"남자": "남", "여자": "여"})
Kc = N.groupby(["year", "sex", "age"]).DT.sum().rename("k").reset_index()
NP = P.groupby(["year", "sex", "age"])["pop"].sum().rename("n").reset_index(); R = Kc.merge(NP, on=["year", "sex", "age"]); R["rate"] = R.k / R.n
assert len(R) == 13 * 16; R.to_csv(os.path.join(PAN, "TBNW_national_rates_2013_2025.csv"), index=False, encoding="utf-8-sig")
E = P.merge(R[["year", "sex", "age", "rate"]], on=["year", "sex", "age"]); E["e"] = E["pop"] * E.rate; E = E.groupby(["year", "sigungu_cd"]).e.sum().rename("E_raw")
C = pd.read_csv(os.path.join(PAN, "next5e_TBNW_counts_2013_2025.csv"), dtype={"sigungu_cd": str}).set_index(["year", "sigungu_cd"]).cases
X = base.set_index(["year", "sigungu_cd"]).join(C).join(E).reset_index(); assert X.cases.notna().all() and len(X) == 229 * 13 and (X.E_raw > 0).all()
sc_ = X.groupby("year").cases.sum() / X.groupby("year").E_raw.sum(); X["E_std"] = X.E_raw * X.year.map(sc_)
X["E_crude"] = X.population * X.year.map(X.groupby("year").cases.sum() / X.groupby("year").population.sum())
X = X.rename(columns={"population": "offset"}); assert (X.E_std > 0).all() and not X.duplicated(["year", "fbd_region"]).any()
assert X[X.fbd_region == NFC("세종시세종시")].year.nunique() == 13, "세종 연도 누락"
nat = {int(r_["PRD_DE"]): float(r_["DT"]) for r_ in json.load(open(os.path.join(SRC, "D_KDCA_결핵", "DT_117N_A00108.json"), encoding="utf-8")) if r_["C1"] == "00" and r_["ITM_NM"] == "신환자수"}
yt = X.groupby("year").cases.sum(); assert all(abs(yt[y] - nat[y]) < 0.5 for y in yt.index), "시군구 합 ≠ 전국"
print("[52E] 연도 건수(=전국)", yt.astype(int).to_dict(), "합", int(yt.sum()), "0칸", int((X.cases == 0).sum()))
X[["year", "fbd_region", "sigungu_cd", "offset", "cases", "E_std", "E_crude"]].to_csv(os.path.join(PAN, "TBNW_Estd25.csv"), index=False, encoding="utf-8-sig")
old = pd.read_csv(os.path.join(PAN, "TBNW_Estd3r.csv"), encoding="utf-8-sig"); old["fbd_region"] = old.fbd_region.map(NFC)
mm = old.merge(X, on=["year", "fbd_region"], suffixes=("_o", ""))
print("[52E] 2013-24 선별 E 재현 최대 |ΔE|", round(float((mm.E_std_o - mm.E_std).abs().max()), 6), "Δcases", int((mm.cases_o - mm.cases).abs().sum()), "행", len(mm))
print("[52E] E_std/E_crude", X.eval("E_std/E_crude").describe()[["min", "50%", "max"]].round(3).to_dict())
s = X.groupby("fbd_region")[["cases", "E_std"]].sum(); s["SIR"] = s.cases / s.E_std; print("[52E] 2013-25 SIR P10/P50/P90", s.SIR.quantile([.1, .5, .9]).round(3).tolist())
