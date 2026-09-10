#!/usr/bin/env python3
"""
Methods schematic for HEE-MH-paper-1: the four construction stages, the point at
which data first enters, and what each data-facing check can and cannot decide.

Output: pipeline.{png,pdf}
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))

C_PRIOR = "#0F6E6E"    # knowledge-driven stages
C_DATA  = "#2F6FB0"    # data-facing stages
C_OUT   = "#7B3FA0"
C_TXT   = "#20242B"
C_MUTE  = "#5F6368"
C_RULE  = "#C1443B"


def box(ax, x, y, w, h, title, body, colour, fill, fs_t=10.2, fs_b=8.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.04,rounding_size=0.13",
                                facecolor=fill, edgecolor=colour, lw=1.7, zorder=3))
    ax.text(x + w / 2, y + h - 0.30, title, ha="center", va="top",
            fontsize=fs_t, fontweight="bold", color=colour, zorder=4)
    ax.text(x + w / 2, y + h - 0.72, body, ha="center", va="top",
            fontsize=fs_b, color=C_TXT, zorder=4, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, colour=C_MUTE, lw=1.9, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=15, color=colour, lw=lw,
                                 ls=ls, zorder=2))


def main():
    fig, ax = plt.subplots(figsize=(15.0, 6.4))
    ax.set_xlim(0, 15.0); ax.set_ylim(0, 6.4); ax.axis("off")

    ax.text(0.15, 6.15, "Constructing the graph, then confronting it with data",
            fontsize=13.0, fontweight="bold", color=C_TXT, va="top")

    # ---- knowledge-driven stages -------------------------------------------
    ax.text(0.15, 5.52, "STAGE 1–4  ·  no data consulted", fontsize=8.6,
            fontweight="bold", color=C_PRIOR, va="top")

    W, H, Y = 2.28, 1.62, 3.42
    xs = [0.15, 2.63, 5.11, 7.59]
    stages = [
        ("1.  Nodes",
         "25 constructs, grouped by\ncausal role\n(hierarchical abstraction)"),
        ("2.  Edges",
         "53 papers screened on\ntemporal precedence,\nmechanism, empirical support"),
        ("3.  Expert review",
         "interactive DAG + issue\ntracker, then workshop\nsign-off  →  89 edges"),
        ("4.  Identification",
         "backdoor criterion (dagitty)\n$\\mathcal{A}$ = {Climate, Econ. Capital,\nHousing, Tenure, Urbanicity}"),
    ]
    for x, (t, b) in zip(xs, stages):
        col = C_OUT if t.startswith("4") else C_PRIOR
        box(ax, x, Y, W, H, t, b, col, "#F1F7F7" if col == C_PRIOR else "#F5F0FA")
    for x in xs[:-1]:
        arrow(ax, x + W + 0.03, Y + H / 2, x + W + 0.17, Y + H / 2)

    # ---- the firewall -------------------------------------------------------
    ax.plot([10.12, 10.12], [0.30, 5.62], color=C_RULE, lw=1.6,
            ls=(0, (5, 3.5)), zorder=1)
    ax.text(10.12, 5.80, "the graph is fixed here", ha="center", fontsize=8.8,
            fontweight="bold", color=C_RULE)
    arrow(ax, xs[-1] + W + 0.03, Y + H / 2, 10.34, Y + H / 2, colour=C_RULE)

    # ---- data-facing stage --------------------------------------------------
    ax.text(10.46, 5.62, "STAGE 5  ·  data enters  (n = 31,802 LSOAs)",
            fontsize=8.6, fontweight="bold", color=C_DATA, va="top")

    RX, RW = 10.46, 4.42
    box(ax, RX, 3.84, RW, 1.30,
        "5a.  Test the implied independencies",
        "80 implications of the 16-node measured subgraph,\n"
        "judged by |partial $r$|, each labelled by whether\n"
        "the pair is d-connected in the full 25-node DAG",
        C_DATA, "#F0F5FA", fs_t=9.4, fs_b=7.7)

    box(ax, RX, 2.32, RW, 1.30,
        "5b.  Recover structure from data alone",
        "PC-stable (assumes no latent confounders) and FCI\n"
        "(latent-robust), $\\alpha \\in \\{.01, .005, .001\\}$, with and\n"
        "without the expert ordering as background knowledge",
        C_DATA, "#F0F5FA", fs_t=9.4, fs_b=7.7)

    arrow(ax, RX + RW / 2, 3.78, RX + RW / 2, 3.70, colour=C_DATA, lw=1.4)
    arrow(ax, RX + RW / 2, 2.26, RX + RW / 2, 2.00, colour=C_DATA, lw=1.4)

    box(ax, RX, 0.62, RW, 1.30,
        "Verdict against pre-stated conditions",
        "(i) no HEE–MH adjacency appeared;  (ii) failed\n"
        "implications were dominated by latent-cut pairs,\n"
        "not by pairs the full DAG separates.  Neither triggered.",
        C_OUT, "#F5F0FA", fs_t=9.4, fs_b=7.7)

    ax.text(RX + RW / 2, 0.40,
            "$\\mathcal{A}$ carried forward to the companion estimation paper",
            ha="center", va="top", fontsize=8.2, color=C_OUT, fontweight="bold")

    # ---- what the checks cannot do -----------------------------------------
    ax.add_patch(FancyBboxPatch((0.15, 1.30), 9.45, 1.30,
                                boxstyle="round,pad=0.04,rounding_size=0.13",
                                facecolor="#FBF7F0", edgecolor="#B8860B",
                                lw=1.4, zorder=3))
    ax.text(0.45, 2.42, "What stage 5 cannot do", fontsize=9.4,
            fontweight="bold", color="#B8860B", va="top")
    ax.text(0.45, 2.06,
            "Discovery returns an equivalence class, so a recovered orientation is not\n"
            "evidence of causal direction.  It cannot estimate the HEE$\\rightarrow$MH effect: all but one\n"
            "of the mediators carrying it are unmeasured.  Agreement therefore corroborates\n"
            "the graph; only disagreement of the two pre-stated kinds could refute it.",
            fontsize=7.9, color=C_TXT, va="top", linespacing=1.55)

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"pipeline.{ext}")
        fig.savefig(out, dpi=260 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
