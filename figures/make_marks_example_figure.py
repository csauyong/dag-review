#!/usr/bin/env python3
"""
(a) One implied-independence test, worked through on the Education exclusion,
    with a second exclusion shown for contrast.
(b) Key to the edge marks used in the paper.

Interpretation is in the text; the figure carries the structure and the
statistics only.

Numbers: localtests_primary_DepRate.csv (rows ED-HEE and D-HEE).
Output: marks_and_example.{png,pdf}
"""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "..", "causal_discovery_validation",
                   "localtests_primary_DepRate.csv")

C_TXT = "#20242B"; C_MUTE = "#5F6368"
C_OK = "#0F6E6E"; C_WARN = "#B8860B"; C_BAD = "#C1443B"
C_HEE = "#2F6FB0"; C_LAT = "#7B3FA0"


def fetch():
    import pandas as pd
    d = pd.read_csv(CSV)
    def row(x, y):
        m = d[((d.x == x) & (d.y == y)) | ((d.x == y) & (d.y == x))]
        assert len(m) == 1, (x, y, len(m))
        return m.iloc[0]
    return row("ED", "HEE"), row("D", "HEE")


def node(ax, x, y, lab, fc="#F2F4F7", ec="#7A828C", tc=C_TXT, r=0.30, lw=1.2, fs=9.4):
    ax.add_patch(plt.Circle((x, y), r, facecolor=fc, edgecolor=ec, lw=lw, zorder=5))
    ax.text(x, y, lab, ha="center", va="center", fontsize=fs, zorder=6,
            color=tc, fontweight="bold")


def arr(ax, p, q, colour=C_MUTE, lw=1.7, ls="-", sh=17):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12,
                                 connectionstyle="arc3,rad=0", color=colour,
                                 lw=lw, ls=ls, shrinkA=sh, shrinkB=sh, zorder=3))


def panel_example(ax, ed_row, d_row):
    ax.set_title("(a)  One implied independence, tested", fontsize=10.6,
                 fontweight="bold", color=C_TXT, pad=6, loc="left")
    ax.set_xlim(0, 8.4); ax.set_ylim(0.55, 4.30); ax.set_aspect("equal"); ax.axis("off")

    y0 = 2.55
    node(ax, 0.62, y0, "ED")
    for dy, lab in ((0.66, "EC"), (0.0, "H"), (-0.66, "T")):
        node(ax, 2.30, y0 + dy, lab, fc="#F0E9F7", ec=C_LAT, tc=C_LAT)
        arr(ax, (0.62, y0), (2.30, y0 + dy), C_OK, lw=1.6)
        arr(ax, (2.30, y0 + dy), (3.98, y0), C_OK, lw=1.6)
    node(ax, 3.98, y0, "HEE", fc=C_HEE, ec=C_HEE, tc="white", r=0.34, lw=1.6, fs=9.0)

    arr(ax, (0.62, y0 - 1.24), (3.98, y0 - 1.24), C_BAD, lw=1.5, ls=(0, (4, 3)), sh=4)
    ax.text(2.30, y0 - 1.24, "$\\times$", ha="center", va="center", fontsize=14,
            color=C_BAD, fontweight="bold", zorder=6,
            bbox=dict(boxstyle="circle,pad=0.10", fc="white", ec="none"))
    ax.text(2.30, y0 - 1.60, "tested: no direct edge", ha="center",
            fontsize=8.0, color=C_BAD, style="italic")

    def verdict(x, y, h, title, txt, colour, tone):
        ax.add_patch(FancyBboxPatch((x, y), 3.30, h,
                                    boxstyle="round,pad=0.05,rounding_size=0.12",
                                    facecolor=tone, edgecolor=colour, lw=1.5, zorder=3))
        ax.text(x + 0.18, y + h - 0.18, title, fontsize=8.8, fontweight="bold",
                color=colour, va="top")
        ax.text(x + 0.18, y + h - 0.56, txt, fontsize=8.0, color=C_TXT, va="top",
                linespacing=1.5)

    verdict(4.90, 2.42, 1.42, "Upheld",
            f"$r$(ED, HEE $\\mid$ D, EC, U) = {ed_row.estimate:+.3f}\n"
            f"95% CI [{ed_row.ci_lo:+.3f}, {ed_row.ci_hi:+.3f}]\n"
            f"$n$ = 31,802",
            C_OK, "#F1F7F7")
    verdict(4.90, 0.70, 1.42, "Not upheld",
            f"$r$(D, HEE $\\mid$ C, EC, H, U) = {d_row.estimate:+.3f}\n"
            f"95% CI [{d_row.ci_lo:+.3f}, {d_row.ci_hi:+.3f}]\n"
            f"$n$ = 31,802",
            C_WARN, "#FBF7F0")


MARKS = [
    ("$X \\rightarrow Y$", "Expert DAG", "$X$ is assumed a direct cause of $Y$", "#0F6E6E"),
    ("$X \\rightarrow Y$", "PC (CPDAG)", "oriented in every DAG consistent with the tests", "#2F6FB0"),
    ("$X - Y$", "PC (CPDAG)", "adjacent; orientation not determined", "#2F6FB0"),
    ("$X \\leftrightarrow Y$", "FCI (PAG)", "unmeasured common cause", "#7B3FA0"),
    ("$X \\; \\circ\\!\\!\\rightarrow Y$", "FCI (PAG)", "endpoint at $X$ undetermined", "#7B3FA0"),
]


def panel_marks(ax):
    ax.set_title("(b)  Edge marks", fontsize=10.6, fontweight="bold",
                 color=C_TXT, pad=6, loc="left")
    ax.set_xlim(0, 7.2); ax.set_ylim(0.55, 4.30); ax.axis("off")

    ax.text(0.05, 4.10, "mark", fontsize=7.6, fontweight="bold", color=C_MUTE)
    ax.text(1.30, 4.10, "graph", fontsize=7.6, fontweight="bold", color=C_MUTE)
    ax.text(2.70, 4.10, "asserts", fontsize=7.6, fontweight="bold", color=C_MUTE)
    ax.plot([0.05, 7.10], [3.94, 3.94], color="#9AA1A9", lw=0.9)

    y = 3.60
    for glyph, where, says, col in MARKS:
        ax.text(0.05, y, glyph, fontsize=11.5, color=col, va="center", fontweight="bold")
        ax.text(1.30, y, where, fontsize=8.2, color=col, va="center", fontweight="bold")
        ax.text(2.70, y, says, fontsize=8.2, color=C_TXT, va="center")
        y -= 0.62
        ax.plot([0.05, 7.10], [y + 0.30, y + 0.30], color="#E3E7EB", lw=0.7)


def main():
    ed_row, d_row = fetch()
    print(f"ED-HEE r={ed_row.estimate:+.4f} | D-HEE r={d_row.estimate:+.4f}")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14.6, 3.6),
                                 gridspec_kw=dict(width_ratios=[1.0, 0.86], wspace=0.05))
    panel_example(a1, ed_row, d_row)
    panel_marks(a2)
    fig.subplots_adjust(left=0.02, right=0.99, top=0.90, bottom=0.02)
    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"marks_and_example.{ext}")
        fig.savefig(out, dpi=260 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
