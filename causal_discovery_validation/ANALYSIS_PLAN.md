# Analysis plan — testing the expert-reviewed DAG against data (paper 1)

Status: **fixed 18 Oct 2026, before any of the analyses below were run on the real data.**
Tagged as `analysis-plan-v1` in this repository. Any later change is listed, dated,
under *Amendments* at the end, and reported in the paper.

An earlier exploratory run with linear (Fisher-z) tests was done in July 2026
(`causal_discovery_validation.py`, `results.json`). Its results were seen and informed
this plan. Every result reported in the rewritten paper comes from the runs specified
here; the July run is cited only as exploratory.

## 1. What is being tested

The DAG under test is the expert-reviewed DAG (`v1.1.2`; 25 nodes, 89 directed edges;
edge list in `expert_dag.py`). The DAG is the paper's output and is **not edited on the
basis of these analyses**. The analyses ask whether the area-level data contradict it,
and whether its minimal adjustment set for HEE → MH depends on its contested edges.

## 2. Data

- `mental-health/datasets/merged_data.csv` (LSOA 2011, England) plus
  `fuel_poverty_lsoa.csv` (DESNZ LILEE). Complete cases on the 16 measured nodes
  (expected n = 31,802).
- One variable per measured node, as in `expert_dag.MEASURED`. Mental health =
  QOF depression prevalence (`Dep rate`, matches QOF 2015 exactly); SAMHI 2018 as the
  secondary outcome.
- Weak proxies, named in advance: Climate (`DJF_w`, mean winter temperature),
  Urbanicity (`pop_density`), Overcrowding (`hhsize_ave`).
- Optional addition (D1): if Census 2011 tenure by LSOA (KS402EW) is obtained, the
  private-rented share replaces `rented` for Tenure in a sensitivity run.

## 3. Comparators

The DAG has nine unobserved nodes, so its plain induced subgraph over the 16 measured
nodes misstates what the DAG predicts for them. Two comparators are used:

1. **Primary — latent projection.** The maximal ancestral graph (MAG) of the full DAG
   over the 16 measured nodes, with the other nine nodes treated as unobserved.
   Two measured nodes are adjacent iff the full DAG has an inducing path between them
   relative to the unobserved set (Richardson & Spirtes 2002).
2. **Secondary — induced subgraph** (the July comparator), for continuity.

## 4. Conditional-independence tests

| Code | Test | Sample | Used in |
|---|---|---|---|
| L | Fisher-z partial correlation (linear) | full | PC, FCI, bootstrap |
| R | Fisher-z on normal scores of ranks (Gaussian copula; monotone non-linear) | full | PC, FCI, bootstrap |
| K | RCIT, randomised conditional independence test (Strobl, Zhang & Visweswaran 2019; kernel-based, any form of dependence) | full | PC, FCI |
| D | Conditional distance covariance with local bootstrap, 199 replicates (Wang et al. 2015; as in Chakraborty & Shojaie 2022) | 5 random subsamples of 500 LSOAs | PC (= nonPC); key tests at 1,000 |
| G | Generalised covariance measure with gradient-boosted regressions, 5-fold cross-fitting (Shah & Peters 2020) | full | key tests only |

CdCov's cost grows roughly with n³ per test, so it cannot run on the full sample;
subsample results have lower power and are reported as edge frequencies.

## 5. Analyses

**A1 — PC-stable and FCI, tests L and R.** α ∈ {0.01, 0.005, 0.001}; PC with and without
the tier ordering from `LAYERS` (MH last). Outcomes: depression (primary), SAMHI.

**A2 — PC-stable and FCI, test K** at α = 0.01 (PC with and without tiers); **nonPC with
test D** at α = 0.01 on each of 5 subsamples (n = 500, seeds 1–5).

**A3 — key tests with D (n = 1,000, 10 subsamples) and G (full sample):**
Education ⊥ HEE | {Demographics, Economic_Capital, Urbanicity};
Demographics ⊥ HEE | {Climate, Economic_Capital, Housing, Urbanicity};
Fuel_Poverty ⊥ MH | A; HEE ⊥ MH | S, where S is the separating set PC-stable (test L,
α = 0.01, no tiers) used to remove the HEE–MH edge; and HEE ⊥ Fuel_Poverty | A
(dependence expected). A = {Climate, Economic_Capital, Housing, Tenure, Urbanicity}.

**A4 — cluster bootstrap.** 200 resamples of local authority districts (326 clusters),
with replacement; PC-stable (L and R, α = 0.01, with and without tiers) and FCI
(L, α = 0.01). Report per-pair adjacency frequency and 95% percentile intervals for
precision, recall and SHD against both comparators. Seed 20261018.

**A5 — robustness of the adjustment set.** Minimal adjustment sets for the total effect
of HEE on MH (U_AreaHistory and Neighbourhood unobservable), and whether A remains a
valid adjustment set, after each change below:
- remove Climate → HEE (challenged at the review workshop);
- remove each edge into HEE whose adjacency appears in fewer than half of A4's PC
  runs (test L, α = 0.01, no tiers), one at a time and all together;
- the 6,561 orientation configurations already computed
  (`bidirectionality_sensitivity/`) are summarised, not rerun.

**A6 — permutation test of the DAG** (Eulig et al. 2025). Local Markov conditions of
the induced DAG over the 16 measured nodes: each node independent of its
non-descendants given its parents. A violation is |partial r| ≥ 0.10 (main) or
p < 0.01 with test L on a random subsample of 1,000 (sensitivity). The DAG's share of
violations is compared with 1,000 random relabellings of its nodes; p = share of
relabellings with as few or fewer violations.

**Chance baseline** for every agreement measure: expected agreement for a graph with the
same number of edges placed uniformly at random (hypergeometric), and for 1,000
degree-preserving rewirings of the discovered skeleton.

## 6. Key structure, defined by role

| Set | Members | What agreement means |
|---|---|---|
| K1 | HEE–MH | non-adjacent |
| K2 | Climate, Economic_Capital, Housing, Tenure, Urbanicity → HEE | adjacent to HEE |
| K3 | HEE → Fuel_Poverty, Fuel_Poverty → MH | adjacent |
| K4 | Education–HEE, Demographics–HEE | non-adjacent |

Agreement is reported per member, per test type, as bootstrap frequency where available.

## 7. Classifying disagreements

Each disagreement on the primary comparator is put in the first class it meets;
anything else is reported as **unexplained**.

1. **Measured route.** A missing DAG edge X → Y where the DAG also has a directed path
   X → … → Y through measured nodes, and |partial r(X, Y | those nodes ∪ separating set)|
   < 0.10.
2. **Weak proxy.** The disagreement involves Climate, Urbanicity or Overcrowding and
   disappears under test R, K or D in at least one configuration.
3. **Direction only.** The adjacency agrees but the orientation does not. Orientation
   from data is reported, never used to reverse a DAG edge; directions that break time
   order (e.g. HEE → Housing) are named as such.

## 8. Decision rules

The data are judged to **contradict the DAG** if either holds:
- HEE–MH are adjacent in at least half of A4 bootstrap runs for any algorithm, or in
  the full-sample run with test K; or
- in A6, the DAG does not have fewer violations than random relabellings (p ≥ 0.05).

Either result is reported as a finding against the DAG. Results are also shown at
neighbouring thresholds (|r| 0.05 and 0.15; α 0.005 and 0.001) so the cut-offs can be
seen not to drive the conclusion.

## 9. Software and seeds

Python 3.13; causal-learn 0.1.4.8; DoWhy 0.14; networkx 3.6.1; scikit-learn 1.9.1.
Seeds as stated above. Code: `dag_tests_2026-10.py`; outputs to `results_2026-10/`.

## Amendments

(none)
