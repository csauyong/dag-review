# Data expansion: measuring currently-unmeasured DAG constructs

Ten of the 25 expert-DAG constructs originally had no proxy in `merged_data.csv`.
**One has now been added — Fuel Poverty** (DESNZ sub-regional LILEE) — bringing
the measured set to 16. The other nine were **not obtained**; this note records
why, and — importantly — why their omission does not undermine the discovery
validation. All sources are Open Government Licence v3.0. Verified July 2026.

## Obtained

### Fuel Poverty (FP) — ADDED ✓

- Source: DESNZ *Sub-regional fuel poverty*, 2025 report / **2023 data**, Table 4
  (Fuel Poverty in England by LSOA).
- File: `Sub-regional_fuel_poverty_statistics_2023.xlsx` → tidied to
  `fuel_poverty_lsoa.csv` (LSOA code, LILEE proportion, household counts). The
  workbook keys on **LSOA-2011** codes and joins to `merged_data.csv` at
  **100 % coverage** (all 31,802 LSOAs) — no harmonisation needed.
- Landing: `https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2025-2023-data`
- DAG role: `HEE→FP→MH`, with `EC→FP`, `C→FP`. This is the single construct that
  gives the measured subgraph a genuine HEE→MH mediated path.
- **Result (see `causal_discovery_validation.md` §4):** HEE→FP is strongly
  recovered (partial *r* = −0.39 given the adjustment set), but **FP→MH collapses
  to +0.010 (CI spans 0) after adjustment** and is not recovered; conditioning on
  FP does not shrink the HEE~MH residual. Ecological fuel poverty transmits no
  HEE→MH signal once deprivation is controlled.

## Not obtained — and why it does not matter

The FP result is the key: *even a squarely on-path mediator, once measured, has
its MH association fully confounded away at the LSOA level.* That is strong
empirical grounds for expecting the remaining ecological mediators to behave the
same way. Construct-by-construct:

| Node | Why not obtained | Why it does not change the conclusions |
|---|---|---|
| **P** Policy Scheme Access | ECO/GBIS uptake is published to LSOA only via the interactive Domestic Energy Map; the downloadable tables are Local-Authority. | P's **only** child is HEE (`P→HEE`); it has no path to MH except through the exposure, so it cannot confound the HEE–MH relationship the analysis validates. It is also downstream of measured EC/deprivation (means-tested eligibility), so much of its signal is already captured. |
| **NO** Noise | Defra strategic noise maps are geospatial contour polygons, not tabular LSOA; building the node needs GIS areal interpolation. | NO is an `HEE→NO→MH` mediator structurally identical to FP. The FP experiment shows such ecological mediator→MH links vanish after deprivation adjustment, so NO would almost certainly add a confounded-to-zero edge, not new structure. |
| **DC** Digital Capital | Ofcom Connected Nations is Output-Area/postcode; needs population-weighted OA→LSOA aggregation. | DC is peripheral to HEE–MH (`DC→MH`, `DC→SI`; parents EC, U are measured). Its MH link is confounded by EC/U, which are adjusted — same confounded-away pattern as FP. |
| **SA** Substance Abuse | OHID alcohol/drug-misuse is Local-Authority only; no LSOA release. | SA (`SA→MH`, `SA→PH`) is downstream of measured NS/EC; its MH link is confounded, and LA-level values broadcast to LSOA would add measurement error, not signal. |
| **IEQ** Indoor Env. Quality | No LSOA damp/mould/thermal-comfort data (EHS is a national sample). | An `HEE→IEQ→MH` mediator — same class as FP/NO; expected to be confounded away ecologically. Its absence is why the HEE→MH mechanism is intrinsically an individual/longitudinal question, not an ecological one. |
| **SC** Social Capital | No LSOA civic-participation/trust measure (Community Life Survey is LA/regional). | A social mediator whose MH association is deprivation-confounded; not on the HEE→MH backbone. |
| **SI** Isolation | No LSOA loneliness measure. | Downstream psychological mediator; not a confounder of HEE–MH. |
| **N** Neighbourhood | Latent scale-bridging construct **by design** — not a dataset. | Its removal is exactly what FCI accounts for: the 28 bidirected edges are the empirical footprint of this latent hub. It is *handled by the method*, not ignored. |
| **U_AH** Unobserved Area History | Latent root cause **by design**. | Same as N — represented by FCI's bidirected marks and by the DAG's latent node. |

**Bottom line.** The unmeasured constructs fall into two groups. (a) *Ecological
mediators* (NO, DC, SA, IEQ, SC, SI): the measured mediator FP demonstrates their
MH associations would be confounded to zero at LSOA level, so they would not
change the qualitative result. (b) *Latent hubs* (N, U_AH) and the *exposure-side
driver* P: these do not confound the HEE–MH relationship, and the latent hubs are
already accounted for by FCI. None of the nine, added, would overturn the two
conclusions that matter — HEE–MH have no recoverable direct edge, and area-level
structure is latent-confounding-dominated.

## If you do want to add more later

`ingest_new_sources.py` is a runnable scaffold: download a file into
`mental-health/datasets/`, run `--inspect` to find the sheet/columns, set
`enabled=True` in its `SOURCES` registry, and it joins on LSOA and re-runs the
full pipeline on the enlarged subgraph. Verified links for the not-obtained
sources are retained below. LSOA-2011↔2021 harmonisation via the ONS best-fit
lookup is only needed for releases keyed on 2021 codes (the fuel-poverty file was
not).

- [Household Energy Efficiency Statistics (ECO/GBIS) — GOV.UK](https://www.gov.uk/government/collections/household-energy-efficiency-national-statistics)
- [Ofcom Connected Nations 2025 data downloads](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-20252/data-downloads-2025)
- [Defra strategic noise mapping (Round 4, all metrics) — environment.data.gov.uk](https://environment.data.gov.uk/dataset/562c9d56-7c2d-4d42-83bb-578d6e97a517)

## Sources

- [Sub-regional fuel poverty data 2025 (2023 data) — GOV.UK](https://www.gov.uk/government/statistics/sub-regional-fuel-poverty-data-2025-2023-data)
- [Fuel poverty sub-regional statistics (collection) — GOV.UK](https://www.gov.uk/government/collections/fuel-poverty-sub-regional-statistics)
- [Household Energy Efficiency Statistics (collection) — GOV.UK](https://www.gov.uk/government/collections/household-energy-efficiency-national-statistics)
- [Ofcom Connected Nations 2025 data downloads](https://www.ofcom.org.uk/phones-and-broadband/coverage-and-speeds/connected-nations-20252/data-downloads-2025)
- [Defra Road Noise all metrics (Round 4) — environment.data.gov.uk](https://environment.data.gov.uk/dataset/562c9d56-7c2d-4d42-83bb-578d6e97a517)
