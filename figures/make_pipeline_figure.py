#!/usr/bin/env python3
"""
Methods schematic for HEE-MH-paper-1: the four knowledge-driven construction
stages, the point at which data first enter, and the two data-facing checks.

Interpretation belongs in the text, not here. The figure carries the sequence
and the counts only.

Output: pipeline.{png,pdf}
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))

C_PRIOR = "#0F6E6E"
C_DATA  = "#2F6FB0"
C_OUT   = "#7B3FA0"
C_TXT   = "#20242B"
C_MUTE  = "#5F6368"
C_RULE  = "#C1443B"


def box(ax, x, y, w, h, title, body, colour, fill):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.03,rounding_size=0.11",
                                facecolor=fill, edgecolor=colour, lw=1.5, zorder=3))
    ax.text(x + w / 2, y + h - 0.26, title, ha="center", va="top",
            fontsize=9.6, fontweight="bold", color=colour, zorder=4)
    ax.text(x + w / 2, y + h - 0.60, body, ha="center", va="top",
            fontsize=7.9, color=C_TXT, zorder=4, linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, colour=C_MUTE, lw=1.7):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=13, color=colour, lw=lw, zorder=2))


def main():
    fig, ax = plt.subplots(figsize=(14.6, 3.15))
    ax.set_xlim(0, 14.6); ax.set_ylim(0, 3.15); ax.axis("off")

    ax.text(0.12, 3.00, "STAGES 1–4  ·  NO DATA CONSULTED", fontsize=8.2,
            fontweight="bold", color=C_PRIOR, va="top")

    W, H, Y = 2.24, 1.66, 0.92
    xs = [0.12, 2.56, 5.00, 7.44]
    stages = [
        ("1.  Nodes", "25 constructs,\ngrouped by causal role"),
        ("2.  Edges", "53 papers screened on\ntemporal precedence,\nmechanism, evidence"),
        ("3.  Expert review", "asynchronous comment,\nworkshop, sign-off\n89 edges"),
        ("4.  Identification", "backdoor criterion\n$\\mathcal{A}$ = {Climate, Econ.\nCapital, Housing,\nTenure, Urbanicity}"),
    ]
    for x, (t, b) in zip(xs, stages):
        col = C_OUT if t.startswith("4") else C_PRIOR
        box(ax, x, Y, W, H, t, b, col, "#F5F0FA" if col == C_OUT else "#F1F7F7")
    for x in xs[:-1]:
        arrow(ax, x + W + 0.02, Y + H / 2, x + W + 0.18, Y + H / 2)

    ax.plot([10.02, 10.02], [0.30, 2.92], color=C_RULE, lw=1.5, ls=(0, (5, 3.5)), zorder=1)
    ax.text(9.90, 3.02, "graph fixed", ha="right", fontsize=8.0,
            fontweight="bold", color=C_RULE, va="top")
    arrow(ax, xs[-1] + W + 0.02, Y + H / 2, 10.22, Y + H / 2, colour=C_RULE)

    ax.text(10.38, 3.00, "STAGE 5  ·  $n$ = 31,802 LSOAs", fontsize=8.2,
            fontweight="bold", color=C_DATA, va="top")

    RX, RW = 10.38, 4.10
    box(ax, RX, 1.62, RW, 0.96, "5a.  Implied independencies",
        "80 tests, judged by |partial $r$|", C_DATA, "#F0F5FA")
    box(ax, RX, 0.42, RW, 0.96, "5b.  Structure recovery",
        "PC-stable and FCI, $\\alpha \\in \\{.01, .005, .001\\}$", C_DATA, "#F0F5FA")
    arrow(ax, RX + RW / 2, 1.56, RX + RW / 2, 1.44, colour=C_DATA, lw=1.3)

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"pipeline.{ext}")
        fig.savefig(out, dpi=260 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
