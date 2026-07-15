#!/usr/bin/env python3
"""
Causal-discovery validation of the expert-reviewed HEE -> MH DAG.
Robustness / triangulation section for HEE-MH-paper-1.

Pipeline
--------
1. Load LSOA-level data (mental-health/datasets/merged_data.csv) and build the
   measured-construct matrix from the mapping in expert_dag.py.
2. localTests-equivalent: test every implied conditional independence of the
   induced measured subgraph via partial correlation (Fisher z). With n~32k,
   effect size (|partial r|), not the p-value, is the decision criterion.
3. PC-stable at alpha in {0.01, 0.005, 0.001}, with and without tier
   background knowledge (LAYERS -> tiers; MH last).
4. FCI at the same alphas: latent-confounder-robust check (causal sufficiency
   is violated because 10 constructs are unmeasured).
5. Compare discovered CPDAG/PAG skeletons and orientations to the expert
   induced subgraph: precision/recall, SHD, v-structure agreement, and the two
   edge-difference tables.

All data are cross-sectional, area-level. Everything reported is ASSOCIATIONAL
structure. No causal claim beyond mental-health/CONCLUSIONS.md.

Deviation note: the canonical workflow is R (pcalg/bnlearn/dagitty). This
sandbox has no R/CRAN access, so the discovery engine is Python
(causal-learn PC/FCI; networkx for d-separation / the localTests basis). The
expert DAG remains primary; this is corroborating evidence only.
"""

from __future__ import annotations
import json
import io
import itertools
import warnings
import contextlib
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import norm

import expert_dag as ed

warnings.filterwarnings('ignore')
np.random.seed(0)

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / 'mental-health' / 'datasets' / 'merged_data.csv'
FP_FILE = HERE / 'fuel_poverty_lsoa.csv'   # DESNZ sub-regional LILEE (tidy)
ALPHAS = [0.01, 0.005, 0.001]
EFFECT_THRESHOLDS = [0.05, 0.10, 0.15]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def read_base_df() -> pd.DataFrame:
    """merged_data (LSOA-2011) with the external Fuel Poverty column merged in."""
    df = pd.read_csv(DATA).rename(columns={'Unnamed: 0': 'lsoa'})
    if FP_FILE.exists():
        fp = pd.read_csv(FP_FILE)[['lsoa', 'fuel_poor_pct']]
        df = df.merge(fp, on='lsoa', how='left')
    return df


def load_matrix(mh_col: str) -> pd.DataFrame:
    """Return a standardized measured-construct matrix (one col per construct)."""
    df = read_base_df()
    cols = {}
    for node, (col, _note, _sign) in ed.MEASURED.items():
        c = mh_col if node == 'MH' else col
        cols[node] = pd.to_numeric(df[c], errors='coerce')
    X = pd.DataFrame(cols)
    X = X[ed.MEASURED_NODES]          # stable column order
    X = X.dropna()
    # standardize (Fisher-z / PC use correlations; standardizing is harmless)
    X = (X - X.mean()) / X.std(ddof=0)
    return X


# ---------------------------------------------------------------------------
# Partial correlation (Fisher z)  -- localTests engine
# ---------------------------------------------------------------------------
def pcor(X: pd.DataFrame, x: str, y: str, Z: list[str]):
    n = len(X)
    if Z:
        A = np.column_stack([np.ones(n)] + [X[z].values for z in Z])
        bx, *_ = np.linalg.lstsq(A, X[x].values, rcond=None)
        by, *_ = np.linalg.lstsq(A, X[y].values, rcond=None)
        rx = X[x].values - A @ bx
        ry = X[y].values - A @ by
    else:
        rx = X[x].values - X[x].values.mean()
        ry = X[y].values - X[y].values.mean()
    r = float(np.corrcoef(rx, ry)[0, 1])
    r = max(min(r, 0.999999), -0.999999)
    k = len(Z)
    dof = n - k - 3
    z = 0.5 * np.log((1 + r) / (1 - r))
    se = 1.0 / np.sqrt(dof)
    p = float(2 * norm.sf(abs(z / se)))
    lo, hi = np.tanh(z - 1.96 * se), np.tanh(z + 1.96 * se)
    return r, p, float(lo), float(hi), dof


def implied_cis(G: nx.DiGraph):
    """One implied CI per non-adjacent pair, using a minimal d-separator.

    Mirrors dagitty's default localTests basis (one testable implication per
    missing edge)."""
    skel = {frozenset((u, v)) for u, v in G.to_undirected().edges()}
    out = []
    for u, v in itertools.combinations(sorted(G.nodes()), 2):
        if frozenset((u, v)) in skel:
            continue
        Z = _sep_set(G, u, v)
        if Z is None:
            continue
        out.append((u, v, sorted(Z)))
    return out


def _sep_set(G, u, v):
    """A valid d-separating set for non-adjacent u,v (minimal if available)."""
    try:
        Z = nx.find_minimal_d_separator(G, u, v)
        if Z is not None:
            return set(Z)
    except Exception:
        pass
    # fallback: parents of both (local Markov), verified by d-separation
    Z = (set(G.predecessors(u)) | set(G.predecessors(v))) - {u, v}
    try:
        if nx.is_d_separator(G, {u}, {v}, Z):
            return Z
    except Exception:
        pass
    return None


def run_localtests(X, G, full_dag=None):
    """Test implied CIs of the induced subgraph.

    Each implication is annotated with ``dconn_full_dag``: whether the same pair
    is d-CONNECTED given the same Z in the *full* 25-node expert DAG. A failing
    implication with dconn_full_dag=True is EXPECTED -- the induced subgraph only
    implied independence because it cut a latent path (e.g. through the
    Neighbourhood or Area-History hubs). Failures with dconn_full_dag=False are
    the genuine tensions to scrutinise (proxy/measurement, spatial aggregation,
    or a candidate missing edge)."""
    rows = []
    for u, v, Z in implied_cis(G):
        r, p, lo, hi, dof = pcor(X, u, v, Z)
        dconn = None
        if full_dag is not None:
            dconn = not nx.is_d_separator(full_dag, {u}, {v}, set(Z))
        rows.append(dict(x=u, y=v, given='{' + ','.join(Z) + '}' if Z else '{}',
                         n_cond=len(Z), estimate=r, abs_estimate=abs(r),
                         p_value=p, ci_lo=lo, ci_hi=hi, dof=dof,
                         dconn_full_dag=dconn))
    res = pd.DataFrame(rows).sort_values('abs_estimate', ascending=False)
    return res.reset_index(drop=True)


# ---------------------------------------------------------------------------
# PC / FCI  (causal-learn)  + edge extraction
# ---------------------------------------------------------------------------
def _endpoint(ep):
    from causallearn.graph.Endpoint import Endpoint
    if ep == Endpoint.TAIL:
        return 't'
    if ep == Endpoint.ARROW:
        return 'a'
    if ep == Endpoint.CIRCLE:
        return 'c'
    return '?'


def edges_from_general_graph(edge_list, node_names):
    """Return list of dicts: a, b, mark_a, mark_b, kind, skeleton frozenset."""
    out = []
    for e in edge_list:
        n1 = e.get_node1().get_name()
        n2 = e.get_node2().get_name()
        m1 = _endpoint(e.get_endpoint1())   # mark at n1
        m2 = _endpoint(e.get_endpoint2())   # mark at n2
        # classify
        marks = (m1, m2)
        if marks == ('t', 'a'):
            kind, a, b = 'directed', n1, n2          # n1 -> n2
        elif marks == ('a', 't'):
            kind, a, b = 'directed', n2, n1          # n2 -> n1
        elif marks == ('t', 't'):
            kind, a, b = 'undirected', n1, n2
        elif marks == ('a', 'a'):
            kind, a, b = 'bidirected', n1, n2
        elif marks == ('c', 'a'):
            kind, a, b = 'partial', n1, n2           # n1 o-> n2
        elif marks == ('a', 'c'):
            kind, a, b = 'partial', n2, n1           # n2 o-> n1
        elif marks == ('c', 'c'):
            kind, a, b = 'nondirected', n1, n2       # o-o
        elif marks == ('c', 't'):
            kind, a, b = 'partial_tail', n2, n1
        elif marks == ('t', 'c'):
            kind, a, b = 'partial_tail', n1, n2
        else:
            kind, a, b = 'other', n1, n2
        out.append(dict(a=a, b=b, kind=kind,
                        disp=_disp(n1, n2, m1, m2),
                        skel=frozenset((n1, n2))))
    return out


def _disp(n1, n2, m1, m2):
    left = {'t': '', 'a': '<', 'c': 'o'}[m1]
    right = {'t': '', 'a': '>', 'c': 'o'}[m2]
    return f'{n1} {left}-{right} {n2}'


def build_tier_bk(cg_nodes):
    from causallearn.utils.PCUtils.BackgroundKnowledge import BackgroundKnowledge
    tiers = ed.measured_tiers()
    # put MH strictly last (own tier beyond the max)
    maxt = max(tiers.values())
    tiers = dict(tiers)
    tiers['MH'] = maxt + 1
    bk = BackgroundKnowledge()
    name2node = {nd.get_name(): nd for nd in cg_nodes}
    for name, t in tiers.items():
        bk.add_node_to_tier(name2node[name], t)
    return bk


def run_pc(X, alpha, use_tiers):
    from causallearn.search.ConstraintBased.PC import pc
    labels = list(X.columns)
    data = X.values.astype(float)
    bk = None
    with contextlib.redirect_stdout(io.StringIO()):
        if use_tiers:
            # need node objects; do a throwaway to get CausalGraph node handles
            cg0 = pc(data, alpha, 'fisherz', stable=True, node_names=labels,
                     show_progress=False)
            bk = build_tier_bk(cg0.G.get_nodes())
        cg = pc(data, alpha, 'fisherz', stable=True, background_knowledge=bk,
                node_names=labels, show_progress=False)
    return edges_from_general_graph(cg.G.get_graph_edges(), labels)


def run_fci(X, alpha):
    from causallearn.search.ConstraintBased.FCI import fci
    labels = list(X.columns)
    data = X.values.astype(float)
    with contextlib.redirect_stdout(io.StringIO()):
        g, edge_list = fci(data, 'fisherz', alpha, verbose=False,
                           show_progress=False, node_names=labels)
    return edges_from_general_graph(edge_list, labels)


# ---------------------------------------------------------------------------
# Comparison to expert induced subgraph
# ---------------------------------------------------------------------------
def expert_structures(G):
    skel = {frozenset((u, v)) for u, v in G.to_undirected().edges()}
    directed = {(u, v) for u, v in G.edges()}
    # unshielded colliders x->z<-y with x,y non-adjacent
    colliders = set()
    for z in G.nodes():
        pars = list(G.predecessors(z))
        for x, y in itertools.combinations(pars, 2):
            if not (G.has_edge(x, y) or G.has_edge(y, x)):
                colliders.add((frozenset((x, y)), z))
    return skel, directed, colliders


def discovered_structures(edges):
    skel = {e['skel'] for e in edges}
    directed = set()
    colliders_arrowsinto = {}
    for e in edges:
        if e['kind'] in ('directed',):
            directed.add((e['a'], e['b']))
    # colliders in a CPDAG/PAG: node z with two arrowheads into it from
    # non-adjacent x,y (directed or partial both count as arrow into z)
    arrows_into = {}
    for e in edges:
        # arrowhead at b?
        a, b, kind = e['a'], e['b'], e['kind']
        if kind in ('directed', 'partial'):     # a *-> b
            arrows_into.setdefault(b, set()).add(a)
        if kind == 'bidirected':
            arrows_into.setdefault(a, set()).add(b)
            arrows_into.setdefault(b, set()).add(a)
    colliders = set()
    skelpairs = skel
    for z, srcs in arrows_into.items():
        for x, y in itertools.combinations(sorted(srcs), 2):
            if frozenset((x, y)) not in skelpairs:
                colliders.add((frozenset((x, y)), z))
    return skel, directed, colliders


def compare(expert_G, edges):
    e_skel, e_dir, e_coll = expert_structures(expert_G)
    d_skel, d_dir, d_coll = discovered_structures(edges)

    tp = len(d_skel & e_skel)
    prec = tp / len(d_skel) if d_skel else float('nan')
    rec = tp / len(e_skel) if e_skel else float('nan')
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else float('nan')

    # SHD (CPDAG/PAG vs expert DAG): missing + extra + orientation-mismatch on
    # common skeleton edges. A discovered edge matches an expert a->b only if it
    # is exactly a->b (directed); undirected/partial/bidirected/reversed = 1.
    missing = e_skel - d_skel
    extra = d_skel - e_skel
    common = e_skel & d_skel
    disc_dir = {(e['a'], e['b']): e['kind'] for e in edges}
    orient_mismatch = 0
    for pair in common:
        u, v = tuple(pair)
        exp = (u, v) if (u, v) in e_dir else (v, u)
        matched = disc_dir.get(exp) == 'directed'
        if not matched:
            orient_mismatch += 1
    shd = len(missing) + len(extra) + orient_mismatch

    # v-structures
    vtp = len(d_coll & e_coll)
    vprec = vtp / len(d_coll) if d_coll else float('nan')
    vrec = vtp / len(e_coll) if e_coll else float('nan')

    return dict(
        n_expert_edges=len(e_skel), n_discovered_edges=len(d_skel),
        skeleton_tp=tp, skeleton_precision=prec, skeleton_recall=rec, skeleton_f1=f1,
        shd=shd, orient_mismatch=orient_mismatch,
        n_missing=len(missing), n_extra=len(extra),
        n_expert_vstruct=len(e_coll), n_discovered_vstruct=len(d_coll),
        vstruct_tp=vtp, vstruct_precision=vprec, vstruct_recall=vrec,
        missing_edges=sorted(tuple(sorted(p)) for p in missing),
        extra_edges=sorted(tuple(sorted(p)) for p in extra),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ed.verify_counts()
    G = ed.induced_measured_digraph()
    print('\nInduced subgraph:', G.number_of_nodes(), 'nodes,',
          G.number_of_edges(), 'edges')
    if 'FP' in ed.MEASURED_NODES:
        has_path = 'FP' in list(G.successors('HEE'))
        print('Note: Fuel Poverty is now measured -> HEE has a measured child '
              f'(HEE->FP: {has_path}); the induced subgraph now contains a '
              'directed HEE->FP->MH mediated path for the first time.')
    else:
        print('Note: HEE has no measured child (all HEE mediators IEQ/FP/NO are '
              'unmeasured) -> the measured subgraph contains NO directed HEE->MH '
              'path; HEE and MH are connected only through common causes.')

    results = {'counts': ed.verify_counts(verbose=False), 'runs': {}}

    for mh_label, mh_col in [('primary_DepRate', ed.MEASURED['MH'][0]),
                             ('robustness_SAMHI', ed.MH_ROBUSTNESS[0])]:
        X = load_matrix(mh_col)
        print(f'\n############ MH = {mh_label} ({mh_col}) | n={len(X)} ############')
        block = {'n': len(X)}

        # --- localTests ---
        lt = run_localtests(X, G, full_dag=ed.expert_digraph())
        lt.to_csv(HERE / f'localtests_{mh_label}.csv', index=False)
        n_ci = len(lt)
        fails = {f'ge_{t}': int((lt.abs_estimate >= t).sum()) for t in EFFECT_THRESHOLDS}
        f10 = lt[lt.abs_estimate >= 0.10]
        n_lat = int(f10.dconn_full_dag.sum())
        block['localtests'] = {
            'n_implications': n_ci, 'failures': fails,
            'max_abs_r': float(lt.abs_estimate.max()),
            'median_abs_r': float(lt.abs_estimate.median()),
            'fail_ge_0.10': len(f10),
            'fail_explained_by_latent': n_lat,
            'fail_genuine_tension': len(f10) - n_lat}
        print(f'  localTests: {n_ci} implied CIs; '
              f'|r|>=0.10: {fails["ge_0.1"]}; |r|>=0.15: {fails["ge_0.15"]}; '
              f'max|r|={lt.abs_estimate.max():.3f}')
        print(f'    of the {len(f10)} failures at |r|>=0.10: {n_lat} '
              f'({100*n_lat/max(len(f10),1):.0f}%) are d-connected in the FULL '
              f'25-node DAG (latent path cut -> expected); '
              f'{len(f10)-n_lat} are genuine tensions.')
        print('  Top 8 violated implications (by |partial r|):')
        for _, r in lt.head(8).iterrows():
            tag = 'latent-cut' if r.dconn_full_dag else 'GENUINE'
            print(f'    {r.x:>3} _||_ {r.y:<3} | {r.given:<28} r={r.estimate:+.3f} [{tag}]')

        # --- PC / FCI grid ---
        block['pc'] = {}
        block['fci'] = {}
        pc_edge_rows, fci_edge_rows = [], []
        do_alphas = ALPHAS if mh_label == 'primary_DepRate' else [0.01]
        for alpha in do_alphas:
            for use_tiers in (False, True):
                tag = f'pc_a{alpha}_{"tier" if use_tiers else "notier"}'
                edges = run_pc(X, alpha, use_tiers)
                cmp = compare(G, edges)
                block['pc'][tag] = cmp
                for e in edges:
                    pc_edge_rows.append(dict(config=tag, alpha=alpha,
                                             tiers=use_tiers, **{k: e[k] for k in ('a', 'b', 'kind', 'disp')}))
                print(f'  [{tag}] edges={cmp["n_discovered_edges"]} '
                      f'skelP={cmp["skeleton_precision"]:.2f} skelR={cmp["skeleton_recall"]:.2f} '
                      f'SHD={cmp["shd"]} vstructR={cmp["vstruct_recall"]:.2f}')
            # FCI (latent-robust)
            tag = f'fci_a{alpha}'
            fedges = run_fci(X, alpha)
            fcmp = compare(G, fedges)
            block['fci'][tag] = fcmp
            for e in fedges:
                fci_edge_rows.append(dict(config=tag, alpha=alpha,
                                          **{k: e[k] for k in ('a', 'b', 'kind', 'disp')}))
            n_bi = sum(1 for e in fedges if e['kind'] == 'bidirected')
            n_circ = sum(1 for e in fedges if e['kind'] in ('partial', 'nondirected'))
            print(f'  [{tag}] edges={fcmp["n_discovered_edges"]} '
                  f'skelP={fcmp["skeleton_precision"]:.2f} skelR={fcmp["skeleton_recall"]:.2f} '
                  f'SHD={fcmp["shd"]} bidirected(<->)={n_bi} circle-marks={n_circ}')

        pd.DataFrame(pc_edge_rows).to_csv(HERE / f'pc_edges_{mh_label}.csv', index=False)
        pd.DataFrame(fci_edge_rows).to_csv(HERE / f'fci_edges_{mh_label}.csv', index=False)
        results['runs'][mh_label] = block

    with open(HERE / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print('\nWrote results.json + per-run CSVs to', HERE)
    _write_mapping_outputs()
    _write_tex(results)


def _write_mapping_outputs():
    rows = []
    for node in ed.ALL_NODES:
        if node in ed.MEASURED:
            col, note, sign = ed.MEASURED[node]
            rows.append(dict(node=node, full_name=ed.FULL_NAMES[node],
                             status='measured', column=col, note=note))
        else:
            rows.append(dict(node=node, full_name=ed.FULL_NAMES[node],
                             status='excluded', column='',
                             note=ed.EXCLUDED.get(node, '')))
    pd.DataFrame(rows).to_csv(HERE / 'variable_mapping.csv', index=False)


def _write_tex(results):
    """Auto-generate a tex-ready edge-difference table for the primary run
    (PC no-tier and tier at alpha=0.01) + a metrics summary table."""
    prim = results['runs']['primary_DepRate']
    fn = ed.FULL_NAMES
    Gm = ed.induced_measured_digraph()
    nnodes, nedges = Gm.number_of_nodes(), Gm.number_of_edges()

    def nm(x):
        return fn.get(x, x).replace('&', '\\&')

    lines = []
    lines.append('% Auto-generated by causal_discovery_validation.py -- do not hand-edit.')
    lines.append('% Robustness section for HEE-MH-paper-1: causal-discovery validation.')
    lines.append('')
    # ---- metrics table ----
    lines.append('\\begin{table}[htbp]\\centering')
    lines.append('\\caption{Agreement between the PC-stable / FCI discovered graphs and the '
                 f'induced measured subgraph of the expert DAG ({nnodes} nodes, {nedges} directed edges; '
                 'MH = QOF depression). Skeleton precision/recall are for undirected adjacency; '
                 'SHD counts missing, extra, and orientation-mismatched edges.}')
    lines.append('\\label{tab:cd-metrics}')
    lines.append('\\begin{tabular}{@{}lrrrrr@{}}')
    lines.append('\\toprule')
    lines.append('Configuration & Edges & Skel.\\ P & Skel.\\ R & SHD & V-struct R \\\\')
    lines.append('\\midrule')
    order = [('pc', 'pc_a0.01_notier', 'PC $\\alpha{=}0.01$, no tiers'),
             ('pc', 'pc_a0.01_tier', 'PC $\\alpha{=}0.01$, tiers'),
             ('pc', 'pc_a0.005_notier', 'PC $\\alpha{=}0.005$, no tiers'),
             ('pc', 'pc_a0.005_tier', 'PC $\\alpha{=}0.005$, tiers'),
             ('pc', 'pc_a0.001_notier', 'PC $\\alpha{=}0.001$, no tiers'),
             ('pc', 'pc_a0.001_tier', 'PC $\\alpha{=}0.001$, tiers'),
             ('fci', 'fci_a0.01', 'FCI $\\alpha{=}0.01$'),
             ('fci', 'fci_a0.005', 'FCI $\\alpha{=}0.005$'),
             ('fci', 'fci_a0.001', 'FCI $\\alpha{=}0.001$')]
    for grp, tag, lab in order:
        c = prim[grp].get(tag)
        if not c:
            continue
        lines.append(f'{lab} & {c["n_discovered_edges"]} & {c["skeleton_precision"]:.2f} & '
                     f'{c["skeleton_recall"]:.2f} & {c["shd"]} & {c["vstruct_recall"]:.2f} \\\\')
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    lines.append('')

    # ---- edge-difference tables (PC no-tier alpha=0.01) ----
    c = prim['pc']['pc_a0.01_notier']
    lines.append('\\begin{table}[htbp]\\centering')
    lines.append('\\caption{Edge-level disagreement between the expert induced subgraph and the '
                 'PC-stable CPDAG ($\\alpha{=}0.01$, no tiers, MH = QOF depression). '
                 '(a) expert adjacencies not recovered; (b) recovered adjacencies absent from the '
                 'expert DAG. Candidate explanations are given in the accompanying markdown.}')
    lines.append('\\label{tab:cd-edgediff}')
    lines.append('\\begin{tabular}{@{}ll@{}}')
    lines.append('\\toprule')
    lines.append('\\multicolumn{2}{@{}l}{\\textit{(a) In expert subgraph, not recovered}} \\\\')
    lines.append('\\midrule')
    for u, v in c['missing_edges']:
        lines.append(f'{nm(u)} & {nm(v)} \\\\')
    lines.append('\\midrule')
    lines.append('\\multicolumn{2}{@{}l}{\\textit{(b) Recovered, absent from expert subgraph}} \\\\')
    lines.append('\\midrule')
    for u, v in c['extra_edges']:
        lines.append(f'{nm(u)} & {nm(v)} \\\\')
    lines.append('\\bottomrule')
    lines.append('\\end{tabular}')
    lines.append('\\end{table}')
    (HERE / 'causal_discovery_edges.tex').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
