#!/usr/bin/env python3
"""
Three-panel figure on a SHARED node layout, comparing the expert-elicited DAG
with two constraint-based causal-discovery graphs.

Panel A  Expert DAG, induced subgraph over the 16 measured constructs (the
         directly-comparable slice of the full 25-node DAG; the 9 latent /
         unmeasured nodes are omitted -- they are the subject of the FCI check).
Panel B  PC-stable CPDAG  -- data-driven, assumes causal sufficiency
         (no latent confounders). alpha = 0.01, no tier background knowledge.
Panel C  FCI PAG         -- data-driven, latent-confounder-robust. alpha = 0.01.

All three panels share identical node positions (a topological-tier layout from
expert_dag.LAYERS) so they are directly comparable edge-by-edge.

Colour / mark scheme
  teal  single arrow   directed adjacency also present in the expert DAG
  orange              discovered-only adjacency (novel; not in expert DAG)
  grey dashed         expert adjacency the method did NOT recover (missed)
  plain line (B)      PC unoriented edge (CPDAG equivalence class)
  purple double arrow FCI bidirected edge (<->) = latent common cause
HEE (exposure) and MH (outcome) are highlighted. The figure shows HEE and MH are
NON-ADJACENT in all three graphs -- the DAG's fully-mediated HEE->MH claim,
recovered by unconstrained discovery both with and without a causal-sufficiency
assumption.

Everything is associational structure over cross-sectional, area-level (LSOA)
data. No causal claim beyond mental-health/CONCLUSIONS.md is implied.

Run:  python3 make_comparison_figure.py [--pc pc_a0.01_notier] [--fci fci_a0.01]
Outputs: dag_vs_pc_fci_comparison.{png,pdf}
"""
from __future__ import annotations
import argparse
import os
import sys

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import expert_dag as ed  # source of truth for nodes/edges/mapping

# --------------------------------------------------------------------------- #
# Colours / style
# --------------------------------------------------------------------------- #
C_SHARED = "#0F6E6E"   # adjacency shared with the expert DAG
C_MISS = "#B9BFC6"     # expert-only (method missed) -- grey, dashed
C_NOVEL = "#E8792B"    # discovered-only (novel) -- orange
C_BIDIR = "#7B3FA0"    # FCI bidirected = latent common cause -- purple
C_NODE = "#EEF1F4"
C_NODE_EDGE = "#5F6368"
C_HEE = "#2F6FB0"      # exposure highlight
C_MH = "#C1443B"       # outcome highlight
C_TXT = "#20242B"

# Shared tiered layout (x, y); y high = exogenous/top, low = MH/PH sink
POS = {
    "U": (3.5, 6.0), "C": (6.5, 6.0),
    "D": (1.6, 5.0), "EC": (5.0, 5.0), "ED": (8.4, 5.0),
    "NS": (0.5, 4.0), "T": (2.7, 4.0), "HEE": (4.7, 4.0), "H": (6.7, 4.0), "O": (8.7, 4.0),
    "FP": (4.7, 3.0),
    "AP": (2.8, 2.0), "GS": (5.0, 2.0), "A": (7.2, 2.0),
    "PH": (3.4, 1.0), "MH": (6.4, 1.0),
}
HL = {"HEE": C_HEE, "MH": C_MH}


def load_edges(fname, config, kinds):
    """Return dict kind -> set of pairs (tuples for directed, frozensets else)."""
    df = pd.read_csv(os.path.join(HERE, fname))
    df = df[df["config"] == config]
    if df.empty:
        opts = sorted(pd.read_csv(os.path.join(HERE, fname))["config"].unique())
        raise SystemExit(f"No rows for config={config!r} in {fname}. Options: {opts}")
    out = {k: set() for k in kinds}
    for _, r in df.iterrows():
        if r["kind"] == "directed":
            out["directed"].add((r["a"], r["b"]))
        else:
            out[r["kind"]].add(frozenset((r["a"], r["b"])))
    return out


def adjset(*collections):
    out = set()
    for coll in collections:
        for p in coll:
            a, b = tuple(p)
            out.add(frozenset((a, b)))
    return out


def draw_node(ax, n):
    x, y = POS[n]
    fc = HL.get(n, C_NODE)
    txt_c = "white" if n in HL else C_TXT
    r = 0.34 if n in HL else 0.30
    ax.add_patch(plt.Circle((x, y), r, facecolor=fc,
                            edgecolor=(fc if n in HL else C_NODE_EDGE),
                            lw=1.6 if n in HL else 1.1, zorder=4))
    ax.text(x, y, n, ha="center", va="center", zorder=5,
            fontsize=10.5 if n in HL else 9.3,
            fontweight="bold" if n in HL else "normal", color=txt_c)


def draw_edge(ax, a, b, color, head="single", dashed=False, lw=1.7, z=2, alpha=0.95):
    xa, ya = POS[a]; xb, yb = POS[b]
    style = {"single": "-|>", "double": "<|-|>", "none": "-"}[head]
    ax.add_patch(FancyArrowPatch(
        (xa, ya), (xb, yb), arrowstyle=style,
        mutation_scale=13 if head != "none" else 0,
        connectionstyle="arc3,rad=0.06", color=color, lw=lw,
        ls="--" if dashed else "-", shrinkA=13, shrinkB=13, zorder=z, alpha=alpha))


def setup(ax, title):
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=C_TXT, pad=8)
    ax.set_xlim(-0.4, 9.6); ax.set_ylim(0.2, 6.8)
    ax.set_aspect("equal"); ax.axis("off")


def draw_missed(ax, expert_adj, method_adj):
    for pair in (expert_adj - method_adj):
        a, b = tuple(pair)
        draw_edge(ax, a, b, C_MISS, head="none", dashed=True, lw=1.2, z=1, alpha=0.9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pc", default="pc_a0.01_notier")
    ap.add_argument("--fci", default="fci_a0.01")
    args = ap.parse_args()

    # expert induced subgraph (source of truth)
    G = ed.induced_measured_digraph()
    expert_adj = adjset(G.edges())

    pc = load_edges("pc_edges_primary_DepRate.csv", args.pc, ["directed", "undirected"])
    pc_adj = adjset(pc["directed"], pc["undirected"])

    fci = load_edges("fci_edges_primary_DepRate.csv", args.fci, ["directed", "bidirected"])
    fci_adj = adjset(fci["directed"], fci["bidirected"])

    # ---- verification stats ----
    hee_mh = frozenset(("HEE", "MH"))
    def stats(name, madj):
        rec = expert_adj & madj
        return (len(madj), len(rec), len(expert_adj - madj), len(madj - expert_adj),
                len(rec) / len(madj), len(rec) / len(expert_adj))
    pc_n, pc_rec, pc_miss, pc_nov, pc_p, pc_r = stats("PC", pc_adj)
    fci_n, fci_rec, fci_miss, fci_nov, fci_p, fci_r = stats("FCI", fci_adj)
    hee_fci_edges = [tuple(p) for p in fci["bidirected"] if "HEE" in p]
    hee_all_edges = [e for e in fci_adj if "HEE" in e]
    print(f"=== PC ({args.pc}) ===")
    print(f"  adj={pc_n} recovered={pc_rec} missed={pc_miss} novel={pc_nov} "
          f"precision={pc_p:.2f} recall={pc_r:.2f}")
    print(f"=== FCI ({args.fci}) ===")
    print(f"  adj={fci_n} bidirected={len(fci['bidirected'])} directed={len(fci['directed'])} "
          f"recovered={fci_rec} missed={fci_miss} novel={fci_nov} "
          f"precision={fci_p:.2f} recall={fci_r:.2f}")
    print(f"  HEE edges in FCI = {len(hee_all_edges)}; bidirected = {len(hee_fci_edges)} "
          f"(all bidirected: {len(hee_all_edges) == len(hee_fci_edges)})")
    print(f"  HEE-MH adjacent?  expert={hee_mh in expert_adj}  "
          f"PC={hee_mh in pc_adj}  FCI={hee_mh in fci_adj}")

    # ---- figure ----
    fig, (axA, axB, axC) = plt.subplots(1, 3, figsize=(21.5, 8.6))

    # Panel A: expert reference
    setup(axA, "A.  Expert DAG  (induced subgraph, 16 constructs)")
    for a, b in G.edges():
        draw_edge(axA, a, b, C_SHARED, head="single", lw=1.7)
    for n in POS:
        draw_node(axA, n)

    # Panel B: PC
    setup(axB, "B.  PC-stable  (data-driven, assumes no latent confounders)")
    draw_missed(axB, expert_adj, pc_adj)
    for a, b in pc["directed"]:
        c = C_SHARED if frozenset((a, b)) in expert_adj else C_NOVEL
        draw_edge(axB, a, b, c, head="single", lw=1.8)
    for pair in pc["undirected"]:
        a, b = tuple(pair)
        c = C_SHARED if pair in expert_adj else C_NOVEL
        draw_edge(axB, a, b, c, head="none", lw=1.8)
    for n in POS:
        draw_node(axB, n)

    # Panel C: FCI
    setup(axC, "C.  FCI  (data-driven, latent-confounder-robust)")
    draw_missed(axC, expert_adj, fci_adj)
    for a, b in fci["directed"]:
        c = C_SHARED if frozenset((a, b)) in expert_adj else C_NOVEL
        draw_edge(axC, a, b, c, head="single", lw=1.8)
    for pair in fci["bidirected"]:
        a, b = tuple(pair)
        draw_edge(axC, a, b, C_BIDIR, head="double", lw=1.9)
    for n in POS:
        draw_node(axC, n)

    fig.suptitle("Expert-elicited DAG vs constraint-based causal discovery "
                 "(HEE–MH structure, LSOA cross-section)",
                 fontsize=15.5, fontweight="bold", color=C_TXT, y=0.985)

    cap = (
        f"Shared node layout. PC recovers {pc_rec}/{len(expert_adj)} expert adjacencies "
        f"(recall {pc_r:.2f}, precision {pc_p:.2f}); FCI recovers {fci_rec}/{len(expert_adj)} "
        f"(recall {fci_r:.2f}, precision {fci_p:.2f}) and marks {len(fci['bidirected'])}/{fci_n} edges "
        f"bidirected (↔, latent common cause) — including all {len(hee_all_edges)} HEE edges. "
        f"HEE and MH are non-adjacent in all three graphs — the DAG's fully-mediated HEE→MH claim, "
        f"recovered with and without a causal-sufficiency assumption. Orientations are CPDAG/PAG "
        f"equivalence-class statements; all associations are area-level."
    )
    fig.text(0.5, 0.105, cap, ha="center", va="top", fontsize=9.4, color="#3c4043", wrap=True)

    handles = [
        Line2D([0], [0], color=C_SHARED, lw=2.4, label="Directed adjacency shared with expert DAG"),
        Line2D([0], [0], color=C_NOVEL, lw=2.2, label="Discovered-only (novel)"),
        Line2D([0], [0], color=C_MISS, lw=2.0, ls="--", label="Expert edge not recovered"),
        Line2D([0], [0], color=C_BIDIR, lw=2.4, label="FCI bidirected ↔ (latent common cause)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_HEE, markersize=11, label="HEE (exposure)"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor=C_MH, markersize=11, label="MH (outcome)"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False,
               fontsize=9.6, bbox_to_anchor=(0.5, 0.045))

    key_items = [f"{k} = {ed.FULL_NAMES[k]}" for k in sorted(POS)]
    mid = (len(key_items) + 1) // 2
    key_txt = "   ".join(key_items[:mid]) + "\n" + "   ".join(key_items[mid:])
    fig.text(0.5, 0.018, key_txt, ha="center", va="bottom", fontsize=7.6, color="#5f6368")

    fig.subplots_adjust(left=0.015, right=0.985, top=0.92, bottom=0.19, wspace=0.04)
    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"dag_vs_pc_fci_comparison.{ext}")
        fig.savefig(out, dpi=300 if ext == "png" else None, bbox_inches="tight")
        print("wrote", out)


if __name__ == "__main__":
    main()
