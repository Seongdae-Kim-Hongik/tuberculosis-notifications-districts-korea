# Notified new tuberculosis across districts of the Republic of Korea, 2013-2025

Analysis code for the manuscript

> Kim S. *As tuberculosis declined in Korea, its district geography concentrated rather than flattened.* Submitted to *Thorax*.

Archived version: Zenodo, https://doi.org/10.5281/zenodo.24220642 (v1.0.0).

## Contents

This repository contains code only. The processed district-year data (analytic panel, expected cases, covariate pool, result tables, adjacency graph and boundary file) are not included; they are available from the author on reasonable request. All source statistics are public (see Data sources).

| Path | What it is |
|---|---|
| `01_스크립트/` | Analysis scripts (below) |
| `04_분석/TBNW/sets_TBNW_std3.json`, `sets_TBNW_s577.json`, `sets_TBNW_s2.json`, `sets_TBNW_sc.json`, `sets_TBNW_y24.json`, `config_TBNW_std3.json`, `run_std3_chain.sh` | District characteristics with expected directions, forced controls, negative controls and model settings (principal model `std3`; sensitivity versions with the queen contiguity graph, without the share aged 80 or older, with crude expected cases and restricted to 2013-2024) |
| `04_분석/TBNW/MS/` | Scripts that read the result tables and write every number, table and figure in the manuscript and supporting information, including `content_tbnw.py`, which generates the Methods and Results text (the draft source of the Introduction and Discussion is not included) |

Folder and some column names are in Korean because the source tables are Korean; each script has a header comment describing its inputs and outputs.

## Data sources

All inputs are public, aggregated statistics. No individual-level data are included.

- Notified new tuberculosis patients by district of residence, 2013-2025, and nationally by sex and 5-year age group: Korea Disease Control and Prevention Agency, Korean Statistical Information Service (KOSIS) tables 117N_A00108 and 117N_A00102 (2026 excluded as incomplete). Table 117N_A00119 (foreign nationals) is national only.
- Population by sex and age group: notification population file and Ministry of the Interior and Safety resident registration statistics (2025 from KOSIS DT_1B04005N, December 2025). The 2023 age block of Changwon duplicated the 2022 block and was corrected.
- Respiratory tuberculosis deaths (A15-A16) by district: cause-of-death statistics, 2013-2024.
- District characteristics (older adults living alone, Medical Aid type 1 patients, suspected diabetes at national health screening, current smoking, foreign residents, long-term care and general hospitals, forced and negative controls): the read-only national district database, KOSIS local indicators, the Korea Community Health Survey and National Health Insurance Service statistics.

## Pipeline

Run from the repository root (set `ST_DATA_ROOT`, `ST_FBDZIP_CORRECTED` and `ST_GPT_DATASET` to the local copies of the public source files and the read-only district database).

| Step | Script | Output |
|---|---|---|
| 1 | `99R_next5e_E.py`, `52E_tbnw_Estd_2025.py`, `52F_tbnw_fetch_foreign.py` | District counts joined by administrative code; expected cases by indirect standardisation (sex by eight age groups), 2013-2025 |
| 2 | `99c_extra_canonical_pool_tbnw.py` | District characteristics with the explicit 2025 rule (observed values first, otherwise carried forward from 2024) |
| 3 | `52D_tbnw_national.py` | National rates by sex and age, age-standardised rates |
| 4 | `80_build_disease_panel_v25.py TBNW` (`ST_VER=std3`) | Analytic panel |
| 5 | `81_fit_inla_z.R TBNW` (`ST_VER=std3`, `ST_GRAPH=04_분석/TBNW/graph_593.graph`, `ST_THREADS=1`; see `04_분석/TBNW/run_std3_chain.sh`, which wraps R jobs in `rslot.sh`) | Principal model, set comparison, all 127 covariate subsets, window models |
| 6 | `52L_tbnw_likelihood.R`, `52P_tbnw_prior_sens.R`, `52T_tbnw_tbd_aux.R`, `52S_tbnw_from2015.R` | Likelihoods, priors, respiratory tuberculosis deaths, 2015-2025 restriction |
| 7 | `85_window_maps.R`, `86_yearly_maps_ehsa_tbnw.py`, `87_window_grid.py` | Maps, yearly smoothed ratios, persistence and emerging hot spot analysis |
| 8 | `88g_sens_prep.py TBNW std3 TRANS,GCA`, `88g_sens_suite.R` (`GROUP=1..6`), `88h_ppc_varpart.R`, `88k_struct_kh_tbnw.R` (nb, struct, kh, review) with `kh_constraints_tbnw.R`, `89g_sens_combine.py` | Sensitivity analyses, comparison outcomes, Knorr-Held models |
| 9 | `04_분석/TBNW/MS/build/` (`build_refs_tbnw.py`, `figs_tbnw.py`, `build_thorax_tbnw.py`, `esm_tbnw.py`, `cover_thorax_tbnw.py`, `check_thorax_tbnw.py`; `run_all_tbnw.sh`) | Manuscript, supporting information, figures and checks |

The boundary file is found at `data/boundary/final.shp` by default; set `ST_SHP` to use another path.

## Software

R 4.6.0 with R-INLA 25.10.19, spdep and sf; Python 3.9 with pandas, geopandas, numpy, scipy, matplotlib and python-docx.

## Licence

MIT (see `LICENSE`).
