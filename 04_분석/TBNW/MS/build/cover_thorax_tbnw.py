# cover_thorax_tbnw.py — TBNW Thorax 커버레터(2026-11-14, cover_tmih_scrt.py 이식). Thorax 요구: 학회 발표 여부 + 결과·임상 맥락 진술. 영국식, 1쪽, 단독 저자 비인칭, 김성대 명의. 자료 중복 고지 금지(저자 결정), 제외 심사자는 포털 칸에만. IRB 번호 포함.
#  Zenodo는 공개(open) 게시, 커버레터에는 공개 DOI만. --draft면 DOI 자리표시자 허용.
import os, re, sys, datetime, subprocess
from docx import Document
from docx.shared import Pt, Cm
import content_tbnw as C
from build_thorax_tbnw import TITLE as DTITLE, ZENODO, ADDRESS
from british import brit
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), "out"); DRAFT = "--draft" in sys.argv
N = C.N; W = dict(l.split("=") for l in open(os.path.join(OUT, "wordcount_thorax.txt")).read().split())
if not DRAFT: assert ZENODO.startswith("10.5281/zenodo."), "공개 DOI 없음(투고 전 게이트)"
_d = datetime.date.today(); cl = [f"{_d.day} {_d:%B} {_d.year}", "The Editors", "Thorax", "",
      "Dear Editors,",
      f"Please find enclosed the manuscript entitled \"{DTITLE}\" by Seongdae Kim, for consideration as an Original research article in Thorax. The work has not been presented at a conference.",
      f"Tuberculosis notifications in the Republic of Korea have fallen by more than two-thirds over the past decade, and most new patients are now older adults with reactivation of latent infection. This study covers all {N['cases_total']:,} new cases notified in the {N['n_districts']} districts of the country from 2013 to 2025. "
      "After age and sex standardisation, notifications did not decline evenly: the relative gap between high- and low-notification districts was widest at the end of the period and district rankings persisted. District smoking prevalence was associated with excess notifications in all covariate subsets and space–time models and was not associated with comparison outcomes that share the rural and ageing gradient of Korean districts, whereas the share of older adults living alone marked stable differences between districts mainly in earlier years.",
      "In clinical and public health terms, these findings indicate where the remaining tuberculosis burden of an ageing country with declining incidence is concentrated, and which district markers could inform the planning of case finding and treatment support; the associations describe districts rather than individual risk. "
      "The study used only published aggregate statistics; the Institutional Review Board of Hongik University approved it (7002340-202511-HR-012) and its continuing review (7002340-202611-HR-040). The manuscript has not been published and is not under consideration elsewhere.",
      f"The main text contains {int(W['body_words'])} words, with a structured abstract of {int(W['abstract_words'])} words, key messages, two tables, three figures and {W['refs']} references. Supporting Information and the completed STROBE checklist are provided. The analysis code is openly available on Zenodo (https://doi.org/{ZENODO}).",
      "The author used Claude (Anthropic) and ChatGPT (OpenAI) only for translation and English-language editing of the manuscript, reviewed and edited all output, and takes full responsibility for the content.",
      "Thank you for considering this manuscript.", "", "Yours sincerely,", "",
      "Seongdae Kim, PhD (corresponding author)", ADDRESS, "Email: kimsd@hongik.ac.kr"]
d = Document(); st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(11); st.paragraph_format.space_after = Pt(4); st.paragraph_format.line_spacing = 1.0
for s in d.sections: s.page_width, s.page_height = Cm(21), Cm(29.7); s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(2.54)
gap = False
for t in cl:
    if t == "": gap = True; continue
    p = d.add_paragraph(brit(t))
    if gap: p.paragraph_format.space_before = Pt(10); gap = False
d.core_properties.author = "Seongdae Kim"; d.core_properties.last_modified_by = "Seongdae Kim"; d.core_properties.title = "Cover Letter"; d.core_properties.comments = ""
fp = os.path.join(OUT, "Cover_Letter_Thorax_TBNW.docx"); d.save(fp)
subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "-env:UserInstallation=file:///tmp/lo_tbnw_cl", "--convert-to", "pdf", "--outdir", OUT, fp], capture_output=True)
txt = subprocess.run(["pdftotext", fp.replace(".docx", ".pdf"), "-"], capture_output=True, text=True).stdout
assert not re.search(r"\b(we|our|us|I)\b", txt) and "—" not in txt and re.search(r"7002340-?\s*202611-?\s*HR-040", txt) and not re.search(r"(?i)funding|competing|overlap|previously submitted|token|private link", txt), "문체·IRB·금지 항목"
pages = subprocess.run(["pdfinfo", fp.replace(".docx", ".pdf")], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0]
assert pages == "1", pages; print("cover pages", pages, "draft" if DRAFT else "")
