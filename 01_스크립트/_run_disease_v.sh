#!/bin/zsh
# _v 사본(2026-10-19): 80 만 80_build_disease_panel_v.py(sets json extra_columns 병합)로 교체. 질환 1개 전체 체인: 80 패널 → 81 INLA → 82 핵심 보고서 → 83 검사. 사용: ./_run_disease.sh <TAG> <YYMMDD>
#  환경변수: ST_THREADS(INLA 스레드, 기본 2), ST_MV_N(다중우주 사양 수 덮어쓰기), ST_VER(""=v1, "v2"=세트 v2 분기)
set -u
TAG=$1; DATE=$2
VER="${ST_VER:-}"; SUF=""; [[ -n "$VER" ]] && SUF="_$VER"   # 버전 분기: ST_VER=v2 → results_v2/, run_v2.log, *_v2 산출(80~83 이 같은 환경변수를 읽음)
export ST_VER="$VER"
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(dirname "$HERE"); OUT="$ROOT/04_분석/$TAG"; mkdir -p "$OUT/results$SUF"
LOG="$OUT/run$SUF.log"; export TMPDIR=/tmp
{
echo "===== $(date '+%F %T') START $TAG $DATE ver=${VER:-v1} ====="
T0=$(date +%s)
python3 "$HERE/80_build_disease_panel_v.py" "$TAG" || { echo "FAIL 80"; exit 1; }
echo "----- $(date '+%F %T') 80 done ($(( $(date +%s)-T0 ))s)"
( cd "$HERE" && Rscript 81_fit_inla.R "$TAG" ) || { echo "FAIL 81"; exit 1; }   # 상대 경로 호출: 절대 경로(한글 NFD)로 넘기면 jsonlite가 파일로 인식 못 함
echo "----- $(date '+%F %T') 81 done ($(( $(date +%s)-T0 ))s)"
python3 "$HERE/82_core_report.py" "$TAG" "$DATE" || { echo "FAIL 82"; exit 1; }
echo "----- $(date '+%F %T') 82 done ($(( $(date +%s)-T0 ))s)"
python3 "$HERE/83_check_report.py" "$TAG" "$DATE"; RC=$?
echo "===== $(date '+%F %T') END $TAG rc=$RC total $(( $(date +%s)-T0 ))s ====="
exit $RC
} 2>&1 | tee -a "$LOG"
