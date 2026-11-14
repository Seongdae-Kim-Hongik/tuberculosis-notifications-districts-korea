# -*- coding: utf-8 -*-
# jkms_engine.py — JKMS Original Article docx 엔진 (Style Guide for JKMS Text-202503 + Information for Contributors 27th rev.)
#  규격: Times New Roman 11pt, 더블스페이스, 줄번호(연속), 페이지번호; 순서 = 타이틀페이지 → 초록/키워드 → INTRODUCTION → METHODS → RESULTS → DISCUSSION → REFERENCES → Figure legends → Tables(각 별도 페이지)
#  텍스트 마크업: {{key1,key2}} = 인용(등장순 번호, 위첨자), <i>…</i> 이탤릭, <sup>…</sup> 위첨자, <b>…</b> 볼드. P값은 본문에서 <i>P</i>로 쓸 것.
import re, os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_BREAK
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT="Times New Roman"

class JKMS:
    def __init__(self,cite="sup"):
        self.cite=cite   # "sup"=JKMS 위첨자, "bracket"=Springer [1-3]
        self.doc=Document(); d=self.doc
        st=d.styles["Normal"]; st.font.name=FONT; st.font.size=Pt(12); st.element.rPr.rFonts.set(qn("w:eastAsia"),FONT)
        st.paragraph_format.space_after=Pt(0); st.paragraph_format.line_spacing_rule=WD_LINE_SPACING.DOUBLE
        for s in d.sections:
            s.page_width=Cm(21.0); s.page_height=Cm(29.7); s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
            # 줄번호(연속) + 페이지번호
            sp=s._sectPr; ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
            fp=s.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
            for kind,txt in (("begin",None),("instr","PAGE"),("end",None)):
                r=fp.add_run(); r.font.size=Pt(10); r.font.name=FONT
                if kind=="instr": it=OxmlElement("w:instrText"); it.set(qn("xml:space"),"preserve"); it.text=txt; r._element.append(it)
                else: fc=OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"),kind); r._element.append(fc)
        self.cites=[]; self.refs={}; self.body_words=0; self.counting=False; self.tables=[]; self.legends=[]
    # ── 인용 관리 ──
    def cite_num(self,key):
        if key not in self.cites: self.cites.append(key)
        return self.cites.index(key)+1
    # ── 마크업 파서 → runs ──
    def _emit(self,p,text,sz=12,bold=False,italic=False):
        tok=re.split(r"(\{\{.*?\}\}|<i>|</i>|<sup>|</sup>|<b>|</b>)",text)
        it=italic; sup=False; bo=bold
        for t in tok:
            if t=="" : continue
            if t=="<i>": it=True; continue
            if t=="</i>": it=italic; continue
            if t=="<sup>": sup=True; continue
            if t=="</sup>": sup=False; continue
            if t=="<b>": bo=True; continue
            if t=="</b>": bo=bold; continue
            if t.startswith("{{") and t.endswith("}}") and self.cite=="ay":   # 2026-11-06 EJCP 저자-연도: aylabel(key)->(정렬키, "Kim et al., 2020"), 여러 개는 연도순 "; "
                keys=[k.strip() for k in t[2:-2].split(",") if k.strip()]
                for k in keys: self.cite_num(k)
                labs=sorted((self.aylabel(k) for k in keys), key=lambda x: x[0]); txt="("+"; ".join(l for _, l in labs)+")"
                r=p.add_run(txt); r.font.size=Pt(sz); r.font.name=FONT
                if self.counting: self.body_words+=len(txt.split())
                continue
            if t.startswith("{{") and t.endswith("}}"):
                keys=[k.strip() for k in t[2:-2].split(",") if k.strip()]; nums=sorted({self.cite_num(k) for k in keys})
                # 연속 번호는 범위로(1-3), 나머지 콤마
                parts=[]; i=0
                while i<len(nums):
                    j=i
                    while j+1<len(nums) and nums[j+1]==nums[j]+1: j+=1
                    parts.append(f"{nums[i]}-{nums[j]}" if j-i>=2 else ("," if self.cite=="sup" else ", ").join(str(n) for n in nums[i:j+1])); i=j+1
                if self.cite=="bracket":
                    r=p.add_run("["+", ".join(parts)+"]"); r.font.size=Pt(sz); r.font.name=FONT
                    if self.counting: self.body_words+=1
                    continue
                r=p.add_run(",".join(parts)); r.font.superscript=True; r.font.size=Pt(sz); r.font.name=FONT; continue
            r=p.add_run(t); r.font.size=Pt(sz); r.font.name=FONT; r.bold=bo; r.italic=it; r.font.superscript=sup
            r._element.rPr.rFonts.set(qn("w:eastAsia"),FONT)
            if self.counting and not sup: self.body_words+=len(t.split())
    def para(self,text,sz=12,bold=False,italic=False,align="left",double=True,before=0,after=0,indent=False):
        p=self.doc.add_paragraph(); pf=p.paragraph_format; pf.space_before=Pt(before); pf.space_after=Pt(after)
        if getattr(self,"_pb",False): pf.page_break_before=True; self._pb=False
        pf.line_spacing_rule=WD_LINE_SPACING.DOUBLE if double else WD_LINE_SPACING.SINGLE
        p.alignment={"left":WD_ALIGN_PARAGRAPH.LEFT,"center":WD_ALIGN_PARAGRAPH.CENTER,"justify":WD_ALIGN_PARAGRAPH.JUSTIFY}[align]
        if indent: pf.first_line_indent=Cm(0.75)
        self._emit(p,text,sz,bold,italic); return p
    def head(self,text,level=1):
        # level1 = 대문자 절 제목(INTRODUCTION), level2 = 소제목(볼드), level3 = 이탤릭 소소제목
        c=self.counting; self.counting=False
        if level==1: self.para(text,bold=True,before=12,after=0)
        elif level==2: self.para(text,bold=True,before=6)
        else: self.para(text,italic=True,before=4)
        self.counting=c
    def page_break(self):
        # 빈 문단 + 페이지 나눔은 앞 쪽이 꽉 차면 빈 줄이 다음 쪽으로 밀려 백지 한 쪽이 생긴다(2026-09-15 EHEC 3쪽).
        # → 다음에 오는 문단(제목·표 제목)에 page_break_before를 붙인다.
        self._pb=True
    def new_page(self,orient="portrait"):
        """표 시작 페이지. 방향이 같으면 페이지 나눔, 다르면 새 섹션(줄번호·페이지번호 유지)."""
        cur=self.doc.sections[-1]; cur_or="landscape" if cur.orientation==WD_ORIENT.LANDSCAPE else "portrait"
        if orient==cur_or: self.page_break(); return cur
        s=self.doc.add_section(WD_SECTION.NEW_PAGE)
        if orient=="landscape": s.orientation=WD_ORIENT.LANDSCAPE; s.page_width=Cm(29.7); s.page_height=Cm(21.0)
        else: s.orientation=WD_ORIENT.PORTRAIT; s.page_width=Cm(21.0); s.page_height=Cm(29.7)
        s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
        sp=s._sectPr
        if sp.find(qn("w:lnNumType")) is None:
            ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
        s.footer.is_linked_to_previous=True
        return s
    def landscape_section(self):
        """표용 가로 섹션 시작(줄번호·페이지번호 유지). 이후 표는 24.6cm 폭 사용 가능."""
        s=self.doc.add_section(WD_SECTION.NEW_PAGE)
        s.orientation=WD_ORIENT.LANDSCAPE; s.page_width=Cm(29.7); s.page_height=Cm(21.0)
        s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Cm(2.54)
        sp=s._sectPr; ln=OxmlElement("w:lnNumType"); ln.set(qn("w:countBy"),"1"); ln.set(qn("w:restart"),"continuous"); ln.set(qn("w:distance"),"360"); sp.append(ln)
        s.footer.is_linked_to_previous=True   # 페이지번호는 앞 섹션 푸터 상속(중복 방지)
        return s
    # ── 표 ──
    def table_fit(self,title,header,rows,footnote="",fs_max=11,**k):
        """06 §17: 세로 고정 + 글꼴 티어·최장 토큰 열 폭(tablefit)."""
        import tablefit
        sec=self.doc.sections[-1]; avail=(sec.page_width-sec.left_margin-sec.right_margin)/360000
        fs,ws=tablefit.fit(header,rows,avail=avail,tiers=tuple(t for t in (11,10,9,8.5,8,7.5,7,6.5) if t<=fs_max))
        return self.table(title,header,rows,ws,footnote,fs=fs,**k)
    def table(self,title,header,rows,widths_cm,footnote="",fs=11,center_cols=(),title_bold=True):
        """rows: list of lists; 셀 문자열에 마크업 허용; 행 첫 셀이 '__H__'면 그룹 라벨 행(볼드, 병합)."""
        d=self.doc; tp=self.para(title,bold=title_bold,double=True,before=0,after=6); tp.paragraph_format.keep_with_next=True
        # 현재 섹션 본문 폭을 넘으면 비례 축소(세로 15.0 cm / 가로 23.7 cm (IJRD 여백 30 mm))
        sec=d.sections[-1]; avail=(sec.page_width-sec.left_margin-sec.right_margin)/360000
        if sum(widths_cm)>avail:   # 축소 시 첫 열(라벨) 44% 확보 → 긴 라벨 줄바꿈 최소화, 나머지는 원래 비율
            rest=sum(widths_cm[1:]); first=max(widths_cm[0]*avail/sum(widths_cm),0.44*avail)
            widths_cm=[first]+[w*(avail-first)/rest for w in widths_cm[1:]]
        ncol=len(header); tbl=d.add_table(rows=1,cols=ncol); tbl.alignment=WD_TABLE_ALIGNMENT.CENTER; tbl.autofit=False
        def trflag(row,tag):
            trPr=row._tr.get_or_add_trPr()
            if trPr.find(qn(f"w:{tag}")) is None: trPr.append(OxmlElement(f"w:{tag}"))
        def keepnext(row):
            for c in row.cells:
                for pp in c.paragraphs: pp.paragraph_format.keep_with_next=True
        tblPr=tbl._tbl.tblPr
        # 수직선 없음: 상단/헤더하단/하단 가로선만
        borders=OxmlElement("w:tblBorders")
        for edge,val in (("top","single"),("bottom","single"),("insideH","nil"),("insideV","nil"),("left","nil"),("right","nil")):
            e=OxmlElement(f"w:{edge}"); e.set(qn("w:val"),val); e.set(qn("w:sz"),"6"); e.set(qn("w:space"),"0"); e.set(qn("w:color"),"000000"); borders.append(e)
        tblPr.append(borders)
        # 열 너비는 tcW만으로는 LibreOffice가 무시 → 고정 레이아웃 + 격자(gridCol) 너비 직접 지정
        lay=OxmlElement("w:tblLayout"); lay.set(qn("w:type"),"fixed"); tblPr.append(lay)
        for gc,w in zip(tbl._tbl.tblGrid.findall(qn("w:gridCol")),widths_cm): gc.set(qn("w:w"),str(int(w*567)))
        def cell(c,text,bold=False,align="left",fs=fs):
            # 더블스페이스 = 글자 크기의 정확히 2배(11pt → 22pt). WD_LINE_SPACING.DOUBLE은 글꼴 줄높이×2(TNR 약 25pt)라
            # 표가 휑하고 Table 1이 두 쪽으로 갈라졌다(2026-09-15 저자 피드백). 규정(11pt·double space)은 그대로 충족.
            c.text=""; p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0); p.paragraph_format.space_before=Pt(0)
            p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY; p.paragraph_format.line_spacing=Pt(2*fs)
            p.alignment={"left":WD_ALIGN_PARAGRAPH.LEFT,"center":WD_ALIGN_PARAGRAPH.CENTER}[align]
            cc=self.counting; self.counting=False; self._emit(p,text,fs,bold); self.counting=cc
        hdr=tbl.rows[0]; trflag(hdr,"tblHeader"); trflag(hdr,"cantSplit")   # 다음 페이지로 넘어가면 머리행 반복
        for i,h in enumerate(header): cell(hdr.cells[i],h,bold=True,align="center" if i>0 else "left"); hdr.cells[i].width=Cm(widths_cm[i])
        # 헤더 아래 선
        for c in hdr.cells:
            tcPr=c._tc.get_or_add_tcPr(); b=OxmlElement("w:tcBorders"); e=OxmlElement("w:bottom"); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"6"); e.set(qn("w:color"),"000000"); b.append(e); tcPr.append(b)
        last=None; made=[]
        for row in rows:
            r=tbl.add_row(); trflag(r,"cantSplit"); last=r; made.append((r,bool(row) and row[0]=="__H__"))
            if row and row[0]=="__H__":
                m=r.cells[0].merge(r.cells[ncol-1]); cell(m,row[1],bold=True); continue
            for i,v in enumerate(row):
                cell(r.cells[i],str(v),align="center" if (i in center_cols or (i>0 and "(" in str(v)) or i>0) else "left"); r.cells[i].width=Cm(widths_cm[i])
        # 한 그룹(라벨+행)은 한 덩어리로: 그룹 마지막 행 전까지 keep_with_next → 행 하나만 다음 쪽으로 넘어가는 일 방지
        for k,(r,is_h) in enumerate(made):
            nxt_is_h = k+1<len(made) and made[k+1][1]
            if k+1<len(made) and not nxt_is_h: keepnext(r)
        if footnote:
            if last is not None: keepnext(last)   # 각주가 홀로 다음 페이지로 밀리지 않게
            fp=self.para(footnote,sz=12,double=True,before=4,after=0); fp.paragraph_format.keep_together=True
            fp.paragraph_format.line_spacing_rule=WD_LINE_SPACING.EXACTLY; fp.paragraph_format.line_spacing=Pt(22)   # 표 셀과 같은 22pt
    # ── 저장 ──
    def no_black_squares(self):
        """Word 왼쪽 검은 네모(keepNext·keepLines·pageBreakBefore) 0건(메모리 docx-word-black-squares, 2026-09-20 저자 지시). pageBreakBefore는 문단 앞 쪽 나눔 런으로 바꾼다."""
        body=self.doc.element.body
        for pPr in body.iter(qn("w:pPr")):
            for tag in ("w:keepNext","w:keepLines"):
                for e in pPr.findall(qn(tag)): pPr.remove(e)
            for e in pPr.findall(qn("w:pageBreakBefore")):
                pPr.remove(e); p=pPr.getparent(); r=OxmlElement("w:r"); br=OxmlElement("w:br"); br.set(qn("w:type"),"page"); r.append(br); pPr.addnext(r)
        # U+2011(글꼴에 없어 네모로 보임) → Word 줄바꿈 금지 하이픈 요소 <w:noBreakHyphen/>
        import copy
        for r in list(body.iter(qn("w:r"))):
            t=r.find(qn("w:t"))
            if t is None or t.text is None or "\u2011" not in t.text: continue
            parts=t.text.split("\u2011"); rPr=r.find(qn("w:rPr")); anchor=r
            for i,part in enumerate(parts):
                if i>0:
                    nr=OxmlElement("w:r")
                    if rPr is not None: nr.append(copy.deepcopy(rPr))
                    nr.append(OxmlElement("w:noBreakHyphen")); anchor.addnext(nr); anchor=nr
                if part:
                    nr=OxmlElement("w:r")
                    if rPr is not None: nr.append(copy.deepcopy(rPr))
                    nt=OxmlElement("w:t"); nt.text=part; nt.set("{http://www.w3.org/XML/1998/namespace}space","preserve"); nr.append(nt); anchor.addnext(nr); anchor=nr
            r.getparent().remove(r)
        st=self.doc.styles.element
        for tag in ("w:keepNext","w:keepLines","w:pageBreakBefore"):
            for e in list(st.iter(qn(tag))): e.getparent().remove(e)
    def save(self,path):
        import booktabs, tablefit; tablefit.ind_cells(self.doc); booktabs.fix(self.doc); self.no_black_squares(); self.doc.core_properties.author="Seongdae Kim"; self.doc.core_properties.last_modified_by="Seongdae Kim"; self.doc.core_properties.comments=""; self.doc.core_properties.title=getattr(self,"doc_title",""); self.doc.save(path)

def vancouver(ref):
    """ref dict: authors(list 'Surname AB'), title, journal(abbr), year, vol, issue, pages, doi, url, accessed, type('journal'|'web'|'code')"""
    if ref.get("type")=="web":
        return f"{ref['authors']}. {ref['title']}. {ref['url']}. {('Updated '+ref['updated']+'. ') if ref.get('updated') else ''}Accessed {ref['accessed']}."
    if ref.get("type")=="code":
        return f"{ref['authors']}. {ref['title']}. {ref.get('publisher','')}; {ref['year']}. {ref.get('url','')}"
    a=ref["authors"]; a=", ".join(a[:6])+(", et al" if len(a)>6 else "")
    vol=ref.get("vol",""); iss=f"({ref['issue']})" if ref.get("issue") else ""; pg=f":{ref['pages']}" if ref.get("pages") else ""
    return f"{a}. {ref['title']}. <i>{ref['journal']}</i> {ref['year']};{vol}{iss}{pg}."
