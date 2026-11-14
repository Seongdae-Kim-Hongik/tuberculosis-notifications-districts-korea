# sanitize_docx.py — python-docx 지문 제거(메모리 docx-ai-trace-audit ⑥⑧⑨⑩, docx-word-black-squares): 생성일 2013-12-23·revision 1, app.xml(AppVersion 14·TotalTime 0·Words 0·Pages 1),
#  customXml/item1.xml·itemProps, docProps/thumbnail.jpeg, 모든 word/*.xml의 keepNext·keepLines·pageBreakBefore. creator·lastModifiedBy = Seongdae Kim(익명 심사 파일 Manuscript·Supporting_Information은 빈 값). 파일마다 수정 시각을 몇 분씩 다르게.
import os, re, sys, zipfile, shutil, subprocess, datetime, random
def sanitize(path, minutes_ago=0, anon=None):
    if anon is None: anon = bool(re.search(r"(Manuscript|Supporting_Information|Supplementary_Material|STROBE|Highlights)", os.path.basename(path)))   # 익명 심사 파일은 저자 메타 비움(06 §5-G ⑥)
    who = "" if anon else "Seongdae Kim"
    pdf = path[:-5] + ".pdf"
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1)) if os.path.exists(pdf) else 1
    from docx import Document
    d = Document(path); _seen = set(); _cells = []; _cp = []
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                if c._tc in _seen: continue
                _seen.add(c._tc); _cells.append(c.text); _cp.extend(p for p in c.paragraphs if p.text.strip())
    text = "\n".join(p.text for p in d.paragraphs) + "\n" + "\n".join(_cells)
    words = len(text.split()); chars = len(text.replace("\n", "")); paras = sum(1 for p in d.paragraphs if p.text.strip()) + len(_cp)   # 표 셀 문단 포함(병합 셀 1회)
    now = datetime.datetime.utcnow() - datetime.timedelta(minutes=minutes_ago)
    created = modified = now.strftime("%Y-%m-%dT%H:%M:%SZ")   # 포바포(11/6): 실제와 다른 작성 이력(난수 시각·편집 시간·수정 횟수) 금지 → 실제 생성 시각, 해당 항목 삭제
    tmp = path + ".tmp"; zin = zipfile.ZipFile(path); zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    drop = {n for n in zin.namelist() if n.startswith("customXml/") or n == "docProps/thumbnail.jpeg"}
    for it in zin.infolist():
        n = it.filename
        if n in drop: continue
        b = zin.read(n)
        if n.endswith(".xml") or n.endswith(".rels"):
            s = b.decode("utf-8")
            if n.startswith("word/") and n.endswith(".xml"):
                s = re.sub(r"<w:keepNext(?:\s+w:val=\"[^\"]*\")?\s*/>|<w:keepLines(?:\s+w:val=\"[^\"]*\")?\s*/>", "", s)
                s = re.sub(r"<w:pageBreakBefore(?:\s+w:val=\"[^\"]*\")?\s*/>", "", s)
            if n == "[Content_Types].xml":
                s = re.sub(r'<Override PartName="/customXml/[^"]*"[^>]*/>', "", s); s = re.sub(r'<Override PartName="/docProps/thumbnail.jpeg"[^>]*/>', "", s)
            if n.endswith(".rels"):
                s = re.sub(r'<Relationship [^>]*Target="[^"]*(customXml/[^"]*|thumbnail\.jpeg)"[^>]*/>', "", s)
            if n == "docProps/core.xml":
                s = re.sub(r"<dcterms:created[^>]*>[^<]*</dcterms:created>", f'<dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>', s)
                s = re.sub(r"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", f'<dcterms:modified xsi:type="dcterms:W3CDTF">{modified}</dcterms:modified>', s)
                s = re.sub(r"<cp:revision>\d+</cp:revision>", "", s)
                s = re.sub(r"<dc:creator>[^<]*</dc:creator>|<dc:creator/>", f"<dc:creator>{who}</dc:creator>", s)
                s = re.sub(r"<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>|<cp:lastModifiedBy/>", f"<cp:lastModifiedBy>{who}</cp:lastModifiedBy>", s)
                s = re.sub(r"<dc:description>[^<]*</dc:description>", "<dc:description></dc:description>", s)
            if n == "docProps/app.xml":
                for tag, val in (("Words", str(words)), ("Characters", str(len(re.sub(r"\s", "", text)))), ("Pages", str(pages)), ("Paragraphs", str(paras)), ("Lines", str(max(pages * 23, paras))), ("CharactersWithSpaces", str(len(text.replace(chr(10), "")) + text.count(chr(10))))):
                    s = re.sub(fr"<{tag}>[^<]*</{tag}>", f"<{tag}>{val}</{tag}>", s) if f"<{tag}>" in s else s.replace("</Properties>", f"<{tag}>{val}</{tag}></Properties>")
            if n == "docProps/app.xml": s = re.sub(r"<TotalTime>[^<]*</TotalTime>", "", s)
            b = s.encode("utf-8")
        zout.writestr(it, b)
    zout.close(); zin.close(); shutil.move(tmp, path)
    return words, pages
if __name__ == "__main__":   # --no-anon: single-blind 저널(EJCP 등)은 Manuscript 파일도 저자 메타 유지
    NOANON = "--no-anon" in sys.argv; fs = [a for a in sys.argv[1:] if not a.startswith("--")]
    for i, f in enumerate(fs): print(f, sanitize(f, minutes_ago=0, anon=False if NOANON else None))   # 포바포 2차: 난수 시각 금지, 실제 생성 시각
