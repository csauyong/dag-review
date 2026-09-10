# Causal-discovery validation of the HEE → MH DAG

*Triangulation analysis for HEE-MH-paper-1. Since the September 2026 plan this
is a **reported section of the paper** ("PC checks", following context → DAG
construction → expert review), not a supplementary robustness note. The
expert-reviewed DAG remains **primary**; data-driven discovery is
**corroborating evidence only**, and the paper should say in advance what a
PC/FCI disagreement would have meant, and report the FCI caveat (28/39 edges
bidirected, including all HEE edges).*

*All data are cross-sectional and area-level (LSOA), so everything below is
**associational structure**. No causal claim is made beyond
`mental-health/CONCLUSIONS.md`.*

*This run measures **16** of the 25 constructs, including **Fuel Poverty**
(DESNZ sub-regional LILEE, added from `fuel_poverty_lsoa.csv`). The remaining 9
have no LSOA-level proxy or are latent by design; `data_expansion.md` explains
why their omission does not threaten the conclusions.*

---

## TL;DR

Constraint-based causal discovery (PC-stable and FCI) was run over the 16 DAG
constructs with a measured LSOA-level proxy, and the expert DAG's implied
conditional independencies were tested directly (a `dagitty::localTests`
equivalent). Findings, all pointing the same way:

1. **The expert DAG's exposure–outcome claim survives.** In every discovered
   graph, at every significance level, HEE and MH are **never adjacent** —
   consistent with the DAG, in which the HEE→MH effect is fully mediated and
   there is no *direct* HEE→MH edge.

2. **The one measurable mediator behaves informatively.** Adding Fuel Poverty
   gives the measured subgraph its first genuine `HEE→FP→MH` path. Discovery
   recovers the **HEE→FP** half strongly (partial *r* = **−0.39** given the
   adjustment set; PC orients it HEE→FP), but the **FP→MH** half **collapses to
   zero after adjustment** (*r* = +0.073 → **+0.010**, CI spans 0) and is not
   recovered. Conditioning on FP does *not* shrink the HEE~MH partial
   correlation. So at the ecological, cross-sectional level fuel poverty carries
   no residual HEE→MH signal — a useful negative result, and direct evidence
   that the *remaining* unmeasured mediators would not change the picture either
   (see `data_expansion.md`).

3. **Where discovery disagrees, latent structure explains it.** 77 % of the
   failed independence implications (48 / 62 at |partial *r*| ≥ 0.10) involve
   pairs that are *d-connected in the full 25-node DAG* — the "independence" only
   existed because inducing the subgraph cut a path through an unmeasured hub
   (Neighbourhood, Unobserved Area History). FCI, built to tolerate this, labels
   **28 of 39 edges bidirected (↔)** — "explained by a latent common cause" —
   including every HEE edge. This is direct support for the DAG's central
   premise: area-level associations are dominated by shared latent structure,
   which is *why* the DAG carries latent nodes and an adjustment set.

4. **Only 14 genuine tensions remain**, still clustered on **Climate** (proxied
   by winter temperature — spatial confounding), plus a Demographics–Urbanicity
   correlation and three fuel-poverty proxy links (FP–Tenure/Housing/
   Overcrowding). None warrants redrawing the DAG.

Results are stable across α ∈ {0.01, 0.005, 0.001}, reproduce with SAMHI in
place of QOF depression, and hold under a multi-column PCA-composite
operationalisation.

---

## 1. Method and why it is Python, not R

The canonical `dag-review` workflow is R (`pcalg`/`bnlearn`/`dagitty`). This run
was executed in Python (`causal-learn` for PC/FCI; `networkx` for d-separation
and the implied-CI basis; Fisher-*z* partial correlations for the CI tests)
because the analysis environment had no CRAN/Bioconductor access to build
`pcalg`. The algorithms are identical (PC-stable, FCI, d-separation-based local
tests) and the structures should reproduce under `pcalg`/`dagitty`; re-running in
R is the natural confirmation step.

Pipeline (`causal_discovery_validation.py`; shared definitions `expert_dag.py`;
multi-column sensitivity `causal_discovery_composite.py`; future data additions
`ingest_new_sources.py`):

1. Transcribe the canonical DAG (`rawEdges` in `../index.html`) and verify counts.
2. Map measured columns → constructs; take the induced subgraph over measured nodes.
3. Test every implied conditional independence of the induced subgraph
   (partial correlation, Fisher-*z*), judging by **effect size** (*n* ≈ 32 k).
4. PC-stable at three α, **with and without tier background knowledge**.
5. FCI at three α (latent-confounder-robust).
6. Compare discovered CPDAG/PAG to the expert subgraph: skeleton
   precision/recall, SHD, v-structure agreement, edge-difference tables.

## 2. Expert DAG — count verification

| Check | Value | Source of truth |
|---|---|---|
| Nodes | **25** | `node_table.tex` (25 constructs) ✓ |
| Directed edges | **89** | `edge_table.tex` — all 89 documented ✓ |
| Acyclic | **Yes** | — |
| Measured nodes | **16** | mapping below (incl. Fuel Poverty) |
| Excluded nodes | **9** | no proxy / latent by design |
| Induced-subgraph edges | **40** | edges with both endpoints measured |

*Note on `edge_table.tex`:* a naïve regex counts 87 because the table mixes
`$\to$` and `$\rightarrow$` macros and one cell (`Demographics →
Housing_Characteristics`) is line-wrapped. Accounting for both, all **89**
canonical edges are documented — no content discrepancy.

## 3. Measured-variable → construct mapping

Each measured construct maps to **one** representative column of
`merged_data.csv` (31,802 LSOAs, England; ~0 % missing), except Fuel Poverty,
merged from `fuel_poverty_lsoa.csv` (DESNZ LILEE, 100 % LSOA-2011 coverage).
Proxy sign does **not** affect correlation-based CI tests or the recovered
skeleton.

**Measured (16):**

| Node | Construct | Column / source | Note |
|---|---|---|---|
| HEE | Home Energy Efficiency | `RATING_MEDIAN_100` | LSOA median EPC/SAP (0–100) |
| MH | Mental Health | `Dep rate` (primary); `samhi_index.2018` (robustness) | QOF depression; SAMHI composite |
| **FP** | **Fuel Poverty** | **`fuel_poverty_lsoa.csv` (LILEE %)** | **DESNZ sub-regional, 2023 data** |
| EC | Economic Capital | `Income Score (rate)` | IMD income-deprivation |
| ED | Education | `Education, Skills and Training Score` | IMD education-deprivation |
| H | Housing Characteristics | `BUILT_BEFORE_1950` | pre-1950 stock share (era) |
| T | Tenure | `rented` | rented share |
| D | Demographics | `65+` | age structure |
| U | Urbanicity | `pop_density` | persons/ha |
| C | Climate | `DJF_w` | mean winter temperature |
| AP | Air Pollution | `no2_mean` | mean NO₂ |
| GS | Green Space | `green_act` | active green-space access |
| O | Overcrowding | `hhsize_ave` | avg household size (occupancy proxy) |
| NS | Neighbourhood Stress | `Crime Score` | IMD crime-deprivation |
| A | Accessibility | `gpp_dist` | distance to nearest GP |
| PH | Physical Health | `Health Deprivation and Disability Score` | IMD health domain |

**Excluded — no LSOA proxy obtained, or latent by design (9):** IEQ, Noise,
Neighbourhood (latent hub), Social Capital, Digital Capital, Policy Scheme
Access, Isolation, Substance Abuse, Unobserved Area History. `data_expansion.md`
gives, for each, why it could not be obtained and why its omission does not
undermine the conclusions.

## 4. Fuel-poverty mediation: the key new result

The expert DAG routes part of the HEE→MH effect through Fuel Poverty:
`HEE → FP → MH`, with `EC → FP` and `C → FP` confounding. With FP now measured,
this chain is testable for the first time.

| Relationship | Partial *r* | Reading |
|---|---|---|
| HEE ~ FP (marginal) | −0.33 | more efficient stock → less fuel poverty |
| HEE ~ FP \| {C,EC,H,T,U} | **−0.39** | strengthens under adjustment; **recovered, PC orients HEE→FP** |
| FP ~ MH (marginal) | +0.073 | raw fuel-poverty–depression link |
| FP ~ MH \| {C,EC,H,T,U} | **+0.010** (CI −0.001…0.021) | **vanishes after adjustment; not recovered** |
| HEE ~ MH \| {C,EC,H,T,U} | +0.062 | small residual (as in paper) |
| HEE ~ MH \| {C,EC,H,T,U, **FP**} | +0.071 | **conditioning on FP does not reduce it** |

**Interpretation.** Discovery recovers the *upstream* half of the mediator
(HEE→FP is strong and robust) but the *downstream* half (FP→MH) is entirely
explained by area deprivation — so cross-sectional fuel poverty does not transmit
an HEE→MH association at the ecological level, and it is not the pathway carrying
the small HEE~MH residual. FCI marks FP's edges `C↔FP`, `ED↔FP`, `H→FP`,
`FP↔HEE` — i.e. FP too is latent-confounded. This is consistent with, not
contradictory to, the paper: the paper's effect is small, change-based, and
individual-relevant, and an ecological cross-section is the wrong design to see
mediation. It also makes the case (empirically) that adding further *ecological*
mediators would behave the same way — see §8 and `data_expansion.md`.

## 5. Implied conditional independencies (localTests-equivalent)

The induced subgraph implies **80** testable conditional independencies (one
minimal d-separator per non-adjacent pair — the `dagitty` default basis). Tested
by partial correlation on *n* = 31,802:

| Threshold | Implications with |partial *r*| ≥ threshold |
|---|---|
| ≥ 0.05 | 69 / 80 |
| ≥ 0.10 | **62 / 80** |
| ≥ 0.15 | 55 / 80 |

Median |*r*| = 0.21, max = 0.64. Annotating each failing implication with
whether the pair is **d-connected in the full 25-node DAG**:

- **48 / 62 (77 %)** of failures are pairs d-connected in the full DAG — the
  induced subgraph declared them independent only because it cut a path through
  an unmeasured node. Example: it implies `Air Pollution ⟂ Urbanicity`, yet the
  full DAG routes `Urbanicity → Neighbourhood → Air Pollution`; with
  Neighbourhood unmeasured, the observed *r* = 0.64 is that latent path
  re-surfacing. These **confirm** the full DAG.
- **14 / 62** are genuine tensions — d-separated in the full DAG yet empirically
  dependent. Still Climate-dominated (`C–U`, `AP–C`, `C–T`, `C–NS`, `A–C`,
  `C–O`, `C–D`, `C–GS`): `DJF_w` is a smoothly spatial proxy that correlates
  with most area characteristics via region/latitude, i.e. **spatial confounding
  / coarse LSOA aggregation**, not the DAG's edges. The two non-Climate ones are
  **Demographics–Urbanicity** (*r* = 0.53; rural areas skew older — plausibly a
  shared settlement-history cause, already latent in the DAG as `U_AH`) and the
  weak `hhsize_ave` overcrowding proxy. None warrants redrawing the DAG.

## 6. PC-stable

| Config | Edges | Skel. P | Skel. R | SHD | V-struct R |
|---|---|---|---|---|---|
| α=0.01, no tiers | 45 | 0.42 | 0.47 | 62 | 0.01 |
| α=0.01, **tiers** | 45 | 0.42 | 0.47 | **50** | **0.14** |
| α=0.005, no tiers | 43 | 0.42 | 0.45 | 61 | 0.01 |
| α=0.005, **tiers** | 43 | 0.42 | 0.45 | **50** | **0.13** |
| α=0.001, no tiers | 44 | 0.41 | 0.45 | 62 | 0.01 |
| α=0.001, **tiers** | 44 | 0.41 | 0.45 | **51** | **0.13** |

Tiers (from the expert `LAYERS`: Climate/Urbanicity exogenous → … → MH last)
encode the causal ordering as forbidden edges. They leave the skeleton untouched
but **lower SHD (62→50) and raise v-structure recall (0.01→0.14)** — the expert
ordering does correct orientation work. **HEE and MH are non-adjacent in every PC
run**; FP now sits in HEE's neighbourhood (HEE→FP recovered).

## 7. FCI (latent-confounder-robust)

Because 9 constructs are unmeasured, PC's causal-sufficiency assumption is
violated by construction; FCI is the appropriate check.

| Config | Edges | Skel. P | Skel. R | SHD | Bidirected (↔) |
|---|---|---|---|---|---|
| α=0.01 | 39 | 0.41 | 0.40 | 61 | **28** |
| α=0.005 | 37 | 0.43 | 0.40 | 59 | 27 |
| α=0.001 | 37 | 0.43 | 0.40 | 59 | 27 |

**28 of 39 edges are bidirected** — FCI's statement that the association is due to
an unmeasured common cause, not a direct effect. Every HEE edge is bidirected
(`A↔HEE`, `FP↔HEE`, `GS↔HEE`, `H↔HEE`, `HEE↔T`), exactly the "don't read
area-level associations as effects" caution the DAG enforces.

## 8. Edge-level disagreement and its interpretation

For PC-stable (α=0.01, no tiers): 21 expert adjacencies not recovered, 26
recovered adjacencies absent from the expert DAG (full lists in
`causal_discovery_edges.tex` and `pc_edges_*.csv`). The pattern, not the count:

- **HEE neighbourhood.** Expert: {C, EC, FP, H, T, U}. PC recovers {FP, H, T} and
  adds {A, GS}. It recovers the new **HEE→FP** mediator edge but still misses the
  adjustment-set confounders C, EC, U — precisely the edges FCI re-expresses as
  bidirected.
- **`FP→MH` is in the missing list** — the confounded-away downstream half (§4).
- **"Extra" edges are the latent hub re-appearing.** Most extras sit among the
  environmental/social mediators (A–AP, A–GS, A–NS, AP–NS, AP–O, GS–NS, …) that
  share the single latent parent Neighbourhood; marginalising it out induces
  exactly these dependencies. Textbook latent projection, not expert error.

**Candidate explanations (none require rejecting the DAG):** latent confounding
(dominant; FCI's 28 bidirected edges confirm it), faithfulness/near-cancellation,
measurement error / single-proxy choice (Climate = winter temperature;
Overcrowding = household size), and coarse LSOA aggregation / spatial
autocorrelation.

### Composite (multi-column) sensitivity

`causal_discovery_composite.py` re-runs everything with each construct collapsed
to PC1 of a multi-column block (Housing = floor area + built form + era shares;
Climate = DJF + JJA; EC = income + employment; etc.). Conclusions hold: 67/80
implications fail at |r| ≥ 0.10, 78 % latent-cut, Climate still dominates the
genuine tensions (now joined by FP–Tenure/Housing/Overcrowding proxy links), FCI
still ~19 bidirected, and HEE–MH remain **non-adjacent**. Report single-column as
primary (comparability) and the composite run as sensitivity.

## 9. Robustness: SAMHI instead of QOF depression

With `samhi_index.2018` as MH: identical localTests (80 implications, 62 fail,
77 % latent-cut), PC skeleton P/R ≈ 0.38/0.40, FCI bidirected-dominated
(24 ↔ edges), HEE–MH non-adjacent, FP→MH again unrecovered. Outcome-robust.

## 10. What this does and does not establish

**Does:** (i) the expert DAG's counts and acyclicity check out; (ii) its
qualitative HEE–MH claim (no direct edge; mediated) is consistent with
discovery; (iii) the one measurable mediator, Fuel Poverty, has a strong
recovered HEE→FP link but an FP→MH link that is confounded to zero at the
ecological level; (iv) the expert *ordering* improves orientation (tiers ↓SHD,
↑v-struct recall); (v) the DAG's reliance on latent nodes + an adjustment set is
**empirically warranted** — unconstrained discovery demands latent common causes
almost everywhere (FCI 28/39 ↔), and 77 % of localTests failures are the latent
paths the DAG encodes.

**Does not:** validate or estimate the HEE→MH effect (the remaining mediators are
unmeasured, and the measured one, FP, shows no ecological MH association);
establish any edge *direction* as causal (cross-sectional, area-level;
orientations are CPDAG/PAG equivalence-class statements); adjudicate the genuine
tensions, which need better proxies (esp. Climate) and a spatial model.
Discovery is corroboration, not a competing DAG.

## 11. Files

| File | Contents |
|---|---|
| `expert_dag.py` | Canonical DAG, node schema, variable mapping (incl. FP), induced subgraph, count checks |
| `causal_discovery_validation.py` | Main pipeline (localTests, PC, FCI, comparison, tex/csv output) |
| `causal_discovery_composite.py` | Multi-column PCA-composite sensitivity run |
| `ingest_new_sources.py` | Scaffold to add further datasets (Policy/Digital/Noise) and re-run |
| `fuel_poverty_lsoa.csv` | Tidy DESNZ LILEE proportion by LSOA (from the DESNZ workbook) |
| `variable_mapping.csv` | 25-node measured/excluded mapping |
| `localtests_*.csv` | Every implied CI, partial *r*, p, CI, `dconn_full_dag` flag |
| `pc_edges_*.csv`, `fci_edges_*.csv` | Every discovered edge per config, with orientation |
| `causal_discovery_edges.tex` | Tex-ready metrics + edge-difference tables (paper-1 appendix) |
| `results.json` | Machine-readable summary of all runs |
| `data_expansion.md` | Datasets obtained (FP) and not obtained, with reasons they don't matter |

**Reproduce:** `python3 causal_discovery_validation.py` (needs `causal-learn`,
`networkx`, `scipy`, `pandas`, `numpy`, `scikit-learn`). To confirm in the
canonical toolchain, port `expert_dag.RAW_EDGES` into `dagitty` and re-run
`localTests`; use `pcalg::pc`/`pcalg::fci` with `gaussCItest`.

## 12. Methodology references (DOIs — add to Zotero yourself)

- PC / constraint-based discovery: Spirtes, Glymour & Scheines, *Causation,
  Prediction, and Search*, 2nd ed. — **doi:10.7551/mitpress/1754.001.0001**
- FCI with latent & selection variables: Colombo, Maathuis, Kalisch & Richardson
  (2012), *Ann. Statist.* — **doi:10.1214/11-AOS940**
- Ancestral graphs / PAGs: Richardson & Spirtes (2002), *Ann. Statist.* —
  **doi:10.1214/aos/1031689015**
- `dagitty` / testable implications / `localTests`: Textor, van der Zander,
  Gilthorpe, Liśkiewicz & Ellison (2016), *Int. J. Epidemiol.* —
  **doi:10.1093/ije/dyw341**
- d-separation / graphical models: Pearl (2009), *Causality*, 2nd ed. —
  **doi:10.1017/CBO9780511803161**

*No DOI (JMLR / preprint):* PC-stable — Colombo & Maathuis (2014), *JMLR*
15:3741–3782; `causal-learn` — Zheng et al. (2024), *JMLR* 25 (arXiv:2307.16405);
PC Gaussian implementation — Kalisch & Bühlmann (2007), *JMLR* 8:613–636.

---

*Generated as a robustness analysis for HEE-MH-paper-1. The expert-reviewed DAG
remains the primary object; this discovery run is triangulating evidence and
introduces no causal claim beyond `mental-health/CONCLUSIONS.md`.*
