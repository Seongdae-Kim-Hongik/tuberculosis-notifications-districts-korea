#!/usr/bin/env python3
# 52D — TBNW 전국 기술(2026-11-14, 48D 구조): 연도×성 신환자 수, 조율, 연령표준화율(2020 인구 표준, 8연령), 성×8연령 발생률(2013–2025 합, 10만 인년당).
#  분자 = KOSIS DT_117N_A00102 전국 성×5세 신환자(미상 제외 후 연도·성별 총수로 재척도), 분모 = 52E와 같은 성×8연령 인구(age_final 구성 × 기준 SQLite 총인구, 2025 = KOSIS 2025-12 구성 × region_year).
import os, re, json, runpy, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); R = os.path.join(ROOT, "04_분석", "TBNW", "results_desc"); os.makedirs(R, exist_ok=True)
g = runpy.run_path(os.path.join(HERE, "52E_tbnw_Estd_2025.py")); P = g["P"]; AG = g["AG"]   # 성×8연령 인구(재척도)
POP = P.groupby(["year", "sex", "age"])["pop"].sum()
N = pd.DataFrame(json.load(open(os.path.join(ROOT, "00_원천", "D_KDCA_결핵", "DT_117N_A00102.json"), encoding="utf-8")))
N = N[(N.ITM_NM == "신환자수")].copy(); N["DT"] = pd.to_numeric(N.DT, errors="coerce"); N["year"] = N.PRD_DE.astype(int); N = N[N.year.between(2013, 2025)]
TOT = N[N.C1_NM == "계"].set_index(["year", "C2_NM"]).DT
K = N[~N.C1_NM.isin(["계", "미상"]) & N.C2_NM.isin(["남자", "여자"])].copy()
K["age"] = [AG[min(int(re.match(r"(\d+)", a).group(1)) // 10, 7)] for a in K.C1_NM]; K["sex"] = K.C2_NM.map({"남자": "남", "여자": "여"})
K = K.groupby(["year", "sex", "age"]).DT.sum()
std = POP.loc[2020].groupby("age").sum(); std = std / std.sum(); rows = []
for y in range(2013, 2026):
    for sx, kn in (("남", "남자"), ("여", "여자"), ("계", "계")):
        p = POP.loc[y].groupby("age").sum() if sx == "계" else POP.loc[(y, sx)]
        k = (K.loc[y].groupby("age").sum() if sx == "계" else K.loc[(y, sx)]).reindex(p.index).fillna(0)
        tot = float(TOT.loc[(y, kn)]); rate = k / p * 1e5; asr = float((rate * std.reindex(p.index)).sum()) * tot / k.sum()
        rows.append(dict(year=y, sex={"남": "Men", "여": "Women", "계": "Both"}[sx], cases=int(tot), unknown_age=int(tot - k.sum()), crude=tot / p.sum() * 1e5, asr_2020=asr,
                         pct65=float(100 * k[[a for a in p.index if a in ("60~69세",)]].sum() * 0 + 100 * K.loc[y].groupby("age").sum().get("70세 이상", 0) / K.loc[y].sum()) if sx == "계" else None))
D = pd.DataFrame(rows).drop(columns=["pct65"]); D.to_csv(os.path.join(R, "S52D_national.csv"), index=False, encoding="utf-8-sig")
S5 = N[~N.C1_NM.isin(["계", "미상"]) & (N.C2_NM == "계")].copy(); S5["lo"] = S5.C1_NM.str.extract(r"(\d+)")[0].astype(int)
sh = pd.DataFrame({"pct65": 100 * S5[S5.lo >= 65].groupby("year").DT.sum() / TOT.xs("계", level=1), "pct80": 100 * S5[S5.lo >= 80].groupby("year").DT.sum() / TOT.xs("계", level=1)})
sh.to_csv(os.path.join(R, "S52D_oldshare.csv"), encoding="utf-8-sig")
pp = POP.groupby(["sex", "age"]).sum().rename("py").reset_index(); G = K.groupby(["sex", "age"]).sum().rename("cases").reset_index()
AR = G.merge(pp, on=["sex", "age"]); AR["rate_per100k_py"] = AR.cases / AR.py * 1e5; AR["sex"] = AR.sex.map({"남": "Men", "여": "Women"})
AR.to_csv(os.path.join(R, "S52D_agerate.csv"), index=False, encoding="utf-8-sig")
print(D[D.sex == "Both"].round(2).to_string(index=False)); print(D.groupby("sex").cases.sum()); print(sh.round(1).T); print(AR.round(1).to_string(index=False))
