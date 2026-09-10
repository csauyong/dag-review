#!/usr/bin/env python3
"""
Two things readers of the discovery section need and the current text does not
give them: a worked example of a single implied-independence test on this
project's own identification claim, and an unambiguous key to the edge marks.

Panel A  The Education exclusion, tested.  The DAG's minimal adjustment set is
         minimal only because Education has no direct edge into HEE.  That is a
         testable implication, and it is the same test the 80-implication
         battery runs.  The Demographics exclusion is shown alongside because it
         behaves differently.
Panel B  Every mark used in the paper, what it asserts, and -- for the bidirected
         arrow specifically -- what it does NOT assert.

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


def arr(ax, p, q, colour=C_MUTE, lw=1.7, rad=0.0, style="-|>", ms=12, sh=17, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms,
                                 connectionstyle=f"arc3,rad={rad}", color=colour,
                                 lw=lw, ls=ls, shrinkA=sh, shrinkB=sh, zorder=3))


# --------------------------------------------------------------------------- #
def panel_example(ax, ed_row, d_row):
    ax.set_title("A.  One implied independence, tested — the Education exclusion",
                 fontsize=11.6, fontweight="bold", color=C_TXT, pad=8, loc="left")
    ax.set_xlim(0, 8.9); ax.set_ylim(-0.2, 5.4); ax.set_aspect("equal"); ax.axis("off")

    ax.text(0.05, 5.28,
            "$\\mathcal{A}$ is minimal only if Education reaches HEE entirely\n"
            "through Economic Capital, Housing and Tenure. That is a\n"
            "claim about the data, and the 80-implication battery is\n"
            "80 tests of exactly this kind.",
            fontsize=8.3, color=C_MUTE, va="top", linespacing=1.55)

    # --- the claim, drawn
    y0 = 2.15
    node(ax, 0.62, y0, "ED")
    node(ax, 2.30, y0 + 0.66, "EC", fc="#F0E9F7", ec=C_LAT, tc=C_LAT)
    node(ax, 2.30, y0, "H", fc="#F0E9F7", ec=C_LAT, tc=C_LAT)
    node(ax, 2.30, y0 - 0.66, "T", fc="#F0E9F7", ec=C_LAT, tc=C_LAT)
    node(ax, 3.98, y0, "HEE", fc=C_HEE, ec=C_HEE, tc="white", r=0.34, lw=1.6, fs=9.0)
    for dy in (0.66, 0.0, -0.66):
        arr(ax, (0.62, y0), (2.30, y0 + dy), C_OK, lw=1.6)
        arr(ax, (2.30, y0 + dy), (3.98, y0), C_OK, lw=1.6)
    ax.text(2.30, y0 + 1.32, "Education's effect is routed through these three",
            ha="center", fontsize=7.9, color=C_OK, style="italic")
    arr(ax, (0.62, y0 - 1.20), (3.98, y0 - 1.20), C_BAD, lw=1.6,
        ls=(0, (4, 3)), sh=4)
    ax.text(2.30, y0 - 1.20, "$\\times$", ha="center", va="center", fontsize=15,
            color=C_BAD, fontweight="bold", zorder=6,
            bbox=dict(boxstyle="circle,pad=0.10", fc="white", ec="none"))
    ax.text(2.30, y0 - 1.52, "no direct edge  —  the claim under test",
            ha="center", fontsize=7.9, color=C_BAD, style="italic")

    # --- the test result
    def verdict(x, y, h, title, txt, colour, tone):
        ax.add_patch(FancyBboxPatch((x, y), 3.62, h,
                                    boxstyle="round,pad=0.05,rounding_size=0.12",
                                    facecolor=tone, edgecolor=colour, lw=1.6, zorder=3))
        ax.text(x + 0.18, y + h - 0.16, title, fontsize=9.0, fontweight="bold",
                color=colour, va="top")
        ax.text(x + 0.18, y + h - 0.54, txt, fontsize=7.6, color=C_TXT, va="top",
                linespacing=1.55)

    verdict(5.20, 3.28, 1.72,
            "Upheld",
            f"partial $r$(ED, HEE $\\mid$ D, EC, U) = {ed_row.estimate:+.3f}\n"
            f"95% CI [{ed_row.ci_lo:+.3f}, {ed_row.ci_hi:+.3f}],  $n$ = 31,802\n"
            "$p$ < 0.01, yet the magnitude is ~0. At this $n$\n"
            "significance is uninformative and effect\n"
            "size is what the verdict rests on.",
            C_OK, "#F1F7F7")

    verdict(5.20, 1.06, 1.96,
            "Not upheld — and worth saying so",
            f"partial $r$(D, HEE $\\mid$ C, EC, H, U) = {d_row.estimate:+.3f}\n"
            "The full DAG can account for it: conditioning\n"
            "on EC and H opens collider paths into U$_{AH}$.\n"
            "But the Demographics exclusion is not clean\n"
            "the way the Education exclusion is, and $\\mathcal{A}$\n"
            "rests on both equally.",
            C_WARN, "#FBF7F0")

    ax.text(0.05, 0.28,
            "A test at $n \\approx 32{,}000$ rejects almost any exact null, so implications are judged by "
            "|partial $r$|, not $p$. A failure counts\nagainst the graph only if the pair stays d-separated "
            "once the unmeasured nodes are restored.",
            fontsize=8.0, color=C_MUTE, va="top", linespacing=1.55)


# --------------------------------------------------------------------------- #
MARKS = [
    ("expert", "single", "#0F6E6E",
     "$X \\rightarrow Y$", "Expert DAG",
     "$X$ is assumed to be a direct cause of $Y$ at LSOA scale.",
     "Not a finding. The direction is an assumption defended by literature and review."),
    ("pc_dir", "single", "#2F6FB0",
     "$X \\rightarrow Y$", "PC output (CPDAG)",
     "Every DAG consistent with the tested independencies orients it this way.",
     "Not evidence of direction: PC also assumes no unmeasured confounders, which is false here."),
    ("pc_und", "none", "#2F6FB0",
     "$X - Y$", "PC output (CPDAG)",
     "$X$ and $Y$ are adjacent; the data do not determine which way.",
     "Not a symmetric or mutual effect."),
    ("fci_bi", "double", "#7B3FA0",
     "$X \\leftrightarrow Y$", "FCI output (PAG)",
     "Neither is an ancestor of the other; an unmeasured common cause drives the association.",
     "NOT mutual causation, NOT feedback, NOT a two-way effect. 28 of 39 FCI edges are of this kind."),
    ("fci_circ", "circle", "#7B3FA0",
     "$X \\; \\circ\\!\\!\\rightarrow Y$", "FCI output (PAG)",
     "The mark at $X$ is undetermined: the edge may be $X \\rightarrow Y$ or $X \\leftrightarrow Y$.",
     "Not a weaker version of an arrow — an explicit statement of what the data cannot settle."),
]


def panel_marks(ax):
    ax.set_title("B.  What each mark means — and what it does not",
                 fontsize=11.6, fontweight="bold", color=C_TXT, pad=8, loc="left")
    ax.set_xlim(0, 9.4); ax.set_ylim(-0.3, 5.4); ax.axis("off")

    ax.text(0.05, 5.12, "mark", fontsize=7.6, fontweight="bold", color=C_MUTE)
    ax.text(1.28, 5.12, "appears in", fontsize=7.6, fontweight="bold", color=C_MUTE)
    ax.text(2.95, 5.12, "asserts", fontsize=7.6, fontweight="bold", color=C_MUTE)

    y = 4.72
    for key, kind, col, glyph, where, says, notsays in MARKS:
        ax.text(0.05, y - 0.14, glyph, fontsize=12.0, color=col, va="center",
                fontweight="bold")
        ax.text(1.28, y - 0.14, where, fontsize=8.0, color=col, va="center",
                fontweight="bold")
        ax.text(2.95, y + 0.02, says, fontsize=8.0, color=C_TXT, va="center")
        ax.text(2.95, y - 0.30, notsays, fontsize=7.7, color=C_BAD if key == "fci_bi"
                else C_MUTE, va="center", style="italic")
        y -= 0.82
        if key != MARKS[-1][0]:
            ax.plot([0.05, 9.30], [y + 0.30, y + 0.30], color="#E3E7EB", lw=0.8)

    ax.add_patch(FancyBboxPatch((0.05, -0.18), 9.25, 0.96,
                                boxstyle="round,pad=0.05,rounding_size=0.12",
                                facecolor="#FBF7F0", edgecolor=C_WARN, lw=1.5, zorder=3))
    ax.text(0.28, 0.62,
            "One word, three meanings — keep them apart",
            fontsize=8.8, fontweight="bold", color=C_WARN, va="top")
    ax.text(0.28, 0.30,
            "FCI's $\\leftrightarrow$ = latent common cause.  A \"plausibly bidirectional edge\" in the "
            "orientation-sensitivity analysis = an edge whose direction the\nexperts were unsure of.  "
            "A \"substantively bidirectional\" relationship (MH–PH, EC–ED) = genuine feedback that acyclicity forbids.",
            fontsize=7.8, color=C_TXT, va="top", linespacing=1.5)


def main():
    ed_row, d_row = fetch()
    print(f"ED-HEE r={ed_row.estimate:+.4f} given {ed_row.given} "
          f"dconn_full={ed_row.dconn_full_dag}")
    print(f"D-HEE  r={d_row.estimate:+.4f} given {d_row.given} "
          f"dconn_full={d_row.dconn_full_dag}")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16.6, 5.6),
                                 gridspec_kw=dict(width_ratios=[1.0, 1.06],
                                                  wspace=0.06))
    panel_example(a1, ed_row, d_row)
    panel_marks(a2)
    fig.subplots_adjust(left=0.025, right=0.985, top=0.90, bottom=0.03)

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"marks_and_example.{ext}")
        fig.savefig(out, dpi=260 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
