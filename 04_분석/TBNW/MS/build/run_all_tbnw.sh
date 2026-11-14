#!/bin/bash
# run_all_tbnw.sh — TBNW Thorax 빌드(수치 → 참고문헌 → 그림 → 원고 → 보충 → 커버 → 정리 → 검사)
set -e; cd "$(dirname "$0")"
python3 numbers_tbnw.py >/dev/null
python3 build_refs_tbnw.py >/dev/null
python3 figs_tbnw.py
python3 build_thorax_tbnw.py
python3 esm_tbnw.py
python3 cover_thorax_tbnw.py "$@"
python3 sanitize_docx.py --no-anon ../out/Manuscript_Thorax_TBNW.docx ../out/Supporting_Information_Thorax_TBNW.docx ../out/Cover_Letter_Thorax_TBNW.docx ../out/STROBE_Checklist_Thorax_TBNW.docx
for f in Manuscript_Thorax_TBNW Supporting_Information_Thorax_TBNW Cover_Letter_Thorax_TBNW STROBE_Checklist_Thorax_TBNW; do /opt/homebrew/bin/soffice --headless -env:UserInstallation=file:///tmp/lo_tbnw --convert-to pdf --outdir ../out ../out/$f.docx >/dev/null 2>&1; done
python3 check_thorax_tbnw.py
