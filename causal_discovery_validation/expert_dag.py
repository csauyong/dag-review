#!/usr/bin/env python3
"""
Expert DAG definition + measured-variable mapping for the causal-discovery
validation of the HEE -> MH DAG (robustness section for HEE-MH-paper-1).

The canonical DAG is the ``rawEdges`` array in ``../index.html`` (the edge list
used to render the interactive DAG). It is transcribed verbatim below. The
canonical file is never edited; the induced measured subgraph is built in memory.

Node schema (25 constructs) mirrors ``../node_table.tex``; edge rationales/refs
live in ``../edge_table.tex``. This module is the single source of truth for the
Python discovery pipeline in ``causal_discovery_validation.py``.

Everything here is associational structure over cross-sectional, area-level
(LSOA) data. No causal claim beyond mental-health/CONCLUSIONS.md is implied.
"""

from __future__ import annotations
import networkx as nx

# ---------------------------------------------------------------------------
# 1. Canonical expert DAG  (verbatim from rawEdges in ../index.html)
# ---------------------------------------------------------------------------
RAW_EDGES = [
    ('ED', 'EC'), ('ED', 'MH'), ('ED', 'PH'),
    ('EC', 'HEE'), ('EC', 'MH'), ('EC', 'PH'), ('EC', 'H'), ('EC', 'T'),
    ('EC', 'O'), ('EC', 'P'), ('EC', 'N'), ('EC', 'SC'), ('EC', 'DC'), ('EC', 'SA'),
    ('U', 'N'), ('U', 'P'), ('U', 'SI'), ('U', 'EC'), ('U', 'ED'),
    ('U', 'HEE'), ('U', 'SC'), ('U', 'DC'),
    ('U_AH', 'N'), ('U_AH', 'EC'), ('U_AH', 'ED'), ('U_AH', 'PH'),
    ('U_AH', 'T'), ('U_AH', 'SC'),
    ('N', 'AP'), ('N', 'GS'), ('N', 'A'), ('N', 'NS'), ('N', 'H'),
    ('N', 'NO'), ('N', 'SC'),
    ('NS', 'MH'), ('NS', 'PH'), ('NS', 'SI'),
    ('NS', 'SC'), ('NS', 'SA'),
    ('P', 'HEE'),
    ('D', 'MH'), ('D', 'H'), ('D', 'O'), ('D', 'EC'), ('D', 'ED'),
    ('H', 'HEE'), ('H', 'PH'), ('H', 'IEQ'), ('H', 'SI'),
    ('T', 'MH'), ('T', 'HEE'),
    ('O', 'IEQ'), ('O', 'MH'),
    ('C', 'HEE'), ('C', 'H'), ('C', 'MH'), ('C', 'IEQ'),
    ('AP', 'MH'), ('AP', 'PH'), ('AP', 'IEQ'),
    ('GS', 'MH'), ('GS', 'PH'), ('GS', 'IEQ'), ('GS', 'AP'),
    ('SI', 'MH'), ('A', 'MH'), ('A', 'PH'),
    ('HEE', 'IEQ'), ('HEE', 'NO'),
    ('IEQ', 'MH'), ('IEQ', 'PH'),
    ('NO', 'MH'), ('NO', 'PH'), ('NO', 'IEQ'),
    ('SC', 'MH'), ('SC', 'SI'), ('SC', 'SA'),
    ('DC', 'SI'), ('DC', 'MH'),
    ('SA', 'MH'), ('SA', 'PH'),
    ('PH', 'MH'),
    ('HEE', 'FP'), ('EC', 'FP'), ('C', 'FP'),
    ('FP', 'MH'), ('FP', 'PH'), ('FP', 'IEQ'),
]

# Full names (verbatim from FULL_NAMES in ../index.html)
FULL_NAMES = {
    'U_AH': 'Unobserved Area History', 'D': 'Demographics',
    'EC': 'Economic Capital', 'ED': 'Education',
    'U': 'Urbanicity', 'C': 'Climate',
    'N': 'Neighbourhood', 'P': 'Policy Scheme Access',
    'HEE': 'Home Energy Efficiency', 'H': 'Housing Characteristics',
    'T': 'Tenure', 'O': 'Overcrowding',
    'NS': 'Neighbourhood Stress', 'SC': 'Social Capital',
    'DC': 'Digital Capital', 'SA': 'Substance Abuse',
    'IEQ': 'Indoor Environmental Quality', 'NO': 'Noise',
    'AP': 'Air Pollution', 'GS': 'Green Space',
    'A': 'Accessibility', 'SI': 'Isolation',
    'PH': 'Physical Health', 'MH': 'Mental Health',
    'FP': 'Fuel Poverty',
}

# Topological layers (verbatim from LAYERS in ../index.html) -> tier background knowledge
LAYERS = [
    ['U_AH', 'U', 'C'],
    ['D', 'ED', 'EC'],
    ['N', 'P'],
    ['H', 'HEE', 'T', 'O', 'NS'],
    ['SC', 'DC', 'SA', 'FP'],
    ['IEQ', 'NO', 'AP', 'GS', 'A', 'SI'],
    ['PH', 'MH'],
]

# Adjustment set for HEE -> MH total effect (ADJ in ../index.html)
ADJ_SET = ['C', 'EC', 'H', 'T', 'U']

ALL_NODES = sorted(FULL_NAMES.keys())

# ---------------------------------------------------------------------------
# 2. Measured-variable -> construct mapping
# ---------------------------------------------------------------------------
# Each measured construct is mapped to ONE representative column in
# merged_data.csv (documented). Sign notes record whether the proxy runs with or
# against the construct; sign does NOT affect correlation-based CI tests / the
# recovered skeleton, so it does not bias structure discovery -- it only matters
# for interpreting a coefficient's direction, which we do not do here.
#
# Constructs with no adequate area-level proxy (or latent by design) are EXCLUDED
# and the analysis runs on the induced subgraph over measured nodes only.
MEASURED = {
    # construct : (column, proxy_note, sign_vs_construct)
    'HEE': ('RATING_MEDIAN_100', 'LSOA median EPC/SAP rating (0-100)', '+'),
    'MH':  ('Dep rate', 'QOF GP-recorded depression prevalence (primary outcome)', '+ (higher = worse MH)'),
    'EC':  ('Income Score (rate)', 'IMD income-deprivation rate', '- (higher = LESS economic capital)'),
    'ED':  ('Education, Skills and Training Score', 'IMD education-deprivation score', '- (higher = LESS education)'),
    'H':   ('BUILT_BEFORE_1950', 'share of dwellings built pre-1950 (construction era)', 'proxy for older/less-efficient stock'),
    'T':   ('rented', 'share of rented dwellings (private + social)', '+ (higher = more rental tenure)'),
    'D':   ('65+', 'share of residents aged 65+ (age structure)', 'age-composition proxy'),
    'U':   ('pop_density', 'population density (persons/ha)', '+ (higher = more urban)'),
    'C':   ('DJF_w', 'mean winter (DJF) temperature', 'climate proxy'),
    'AP':  ('no2_mean', 'mean NO2 concentration', '+ (higher = more air pollution)'),
    'GS':  ('green_act', 'active green-space access', '+ (higher = more green space)'),
    'O':   ('hhsize_ave', 'average household size', 'proxy for occupancy density/overcrowding'),
    'NS':  ('Crime Score', 'IMD crime-deprivation score', '+ (higher = more neighbourhood stress)'),
    'A':   ('gpp_dist', 'distance to nearest GP practice', '- (higher = LESS accessibility)'),
    'PH':  ('Health Deprivation and Disability Score', 'IMD health-deprivation & disability score', '- (higher = worse physical health)'),
    # Fuel Poverty: added from DESNZ sub-regional LILEE (external file
    # fuel_poverty_lsoa.csv, merged on LSOA-2011 code; 100% coverage of the
    # merged_data frame). Column 'fuel_poor_pct' is injected at load time.
    'FP':  ('fuel_poor_pct', 'DESNZ sub-regional LILEE: proportion of households fuel poor (%)',
            '+ (higher = more fuel poverty)'),
}

# Alternative outcome proxy for the robustness pass.
MH_ROBUSTNESS = ('samhi_index.2018', 'Small Area Mental Health Index (2018 composite)')

# Constructs with NO measured proxy (or latent by design) -> excluded.
# (Fuel Poverty was moved to MEASURED once the DESNZ LILEE file was obtained.)
EXCLUDED = {
    'IEQ': 'No area-level damp/mould/thermal-comfort measure in the data.',
    'NO':  'No environmental-noise (L_den/L_night) measure in the data.',
    'N':   'Latent scale-bridging construct by design; no direct measure.',
    'SC':  'No social-capital / civic-participation measure in the data.',
    'DC':  'No broadband / digital-exclusion measure in the data.',
    'P':   'No ECO/Warm-Home-Discount scheme-uptake measure in the data.',
    'SI':  'No isolation / loneliness measure in the data.',
    'SA':  'No alcohol/drug-misuse prevalence measure (access-distance is not prevalence).',
    'U_AH': 'Unobserved area history; latent root cause by design.',
}

MEASURED_NODES = sorted(MEASURED.keys())


# ---------------------------------------------------------------------------
# 3. Graph builders
# ---------------------------------------------------------------------------
def expert_digraph() -> nx.DiGraph:
    """Full 25-node expert DAG."""
    g = nx.DiGraph()
    g.add_nodes_from(ALL_NODES)
    g.add_edges_from(RAW_EDGES)
    return g


def induced_measured_digraph() -> nx.DiGraph:
    """Subgraph of the expert DAG induced on the measured nodes only.

    Latent-projection (bidirected edges from paths through excluded mediators)
    is NOT added here -- FCI in the main pipeline is the latent-robust check.
    This is the plain induced subgraph, per the task spec.
    """
    g = nx.DiGraph()
    g.add_nodes_from(MEASURED_NODES)
    for a, b in RAW_EDGES:
        if a in MEASURED and b in MEASURED:
            g.add_edge(a, b)
    return g


def tier_of(node: str) -> int:
    for i, layer in enumerate(LAYERS):
        if node in layer:
            return i
    raise KeyError(node)


def measured_tiers() -> dict[str, int]:
    """Compact 0..k tier index over measured nodes, preserving LAYERS order."""
    raw = {n: tier_of(n) for n in MEASURED_NODES}
    order = sorted(set(raw.values()))
    remap = {t: i for i, t in enumerate(order)}
    return {n: remap[t] for n, t in raw.items()}


# ---------------------------------------------------------------------------
# 4. Count verification against node_table.tex / edge_table.tex
# ---------------------------------------------------------------------------
def verify_counts(verbose: bool = True) -> dict:
    n_nodes = len(FULL_NAMES)
    n_edges = len(RAW_EDGES)
    dup = len(RAW_EDGES) - len(set(RAW_EDGES))
    g = expert_digraph()
    acyclic = nx.is_directed_acyclic_graph(g)
    ind = induced_measured_digraph()
    out = {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'duplicate_edges': dup,
        'acyclic': acyclic,
        'n_measured': len(MEASURED_NODES),
        'n_excluded': len(EXCLUDED),
        'n_induced_edges': ind.number_of_edges(),
    }
    if verbose:
        print('=== Expert DAG count verification ===')
        print(f'  nodes           : {n_nodes}  (node_table.tex states 25)')
        print(f'  directed edges  : {n_edges}  (duplicates: {dup})')
        print(f'  acyclic         : {acyclic}')
        print(f'  measured nodes  : {len(MEASURED_NODES)}  {MEASURED_NODES}')
        print(f'  excluded nodes  : {len(EXCLUDED)}  {sorted(EXCLUDED)}')
        print(f'  induced edges   : {ind.number_of_edges()} (over measured subgraph)')
    return out


if __name__ == '__main__':
    verify_counts()
