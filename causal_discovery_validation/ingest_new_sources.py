#!/usr/bin/env python3
"""
Ingest newly-downloaded open datasets for currently-unmeasured DAG constructs,
join them onto the LSOA-2011 frame, and re-run the discovery validation on the
ENLARGED measured subgraph.

See data_expansion.md for the verified sources. The analysis sandbox has no
internet, so this script does NOT download anything: download the files into
`mental-health/datasets/` yourself, then point the SOURCES registry below at
them.

Usage
-----
  # 1. Inspect a downloaded file to find the right sheet / columns:
  python3 ingest_new_sources.py --inspect \
      "../../mental-health/datasets/Sub-regional_fuel_poverty_statistics_2023.xlsx"

  # 2. Configure SOURCES below (set enabled=True, fill sheet/col), then:
  python3 ingest_new_sources.py

Everything is associational, area-level, cross-sectional. No causal claim beyond
mental-health/CONCLUSIONS.md; these additions strengthen the triangulation only.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx

import expert_dag as ed
from causal_discovery_validation import (
    DATA, run_localtests, run_pc, run_fci, compare)

DATASETS = DATA.parent
LSOA11_RE = re.compile(r'^E0[12]\d{6}$')     # England LSOA/MSOA-style codes

# ---------------------------------------------------------------------------
# Registry of new sources.  Fill these in after downloading + --inspect.
# `kind`: 'fuel_poverty' uses the concrete parser; 'generic' uses sheet/code/val.
# `vintage`: '2011' joins directly; '2021' is harmonised via the ONS lookup.
# ---------------------------------------------------------------------------
SOURCES = {
    # FP (Fuel Poverty) is now a BUILT-IN measured node: it was tidied to
    # fuel_poverty_lsoa.csv and is loaded directly by causal_discovery_validation.py
    # (read_base_df). It is therefore NOT re-ingested here. This registry is for
    # the remaining not-yet-obtained sources (Policy, Digital, Noise). The
    # fuel_poverty parser below is kept as a worked example.
    'P': dict(
        enabled=False,
        kind='generic',
        path=DATASETS / 'household_energy_efficiency_measures.csv',
        sheet=0, code_col='LSOA code', value_col='pct_measures',
        vintage='2021',
        higher_is='more scheme uptake (+)',
    ),
    'DC': dict(
        enabled=False,
        kind='generic',
        path=DATASETS / 'connected_nations_lsoa.csv',
        sheet=0, code_col='lsoa11', value_col='median_download_mbps',
        vintage='2011',
        higher_is='more digital capital (+)',
    ),
    # NO (Defra noise) needs a GIS areal-interpolation step first; add its
    # LSOA-aggregated output here as a 'generic' source once computed.
}

# ONS LSOA-2011 -> LSOA-2021 best-fit lookup (download into datasets/ if needed).
LSOA_LOOKUP = DATASETS / 'LSOA2011_to_LSOA2021_lookup.csv'


# ---------------------------------------------------------------------------
# Inspection helper
# ---------------------------------------------------------------------------
def inspect(path):
    path = Path(path)
    print(f'Inspecting {path.name}')
    if path.suffix.lower() in ('.xlsx', '.xls', '.ods'):
        xl = pd.ExcelFile(path)
        print('sheets:', xl.sheet_names)
        for sh in xl.sheet_names:
            df = xl.parse(sh, header=None, nrows=25)
            codecols = [c for c in df.columns
                        if df[c].astype(str).str.match(LSOA11_RE).any()]
            print(f'  [{sh}] shape~{df.shape}; columns containing LSOA codes: {codecols}')
            if codecols:
                hdr = df.head(12).to_string()
                print('   preview:\n', hdr[:1200])
    else:
        df = pd.read_csv(path, nrows=25)
        print('columns:', list(df.columns))
        print(df.head(8).to_string())


# ---------------------------------------------------------------------------
# Concrete parser: DESNZ sub-regional fuel poverty
# ---------------------------------------------------------------------------
def parse_fuel_poverty(cfg):
    """Return Series indexed by LSOA code -> proportion of households fuel poor."""
    xl = pd.ExcelFile(cfg['path'])
    sheet = cfg['sheet']
    if sheet is None:                        # pick the sheet with LSOA codes
        for sh in xl.sheet_names:
            probe = xl.parse(sh, header=None, nrows=60).astype(str)
            if probe.apply(lambda c: c.str.match(LSOA11_RE).any()).any():
                sheet = sh
                break
    raw = xl.parse(sheet, header=None)
    # find header row: the row above the first LSOA-code row
    code_col = None
    hdr_row = None
    for r in range(min(40, len(raw))):
        for c in raw.columns:
            if LSOA11_RE.match(str(raw.iat[r, c])):
                code_col, hdr_row = c, r - 1
                break
        if code_col is not None:
            break
    df = xl.parse(sheet, header=hdr_row)
    df.columns = [str(c).strip() for c in df.columns]
    code_name = df.columns[code_col]
    # proportion column: header mentioning 'propor' / '%' / 'LILEE' + 'fuel poor'
    val = cfg['value_col']
    if val is None:
        cands = [c for c in df.columns
                 if re.search(r'propor|percentage|%', str(c), re.I)
                 and re.search(r'fuel', str(c), re.I)]
        val = cands[0] if cands else [c for c in df.columns
                                      if re.search(r'propor|%', str(c), re.I)][0]
    df = df[[code_name, val]].dropna()
    df = df[df[code_name].astype(str).str.match(LSOA11_RE)]
    s = pd.to_numeric(df[val], errors='coerce')
    s.index = df[code_name].astype(str)
    print(f'  FP: sheet={sheet!r} code={code_name!r} value={val!r} n={s.notna().sum()}')
    return s.dropna()


def parse_generic(cfg):
    p = Path(cfg['path'])
    if p.suffix.lower() in ('.xlsx', '.xls', '.ods'):
        df = pd.read_excel(p, sheet_name=cfg['sheet'])
    else:
        df = pd.read_csv(p)
    df.columns = [str(c).strip() for c in df.columns]
    s = pd.to_numeric(df[cfg['value_col']], errors='coerce')
    s.index = df[cfg['code_col']].astype(str)
    return s.dropna()


# ---------------------------------------------------------------------------
# LSOA 2021 -> 2011 harmonisation (best-fit; rates carried across split/merge)
# ---------------------------------------------------------------------------
def harmonise_to_2011(series, vintage):
    if vintage == '2011':
        return series
    if not LSOA_LOOKUP.exists():
        raise FileNotFoundError(
            f'{LSOA_LOOKUP.name} not found. Download the ONS LSOA(2011)->LSOA(2021) '
            'best-fit lookup into datasets/, or use the 2021-data release on LSOA-2011.')
    lk = pd.read_csv(LSOA_LOOKUP, dtype=str)
    # expect columns like LSOA11CD, LSOA21CD (names vary by release)
    c11 = [c for c in lk.columns if re.search(r'lsoa.*11.*cd', c, re.I)][0]
    c21 = [c for c in lk.columns if re.search(r'lsoa.*21.*cd', c, re.I)][0]
    m = lk[[c11, c21]].copy()
    m['val'] = m[c21].map(series)            # value is a rate -> carry to each 2011 child
    out = m.dropna(subset=['val']).groupby(c11)['val'].mean()
    return out


# ---------------------------------------------------------------------------
# Build enlarged matrix + induced subgraph, then re-run discovery
# ---------------------------------------------------------------------------
def base_frame(mh_col):
    df = pd.read_csv(DATA)
    df = df.rename(columns={'Unnamed: 0': 'lsoa11'})
    cols = {'lsoa11': df['lsoa11'].astype(str)}
    for node, (col, _n, _s) in ed.MEASURED.items():
        c = mh_col if node == 'MH' else col
        cols[node] = pd.to_numeric(df[c], errors='coerce')
    return pd.DataFrame(cols).set_index('lsoa11')


def enlarged_induced_subgraph(measured_nodes):
    g = nx.DiGraph()
    g.add_nodes_from(measured_nodes)
    for a, b in ed.RAW_EDGES:
        if a in measured_nodes and b in measured_nodes:
            g.add_edge(a, b)
    return g


def main(mh_col='Dep rate'):
    active = {k: v for k, v in SOURCES.items() if v.get('enabled')}
    if not active:
        print('No sources enabled. Edit SOURCES (set enabled=True) after '
              'downloading + inspecting the files. See data_expansion.md.')
        return

    X = base_frame(mh_col)
    added = []
    for node, cfg in active.items():
        s = (parse_fuel_poverty if cfg['kind'] == 'fuel_poverty' else parse_generic)(cfg)
        s = harmonise_to_2011(s, cfg['vintage'])
        X[node] = X.index.map(s)
        added.append(node)
        print(f'  added {node} ({ed.FULL_NAMES[node]}): '
              f'{X[node].notna().mean()*100:.1f}% LSOA coverage')

    measured = ed.MEASURED_NODES + added
    X = X[measured].dropna()
    X = (X - X.mean()) / X.std(ddof=0)
    G = enlarged_induced_subgraph(measured)
    print(f'\nEnlarged subgraph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges'
          f' | n={len(X)}')
    print('New induced edges involving added nodes:',
          [f'{u}->{v}' for u, v in G.edges() if u in added or v in added])

    lt = run_localtests(X, G, full_dag=ed.expert_digraph())
    f10 = lt[lt.abs_estimate >= 0.10]
    print(f'localTests: {len(lt)} implications; |r|>=0.10: {len(f10)}; '
          f'latent-cut: {int(f10.dconn_full_dag.sum())}')
    for tag, edges in [('PC notier a0.01', run_pc(X, 0.01, False)),
                       ('PC tier   a0.01', run_pc(X, 0.01, True)),
                       ('FCI       a0.01', run_fci(X, 0.01))]:
        c = compare(G, edges)
        nb = sum(1 for e in edges if e['kind'] == 'bidirected')
        # is any HEE mediator path recovered? report HEE and each added node's nbrs
        print(f'  [{tag}] edges={c["n_discovered_edges"]} skelP={c["skeleton_precision"]:.2f} '
              f'skelR={c["skeleton_recall"]:.2f} SHD={c["shd"]} bidirected={nb}')
    lt.to_csv('localtests_enlarged.csv', index=False)
    print('\nWrote localtests_enlarged.csv')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--inspect', metavar='FILE', help='list sheets/columns of a file')
    ap.add_argument('--mh', default='Dep rate', help='MH outcome column')
    a = ap.parse_args()
    if a.inspect:
        inspect(a.inspect)
    else:
        main(a.mh)
