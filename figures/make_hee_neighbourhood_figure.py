#!/usr/bin/env python3
"""
The three-panel comparison figure is too dense to read at page width, and the
paper's actual claims are local: what happens around HEE, and whether HEE and MH
are adjacent. This figure states those claims in a form a reader can check.

Every edge incident to HEE in ANY of the three graphs is listed once, with what
each graph says about it. The HEE-MH row -- the paper's falsification condition
-- is shown last.

Sources: expert_dag.py (induced subgraph), pc_edges / fci_edges CSVs at
alpha = 0.01, primary outcome (depression prevalence).
Output: hee_neighbourhood.{png,pdf}
"""
from __future__ import annotations
import os, sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
CD = os.path.join(HERE, "..", "causal_discovery_validation")
sys.path.insert(0, CD)
import expert_dag as ed

C_TXT = "#20242B"; C_MUTE = "#5F6368"; C_ABSENT = "#B9BFC6"
C_EXP = "#0F6E6E"; C_PC = "#2F6FB0"; C_FCI = "#7B3FA0"
C_WARN = "#B8860B"; C_BAD = "#C1443B"

ADJ = set(ed.ADJ_SET)


def incident(pairs):
    return {frozenset(p[:2]): p for p in pairs if "HEE" in p[:2]}


def main():
    G = ed.induced_measured_digraph()
    exp = incident([(a, b, "directed") for a, b in G.edges()])

    pc = pd.read_csv(os.path.join(CD, "pc_edges_primary_DepRate.csv"))
    pc = pc[pc.config == "pc_a0.01_notier"]
    P = incident([(r.a, r.b, r["kind"]) for _, r in pc.iterrows()])

    fci = pd.read_csv(os.path.join(CD, "fci_edges_primary_DepRate.csv"))
    fci = fci[fci.config == "fci_a0.01"]
    F = incident([(r.a, r.b, r["kind"]) for _, r in fci.iterrows()])

    keys = sorted(set(exp) | set(P) | set(F),
                  key=lambda k: (frozenset(("HEE", "MH")) == k,
                                 sorted(k - {"HEE"})[0] if k - {"HEE"} else ""))
    keys.append(frozenset(("HEE", "MH")))

    def cell(d, k):
        if k not in d:
            return ("absent", None, None)
        a, b, kind = d[k]
        return (kind, a, b)

    def glyph(kind, a, b, other):
        if kind == "absent":
            return "not recovered", C_ABSENT
        if kind == "bidirected":
            return f"{other} $\\leftrightarrow$ HEE", C_FCI
        if kind == "undirected":
            return f"{other} — HEE", C_PC
        return f"{a} $\\rightarrow$ {b}", None

    def reversed_vs_expert(e, p):
        if e[0] != "directed" or p[0] != "directed":
            return False
        return (p[1], p[2]) == (e[2], e[1])

    rows = []
    for k in keys:
        other = (sorted(k - {"HEE"}) or ["MH"])[0]
        rows.append((other, cell(exp, k), cell(P, k), cell(F, k)))

    fig, ax = plt.subplots(figsize=(12.9, 6.4))
    ax.set_xlim(0, 12.9); ax.set_ylim(0, 6.4); ax.axis("off")

    ax.text(0.15, 6.26, "Every edge at HEE, and what each graph says about it",
            fontsize=12.8, fontweight="bold", color=C_TXT, va="top")
    ax.text(0.15, 5.92,
            "PC-stable and FCI at $\\alpha = 0.01$; depression prevalence; $n = 31{,}802$.",
            fontsize=8.4, color=C_MUTE, va="top")

    XN, XE, XP, XF = 0.30, 3.42, 6.15, 9.20
    ax.text(XN, 5.50, "neighbour of HEE", fontsize=8.4, fontweight="bold", color=C_MUTE)
    ax.text(XE, 5.50, "Expert DAG", fontsize=8.8, fontweight="bold", color=C_EXP)
    ax.text(XP, 5.50, "PC-stable", fontsize=8.8, fontweight="bold", color=C_PC)
    ax.text(XF, 5.50, "FCI", fontsize=8.8, fontweight="bold", color=C_FCI)
    ax.plot([0.15, 12.75], [5.36, 5.36], color="#9AA1A9", lw=1.0)

    y, STEP = 5.06, 0.52
    for i, (other, e, p, f) in enumerate(rows):
        is_mh = other == "MH"
        if is_mh:
            ax.add_patch(FancyBboxPatch((0.15, y - 0.28), 12.60, 0.56,
                                        boxstyle="round,pad=0.02,rounding_size=0.08",
                                        facecolor="#F1F7F7", edgecolor=C_EXP,
                                        lw=1.4, zorder=1))
        name = ed.FULL_NAMES[other].replace("Home Energy Efficiency", "HEE")
        tag = "  (in $\\mathcal{A}$)" if other in ADJ else ""
        ax.text(XN, y, name + tag, fontsize=8.6,
                color=C_EXP if is_mh else C_TXT,
                fontweight="bold" if (other in ADJ or is_mh) else "normal",
                va="center", zorder=3)

        for x, c, base in ((XE, e, C_EXP), (XP, p, C_PC), (XF, f, C_FCI)):
            txt, col = glyph(c[0], c[1], c[2], other)
            ax.text(x, y, txt, fontsize=8.6, color=col or base, va="center",
                    style="italic" if c[0] == "absent" else "normal",
                    fontweight="bold" if c[0] == "bidirected" else "normal",
                    zorder=3)
        if reversed_vs_expert(e, p):
            ax.text(XP + 1.52, y, "direction reversed", fontsize=7.4, color=C_WARN,
                    va="center", style="italic", zorder=3)
        y -= STEP
        if i < len(rows) - 1 and not is_mh:
            ax.plot([0.15, 12.75], [y + 0.26, y + 0.26], color="#E8ECEF", lw=0.7)

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"hee_neighbourhood.{ext}")
        fig.savefig(out, dpi=260 if ext == "png" else None,
                    bbox_inches="tight", facecolor="white")
        print("wrote", out)


if __name__ == "__main__":
    main()
