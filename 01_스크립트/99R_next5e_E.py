#!/usr/bin/env python3
# 99R_next5e — 5차 후보 계수형 분자와 E(2026-11-14; 99R_next5d_kdca_E.py·_cancerscreen_E.py 복제·대상만 교체, 원본 수정 없음).
#  TBNW 결핵 신환자 신고: KOSIS 질병관리청 DT_117N_A00108(시군구 신환자 수, 2013-2025) / 전국 성×5세 DT_117N_A00102.
#    결합: C1(5자리 행정코드) → 기준 SQLite sigungu_cd. 코드로만.
#      - 세종 = 시도 머리행 '29'만 있음 → 29010으로 직접 넣는다.
#      - 일반구(수원시 장안구 31011 등)가 있는 해는 구 합을 쓰고 상위 시 행은 버린다. 창원·포항 2016-23 상위 시 행은 구 합보다 크지만 시도·전국 머리행은 구 합과 같다(검산). 구가 없는 해·시(부천 2016~)는 상위 시 행.
#      - 명시 이관: 23031 남구→23030(미추홀구), 31281 여주군→31280, 34081 당진군→34080, 33015 청원군→33010, 22009 군위군(2023~)→37310, 37051 구미시 선산(2013, 별도 보건소)→37050.
#    E: 성×8연령 간접표준화. 인구 = 질병청 원천 parquet의 성×8연령 구성(기준 SQLite 총인구로 재척도, 99R_next5d 규칙), 율 = 전국 신환자 성×연령(5세→10세 합산, 70+ 합침)/같은 인구.
#    분석 창 2013-2024(공변량 패널 PERIO가 2024까지, parquet 2025 인구 0). 2025는 별도 점검(99R_next5e_tb2025.py).
#  CRE 카바페넴내성장내세균목 감염증 신고: 질병청 parquet(2017~, 2024까지), 99R_next5d 규칙 그대로.
#  LVJD(2018-24, 2016-17은 정의 단절) 간암 검진 양성 판정(추적검사 요망 + 간암의심) / (수검 − 기존 암환자): KOSIS DT_350007N_001(시군구×성, 2016-2024, 상·하반기 합).
#    E = Σ_성 시군구 수검(성) × 전국 양성률(연도·성). 결합은 next5d 대응표 규칙(머리행 제외, 세종 Q1 직접, 일반구→시).
#  산출: 02_패널/<TAG>_Estd3r.csv, 02_패널/next5e_tb_C1_crosswalk.csv, 02_패널/next5e_lvjd_C1_crosswalk.csv
import os, json, sqlite3, unicodedata, re
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); PAN = os.path.join(ROOT, "02_패널"); SRC = os.path.join(ROOT, "00_원천")
DB = os.path.expandvars("$ST_GPT_DATASET") + "/02_체육건강_시공간_GPT버전/02_체육건강_시공간_GPT버전.sqlite"
PQ = os.path.expandvars("$ST_DATA_ROOT") + "/G.Downloads/Foodborn Disease 5/질병관리청데이터_v2026/age_final.parquet"
NFC = lambda s: unicodedata.normalize("NFC", str(s))
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
base = pd.read_sql("select year, fbd_region, sido_std, sigungu, sigungu_cd, population from disease_panel where tag='PERIO'", con)
for c in ("fbd_region", "sido_std", "sigungu"): base[c] = base[c].map(NFC)
base["sigungu_cd"] = base.sigungu_cd.astype(str); S = set(base.sigungu_cd); assert len(S) == 229 and "29010" in S
# ---------- 인구 성×8연령(재척도) ----------
A = pd.read_parquet(PQ); A = A[A.year.between(2011, 2024)].copy(); A["sigungu_cd"] = A.sigungu_cd.astype(str); assert set(A.sigungu_cd) == S
P = A[(A.disease == "수두") & (A.age != "연령미상")].groupby(["year", "sigungu_cd", "sex", "age"], as_index=False).population.first()
tot = P.groupby(["year", "sigungu_cd"]).population.sum().rename("kp"); r = base.set_index(["year", "sigungu_cd"]).join(tot); r = (r.population / r.kp).rename("adj")
P = P.merge(r.reset_index(), on=["year", "sigungu_cd"]); P["pop"] = P.population * P.adj
c23 = P.merge(base, on=["year", "sigungu_cd"]).query("year == 2023 and fbd_region == @NFC('경상남도창원시')")["pop"].sum(); assert abs(c23 - 1009038) < 2, c23
def finish(T, X, lab):
    X = X.copy(); assert X.cases.notna().all() and (X.E_raw > 0).all()
    sc = X.groupby("year").cases.sum() / X.groupby("year").E_raw.sum(); X["E_std"] = X.E_raw * X.year.map(sc)
    X["E_crude"] = X.population * X.year.map(X.groupby("year").cases.sum() / X.groupby("year").population.sum())
    if "offset" not in X: X["offset"] = X.population
    assert not X.duplicated(["year", "fbd_region"]).any() and (X.E_std > 0).all()
    assert X.groupby("year").fbd_region.nunique().min() == 229 and X[X.fbd_region == NFC("세종시세종시")].year.nunique() == X.year.nunique(), "세종·229 누락"
    X[["year", "fbd_region", "offset", "cases", "E_std", "E_crude"]].to_csv(os.path.join(PAN, f"{T}_Estd3r.csv"), index=False, encoding="utf-8-sig")
    yt = X.groupby("year").cases.sum()
    print(f"[99R5e] {T} {lab}: {X.year.min()}-{X.year.max()} 합 {int(X.cases.sum()):,} 연 {yt.min():,.0f}~{yt.max():,.0f} 0칸 {int((X.cases == 0).sum())} 세종 {X[X.fbd_region == NFC('세종시세종시')].year.nunique()}년")
# ---------- TBNW ----------
L = pd.DataFrame(json.load(open(os.path.join(SRC, "D_KDCA_결핵", "DT_117N_A00108.json"), encoding="utf-8")))
L = L[L.ITM_NM == "신환자수"].copy(); L["DT"] = pd.to_numeric(L.DT, errors="coerce"); L["year"] = L.PRD_DE.astype(int); L = L[L.DT.notna()]
EXPL = {"29": "29010", "23031": "23030", "31281": "31280", "34081": "34080", "33015": "33010", "22009": "37310", "37051": "37050"}
rows = []; cxr = []
for y, d in L.groupby("year"):
    have = set(d.C1)
    kidpar = {c[:4] + "0" for c in have if len(c) == 5 and c not in S and c not in EXPL and c[:4] + "0" in S}  # 그해 일반구 행이 있는 상위 시
    for c1, nm, v in d[["C1", "C1_NM", "DT"]].itertuples(index=False):
        if c1 in EXPL: tgt, how = EXPL[c1], "명시 이관"
        elif c1 in kidpar: cxr.append((y, c1, nm, c1, "상위 시 행(일반구 합 사용 → 버림)")); continue
        elif c1 in S: tgt, how = c1, "직접"
        elif len(c1) == 5 and c1[:4] + "0" in S: tgt, how = c1[:4] + "0", "일반구 합산"
        else:
            assert len(c1) <= 2, (y, c1, nm); continue  # 전국·시도 머리행
        rows.append((y, tgt, v)); cxr.append((y, c1, nm, tgt, how))
    # 시도 머리행 = 시도 안 시군구 합(일반구 합 사용) 검산 — 창원·포항 2016-23 상위 시 행은 구 합보다 크지만 시도·전국 합은 구 합과 일치
    for p in kidpar:
        kids = d[(d.C1.str[:4] == p[:4]) & (d.C1 != p) & ~d.C1.isin(S) & ~d.C1.isin(list(EXPL))].DT.sum()
        if p in have: assert kids <= d[d.C1 == p].DT.iat[0], (y, p, kids)
pd.DataFrame(cxr, columns=["year", "C1", "C1_NM", "sigungu_cd", "처리"]).to_csv(os.path.join(PAN, "next5e_tb_C1_crosswalk.csv"), index=False, encoding="utf-8-sig")
TB = pd.DataFrame(rows, columns=["year", "sigungu_cd", "cases"]).groupby(["year", "sigungu_cd"]).cases.sum()
nat = L[L.C1 == "00"].set_index("year").DT; chk = (TB.groupby("year").sum() / nat).dropna()
print("[99R5e] TBNW 시군구 합/전국:", chk.round(4).to_dict()); assert ((chk - 1).abs() < 0.001).all()
assert all(TB.loc[y].index.nunique() == 229 for y in TB.index.get_level_values(0).unique()), "TB 229 아님"
# 2025 시군구 합은 별도 파일(2025 점검용)
TB.reset_index().to_csv(os.path.join(PAN, "next5e_TBNW_counts_2013_2025.csv"), index=False, encoding="utf-8-sig")
N = pd.DataFrame(json.load(open(os.path.join(SRC, "D_KDCA_결핵", "DT_117N_A00102.json"), encoding="utf-8")))
N = N[(N.ITM_NM == "신환자수") & N.C2_NM.isin(["남자", "여자"]) & ~N.C1_NM.isin(["계", "미상"])].copy(); N["DT"] = pd.to_numeric(N.DT, errors="coerce"); N["year"] = N.PRD_DE.astype(int)
def band(a):
    lo = int(re.match(r"(\d+)", a).group(1)); return "70세 이상" if lo >= 70 else f"{lo // 10 * 10}~{lo // 10 * 10 + 9}세"
N["age"] = N.C1_NM.map(band); N["sex"] = N.C2_NM.map({"남자": "남", "여자": "여"})
K = N.groupby(["year", "sex", "age"]).DT.sum().rename("k").reset_index()
NP = P.groupby(["year", "sex", "age"])["pop"].sum().rename("n").reset_index(); R = K.merge(NP, on=["year", "sex", "age"]); R["rate"] = R.k / R.n
assert set(R.age) == set(P.age), (set(R.age), set(P.age))
E = P.merge(R[["year", "sex", "age", "rate"]], on=["year", "sex", "age"]); E["e"] = E["pop"] * E.rate; E = E.groupby(["year", "sigungu_cd"]).e.sum().rename("E_raw")
X = base[base.year.between(2013, 2024)].set_index(["year", "sigungu_cd"]).join(TB).join(E).reset_index()
finish("TBNW", X, "결핵 신환자 신고")
# ---------- CRE ----------
D = A[A.disease == "카바페넴내성장내세균목(CRE) 감염증"]; assert len(D)
cases = D.groupby(["year", "sigungu_cd"]).cases.sum().rename("cases")
K = D[D.age != "연령미상"].groupby(["year", "sex", "age"]).cases.sum().rename("k").reset_index()
NP = P.groupby(["year", "sex", "age"])["pop"].sum().rename("n").reset_index(); R = K.merge(NP, on=["year", "sex", "age"]); R["rate"] = R.k / R.n
E = P.merge(R[["year", "sex", "age", "rate"]], on=["year", "sex", "age"]); E["e"] = E["pop"] * E.rate; E = E.groupby(["year", "sigungu_cd"]).e.sum().rename("E_raw")
y0 = int(D[D.cases > 0].year.min()); X = base[base.year >= y0].set_index(["year", "sigungu_cd"]).join(cases).join(E).reset_index()
print("[99R5e] CRE 연령미상", int(D[D.age == "연령미상"].cases.sum()), "시작", y0)
finish("CRE", X, "CRE 감염증 신고")
# ---------- LVJD ----------
LET = dict(A="서울시", B="부산시", C="대구시", D="인천시", E="광주시", F="대전시", G="울산시", H="경기도", I="강원도", J="충청북도", K="충청남도", L="전라북도", M="전라남도", N="경상북도", O="경상남도", P="제주도", Q="세종시")
REF = base.drop_duplicates("sigungu_cd").set_index(["sido_std", "sigungu"]).sigungu_cd.to_dict()
def code_of(c1, nm):
    if c1.endswith("Q1"): return "29010"
    if len(c1) <= 12: return None
    sido = LET[c1[10]]; n = re.sub(r"\s+", "", nm); m = re.match(r"^(.+?시)(.+구)$", n)
    if m and sido not in ("서울시", "부산시", "대구시", "인천시", "광주시", "대전시", "울산시"): n = m.group(1)
    n = {"청원군": "청주시", "여주군": "여주시", "당진군": "당진시"}.get(n, n)
    if n == "군위군": return REF[("대구시", "군위군")]
    return REF.get((sido, n))
L = pd.read_csv(os.path.join(SRC, "C_NHIS_검진보험", "DT_350007N_001_sgg_long.csv"), dtype=str); L["DT"] = pd.to_numeric(L.DT, errors="coerce"); L["year"] = L.PRD_DE.astype(int)
for c in ("C1_NM", "C2_NM", "C3_NM"): L[c] = L[c].map(lambda v: NFC(v).strip())
cx = L[["C1", "C1_NM"]].drop_duplicates(); cx["sigungu_cd"] = [code_of(a, b) for a, b in zip(cx.C1, cx.C1_NM)]
um = cx[(cx.C1.str.len() > 12) & cx.sigungu_cd.isna()]; assert um.empty, um
cx.to_csv(os.path.join(PAN, "next5e_lvjd_C1_crosswalk.csv"), index=False, encoding="utf-8-sig")
L = L.merge(cx[["C1", "sigungu_cd"]], on="C1"); L = L[L.sigungu_cd.notna() & L.C2_NM.isin(["남자", "여자"])]
POS = ["추적검사 요망(3개월 이내)", "간암의심(정밀검사 요망)"]
num = L[L.C3_NM.isin(POS)].groupby(["year", "sigungu_cd", "C2_NM"]).DT.sum().rename("pos")
den = (L[L.C3_NM == "계"].groupby(["year", "sigungu_cd", "C2_NM"]).DT.sum() - L[L.C3_NM == "기존 암환자"].groupby(["year", "sigungu_cd", "C2_NM"]).DT.sum().reindex(
    L[L.C3_NM == "계"].groupby(["year", "sigungu_cd", "C2_NM"]).DT.sum().index).fillna(0)).rename("den")
Q = pd.concat([num, den], axis=1).fillna({"pos": 0}).reset_index()
nr = Q.groupby(["year", "C2_NM"]).pos.sum() / Q.groupby(["year", "C2_NM"]).den.sum(); Q["e"] = Q.den * Q.set_index(["year", "C2_NM"]).index.map(nr)
G = Q.groupby(["year", "sigungu_cd"]).agg(cases=("pos", "sum"), offset=("den", "sum"), E_raw=("e", "sum"))
Nn = pd.DataFrame(json.load(open(os.path.join(SRC, "C_NHIS_검진보험", "DT_350007N_002_national.json"), encoding="utf-8"))); Nn["DT"] = pd.to_numeric(Nn.DT, errors="coerce")
Nn = Nn[(Nn.C1_NM == "계") & (Nn.C2_NM == "합계")]; nat = Nn[Nn.C3_NM.isin(["추적검사 요망(3개월 이내)", "간암의심(정밀검사 요망)"])].groupby(Nn.PRD_DE.astype(int)).DT.sum()
print("[99R5e] LVJD 시군구 양성 합/전국:", (G.groupby("year").cases.sum() / nat).round(4).to_dict())
X = base[base.year.between(2018, 2024)].set_index(["year", "sigungu_cd"]).join(G).reset_index()  # 2016-17 전국 양성률 63-65% → 2018~ 10%: 판정 정의 단절, 2018-24만
print("[99R5e] LVJD 전국 양성률", (G.groupby("year").cases.sum() / G.groupby("year").offset.sum()).round(4).to_dict())
finish("LVJD", X, "간암 검진 양성 판정(추적+의심)")
