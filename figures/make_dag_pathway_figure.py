#!/usr/bin/env python3
"""
The reviewed DAG in the layered format used at the expert-review workshop
(DAG_Review_Workshop.pptx, slide 7): seven domain columns left to right,
constructs as labelled boxes coloured by causal role.

Panel A  The whole graph, 25 constructs and 89 directed edges, with the two
         channels carrying the entire HEE -> MH effect highlighted.
Panel B  Those two channels in isolation, with the minimal adjustment set
         blocking the backdoor and each mediator's measurement status marked.

Node/edge source of truth: ../causal_discovery_validation/expert_dag.py, which
transcribes rawEdges from ../index.html verbatim. Column membership is
ed.LAYERS; column headings are the workshop deck's.

Outputs: dag_full_pathways.{png,pdf}
Run:  python3 make_dag_pathway_figure.py
"""
from __future__ import annotations
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "causal_discovery_validation"))
import expert_dag as ed

# --------------------------------------------------------------------------- #
# Palette -- workshop deck
# --------------------------------------------------------------------------- #
C_EXPOSURE   = "#C08A45"   # HEE
C_OUTCOME    = "#123037"   # MH
C_CONFOUND   = "#2F6C93"   # structural confounder
C_ENVMED     = "#4E9C80"   # environmental mediator
C_SOCMED     = "#5B7392"   # social / structural mediator
C_HEALTHMED  = "#4E9C80"   # health mediator
C_LATENT     = "#A9AFB4"   # latent, unobserved

C_BG         = "#CFD6DB"   # unhighlighted edges
C_AFFORD     = "#C0781F"   # pathway 1, via Fuel Poverty
C_INDOOR     = "#0F6E6E"   # pathway 2, via IEQ
C_ADJ        = "#7B3FA0"
C_TXT        = "#1E2429"
C_MUTE       = "#6C7780"

ROLE = {
    "U_AH": C_LATENT, "N": C_LATENT,
    "U": C_CONFOUND, "C": C_CONFOUND, "D": C_CONFOUND, "ED": C_CONFOUND,
    "EC": C_CONFOUND, "H": C_CONFOUND, "T": C_CONFOUND, "NS": C_CONFOUND,
    "P": C_SOCMED, "SC": C_SOCMED, "DC": C_SOCMED, "FP": C_SOCMED,
    "A": C_SOCMED, "SI": C_SOCMED,
    "O": C_ENVMED, "IEQ": C_ENVMED, "NO": C_ENVMED, "AP": C_ENVMED,
    "GS": C_ENVMED, "SA": C_HEALTHMED, "PH": C_HEALTHMED,
    "HEE": C_EXPOSURE, "MH": C_OUTCOME,
}

# Display labels, wrapped to fit the box
LABEL = {
    "U_AH": "Area\nHistory", "U": "Urbanicity", "C": "Climate",
    "D": "Demo-\ngraphics", "ED": "Education", "EC": "Economic\nCapital",
    "N": "Neigh-\nbourhood", "P": "Policy\nAccess",
    "H": "Housing\nChars.", "HEE": "HEE", "T": "Tenure",
    "O": "Over-\ncrowding", "NS": "Neigh.\nStress",
    "SC": "Social\nCapital", "DC": "Digital\nCapital",
    "SA": "Substance\nAbuse", "FP": "Fuel\nPoverty",
    "IEQ": "IEQ", "NO": "Noise", "AP": "Air\nPollution",
    "GS": "Green\nSpace", "A": "Access-\nibility", "SI": "Isolation",
    "PH": "Physical\nHealth", "MH": "Mental\nHealth",
}

# Seven domain columns; order within a column is chosen to reduce crossings.
COLUMNS = [
    ("Historical &\nclimatic",   ["U_AH", "U", "C"]),
    ("Socio-\neconomic",         ["D", "ED", "EC"]),
    ("Spatial &\npolicy",        ["N", "P"]),
    ("Dwelling &\nstressors",    ["H", "HEE", "T", "O", "NS"]),
    ("Social &\nfuel",           ["SC", "DC", "SA", "FP"]),
    ("Proximal\nexposures",      ["IEQ", "NO", "AP", "GS", "A", "SI"]),
    ("Health\noutcomes",         ["PH", "MH"]),
]

COL_X = 2.02          # column pitch
ROW_Y = 0.72          # row pitch within a column
BW, BH = 1.44, 0.50   # box width / height
Y_MID = 0.0

ADJ = set(ed.ADJ_SET)

# The two channels carrying the whole HEE -> MH effect.
PATH_AFFORD = [("HEE", "FP"), ("FP", "MH"), ("FP", "PH"), ("PH", "MH"),
               ("FP", "IEQ")]
PATH_INDOOR = [("HEE", "IEQ"), ("IEQ", "MH"), ("IEQ", "PH")]
PATH_EDGES = {e: C_AFFORD for e in PATH_AFFORD}
PATH_EDGES.update({e: C_INDOOR for e in PATH_INDOOR})


def build_positions():
    pos, col_of = {}, {}
    for ci, (_, members) in enumerate(COLUMNS):
        x = ci * COL_X
        n = len(members)
        top = Y_MID + (n - 1) * ROW_Y / 2.0
        for ri, node in enumerate(members):
            pos[node] = (x, top - ri * ROW_Y)
            col_of[node] = ci
    return pos, col_of


POS, COL_OF = build_positions()


def draw_box(ax, node, patches, scale=1.0):
    x, y = POS[node]
    fc = ROLE[node]
    w, h = BW * scale, BH * scale
    box = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                         boxstyle="round,pad=0.008,rounding_size=0.075",
                         facecolor=fc, edgecolor="white" if node == "MH" else fc,
                         lw=1.1 if node == "MH" else 0.6, zorder=5)
    ax.add_patch(box)
    patches[node] = box
    lab = LABEL[node]
    ax.text(x, y, lab, ha="center", va="center", zorder=6,
            fontsize=(6.9 if "\n" in lab else 7.6) * scale,
            fontweight="bold" if node in ("HEE", "MH") else "normal",
            color="white", linespacing=1.12)


def draw_edge(ax, a, b, colour, patches, lw=0.7, z=2, alpha=1.0):
    """Arc from a to b, clipped at each box boundary. Curvature falls with span
    so long edges bow clear of intervening columns."""
    span = abs(COL_OF[b] - COL_OF[a])
    rad = 0.10 if span <= 1 else 0.16 if span <= 3 else 0.22
    if POS[b][1] < POS[a][1]:
        rad = -rad
    ax.add_patch(FancyArrowPatch(
        POS[a], POS[b], arrowstyle="-|>", mutation_scale=6.5,
        connectionstyle=f"arc3,rad={rad}", color=colour, lw=lw,
        patchA=patches[a], patchB=patches[b], shrinkA=0.6, shrinkB=0.6,
        zorder=z, alpha=alpha))


# --------------------------------------------------------------------------- #
# Panel A -- the whole graph
# --------------------------------------------------------------------------- #
def panel_full(ax):
    ax.set_aspect("equal"); ax.axis("off")
    xs = [POS[n][0] for n in POS]; ys = [POS[n][1] for n in POS]
    ax.set_xlim(min(xs) - BW, max(xs) + BW * 0.85)
    ax.set_ylim(min(ys) - 0.30, max(ys) + 1.02)

    # column headings
    head_y = max(ys) + 0.72
    for ci, (title, _) in enumerate(COLUMNS):
        ax.text(ci * COL_X, head_y, title, ha="center", va="center",
                fontsize=6.6, color=C_MUTE, linespacing=1.3)

    patches = {}
    for node in POS:
        draw_box(ax, node, patches)

    for a, b in ed.RAW_EDGES:
        if (a, b) in PATH_EDGES:
            continue
        draw_edge(ax, a, b, C_BG, patches, lw=0.65, z=2, alpha=0.9)
    for (a, b), col in PATH_EDGES.items():
        draw_edge(ax, a, b, col, patches, lw=2.0, z=4)


def legend_block(ax):
    """Role key, the two highlighted pathways, and the adjustment set.
    Labels only; the reading is in the caption and the text."""
    ax.axis("off")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.add_patch(FancyBboxPatch((0.02, 0.30), 0.96, 0.68,
                                boxstyle="round,pad=0.012,rounding_size=0.03",
                                facecolor="white", edgecolor="#D5DBDF",
                                lw=1.0, transform=ax.transAxes, zorder=1))
    rows = [
        (C_EXPOSURE,  "Exposure (HEE)"),
        (C_OUTCOME,   "Outcome (MH)"),
        (C_CONFOUND,  "Structural confounder"),
        (C_ENVMED,    "Environmental mediator"),
        (C_SOCMED,    "Social / structural mediator"),
        (C_LATENT,    "Latent (unobserved)"),
    ]
    for i, (col, lab) in enumerate(rows):
        y = 0.925 - i * 0.070
        ax.add_patch(FancyBboxPatch((0.075, y - 0.020), 0.050, 0.040,
                                    boxstyle="round,pad=0.004,rounding_size=0.012",
                                    facecolor=col, edgecolor=col,
                                    transform=ax.transAxes, zorder=3))
        ax.text(0.150, y, lab, fontsize=7.6, color=C_TXT, va="center")

    ax.plot([0.075, 0.925], [0.470, 0.470], color="#E1E6E9", lw=0.9,
            transform=ax.transAxes)

    for y, col, lab in ((0.405, C_AFFORD, "Pathway 1: HEE $\\rightarrow$ Fuel Poverty $\\rightarrow$ MH"),
                        (0.335, C_INDOOR, "Pathway 2: HEE $\\rightarrow$ IEQ $\\rightarrow$ MH")):
        ax.plot([0.075, 0.132], [y, y], color=col, lw=2.4,
                transform=ax.transAxes, solid_capstyle="round")
        ax.text(0.150, y, lab, fontsize=7.4, color=col, va="center")



# --------------------------------------------------------------------------- #
# Panel B -- the two pathways isolated
# --------------------------------------------------------------------------- #
ZPOS = {
    "ADJ": (1.35, 1.45), "HEE": (4.50, 1.45),
    "FP": (7.30, 2.58), "IEQ": (7.30, 0.32), "MH": (10.20, 1.45),
}
ZLAB = {"HEE": "HEE", "FP": "Fuel\nPoverty", "IEQ": "IEQ", "MH": "Mental\nHealth"}


def panel_zoom(ax):
    ax.set_title("(b)  The two pathways", fontsize=10.4,
                 fontweight="bold", color=C_TXT, pad=6, loc="left")
    ax.set_xlim(-0.75, 12.55); ax.set_ylim(-0.25, 3.45)
    ax.set_aspect("equal"); ax.axis("off")

    patches = {}
    w, h = 1.42, 0.94
    for n, (x, y) in ZPOS.items():
        if n == "ADJ":
            b = FancyBboxPatch((x - 1.50, y - 0.62), 3.00, 1.24,
                               boxstyle="round,pad=0.02,rounding_size=0.14",
                               facecolor="#F3EDF9", edgecolor=C_ADJ, lw=1.7,
                               zorder=5)
            ax.add_patch(b); patches[n] = b
            ax.text(x, y + 0.28, "$\\mathcal{A}$   adjustment set", ha="center",
                    va="center", fontsize=8.8, fontweight="bold", color=C_ADJ,
                    zorder=6)
            ax.text(x, y - 0.22, "Climate · Econ. Capital · Housing\nTenure · Urbanicity",
                    ha="center", va="center", fontsize=7.2, color=C_ADJ,
                    zorder=6, linespacing=1.3)
            continue
        fc = ROLE[n]
        b = FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                           boxstyle="round,pad=0.02,rounding_size=0.12",
                           facecolor=fc, edgecolor=fc, lw=1.0, zorder=5)
        ax.add_patch(b); patches[n] = b
        ax.text(x, y, ZLAB[n], ha="center", va="center", zorder=6,
                fontsize=9.2 if "\n" not in ZLAB[n] else 8.5,
                fontweight="bold", color="white", linespacing=1.15)

    def ze(a, b, col, lw=2.8, rad=0.0, ls="-"):
        ax.add_patch(FancyArrowPatch(ZPOS[a], ZPOS[b], arrowstyle="-|>",
                                     mutation_scale=15,
                                     connectionstyle=f"arc3,rad={rad}",
                                     color=col, lw=lw, ls=ls,
                                     patchA=patches[a], patchB=patches[b],
                                     shrinkA=1.5, shrinkB=1.5, zorder=3))

    ze("ADJ", "HEE", C_ADJ, lw=2.2)
    ze("HEE", "FP", C_AFFORD, rad=-0.10)
    ze("FP", "MH", C_AFFORD, rad=-0.10)
    ze("HEE", "IEQ", C_INDOOR, rad=0.10)
    ze("IEQ", "MH", C_INDOOR, rad=0.10)
    ze("FP", "IEQ", C_AFFORD, lw=1.9, ls=(0, (5, 2.5)))

    # captions sit beside the mediator each describes
    ax.text(11.20, 2.58, "measured (LILEE)", fontsize=8.0, color=C_AFFORD,
            va="center", style="italic")
    ax.text(11.20, 0.32, "not measured", fontsize=8.0, color=C_INDOOR,
            va="center", style="italic")


def main():
    assert len(ed.RAW_EDGES) == 89, f"expected 89 edges, got {len(ed.RAW_EDGES)}"
    assert set(POS) == set(ed.FULL_NAMES), "layout/node mismatch"
    assert sum(len(m) for _, m in COLUMNS) == 25
    assert [sorted(m) for _, m in COLUMNS] == [sorted(l) for l in ed.LAYERS], \
        "column membership must match expert_dag.LAYERS"
    for e in PATH_EDGES:
        assert e in ed.RAW_EDGES, f"highlighted edge {e} not in the DAG"
    assert ("HEE", "MH") not in ed.RAW_EDGES
    print(f"OK: {len(ed.RAW_EDGES)} edges, {len(POS)} nodes in 7 columns, "
          f"{len(PATH_EDGES)} highlighted; HEE-MH non-adjacent.")

    fig = plt.figure(figsize=(15.4, 7.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.68],
                          width_ratios=[1.0, 0.256],
                          hspace=0.04, wspace=0.02,
                          left=0.022, right=0.985, top=0.945, bottom=0.030)

    axA = fig.add_subplot(gs[0, 0])
    axA.set_title("(a)  The reviewed DAG",
                  fontsize=10.4, fontweight="bold", color=C_TXT, pad=8,
                  loc="left")
    panel_full(axA)
    legend_block(fig.add_subplot(gs[0, 1]))

    axB = fig.add_subplot(gs[1, :])
    panel_zoom(axB)

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"dag_full_pathways.{ext}")
        fig.savefig(out, dpi=250 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
