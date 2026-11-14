# booktabs.py — 저장 직전 모든 표를 플레이북 06 §6-B 규격(엄격 3선)으로 통일
#  위선 sz6 + 머리행 아래선 sz4 + 마지막 행 아래선 sz6(셀 수준), 세로줄·행간선·음영·표 스타일 없음,
#  고정 레이아웃, 표 폭 = 그 표가 속한 섹션의 사용 폭(gridCol 비례 확대·축소, tcW는 gridSpan 고려).
#  2026-10-21 SPPE ESM_2가 'Table Grid'(격자선)로 나간 사고 뒤 도입.
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def _border(parent, edge, val, sz):
    e = parent.find(qn(f"w:{edge}"))
    if e is None:
        e = OxmlElement(f"w:{edge}"); parent.append(e)
    e.set(qn("w:val"), val); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")

def _usable_twips(doc):
    """본문 요소 순서대로 각 표가 속한 섹션의 사용 폭(twips)을 돌려준다."""
    body = doc.element.body; out = []; pending = []
    secs = iter(doc.sections); sec = next(secs)
    for el in body.iterchildren():
        if el.tag == qn("w:tbl"):
            pending.append(el)
        elif el.tag == qn("w:p") and el.find(qn("w:pPr")) is not None and el.find(qn("w:pPr")).find(qn("w:sectPr")) is not None:
            w = int((sec.page_width - sec.left_margin - sec.right_margin) / 635)
            out += [(t, w) for t in pending]; pending = []; sec = next(secs, sec)
    last = doc.sections[-1]
    out += [(t, int((last.page_width - last.left_margin - last.right_margin) / 635)) for t in pending]
    return out

def fix(doc):
    n = 0
    for tbl, avail in _usable_twips(doc):
        tblPr = tbl.find(qn("w:tblPr"))
        st = tblPr.find(qn("w:tblStyle"))
        if st is not None: tblPr.remove(st)
        b = tblPr.find(qn("w:tblBorders"))
        if b is None:
            b = OxmlElement("w:tblBorders"); tblPr.append(b)
        for edge, val, sz in (("top", "single", 6), ("left", "nil", 0), ("bottom", "single", 6), ("right", "nil", 0), ("insideH", "nil", 0), ("insideV", "nil", 0)):
            _border(b, edge, val, sz)
        lay = tblPr.find(qn("w:tblLayout"))
        if lay is None:
            lay = OxmlElement("w:tblLayout"); tblPr.append(lay)
        lay.set(qn("w:type"), "fixed")
        # 폭: gridCol 비례 → 섹션 사용 폭
        gcs = tbl.find(qn("w:tblGrid")).findall(qn("w:gridCol"))
        ws = [int(g.get(qn("w:w")) or 0) for g in gcs]
        if sum(ws) <= 0: ws = [1] * len(gcs)
        k = avail / sum(ws); ws = [int(w * k) for w in ws]; ws[0] += avail - sum(ws)
        for g, w in zip(gcs, ws): g.set(qn("w:w"), str(w))
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:w"), str(avail)); tw.set(qn("w:type"), "dxa")
        rows = tbl.findall(qn("w:tr"))
        hdr_idx = [i for i, r in enumerate(rows) if r.find(qn("w:trPr")) is not None and r.find(qn("w:trPr")).find(qn("w:tblHeader")) is not None]
        hlast = hdr_idx[-1] if hdr_idx and hdr_idx == list(range(len(hdr_idx))) else 0
        # 각주 행: 마지막 행이 전 열 병합 단일 셀이고 바로 앞 행이 여러 셀이면 각주 행 → 3선의 아래 선은 그 앞 행 아래, 각주 행엔 선 없음, 표 아래선 없음
        def _ntc(r): return len(r.findall(qn("w:tc")))
        foot = len(rows) >= 3 and _ntc(rows[-1]) == 1 and _ntc(rows[-2]) > 1
        lastdata = len(rows) - 2 if foot else len(rows) - 1
        if foot: _border(b, "bottom", "nil", 0)
        for i, r in enumerate(rows):
            col = 0
            for tc in r.findall(qn("w:tc")):
                tcPr = tc.find(qn("w:tcPr"))
                if tcPr is None:
                    tcPr = OxmlElement("w:tcPr"); tc.insert(0, tcPr)
                span = tcPr.find(qn("w:gridSpan")); sp = int(span.get(qn("w:val"))) if span is not None else 1
                tcw = tcPr.find(qn("w:tcW"))
                if tcw is None:
                    tcw = OxmlElement("w:tcW"); tcPr.insert(0, tcw)
                tcw.set(qn("w:w"), str(sum(ws[col:col + sp]))); tcw.set(qn("w:type"), "dxa"); col += sp
                for s in tcPr.findall(qn("w:shd")): tcPr.remove(s)
                old = tcPr.find(qn("w:tcBorders"))
                if old is not None: tcPr.remove(old)
                cb = OxmlElement("w:tcBorders")
                if i == 0: _border(cb, "top", "single", 6)
                _border(cb, "left", "nil", 0)
                if i == hlast: _border(cb, "bottom", "single", 4)
                elif i == lastdata: _border(cb, "bottom", "single", 6)
                else: _border(cb, "bottom", "nil", 0)
                _border(cb, "right", "nil", 0)
                # tcBorders는 tcW·gridSpan 뒤, shd·vAlign 앞(스키마 순서)
                anchor = next(x for x in (tcPr.find(qn("w:vMerge")), span, tcw) if x is not None)
                anchor.addnext(cb)
        for s in tbl.iter(qn("w:shd")): s.getparent().remove(s)
        n += 1
    return n
