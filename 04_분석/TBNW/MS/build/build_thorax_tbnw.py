# build_thorax_tbnw.py — TBNW Thorax Original research 원고 조립(2026-11-14, build_tmih_scrt.py 이식).
#  Thorax 규정(MS/00_Thorax_투고규정_261114.md): 제목면(제목·저자·소속·교신·ORCID·단어 수) → 구조화 초록 ≤250(Background/Methods/Results/Conclusions) → Key messages 3제목 → Keywords,
#   본문 ≤3,500(서론~고찰), 참고문헌 ≤40(밴쿠버 위첨자), 단일 익명(저자 정보 포함), BMJ 선언문(Contributors·Funding·Competing interests·Patient and public involvement·Ethics approval·Data availability).
#   소속 = 홍익대 단독. AI 고지 = 번역·첨삭만.
import os, re, json, subprocess
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt
import pandas as pd
from jkms_engine import JKMS
from british import brit
import content_tbnw as C
HERE = os.path.dirname(os.path.abspath(__file__)); MS = os.path.dirname(HERE); OUT = os.path.join(MS, "out"); os.makedirs(OUT, exist_ok=True)
N = C.N; REFS = json.load(open(os.path.join(HERE, "refs_tbnw.json"), encoding="utf-8"))
DRAFT = os.path.join(MS, "draft", "01_manuscript.md")
_zf = os.path.join(OUT, "zenodo_doi.txt"); ZENODO = open(_zf).read().strip() if os.path.exists(_zf) else "[ZENODO DOI]"
TITLE = C.TITLE; ORCID = "0000-0002-1525-0091"
AFFIL = "Department of Biohealth Convergence Open Sharing System, Hongik University, Seoul, Republic of Korea"
ADDRESS = "Department of Biohealth Convergence Open Sharing System, Hongik University, 94 Wausan-ro, Mapo-gu, Seoul 04066, Republic of Korea"
AI_STATEMENT = ("The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript. "
                "The author reviewed and edited all output and takes full responsibility for the content of this publication.")
FUNDING = "This study received no specific grant from any funding agency in the public, commercial or not-for-profit sectors."
COI = "None declared."
def data_statement(): return (f"All source data are publicly available aggregate statistics from the Korea Disease Control and Prevention Agency, Statistics Korea (KOSIS), the Ministry of the Interior and Safety, the Korea Community Health Survey and the National Health Insurance Service. "
                             f"The analysis code that generates every number, table and figure is openly available on Zenodo (https://doi.org/{ZENODO}). The processed district-year data are available from the author on reasonable request.")
def read_draft():
    md = open(DRAFT, encoding="utf-8").read(); md = re.sub(r"<!--.*?-->", "", md, flags=re.S); S = {}; cur = None
    for line in md.split("\n"):
        m = re.match(r"^## (.+)$", line)
        if m: cur = m.group(1).strip(); S[cur] = []; continue
        if cur is not None: S[cur].append(line)
    return {k: [p.strip() for p in "\n".join(v).split("\n\n") if p.strip()] for k, v in S.items()}
def pandoc_cites(t): return re.sub(r"\s*\[(@[^\]]+)\]", lambda m: "{{" + ",".join(k.strip().lstrip("@") for k in m.group(1).split(";")) + "}}", t)
def all_keys():
    src = open(os.path.join(HERE, "content_tbnw.py"), encoding="utf-8").read() + open(DRAFT, encoding="utf-8").read()
    src = re.sub(r"<!--.*?-->", "", src, flags=re.S); src = re.sub(r"(?m)^\s*#.*$", "", src)
    return sorted(k for k in {k.strip().lstrip("@") for g in re.findall(r"\[(@[^\]]+)\]", src) for k in g.split(";")} if re.fullmatch(r"(web:)?[a-z][a-z0-9]*", k))
KEYS = all_keys()

def ref(k):   # Vancouver: 저자 6명 이하 전부, 넘으면 6명 + et al. MEDLINE 약어. doi 표기.
    r = REFS[k]
    if r["type"] == "web": return f"{r['authors']}. {r['title']} [Internet]. {r['year']} [cited {r['accessed']}]. Available from: {r['url']}"
    au = r["authors"]; a = ", ".join(au) if len(au) <= 6 else ", ".join(au[:6]) + ", et al"
    t = r["title"].rstrip("."); t = t + ("" if t.endswith(("?", "!")) else ".")
    s = f"{a}. {t} {r['journal']}. {r['year']}"
    if r.get("vol"): s += f";{r['vol']}"
    if r.get("issue"): s += f"({r['issue']})"
    if r.get("pages"): s += f":{r['pages'].replace('-', '–')}"
    s += "."
    if r.get("doi"): s += f" https://doi.org/{r['doi']}"
    elif r.get("pmid"): s += f" Available from: https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
    return s

class TX(JKMS):
    raw = False
    def _emit(self, p, text, sz=12, bold=False, italic=False):
        if not self.raw:
            text = brit(text); text = re.sub(r"(^|[\s(])-(?=\d)", "\\1\u2212", text)
        return super()._emit(p, text, sz, bold, italic)

TAB1_COV = [(C.OS, "Older adults living alone, % of households"), (C.MA, "Medical Aid type 1 patients per 100,000"), (C.DM, "Suspected diabetes at screening, %"), (C.SM, "Current smoking, %"),
            (C.FR, "Foreign residents per 1,000, log(1 + x)"), (C.LTC, "Long-term care hospitals per 100,000 aged ≥ 65 years"), (C.GH, "General hospitals per 100,000"), ("pop80_share", "Population aged ≥ 80 years, %")]
WC = ["W1_2013-15", "W2_2016-19", "W3_2020-25", "ALL"]; WH = ["2013–2015", "2016–2019", "2020–2025", "2013–2025"]
def table1():
    T = N["T1"]; A = N["asr"]
    def mean_asr(a, b): return sum(A[(y, "Both")] for y in range(a, b + 1)) / (b - a + 1)
    rows = [["__H__", "Notifications"], ["  District-years, no."] + [f"{T[c]['n']:,}" for c in WC], ["  New cases notified, no."] + [f"{T[c]['cases']:,}" for c in WC],
            ["  Age-standardised rate per 100,000*"] + [f"{mean_asr(a, b):.1f}" for a, b in ((2013, 2015), (2016, 2019), (2020, 2025), (2013, 2025))],
            ["  District SIR, median (P10–P90)†"] + [f"{T[c]['med']:.2f} ({T[c]['p10']:.2f}–{T[c]['p90']:.2f})" for c in WC], ["__H__", "District characteristics, mean (SD)"]]
    for v, lab in TAB1_COV:
        mx = max(abs(T[c]['cov'][v][0]) for c in WC); dp = 0 if mx >= 100 else (2 if mx < 1 else 1)
        rows.append([f"  {lab}"] + [f"{T[c]['cov'][v][0]:.{dp}f} ({T[c]['cov'][v][1]:.{dp}f})" for c in WC])
    foot = ("P10–P90, 10th–90th percentile; SD, standard deviation; SIR, standardised incidence ratio. *Mean of annual national rates, 2020 resident population as standard. †Observed over sex- and age-standardised expected cases summed over the period. "
            "Characteristics are district-year means. Medical Aid, suspected diabetes, long-term care and general hospitals for 2025 were carried forward from 2024.")
    return (f"Table 1 Notified new tuberculosis and district characteristics, {N['n_districts']} districts, Republic of Korea, 2013–2025", ["Characteristic"] + WH, rows, foot)

GROUPS = [("Reactivation and care-seeking", [C.OS]), ("Deprivation and migration", [C.MA, C.FR]), ("Host susceptibility", [C.DM, C.SM]), ("Congregate care and diagnostic access", [C.LTC, C.GH]),
          ("Forced controls", ["urban_population_share", "physicians_per_1000", "sex_ratio", "fiscal_independence", "pop80_share"])]
LABEL = {C.OS: "Older adults living alone", C.MA: "Medical Aid type 1 patients", C.FR: "Foreign residents", C.DM: "Suspected diabetes at screening", C.SM: "Current smoking",
         C.LTC: "Long-term care hospitals", C.GH: "General hospitals",
         "urban_population_share": "Urban population share", "physicians_per_1000": "Physicians per 1,000", "sex_ratio": "Sex ratio", "fiscal_independence": "Fiscal autonomy", "pop80_share": "Population aged ≥ 80 years"}
def f3(t): return f"{t[0]:.3f} ({t[1]:.3f}–{t[2]:.3f})"
def table2():
    rows = []; assert sum(len(v) for g, v in GROUPS[:-1]) == N["n_hyp"] and set(LABEL) == set(N["main"])
    for g, vs in GROUPS:
        rows.append(["__H__", g])
        for v in vs:
            m = N["main"][v]; mv = N["mv"].get(v); kh = N["s43"].get(("KH_typeII", v)); b = N["bw"].get(v + "__between"); w = N["bw"].get(v + "__within")
            rows.append([f"  {LABEL[v]}", f3((m["IRR"], m["lo"], m["hi"])), f"{round(mv['cred_frac']*mv['n_specs'])}/{mv['n_specs']}" if mv else "Forced", f3(kh) if kh else "–", f3(b) if b else "–", f3(w) if w else "–"])
    foot = (f"CrI, credible interval; RR, rate ratio per 1 standard deviation. All characteristics were expected to raise notifications. Principal model: negative binomial with a Besag–York–Mollié 2 district effect and random-walk and independent year effects, offset by sex- and age-standardised expected cases. "
            f"*Covariate-subset models (all {N['mv_total']} non-empty subsets of the seven characteristics) containing the characteristic in which the CrI excluded 1, over those containing it. †Knorr-Held type II space–time interaction, the best-fitting model. "
            "‡Between-district component = district mean over 2013–2025; within-district component = value minus district mean; entered together; –, not decomposed (decomposition was applied to the four characteristics credible in the principal model).")
    return (f"Table 2 District characteristics and notified new tuberculosis, {N['n_districts']} districts, Republic of Korea, 2013–2025",
            ["Characteristic", "Principal RR (95% CrI)", "Subsets credible, n/N*", "Space–time model RR†", "Between-district RR‡", "Within-district RR‡"], rows, foot)

FIGCAP = {
 1: ("Notified new tuberculosis in the Republic of Korea, 2013–2025. (A) New cases by year and sex. (B) National age-standardised rates (2020 population) by sex. (C) Rates by sex and age group, 2013–2025 combined.",
     "Three panels. Stacked bars show annual new cases falling from about 36,000 in 2013 to about 14,000 in 2025, with more cases in men. Lines show age-standardised rates falling steadily in both sexes. Bars show rates rising steeply with age and highest at 70 years or older."),
 2: ("District geography of notified new tuberculosis, 229 districts, Republic of Korea, 2013–2025. (A) Standardised incidence ratio (observed over sex- and age-standardised expected cases, 13 years pooled). (B) Residual spatial rate ratio from the principal model. (C) Residual hot spots and cold spots (posterior probability of a residual spatial rate ratio above 1 greater than 0.95 or less than 0.05).",
     "Three maps of South Korea. High ratios and hot spots appear in inner-city Seoul and Daegu, eastern Gangwon-do, inland Gyeongsangbuk-do and south-western Jeollanam-do; low ratios and cold spots cover much of Gyeonggi-do and the central provinces."),
 3: ("Rate ratios per 1 standard deviation with 95% credible intervals for four characteristics across models, 229 districts, Republic of Korea: principal model, best-fitting Knorr-Held space–time model, Spatial+-type model (per 1 standard deviation of the residualised characteristic), 2015–2025 only, 2013–2024 only, without the share aged 80 years or older, and transport-injury deaths and gastric cancer patients as comparison outcomes.",
     "Forest plot. Current smoking lies slightly above 1 in every tuberculosis model and near 1 for the comparison outcomes. Older adults living alone lies above 1 in most tuberculosis models but its interval includes 1 in 2015–2025 and for the comparison outcomes. Suspected diabetes loses credibility in the space–time model; general hospitals lie slightly above 1 and below 1 for gastric cancer."),
}
SUPPINFO = ("Appendix S1 Supplementary methods and additional results. Table S1 Source, unit, observed years and expected direction of each district characteristic. "
            "Table S2 Likelihood comparison. Table S3 Rate ratios across alternative specifications. Table S4 Residual hot spots and cold spots. Appendix S2 STROBE checklist.")
def foot_row(J, text, sz=9, ls=13):
    from docx.enum.text import WD_LINE_SPACING
    t = J.doc.tables[-1]; r = t.add_row(); m = r.cells[0].merge(r.cells[-1]); m.text = ""; p = m.paragraphs[0]
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing = Pt(ls); p.paragraph_format.space_before = Pt(4)
    c = J.counting; J.counting = False; J._emit(p, text, sz); J.counting = c
def put_table(J, t, fs=9):
    c = J.counting; J.counting = False; J.table_fit(t[0], t[1], t[2], "", fs_max=fs, title_bold=True); foot_row(J, t[3], 8); J.counting = c

def build(bw=0, aw=0):
    D = read_draft(); J = TX(cite="sup")
    J.para(f"<b>{TITLE}</b>")
    J.para("Seongdae Kim<sup>1</sup>", before=6); J.para(f"<sup>1</sup>{AFFIL}")
    J.para(f"Correspondence to Dr Seongdae Kim, {ADDRESS}; kimsd@hongik.ac.kr. ORCID: {ORCID}", before=6)
    J.para(f"<b>Word count:</b> {bw} words in the main text (Introduction to Discussion); {aw} words in the abstract. <b>Tables:</b> 2. <b>Figures:</b> 3. <b>References:</b> {len(KEYS)}.", before=6)
    J.page_break()
    J.head("Abstract", 1)
    for p in D["Abstract"]:
        m = re.match(r"^(Background|Methods|Results|Conclusions):\s*(.*)$", p, re.S); J.para(f"<b>{m.group(1)}</b> {m.group(2)}")
    J.head("Key messages", 1)
    for p in D["Key messages"]:
        m = re.match(r"^(What is already known on this topic|What this study adds|How this study might affect research, practice or policy):\s*(.*)$", p, re.S)
        J.para(f"<b>{m.group(1)}</b>"); J.para(m.group(2))
    J.para(f"<b>Keywords:</b> {C.KEYWORDS}", before=6)
    J.page_break(); J.counting = True
    J.head("Introduction", 1)
    for p in D["Introduction"]: J.para(pandoc_cites(p), indent=True)
    J.head("Methods", 1)
    for x in C.METHODS:
        J.head(x[0], 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("Patient and public involvement", 2); J.para("Patients or the public were not involved in the design, conduct, reporting or dissemination plans of this research.", indent=True)
    J.head("Results", 1)
    for x in C.RESULTS:
        J.head(x[0], 2)
        for p in x[1:]: J.para(pandoc_cites(p), indent=True)
    J.head("Discussion", 1)
    for p in D["Discussion"]:
        if p.startswith("### "): J.head(p[4:].strip(), 2); continue
        J.para(pandoc_cites(p), indent=True)
    J.counting = False
    J.head("Conclusion", 1)
    for p in D["Conclusion"]: J.para(pandoc_cites(p), indent=True)
    J.head("Contributors", 1); J.para("SK is the sole author and guarantor; he conceived and designed the study, acquired and analysed the data, interpreted the results, wrote and revised the manuscript, approved the final version and is accountable for all aspects of the work.")
    J.head("Funding", 1); J.para(FUNDING)
    J.head("Competing interests", 1); J.para(COI)
    J.head("Patient consent for publication", 1); J.para("Not applicable.")
    J.head("Ethics approval", 1); J.para("The Institutional Review Board of Hongik University approved the study (7002340-202511-HR-012; continuing review 7002340-202611-HR-040) and waived informed consent because only published aggregate statistics were used.")
    J.head("Provenance and peer review", 1); J.para("Not commissioned; externally peer reviewed.")
    J.head("Data availability statement", 1); J.para(data_statement())
    J.head("Use of artificial intelligence", 1); J.para(AI_STATEMENT)
    assert sorted(J.cites) == KEYS, (set(J.cites) ^ set(KEYS))
    J.page_break(); J.head("References", 1); J.raw = True; rl = []
    for i, k in enumerate(J.cites, 1): s = f"{i}. " + ref(k); rl.append(s); J.para(s)
    J.raw = False
    J.head("Supporting Information", 1); J.para(SUPPINFO)
    J.page_break(); J.head("Figure legends", 1)
    for k in sorted(FIGCAP): J.para(f"<b>Figure {k}</b> {FIGCAP[k][0]}"); J.para(f"Alt text: {FIGCAP[k][1]}", after=6)
    J.page_break(); put_table(J, table1())
    J.new_page("landscape"); put_table(J, table2(), fs=8)
    return J, rl, D

def docx_bw(path):   # 본문 단어 수: Introduction ~ Discussion 끝(Conclusion 직전)
    from docx import Document
    t = "\n".join(x.text for x in Document(path).paragraphs)
    i = t.find("\nIntroduction\n"); j = t.find("\nConclusion\n"); assert 0 < i < j; return len(t[i:j].split())
def fix_orphans(path, heads, max_iter=8):
    from docx import Document
    fixed = set()
    for _ in range(max_iter):
        pdf = path.replace(".docx", ".pdf")
        subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_tbnw_thx", "--convert-to", "pdf", "--outdir", os.path.dirname(path), path], check=True, capture_output=True)
        pages = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout.split("\f"); orphan = None
        for pg in pages:
            ls = [re.sub(r"^\d+\s+", "", l.strip()) for l in pg.split("\n") if l.strip()]; ls = [l for l in ls if not re.fullmatch(r"\d+", l)]
            if ls and ls[-1] in heads:
                k = len(ls) - 1
                while k > 0 and ls[k - 1] in heads: k -= 1
                orphan = ls[k]; break
        if orphan is None: return
        if orphan in fixed: print("orphan persists, stop:", orphan); return
        fixed.add(orphan); d = Document(path)
        for p in d.paragraphs:
            if p.text.strip() == orphan:
                np_ = OxmlElement("w:p"); r = OxmlElement("w:r"); br = OxmlElement("w:br"); br.set(qn("w:type"), "page"); r.append(br); np_.append(r); p._p.addprevious(np_); break
        d.save(path); print("orphan fixed:", orphan)

if __name__ == "__main__":
    p = os.path.join(OUT, "Manuscript_Thorax_TBNW.docx"); D = read_draft()
    AB = [re.sub(r"^(Background|Methods|Results|Conclusions):\s*", "", x) for x in D["Abstract"]]; aw = sum(len(x.split()) for x in AB)
    J, rl, D = build(); J.doc_title = "Manuscript"; J.save(p); bw = docx_bw(p)
    J, rl, D = build(bw, aw); J.doc_title = "Manuscript"; J.save(p); assert docx_bw(p) == bw
    heads = {"Provenance and peer review", "Abstract", "Key messages", "Introduction", "Methods", "Results", "Discussion", "Conclusion", "References", "Figure legends", "Contributors", "Funding", "Competing interests", "Patient consent for publication", "Ethics approval", "Data availability statement", "Use of artificial intelligence", "Supporting Information", "Patient and public involvement"} | {x[0] for x in C.METHODS + C.RESULTS}
    fix_orphans(p, heads)
    open(os.path.join(OUT, "wordcount_thorax.txt"), "w").write(f"body_words={bw}\nabstract_words={aw}\nrefs={len(KEYS)}\ntables=2\nfigures=3\nshort_title_chars={len(C.RUNNING)}\n")
    open(os.path.join(OUT, "reference_list.txt"), "w").write("\n".join(rl) + "\n")
    print(f"body {bw} | abstract {aw} | refs {len(KEYS)}")
    assert bw <= 3500 and aw <= 250 and len(KEYS) <= 40, (bw, aw, len(KEYS))
