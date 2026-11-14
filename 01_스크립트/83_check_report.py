#!/usr/bin/env python3
# 83 — 핵심 보고서 자동 검사(플레이북 §5-1 금칙 스캔 0건, §5-2 요지↔CSV 수치 대조, 페이지 수). 사용: python3 83_check_report.py <TAG> [<YYMMDD>]
#  종료코드 0 = 통과, 1 = 실패(항목 출력)
import sys, os, re, glob, subprocess, json
import pandas as pd
from pypdf import PdfReader
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = os.environ.get("ST_VER", "").strip(); SUF = f"_{VER}" if VER else ""   # 버전 분기
TAG = sys.argv[1]; OUTD = os.path.join(ROOT, "04_분석", TAG); RES = os.path.join(OUTD, "results" + SUF)
pdfs = sorted(glob.glob(os.path.join(OUTD, f"{sys.argv[2] if len(sys.argv)>2 else '*'}_{TAG}_핵심{SUF}.pdf")))
assert pdfs, "핵심 PDF 없음"; PDF = pdfs[-1]
txt = subprocess.run(["/opt/homebrew/bin/pdftotext", "-layout", PDF, "-"], capture_output=True, text=True).stdout
if not txt.strip(): txt = "\n".join(p.extract_text() or "" for p in PdfReader(PDF).pages)
npages = len(PdfReader(PDF).pages)
fails = []
# §5-1 금칙(타 질환·타 시리즈 잔재·미산출 표기)
FORB = r"이질|장티푸스|인천만|진주(?!시)|Jinju|Sacheon|NB000|\[미산출\]|age-standardized|notified|Shigell|Typhoid|Salmonell|Norovir|EHEC|nan \(|NaN|None\)|\{.*?\}"
hits = [(m.group(0), txt[max(0, m.start()-25):m.end()+25].replace("\n", " ")) for m in re.finditer(FORB, txt)]
# "인천" 단독은 지도 지역명(인천시…)에 정당하게 쓰이므로 금칙에서 제외; 위 패턴은 '인천만'만 잡음
if hits: fails.append(f"금칙어 {len(hits)}건: " + "; ".join(f"{h[0]}«{h[1]}»" for h in hits[:8]))
# §5-2 수치 대조
rd = lambda f: pd.read_csv(os.path.join(RES, f), encoding="utf-8-sig")
T = re.sub(r"\s+", " ", txt)
MAIN = rd("S3_main_IRR.csv"); META_KO = dict(zip(MAIN['cov'], MAIN.label_ko)); CMP = pd.read_csv(os.path.join(OUTD, f"HM_setcompare_{TAG}{SUF}.csv"), encoding="utf-8-sig")
BEST = dict(l.split("=", 1) for l in open(os.path.join(OUTD, f"HM_best_{TAG}{SUF}.txt"), encoding="utf-8").read().splitlines() if "=" in l)
for r in MAIN[MAIN.role == "hypothesis"].itertuples():
    s = f"{r.IRR:.3f} ({r.lo:.3f}-{r.hi:.3f})"
    if s not in T: fails.append(f"주모형 IRR 미기재: {r.cov} {s}")
    if r.cred and f"{META_KO[r.cov]} {r.IRR:.3f}" not in T: fails.append(f"credible 변수 요지 미기재: {r.cov}")
w = CMP[CMP.set == BEST["best_set"]].WAIC.iloc[0]
if f"{w:,.1f}" not in T: fails.append(f"최선 세트 WAIC 미기재: {w:,.1f}")
if BEST["best_set"] not in T: fails.append("최선 세트 이름 미기재")
WF = rd("S4_window_fit.csv")
for r in WF.itertuples():
    if f"n={r.n_obs:,}" not in T: fails.append(f"창별 n 미기재: {r.window} {r.n_obs}")
MF = rd("S3_main_fit.csv").iloc[0]
if f"핫스팟 {int(MF.n_hotspot)}" not in T: fails.append("핫스팟 수 미기재")
NEG = rd("S3_negcontrol.csv")
for r in NEG.itertuples():
    if f"{r.IRR:.3f} ({r.lo:.3f}-{r.hi:.3f})" not in T: fails.append(f"음성대조 수치 미기재: {r.cov}")
MV = rd("S7_multiverse_summary.csv")
if f"{int(MV.n_specs_total.iloc[0])}사양" not in T: fails.append("다중우주 사양 수 미기재")
# 요지 길이(docx 문단 기준; PDF 추출은 줄바꿈 공백이 섞임)
from docx import Document
ny = 0
for para in Document(PDF[:-4] + ".docx").paragraphs:
    t = para.text.strip()
    if t.startswith("요지: "):
        ny += 1; y = t[4:].strip()
        if len(y) > 480: fails.append(f"요지 480자 초과({len(y)}): {y[:40]}")
if ny < 8: fails.append(f"요지 문단 수 부족: {ny}")
# 표 안 별표 금지
if re.search(r"\d\*", T): fails.append("숫자 뒤 별표 발견")
print(f"[83] {os.path.basename(PDF)} · {npages} pages · 금칙 {len(hits)}건 · 수치 대조 실패 {len(fails)}건")
for f in fails: print("  ✗", f)
sys.exit(1 if fails else 0)
