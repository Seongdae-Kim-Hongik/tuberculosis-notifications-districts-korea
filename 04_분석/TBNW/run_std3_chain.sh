#!/bin/bash
# TBNW (notified new tuberculosis) principal chain
#  주 E = 성×8연령 간접표준화(52E → 02_패널/TBNW_Estd25.csv E_std). 패널 = 80_v25(2025 행 지원). 비교 결과 TRANS·GCA(2011-24 겹치는 해).
#  민감도 s577·s2·sc(조 E)·y24(2013-2024). 우도 5종 52L, 사전분포 52P.
set -x
S="${ST_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"; cd "$S"; RS="$S/01_스크립트/rslot.sh"
GR="$S/04_분석/TBNW/graph_593.graph"; T=TBNW; D=261114; NW=2; NMV=127
q(){ while [ "$(jobs -rp | wc -l)" -ge 2 ]; do sleep 10; done; }
python3 01_스크립트/99c_extra_canonical_pool_tbnw.py > 04_분석/$T/run_99c.log 2>&1 || exit 1
ST_VER=std3 python3 01_스크립트/80_build_disease_panel_v25.py $T > 04_분석/$T/run_80.log 2>&1 || exit 1
python3 ../논문_마스터자료/00_분석전_데이터게이트/data_gate.py 04_분석/$T/panel_${T}_std3.csv --region fbd_region > 04_분석/$T/data_gate_${T}_std3_$D.txt 2>&1
echo "GATE rc=$?"
[ -n "$GATE_ONLY" ] && exit 0
export ST_VER=std3 ST_THREADS=1 ST_GRAPH="$GR"
(cd 01_스크립트 && ST_MV_STOP=1 $RS Rscript 81_fit_inla_z.R $T) > 04_분석/$T/run_std3_81a.log 2>&1 || exit 1
(cd 01_스크립트 && $RS Rscript 52L_tbnw_likelihood.R) > 04_분석/$T/run_std3_52L.log 2>&1 &
STEP=$(( (NMV + NW - 1) / NW ))
for k in $(seq 0 $((NW-1))); do a=$(( k*STEP+1 )); b=$(( (k+1)*STEP )); [ $b -gt $NMV ] && b=$NMV; (cd 01_스크립트 && ST_MV_RANGE=$a-$b $RS Rscript 81_fit_inla_z.R $T) > 04_분석/$T/run_std3_81_mv_$a.log 2>&1 & sleep 20; done
wait
(cd 01_스크립트 && $RS Rscript 81_fit_inla_z.R $T) > 04_분석/$T/run_std3_81b.log 2>&1 || exit 1
(cd 01_스크립트 && $RS Rscript 52P_tbnw_prior_sens.R) > 04_분석/$T/run_std3_52P.log 2>&1 &
for V in s577 s2 sc y24; do ST_VER=$V python3 01_스크립트/80_build_disease_panel_v25.py $T && (cd 01_스크립트 && ST_VER=$V ST_THREADS=1 ST_MV_N=2 ST_GRAPH=$([ $V = s577 ] || echo "$GR") $RS Rscript 81_fit_inla_z.R $T); done > 04_분석/$T/run_sens3.log 2>&1
wait
python3 01_스크립트/82_core_report.py $T $D > 04_분석/$T/run_std3_82.log 2>&1
python3 01_스크립트/83_check_report.py $T $D >> 04_분석/$T/run_std3_82.log 2>&1
echo "CHAIN done"
python3 01_스크립트/87_window_grid.py $T std3; (cd 01_스크립트 && TAG=$T ST_VER=std3 $RS Rscript 85_window_maps.R $T std3); python3 01_스크립트/86_yearly_maps_ehsa_tbnw.py $T std3
python3 01_스크립트/88g_sens_prep.py $T std3 TRANS,GCA || exit 1
cd 01_스크립트; export TAG=$T NCO=TRANS,GCA
L=../04_분석/$T
for G in 1 2 3 4 5 6; do q; GROUP=$G $RS Rscript 88g_sens_suite.R > $L/run_std3_88g_$G.log 2>&1 & sleep 5; done
q; $RS Rscript 88h_ppc_varpart.R > $L/run_std3_88h.log 2>&1 &
for G in nb struct kh review; do q; $RS Rscript 88k_struct_kh_tbnw.R $G > $L/run_std3_88k_$G.log 2>&1 & sleep 5; done
wait
if grep -q 'KH_typeII FAILED' $L/run_std3_88k_kh.log; then mv $L/results_std3/S43_part_KH_typeII.csv $L/results_std3/S43_part_KH_typeII_failed_init.csv.bak; KH_INIT=0 $RS Rscript 88k_struct_kh_tbnw.R kh > $L/run_std3_88k_kh_init0.log 2>&1; fi
cd ..; TAG=$T ST_VER=std3 python3 01_스크립트/89g_sens_combine.py $T std3 > 04_분석/$T/run_std3_89g.log 2>&1
echo "ALL rc=$?"; grep -l "FAILED" 04_분석/$T/run_std3_88*.log; true
