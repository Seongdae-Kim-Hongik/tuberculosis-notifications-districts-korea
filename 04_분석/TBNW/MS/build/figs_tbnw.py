# -*- coding: utf-8 -*-
# figs_tbnw.py — TBNW Thorax 그림(2026-11-14, figs_scrt 이식). 컬러, 패널 문자 = fig.text 상수 PANEL_LABEL_PT(모든 패널 같은 크기·굵기·대문자),
#  방위표 3배(동해 중간), 그림 안 설명문 없음, 결합은 시군구 코드로만. TIFF: 지도 600 dpi, 선화 1200 dpi.
#  Fig 1 (A) 성별 연간 신환자 (B) 성별 연령표준화율 (C) 성·연령별 발생률 · Fig 2 지도 (A) 13년 SIR (B) 잔차 공간 RR (C) 핫·콜드스팟 · Fig 3 4변수 모형별 RR
import os, unicodedata, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch, Polygon, Rectangle
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_tbnw import load, SHP, DESC, OS, SM, GH, DM, P80
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 170 * MM; DPI = 600; LW = 0.3
PANEL_LABEL_PT = 54   # 15 런북 11/10·37호: 48–64 pt, fig.text 상수 하나
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "legend.fontsize": 8, "legend.title_fontsize": 8.5, "axes.linewidth": 0.6, "pdf.fonttype": 42})
NFC = lambda s: unicodedata.normalize("NFC", str(s)).strip()
N = load()
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["region"] = G.region.map(NFC); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")
assert G.region.is_unique and len(G) == 229
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
def label(fig, ax, ch, dx=-0.02, dy=0.01):   # 축 왼쪽 위 바깥, 그림 좌표
    bb = ax.get_position(); fig.text(bb.x0 + dx, bb.y1 + dy, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="bottom", ha="left")
def mapax(ax):
    SIDO.boundary.plot(ax=ax, color="#303030", linewidth=0.5); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    bx, by, bh = x0 + 0.55 * W_, y0 + 0.03 * H_, 0.012 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t in ((0, "0"), (50000, "50"), (100000, "100")): ax.text(bx + k, by + bh + 0.01 * H_, t, ha="center", va="bottom", fontsize=6.5)
    ax.text(bx + 100000 + 0.015 * W_, by + bh / 2, "km", ha="left", va="center", fontsize=6.5)
    nx, ny, nw, nh = x0 + 0.93 * W_, y0 + 0.40 * H_, 0.06 * W_, 0.20 * H_
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=22, fontweight="bold")
def save(fig, k, dpi=DPI):
    p = os.path.join(FIG, f"Thorax_Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi)); im.save(os.path.join(OUTF, f"Figure{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw"); return im.size

# Fig 1 전국 추이·연령
D = pd.read_csv(os.path.join(DESC, "S52D_national.csv")); AR = pd.read_csv(os.path.join(DESC, "S52D_agerate.csv")); yrs = list(range(2013, 2026))
fig = plt.figure(figsize=(W, 4.2)); axs = [fig.add_axes([0.105 + i * 0.33, 0.27, 0.235, 0.45]) for i in range(3)]
SX = (("Men", "Men", "#2166AC", "s"), ("Women", "Women", "#B2182B", "^"))
a = axs[0]; bot = np.zeros(len(yrs))
for s, lab, c, _ in SX:
    v = D[D.sex == s].set_index("year").cases.reindex(yrs).values; a.bar(yrs, v, bottom=bot, color=c, width=0.75, label=lab); bot += v
assert bot.max() < 40000; a.set_ylim(0, 40000); a.set_ylabel("New cases notified, no."); a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=7.5)
a = axs[1]
for s, lab, c, mk in (("Both", "Both sexes", "#000000", "o"),) + SX:
    a.plot(yrs, D[D.sex == s].set_index("year").asr_2020.reindex(yrs), color=c, marker=mk, ms=2.8, lw=1.0, label=lab)
assert D.asr_2020.max() < 120; a.set_ylim(0, 120); a.set_ylabel("Age-standardised rate per 100 000"); a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=7.5)
a = axs[2]; AGES = ["0~9세", "10~19세", "20~29세", "30~39세", "40~49세", "50~59세", "60~69세", "70세 이상"]; AL = ["0–9", "10–19", "20–29", "30–39", "40–49", "50–59", "60–69", "≥ 70"]
x = np.arange(len(AGES)); wd = 0.38
for o, (s, lab, c, _) in zip((-wd / 2, wd / 2), SX):
    v = AR[AR.sex == s].set_index("age").rate_per100k_py.reindex(AGES).values; a.bar(x + o, v, width=wd, color=c, label=lab)
assert AR.rate_per100k_py.max() < 200; a.set_ylim(0, 200); a.set_xticks(x); a.set_xticklabels(AL, rotation=45, ha="right", fontsize=7); a.set_ylabel("Rate per 100 000 person-years")
a.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2, fontsize=7.5)
for a in axs[:2]: a.set_xticks([2013, 2016, 2019, 2022, 2025])
for a in axs: a.spines[["top", "right"]].set_visible(False); a.tick_params(labelsize=8)
for a, ch in zip(axs, "ABC"): label(fig, a, ch, dx=-0.075, dy=0.02)
s1 = save(fig, 1, dpi=1200)

# Fig 2 지도
P = pd.read_csv(os.path.join(os.path.dirname(DESC), "panel_TBNW_std3.csv")); P["sigungu_cd"] = None
S6 = N["s6"].copy(); S6["cd"] = S6.sigungu_cd.astype(str); assert S6.cd.nunique() == 229 and set(S6.cd) == set(G.cd)
d = S6.set_index("cd"); R2C = dict(zip(G.region, G.cd))
sm = P.groupby("fbd_region").agg(c=("cases", "sum"), e=("E", "sum")); sm.index = sm.index.map(NFC).map(R2C); assert sm.index.notna().all() and sm.index.nunique() == 229
d["SMR"] = (sm.c / sm.e).reindex(d.index)
BR = [0, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 999]; LB = ["< 0.70", "0.70–0.79", "0.80–0.89", "0.90–0.99", "1.00–1.09", "1.10–1.24", "1.25–1.49", "≥ 1.50"]
PAL = ["#053061", "#2166AC", "#67A9CF", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
for c in ("SMR", "RR"): assert d[c].min() >= BR[0] and d[c].max() < BR[-1]
fig = plt.figure(figsize=(W, 4.6)); pos = [[0.00, 0.20, 0.33, 0.70], [0.335, 0.20, 0.33, 0.70], [0.67, 0.20, 0.33, 0.70]]
for (col, ch), p in zip((("SMR", "A"), ("RR", "B")), pos[:2]):
    ax = fig.add_axes(p); gg = G.copy(); gg["v"] = gg.cd.map(d[col]); assert gg.v.notna().all()
    gg.plot(ax=ax, column="v", cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#b5b5b5", linewidth=0.2); mapax(ax); label(fig, ax, ch, dx=0.0, dy=-0.005)
fig.legend(handles=[Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)], title="Ratio (A, observed/expected; B, residual spatial)", loc="upper center", bbox_to_anchor=(0.335, 0.20), ncol=4, frameon=False, columnspacing=0.9, handlelength=1.2, fontsize=7)
ax = fig.add_axes(pos[2]); gg = G.copy(); gg["k"] = gg.cd.map(d["class"]); assert gg.k.notna().all()
CK = {"hotspot": "#B2182B", "coldspot": "#2166AC", "neutral": "#EFEFEF"}; gg.plot(ax=ax, color=gg.k.map(CK), edgecolor="#b5b5b5", linewidth=0.2); mapax(ax); label(fig, ax, "C", dx=0.0, dy=-0.005)
fig.legend(handles=[Patch(facecolor=CK[k], edgecolor="#777777", linewidth=LW, label=l) for k, l in (("hotspot", f"Hot spot ({N['n_hot']})"), ("coldspot", f"Cold spot ({N['n_cold']})"), ("neutral", "Neither"))],
           loc="upper center", bbox_to_anchor=(0.835, 0.20), ncol=1, frameon=False, fontsize=7.5, handlelength=1.2)
s2 = save(fig, 2)

# Fig 3 포레스트(4변수 × 모형)
LAB = {OS: "Older adults\nliving alone", SM: "Current smoking", GH: "General hospitals", DM: "Suspected diabetes\nat screening"}
ORD = [OS, SM, GH, DM]
KHS = ("KH_typeI", "KH_typeII", "KH_typeIII", "KH_typeIV"); BK = min(KHS, key=lambda a: N["s43_waic"].get(a, 1e18)); BKL = "Knorr-Held type " + BK.split("type")[1]
SEN = lambda s: (lambda v: N["sens"][s][v][:3] if v in N["sens"][s] else None)
MOD = [("Principal model", lambda v: (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "o", "#000000"),
       (BKL, lambda v: N["s43"][(BK, v)][:3], "D", "#B2182B"),
       ("Spatial+-type", lambda v: N["s41"][("D1_spatial_plus", v)][:3], "v", "#8073AC"),
       ("2015–2025 only", lambda v: N["f15"][v][:3], "s", "#E08214"),
       ("2013–2024 only", SEN("y24"), "s", "#2D004B"),
       ("Without share aged ≥ 80 years", SEN("s2"), "s", "#F4A582"),
       ("Transport-injury deaths as outcome", lambda v: N["nco"][("TRANS", v)][:3], "^", "#2166AC"),
       ("Gastric cancer patients as outcome", lambda v: N["nco"][("GCA", v)][:3], "^", "#4D9221")]
VALS = [t for v in ORD for _, f, _, _ in MOD if (t := f(v)) is not None]; lo_all = min(t[1] for t in VALS); hi_all = max(t[2] for t in VALS)
fig, ax = plt.subplots(figsize=(W, 5.2)); fig.subplots_adjust(left=0.22, right=0.98, top=0.97, bottom=0.27)
off = np.linspace(-0.38, 0.38, len(MOD))
for i, v in enumerate(ORD):
    for (lab, f, mk, fc), o in zip(MOD, off):
        t = f(v)
        if t is None: continue
        e, lo_, hi_ = t; ax.plot([lo_, hi_], [i + o] * 2, color=fc, lw=0.9); ax.plot(e, i + o, marker=mk, mfc=fc, mec=fc, ms=3.8, ls="none")
ax.axvline(1, color="#808080", lw=0.6); ax.set_yticks(range(len(ORD))); ax.set_yticklabels([LAB[v] for v in ORD]); ax.invert_yaxis()
ax.set_xscale("log"); xt = [0.9, 0.95, 1.0, 1.05, 1.1, 1.2, 1.3]; xt = [x for x in xt if x >= lo_all * 0.97 or x == 1.0]; xt = [x for x in xt if x <= hi_all * 1.03 or x <= 1.0]
xt = [max([x for x in [0.85, 0.9, 0.95] if x <= lo_all] or [0.85])] + [x for x in xt if x > max([x for x in [0.85, 0.9, 0.95] if x <= lo_all] or [0.85])]
if xt[-1] < hi_all: xt.append(min(x for x in [1.3, 1.4, 1.5] if x >= hi_all))
assert xt[0] <= lo_all and hi_all <= xt[-1], (lo_all, hi_all, xt)
ax.set_xlim(xt[0], xt[-1]); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}".rstrip("0").rstrip(".") if x != 1 else "1.0" for x in xt]); ax.minorticks_off()
ax.set_xlabel("Rate ratio per 1 standard deviation (95% credible interval, log scale)"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(handles=[Line2D([0], [0], color=fc, marker=m, mfc=fc, mec=fc, lw=0.9, ms=3.8, label=l) for l, _, m, fc in MOD], loc="upper center", bbox_to_anchor=(0.42, -0.13), ncol=2, frameon=False, fontsize=7.5)
s3 = save(fig, 3, dpi=DPI)
for k, s, dp in zip((1, 2, 3), (s1, s2, s3), (1200, DPI, DPI)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/dp*25.4:.0f} x {s[1]/dp*25.4:.0f} mm")
