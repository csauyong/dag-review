#!/usr/bin/env python3
"""
Sensitivity check: per-construct COMPOSITE nodes (multi-column) instead of a
single representative column, for the HEE -> MH DAG discovery validation.

Each construct is collapsed to the first principal component of its measured
column block (standardized, sign-aligned to an anchor column for readability).
This keeps node = construct (so the graph stays comparable to the expert DAG)
while using the richer multi-column operationalisation from the adjustment-set
analysis and reducing single-proxy measurement error.

Compared against the single-column run in causal_discovery_validation.py.
Associational structure only; no causal claim beyond CONCLUSIONS.md.
"""
from __future__ import annotations
import numpy as np, pandas as pd
from sklearn.decomposition import PCA

import expert_dag as ed
from causal_discovery_validation import (
    DATA, read_base_df, run_localtests, run_pc, run_fci, compare)

# construct -> (list of columns, anchor column for sign alignment)
MULTI = {
    'HEE': (['RATING_MEDIAN_100', 'RATING_GTEQ_C'], 'RATING_MEDIAN_100'),
    'MH':  (['Dep rate'], 'Dep rate'),
    'EC':  (['Income Score (rate)', 'Employment Score (rate)'], 'Income Score (rate)'),
    'ED':  (['Education, Skills and Training Score', 'Adult Skills Sub-domain Score'],
            'Education, Skills and Training Score'),
    'H':   (['FLOOR_AREA_MEDIAN', 'mean_internal_area', 'BUILT_BEFORE_1950',
             'prop_detached', 'prop_terraced', 'prop_semi_detached', 'Flats rate',
             'prop_era_early_century', 'prop_era_mid_century', 'prop_era_period'],
            'BUILT_BEFORE_1950'),
    'T':   (['rented'], 'rented'),
    'D':   (['65+', 'Female_ratio', 'white_proportion'], '65+'),
    'U':   (['urban_rural_flag', 'pop_density'], 'pop_density'),
    'C':   (['DJF_w', 'JJA_w'], 'DJF_w'),
    'AP':  (['no2_mean', 'pm10_mean', 'so2_mean'], 'no2_mean'),
    'GS':  (['green_act', 'green_pas', 'blue_dist'], 'green_act'),
    'O':   (['hhsize_ave'], 'hhsize_ave'),
    'NS':  (['Crime Score'], 'Crime Score'),
    'A':   (['gpp_dist', 'ed_dist', 'dent_dist', 'pharm_dist', 'leis_dist'], 'gpp_dist'),
    'PH':  (['Health Deprivation and Disability Score', 'Asthma rate', 'CHD rate',
             'COPD rate', 'Cancer rate'], 'Health Deprivation and Disability Score'),
    'FP':  (['fuel_poor_pct'], 'fuel_poor_pct'),   # external DESNZ LILEE (single col)
}


def composite_matrix(mh_cols=None):
    df = read_base_df()
    out = {}
    for node, (cols, anchor) in MULTI.items():
        block = df[cols].apply(pd.to_numeric, errors='coerce')
        block = (block - block.mean()) / block.std(ddof=0)
        block = block.dropna()
        if block.shape[1] == 1:
            comp = block.iloc[:, 0].values
        else:
            comp = PCA(n_components=1, random_state=0).fit_transform(block.values)[:, 0]
            # sign-align to anchor so PC1 increases with the anchor column
            if np.corrcoef(comp, block[anchor].values)[0, 1] < 0:
                comp = -comp
        s = pd.Series(comp, index=block.index)
        out[node] = s
    X = pd.DataFrame(out).dropna()
    X = X[ed.MEASURED_NODES]
    return (X - X.mean()) / X.std(ddof=0)


def variance_explained():
    df = read_base_df()
    print('Construct  #cols  PC1 var-explained')
    for node, (cols, _a) in MULTI.items():
        if len(cols) == 1:
            print(f'  {node:<4} {len(cols):>4}   (single column)')
            continue
        b = df[cols].apply(pd.to_numeric, errors='coerce')
        b = ((b - b.mean()) / b.std(ddof=0)).dropna()
        ev = PCA(n_components=1, random_state=0).fit(b.values).explained_variance_ratio_[0]
        print(f'  {node:<4} {len(cols):>4}   {ev:0.2f}')


def main():
    G = ed.induced_measured_digraph()
    full = ed.expert_digraph()
    print('=== Composite (multi-column) sensitivity check ===\n')
    variance_explained()
    X = composite_matrix()
    print(f'\nn = {len(X)} LSOAs; nodes = {list(X.columns)}\n')

    lt = run_localtests(X, G, full_dag=full)
    f10 = lt[lt.abs_estimate >= 0.10]
    n_lat = int(f10.dconn_full_dag.sum())
    print(f'localTests: {len(lt)} implications; |r|>=0.10: {len(f10)}; '
          f'latent-cut: {n_lat} ({100*n_lat/max(len(f10),1):.0f}%); '
          f'genuine tensions: {len(f10)-n_lat}; max|r|={lt.abs_estimate.max():.3f}')
    print('  genuine tensions:',
          [f'{r.x}-{r.y}({r.estimate:+.2f})' for _, r in
           f10[~f10.dconn_full_dag].sort_values("abs_estimate", ascending=False).iterrows()])

    for tag, edges in [('PC notier a0.01', run_pc(X, 0.01, False)),
                       ('PC tier   a0.01', run_pc(X, 0.01, True)),
                       ('FCI       a0.01', run_fci(X, 0.01))]:
        c = compare(G, edges)
        nb = sum(1 for e in edges if e['kind'] == 'bidirected')
        hee_mh = any(e['skel'] == frozenset(('HEE', 'MH')) for e in edges)
        print(f'  [{tag}] edges={c["n_discovered_edges"]} skelP={c["skeleton_precision"]:.2f} '
              f'skelR={c["skeleton_recall"]:.2f} SHD={c["shd"]} '
              f'vstructR={c["vstruct_recall"]:.2f} bidirected={nb} HEE-MH_adjacent={hee_mh}')

    lt.to_csv('localtests_composite_DepRate.csv', index=False)
    print('\nWrote localtests_composite_DepRate.csv')


if __name__ == '__main__':
    main()
