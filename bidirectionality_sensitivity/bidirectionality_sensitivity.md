# Bidirectionality sensitivity triage — total effect of HEE on MH

**Estimand.** Minimal sufficient adjustment set for the **total effect** of
`HEE` (Home Energy Efficiency, the exposure) on `MH` (Mental Health, the outcome),
computed with `dagitty::adjustmentSets(g, "HEE", "MH", type = "minimal", effect = "total")`.

**Canonical DAG.** The `rawEdges` array in [`index.html`](index.html#L747) (the
edge list used to render the published DAG, 89 directed edges). It was transcribed
verbatim into [`bidirectionality_sensitivity.R`](bidirectionality_sensitivity.R)
and **never edited** — every perturbation is built in memory.

**Method.** Eight uncertain edges were each assigned one of three states —
`original` (keep the directed edge), `reversed` (flip it), or `latent` (delete the
directed edge and add a bidirected `A <-> B`, i.e. an unobserved common cause). The
full Cartesian product of `3^8 = 6561` joint configurations was enumerated (no
marginal pre-filtering), each wrapped in `tryCatch` and classified as `cyclic`,
`non-identifiable` (empty result), or the sorted minimal adjustment set(s).

Reproduce: `Rscript bidirectionality_sensitivity.R` → writes the full
configuration-by-result table to
[`bidirectionality_sensitivity_results.csv`](bidirectionality_sensitivity_results.csv).

## Candidate edges (task label → real node IDs → committed orientation)

| # | Task label | Edge ID | Committed orientation |
|---|------------|---------|-----------------------|
| 1 | HEE—EconomicCapital | `HEE_EC` | `EC -> HEE` |
| 2 | EconomicCapital—Education | `EC_ED` | `ED -> EC` |
| 3 | EconomicCapital—PolicyAccess | `EC_P` | `EC -> P` |
| 4 | EconomicCapital—MH | `EC_MH` | `EC -> MH` |
| 5 | MH—PH | `PH_MH` | `PH -> MH` |
| 6 | SubstanceAbuse—MH | `SA_MH` | `SA -> MH` |
| 7 | Isolation—MH | `SI_MH` | `SI -> MH` |
| 8 | PhysicalHealth—EconomicCapital | `EC_PH` | `EC -> PH` |

All other 81 edges are held fixed at their committed orientation.

## Configuration-space census (6561 total)

| Outcome class | Count | Share |
|---|---:|---:|
| Cyclic (invalid DAG) | 4833 | 73.7% |
| Valid & **identifiable** | 1242 | 18.9% |
| Valid & **non-identifiable** | 486 | 7.4% |
| Distinct minimal-adjustment-set *signatures* (among identifiable) | 22 | — |

The large cyclic share is itself a finding: four of the eight edges
(`HEE_EC`, `EC_MH`, `SA_MH`, `EC_PH`) sit on a directed feedback path, so **reversing
any one of them alone produces a cycle** — reversal is not even a well-defined
operation for them. This is the structural reason the latent (`<->`) variant is the
more honest robustness check (see Interpretation).

## (b) Baseline (all-original) — highlighted

> **`{ C, EC, H, T, U }`**  *(and the larger alternative `{ C, D, DC, EC, ED, H, N, NS, SC, SI, T, U_AH }`)*

dagitty returns **two** minimal sets at baseline. The compact, practically-reportable
one is **`{ Climate, Economic Capital, Housing, Tenure, Urbanicity }`** — five
baseline-measured area/household confounders.

## (a) Distinct minimal adjustment sets across the 1242 identifiable configs

22 distinct signatures occur (a "signature" is the full set of minimal sets dagitty
returns, since several configs admit more than one). The largest buckets:

| n configs | minimal adjustment set signature | example deviation from baseline |
|---:|---|---|
| 324 | `{C,EC,H,P,T,U}` | `EC_P=reversed`, `EC_MH=latent` |
| 162 | `{C,EC,H,T,U}` *(= baseline compact set, alone)* | `EC_MH=latent` |
| 144 | `{C,D,DC,EC,ED,H,N,NS,SC,T}` \| `{C,D,EC,ED,H,N,NS,SC,T,U}` \| `{C,D,EC,ED,H,T,U,U_AH}` | `HEE_EC=latent`, `PH_MH=reversed`, `SI_MH=reversed` |
| 96 | …+ `{C,EC,H,P,T,U}` | — |
| 72 | three further variants (`…SI…`, `…U_AH…`) | — |
| … | (full 22-row table in the CSV / script stdout) | — |

The recurring structure: the **core confounders `C, EC, H, T`** appear in essentially
every set; what moves is the periphery — whether `U` vs `U_AH`, whether the
mediator-cluster `{D, DC, ED, N, NS, SC, SI}` is pulled in, and whether **`P` (Policy
Access)** must be added (it must, whenever the `EC—P` edge points into `EC`).

## (c) Minimal breaking sets (smallest Hamming deviation from all-original)

The adjustment-set *signature* changes at **Hamming distance 1** — six single-edge
deviations each move it (the other two single-edge moves are either inert or cyclic):

| Deviation | Effect on the estimand |
|---|---|
| `HEE_EC → latent` | signature changes; **compact set `{C,EC,H,T,U}` is lost** |
| `EC_P → reversed` | adds **`P`** → `{C,EC,H,P,T,U}` (Policy Access becomes a confounder) |
| `EC_P → latent` | adds `{C,EC,H,P,T,U}` as an alternative |
| `EC_MH → latent` | signature changes (compact set survives) |
| `PH_MH → reversed` *or* `→ latent` | signature changes (compact set survives) |
| `SI_MH → reversed` *or* `→ latent` | signature changes (compact set survives) |
| `EC_PH → latent` | signature changes (compact set survives) |

**Smallest deviation to lose the compact `{C,EC,H,T,U}` set entirely: Hamming 1** —
`HEE_EC → latent`, `EC_P → reversed`, or `EC_P → latent`.

**Smallest deviation to reach non-identifiability: Hamming 2** (see (d)).

## (d) Non-identifiable configurations

**486 configs (7.4%)** are non-identifiable. The structural cause is sharp:

- **`HEE_EC = latent` is a necessary condition for every single one** (486/486 carry
  `EC <-> HEE`; 0 with the directed edge in either orientation are non-identifiable).
  An unobserved common cause of the exposure `HEE` and the primary confounder `EC`,
  combined with a second latent leg from `EC` into the outcome side, leaves a
  bidirected back-door `HEE <-> EC … MH` that no observed set can block.
- **Minimal (Hamming-2) non-identifiable patterns** — exactly two:
  - `HEE_EC → latent` **&** `EC_MH → latent`  (`HEE <-> EC <-> MH`)
  - `HEE_EC → latent` **&** `EC_PH → latent`  (`HEE <-> EC <-> PH -> MH`)
- All 484 remaining non-identifiable configs are higher-order elaborations that still
  contain `HEE_EC = latent` plus one of those EC–outcome latent legs. `EC_ED`, `EC_P`,
  `PH_MH`, `SI_MH` enter only as free multiplicities (their state is balanced
  162/162/162 across the non-identifiable set — they neither cause nor prevent it).

**Reading:** identification of the HEE→MH total effect breaks **only** when the
HEE–EconomicCapital relationship is treated as confounded by an unmeasured common
cause *and* EconomicCapital is simultaneously linked to the outcome by another
unmeasured common cause. No amount of reorientation among the outcome-side edges,
on its own, destroys identifiability.

## (8) Interpretation — a *joint* robustness claim, not a per-edge one

The pivotality test (hold the other seven edges fixed, vary one; does the outcome
move in any of the `3^7 = 2187` contexts?) separates the edges cleanly:

| Edge | Marginal effect (vs all-original) | Pivotal among **valid** graphs | Verdict |
|---|---|---:|---|
| `SA_MH` (SubstanceAbuse→MH) | inert (latent), cyclic (reversed) | **0 / 2187** | **Robust** — orientation never changes the adjustment set; reversal only ever creates a cycle |
| `EC_ED` (Education→EC) | inert at Hamming-1 | **210 / 2187** | **Marginally inert but jointly load-bearing** |
| `SI_MH` (Isolation→MH) | changes | 252 | Fragile |
| `EC_P` (EC→PolicyAccess) | changes (adds `P`) | 288 | Fragile |
| `PH_MH` (PH→MH) | changes | 216 | Fragile |
| `EC_PH` (EC→PH) | changes (latent) / cyclic (reversed) | 108 | Fragile |
| `EC_MH` (EC→MH) | changes (latent) / cyclic (reversed) | 756 | Fragile |
| `HEE_EC` (EC→HEE) | changes; gateway to non-identifiability | 864 | **Most load-bearing** |

**Why this must be read jointly.** `EC_ED` is *individually inert* — flipping or
latent-izing Education→EconomicCapital on its own leaves the baseline set unchanged,
because `ED` and `EC` are both already in the adjustment set. Yet in **210** joint
contexts it is pivotal: e.g. with `HEE_EC`, `EC_P`, `PH_MH`, `SA_MH`, `SI_MH`, `EC_PH`
all latent, `EC_ED = reversed` drops `ED` from a minimal set
(`{C,D,EC,ED,H,T,U,U_AH}` → `{C,D,EC,H,T,U,U_AH}`). This is exactly why
one-at-a-time sensitivity analysis is insufficient: an edge that looks orientation-free
in isolation can carry weight once other edges are also relaxed.

**Robust core.** The compact identifying set **`{C, EC, H, T, U}`** survives as a
valid minimal set in **288 / 1242 (23%)** of identifiable configurations, and the core
confounders **`C, EC, H, T`** appear in essentially every adjustment set found
anywhere in the space. The total effect of HEE on MH is *identifiable in 71.9% of
non-cyclic configurations* (1242 / 1728).

**Fragile combinations.** Identification is sensitive to (i) the orientation of the
**EC–PolicyAccess** edge (reversal forces `P` into the set), and (ii) any modelling of
the **HEE–EconomicCapital** edge as a latent common cause, which is the sole gateway
to non-identifiability and, jointly with a latent EC–MH or EC–PH link, breaks the
estimand outright.

### Where temporal ordering, not the DAG, does the identification work

A DAG cannot encode true simultaneity. Two of the candidate edges are genuine
feedback loops in calendar time:

- **HEE ↔ EconomicCapital** — income enables retrofit *and* a more efficient dwelling
  relieves the household budget.
- **EconomicCapital ↔ Education** — schooling raises earnings *and* family resources
  shape attainment.

The analysis shows the estimand is fragile precisely at `HEE_EC` (the only edge that
can produce non-identifiability) and depends jointly on `EC_ED`. The committed DAG
resolves both by **temporal precedence, not by the graph**: `EconomicCapital` and
`Education` are treated as **baseline / pre-treatment** confounders, measured *before*
the exposure contrast in `HEE`. Under that measurement protocol the arrows
`ED → EC → HEE` are the correct acyclic encoding of a feedback system observed at
fixed times, and the bidirected (`<->`) variants — which is where non-identifiability
appears — correspond to the case where that temporal separation *fails* (an unmeasured
common cause acting contemporaneously on both). So the identification of the HEE→MH
effect rests on the **design assumption that EC and ED are ascertained at baseline**,
not on anything internal to the DAG. If that baseline-measurement assumption cannot be
defended, the `HEE_EC = latent` row of this analysis is the relevant scenario, and the
effect is not point-identified from observed covariates alone.

### Why the latent (`<->`) variant is the more honest check

Edge *reversal* is frequently not even admissible here: reversing `HEE_EC`, `EC_MH`,
`SA_MH`, or `EC_PH` each creates a directed cycle, so "what if the arrow pointed the
other way" is structurally undefined for half the candidate set. The
**latent-common-cause variant (`A <-> B`)** is the substantively meaningful robustness
question — "what if this association is partly or wholly due to an unmeasured common
cause rather than a directed effect?" — and it is always a valid DAG operation. It is
also the variant that surfaces the only genuine identification failure in the entire
space (the `HEE <-> EC` family). The headline robustness claim should therefore be
stated against the latent variant: **the HEE→MH total effect is identified, with core
adjustment set `{C, EC, H, T}` (plus `U` or `U_AH`), and is robust to the orientation
of every candidate edge except where EconomicCapital is allowed an unmeasured common
cause with both HEE and the outcome side.**

---

*Generated by [`bidirectionality_sensitivity.R`](bidirectionality_sensitivity.R);
full table in [`bidirectionality_sensitivity_results.csv`](bidirectionality_sensitivity_results.csv).
The canonical DAG in `index.html` was not modified.*
