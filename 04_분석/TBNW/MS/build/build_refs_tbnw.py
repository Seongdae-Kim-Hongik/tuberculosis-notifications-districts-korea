# build_refs_tbnw.py — TBNW Thorax 참고문헌 메타데이터 캐시(refs_tbnw.json, 2026-11-14, build_refs_scrt.py 이식). 키 = 원고 원천(draft md + content_scrt.py)의 [@key].
#  방법 문헌은 이미 PubMed·Crossref로 검증된 ILLD·SEPS 캐시에서 복사, 주제 문헌은 manifest(ALL_refs.csv, 문헌 에이전트) PMID → PubMed esummary. 네트워크는 이 스크립트에서만.
import os, re, json, time, glob, urllib.request
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); AN = os.path.dirname(os.path.dirname(MS))
src = open(os.path.join(HERE, "content_tbnw.py"), encoding="utf-8").read() + open(os.path.join(MS, "draft", "01_manuscript.md"), encoding="utf-8").read()
src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
keys = sorted({k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")}); keys = [k for k in keys if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k)]
OLD = {}
for f in (os.path.join(AN, "SEPS/MS/build/refs_seps.json"), os.path.join(AN, "ILLD/MS/build/refs_illd.json"), os.path.join(AN, "SKND/MS/build/refs_sknd.json")): OLD.update(json.load(open(f, encoding="utf-8")))
OLD = {k: v for k, v in OLD.items() if k in ("vonelm2007strengthening","inskip1983methods","gelman2014understanding","besag1991bayesian","simpson2017penalising","rue2009approximate","web:rcore2026","moran1950notes","steegen2016increasing","bell2015explaining","dupont2022spatial","vanderweele2017sensitivity","lipsitch2010negative","kang2015korea","web:mois2026population")}
OLD["web:kdca2026tb"] = dict(type="web", authors="Korea Disease Control and Prevention Agency", title="Tuberculosis notifications: new tuberculosis patients by district of residence (2013–2025) and by sex and age group, Korean Statistical Information Service tables 117N_A00108 and 117N_A00102", url="https://kosis.kr", year=2026, accessed="14 November 2026")
OLD["web:mois2026population"] = dict(type="web", authors="Ministry of the Interior and Safety", title="Resident registration population by district, sex and 5-year age group, 2013–2025", url="https://jumin.mois.go.kr", year=2026, accessed="14 November 2026")
OLD["moran1950notes"] = dict(type="journal", authors=["Moran PA"], title="Notes on continuous stochastic phenomena", journal="Biometrika", year=1950, vol="37", issue="1-2", pages="17-23", doi="10.2307/2332142", verified="Crossref 2026-11-13")
M = pd.read_csv(os.path.join(MS, "refs", "manifest", "ALL_refs.csv"), dtype=str).fillna("").set_index("key")
out = {}; pm = [k for k in keys if k not in OLD]
miss = [k for k in pm if k not in M.index or not M.loc[k, "pmid"]]; assert not miss, miss
ids = ",".join(M.loc[k, "pmid"] for k in pm)
d = json.load(urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ids, timeout=60))["result"]
for k in pm:
    r = d[M.loc[k, "pmid"]]
    au = [a["name"] for a in r["authors"] if a.get("authtype", "Author") == "Author"] or [a["name"] for a in r["authors"]]
    doi = next((a["value"] for a in r["articleids"] if a["idtype"] == "doi"), "") or M.loc[k, "doi"]
    out[k] = dict(type="journal", authors=au, title=r["title"].rstrip("."), journal=r["source"].replace(".", ""), year=int(r["pubdate"][:4]), vol=r.get("volume", ""), issue=r.get("issue", ""), pages=r.get("pages", ""), doi=doi, pmid=M.loc[k, "pmid"], verified="PubMed esummary " + time.strftime("%Y-%m-%d"))
for k in keys:
    if k in OLD: out[k] = OLD[k]
def fullp(p):
    m = re.match(r"^(\d+)-(\d+)$", str(p))
    if not m: return p
    a, b = m.groups(); return p if len(b) >= len(a) else f"{a}-{a[:len(a)-len(b)]+b}"
FIXP = {"carauxpaz2021tuberculosis": "5888", "migliori2023the": "2300499"}   # 전자 논문 번호(DOI 접미와 일치 확인, 11/14)   # 전자 논문 번호(Crossref article-number, 11/13)
FIXDOI = {}   # PubMed ArticleIdList에 DOI 없음 → Crossref 확인(11/14)
for k, v in out.items():
    if k in FIXDOI and not v.get("doi"): v["doi"] = FIXDOI[k]
    if k in FIXP: v["pages"] = FIXP[k]
    if v.get("type") == "journal": v["pages"] = fullp(v.get("pages", "")); v["authors"] = [a.title() if a.isupper() else a for a in v["authors"]]
json.dump(out, open(os.path.join(HERE, "refs_tbnw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(keys), "keys;", len(pm), "from PubMed;", [k for k in keys if k not in out])
for k in keys: v = out[k]; print(k, "|", v.get("journal"), v.get("year"), v.get("vol"), v.get("pages"), "|", str(v.get("title"))[:70])
