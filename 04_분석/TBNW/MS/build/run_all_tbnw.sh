#!/bin/bash
# run_all_tbnw.sh — TBNW ERJ 빌드(수치 → 참고문헌 → 그림 → 원고 → 보충 → 커버 → 정리 → 검사)
set -e; cd "$(dirname "$0")"
python3 numbers_tbnw.py >/dev/null
python3 build_refs_tbnw.py >/dev/null
python3 figs_tbnw.py
python3 build_thorax_tbnw.py
python3 esm_tbnw.py
python3 cover_thorax_tbnw.py "$@"
python3 sanitize_docx.py --no-anon ../out/Manuscript_ERJ_TBNW.docx ../out/Supporting_Information_ERJ_TBNW.docx ../out/Cover_Letter_ERJ_TBNW.docx ../out/STROBE_Checklist_ERJ_TBNW.docx
for f in Manuscript_ERJ_TBNW Supporting_Information_ERJ_TBNW Cover_Letter_ERJ_TBNW STROBE_Checklist_ERJ_TBNW; do /opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_tbnw --convert-to pdf --outdir ../out ../out/$f.docx >/dev/null 2>&1; done
python3 check_thorax_tbnw.py
