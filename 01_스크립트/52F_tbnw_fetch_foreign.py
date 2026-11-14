#!/usr/bin/env python3
# 52F — TBNW: 외국인 결핵 표(KOSIS 177 DT_117N_A00119) 항목·지역 단위 확인 및 수집(2026-11-14). 키 ~/.kosis_key(내용 출력 금지).
import os, json, urllib.request, urllib.parse
KEY = open(os.path.expanduser("~/.kosis_key")).read().strip()
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "00_원천", "D_KDCA_결핵")
def get(url, q):
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(q), timeout=60) as r: return json.loads(r.read().decode("utf-8"))
T = "DT_117N_A00119"
meta = get("https://kosis.kr/openapi/statisticsData.do", dict(method="getMeta", apiKey=KEY, orgId="177", tblId=T, type="ITM", format="json", jsonVD="Y"))
json.dump(meta, open(os.path.join(OUT, f"{T}_meta_ITM.json"), "w"), ensure_ascii=False, indent=0)
for m in meta[:80]: print(m.get("OBJ_ID"), m.get("OBJ_NM"), m.get("ITM_ID"), m.get("ITM_NM"))
# 지역 분류 없음(ITEM·결핵환자/신환자·결핵종류만) → 전국 표. 시군구 민감도 불가, 전국 외국인 신환자 수만 서술용으로 받는다.
d = get("https://kosis.kr/openapi/Param/statisticsParameterData.do", dict(method="getList", apiKey=KEY, itmId="T001", objL1="B02", objL2="A001", format="json", jsonVD="Y", prdSe="Y", startPrdDe="2013", endPrdDe="2025", orgId="177", tblId=T))
json.dump(d, open(os.path.join(OUT, f"{T}.json"), "w"), ensure_ascii=False, indent=0)
print({r["PRD_DE"]: r["DT"] for r in d} if isinstance(d, list) else d)
