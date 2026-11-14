# tablefit.py — 06 플레이북 §17: 표는 세로 고정, 표마다 글꼴 티어를 낮추고 열 폭은 '최장 미분리 토큰' 실측 폭(PIL, Times New Roman)을 최소로 보장한 뒤 남는 폭을 배분.
import re
from PIL import ImageFont
F = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"; FB = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
CM_PER_PT = 2.54 / 72
def _w(text, pt, bold=False):
    f = ImageFont.truetype(FB if bold else F, size=100)
    return f.getlength(text) / 100 * pt * CM_PER_PT
def _plain(s): return re.sub(r"<[^>]+>", "", str(s))
def fit(header, rows, avail=15.9, tiers=(11, 10, 9, 8.5, 8, 7.5, 7, 6.5), pad=0.65):
    """반환 (fs, widths_cm). need = 최장 토큰 폭×1.08 + pad(셀 여백), pref = 셀 전체 문자열 폭. 첫 열(라벨)은 들여쓰기 0.33 cm 포함."""
    data = [r for r in rows if r and r[0] != "__H__"]
    ncol = len(header)
    for fs in tiers:
        need = []; pref = []
        for j in range(ncol):
            cells = [(_plain(header[j]), True)] + [(_plain(r[j]).strip(), False) for r in data if j < len(r)]
            toks = [(t, b) for c, b in cells for t in c.split() if t]
            n = max(_w(t, fs, b) for t, b in toks) * 1.08 + pad + (0.33 if j == 0 else 0)
            p = max(_w(c, fs, b) for c, b in cells) * 1.02 + pad + (0.33 if j == 0 else 0)
            for c, b in cells:   # 하이픈 든 토큰("(A00-B99)" 등)은 하이픈에서 끊기지 않게 여유를 더 줌
                for t in c.split():
                    if "-" in t.strip("-"): n = max(n, _w(t, fs, b) * 1.12 + pad + 0.1)
            if any(re.search(r"\d-\d", c) for c, b in cells[1:]):   # 숫자 범위 하이픈은 줄바꿈 지점이 되므로 셀 전체를 한 줄에
                n = max(n, max(_w(c, fs, b) for c, b in cells[1:]) * 1.05 + pad)
            need.append(n); pref.append(max(p, n))
        if sum(need) <= avail:
            # 저자 규칙(데이터 행은 한 줄): 남는 폭은 먼저 라벨 열(0)이 한 줄이 되도록, 나머지를 비례 배분
            extra = avail - sum(need); g0 = min(extra, max(0, pref[0] - need[0])); need[0] += g0; extra -= g0
            want = [0] + [p - n for n, p in zip(need[1:], pref[1:])]; tw = sum(want)
            ws = [n + (extra * w / tw if tw > 0 else extra / ncol) for n, w in zip(need, want)]
            ws = [min(w, p) if sum(pref) <= avail else w for w, p in zip(ws, pref)]
            if sum(ws) < avail: ws[0] += avail - sum(ws)
            k = (avail - 0.02) / sum(ws); return fs, [w * k for w in ws]   # 합이 쪽 폭보다 조금 작게(엔진 재배분 방지)
    raise ValueError("표가 6.5pt로도 세로 폭에 안 들어감 — 열 분리 필요(§17-A)")
def ind_cells(doc):
    """하위 행 들여쓰기: 셀 맨 앞 공백 두 칸 → w:ind left 187 twips(06 §6-B)."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    n = 0
    for t in doc.tables:
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    rs = [r for r in p.runs if r.text]
                    if rs and rs[0].text.startswith("  "):
                        rs[0].text = rs[0].text.lstrip(" "); pPr = p._p.get_or_add_pPr()
                        ind = pPr.find(qn("w:ind"))
                        if ind is None: ind = OxmlElement("w:ind"); pPr.append(ind)
                        ind.set(qn("w:left"), "187"); n += 1
    return n
