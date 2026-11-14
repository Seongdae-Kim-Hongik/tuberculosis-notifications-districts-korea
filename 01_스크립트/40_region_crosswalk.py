"""시군구 마스터키: FBD 패널(식중독최종.csv, 229 시군구 고정) 기준으로 KCHS 코드·각 원천의 시도/시군구 이름을 잇는다.
- sido_std: 시도 표준명(FBD 표기: 서울시·부산시·…·강원도·전라북도·제주도·세종시)
- key = sido_std + sigungu(공백 제거)
산출: 02_패널/시군구_마스터키.csv, 02_패널/시군구_마스터키_점검.md
"""
import os, re, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "02_패널")
FBD = os.path.expandvars("$ST_DATA_ROOT") + "/기타/R_Studio/FBD_DATA_ZIP/식중독최종.csv"

SIDO_STD = {"서울특별시":"서울시","서울":"서울시","부산광역시":"부산시","부산":"부산시","대구광역시":"대구시","대구":"대구시","인천광역시":"인천시","인천":"인천시",
 "광주광역시":"광주시","광주":"광주시","대전광역시":"대전시","대전":"대전시","울산광역시":"울산시","울산":"울산시","세종특별자치시":"세종시","세종":"세종시",
 "경기도":"경기도","경기":"경기도","강원도":"강원도","강원특별자치도":"강원도","강원":"강원도","충청북도":"충청북도","충북":"충청북도","충청남도":"충청남도","충남":"충청남도",
 "전라북도":"전라북도","전북특별자치도":"전라북도","전북":"전라북도","전라남도":"전라남도","전남":"전라남도","경상북도":"경상북도","경북":"경상북도","경상남도":"경상남도","경남":"경상남도",
 "제주특별자치도":"제주도","제주도":"제주도","제주":"제주도","전남광주통합특별시":"광주시"}
def sido_std(s):
    s = str(s).strip(); return SIDO_STD.get(s, s)
SGG_ALIAS = {"남구@인천시": "미추홀구", "서귀포@제주도": "서귀포시", "제주@제주도": "제주시", "연기군@충청남도": "세종시", "세종특별자치시@세종시": "세종시", "군위군@경상북도": "군위군@대구시"}
def sgg_clean(s, sido=None):
    s = re.sub(r"\s+", "", str(s))
    if sido is not None:
        s = SGG_ALIAS.get(f"{s}@{sido_std(sido)}", s)
        if s == "세종시": return s
    return s
def make_key(sido, sgg):
    sg = sgg_clean(sgg, sido); sd = "세종시" if sg == "세종시" else sido_std(sido)
    if "@" in sg: sg, sd = sg.split("@")   # 경계 변경(군위군 → 대구시, 2024 경계 기준)
    return f"{sd}|{sg}"

if __name__ == "__main__":
    fbd = pd.read_csv(FBD, usecols=["sido", "sigungu", "region"], dtype=str).drop_duplicates()
    fbd["key"] = [make_key(a, b) for a, b in zip(fbd.sido, fbd.sigungu)]
    fbd = fbd.rename(columns={"sido": "fbd_sido", "sigungu": "fbd_sigungu", "region": "fbd_region"})
    k = pd.read_csv(os.path.join(OUT, "KCHS_시군구_연도_wide.csv"), usecols=["year", "sido", "kchs_code", "sigungu"], dtype=str)
    k["key"] = [make_key(a, b) for a, b in zip(k.sido, k.sigungu)]
    kk = k.groupby(["kchs_code", "key"]).agg(kchs_sido=("sido", "last"), kchs_sigungu=("sigungu", "last"), y0=("year", "min"), y1=("year", "max")).reset_index()
    m = fbd.merge(kk, on="key", how="outer", indicator=True)
    lines = ["# 시군구 마스터키 점검", f"- FBD 시군구 {len(fbd)}, KCHS 코드 {kk.kchs_code.nunique()}", f"- 양쪽 일치 {int((m._merge=='both').sum())}",
             "\n## FBD에만 있음(KCHS 이름 불일치 또는 누락)"]
    lines += [f"- {r.key}" for r in m[m._merge == "left_only"].itertuples()]
    lines += ["\n## KCHS에만 있음(폐지·통합 지역 또는 이름 불일치)"]
    lines += [f"- {r.key} code={r.kchs_code} {r.y0}~{r.y1}" for r in m[m._merge == "right_only"].itertuples()]
    dup = m[m._merge == "both"].groupby("key").size(); dup = dup[dup > 1]
    lines += ["\n## 한 key에 KCHS 코드가 둘 이상(코드 변경)"] + [f"- {k_}: {m[m.key==k_].kchs_code.tolist()}" for k_ in dup.index]
    open(os.path.join(OUT, "시군구_마스터키_점검.md"), "w", encoding="utf-8").write("\n".join(lines))
    m.drop(columns="_merge").to_csv(os.path.join(OUT, "시군구_마스터키.csv"), index=False, encoding="utf-8-sig")
    print("\n".join(lines[:4])); print("left_only", (m._merge=="left_only").sum(), "right_only", (m._merge=="right_only").sum())
