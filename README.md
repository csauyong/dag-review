# DAG Review — Energy Efficiency and Mental Health

This repository hosts an interactive Directed Acyclic Graph (DAG) for expert review of the assumed causal structure linking home energy efficiency (HEE) to mental health outcomes at the Lower Layer Super Output Area (LSOA) level in England.

Visit the live DAG: **https://csauyong.github.io/dag-review/**

Expert feedback is collected through GitHub Issues. This document explains how to contribute.

---

## Changelog

### v1.1.1 — 2026-06-24

Changes since v1.1.0.

**DAG structure**

- **Reinstated** edge **Climate → HEE** (reversing its removal in v1.1.0). Regional climate shapes domestic heat-demand profiles and thus the marginal value of efficiency measures: because the absolute energy and cost savings of a given fabric measure scale with underlying heat demand, regional variation in demand alters the cost-effectiveness and geographic targeting of retrofit, and hence the efficiency state ultimately achieved across the stock (Aragón et al. 2022). The edge moves out of the excluded-edges table and into the *Edges into HEE* table.

**Adjustment set**

- With `Climate → HEE` restored, Climate is again a common cause of HEE and MH, so the minimal sufficient adjustment set for the total effect HEE → MH returns to the **five-node set {Climate, Economic Capital, Housing Characteristics, Tenure, Urbanicity}**. (While the edge was excluded in v1.1.0, Climate reached HEE only via `Climate → Housing → HEE`, already blocked by conditioning on Housing, so the set had collapsed to four.) The DAG's adjustment-set highlighting reflects the five-node set.

The graph now has **25 nodes and 89 directed edges**.

### v1.1.0 — 2026-06-23

Changes since v1.0.0.

**New views**

- Added an **Assumptions** tab grouping the identifying assumptions into four themes.
- Added a **Definitions** tab with a per-node construct definition and hypothesised causal role.

**DAG structure (expert-review decision log)**

- **Added** edge **Fuel Poverty → IEQ** — affordability-driven heating rationing lowers internal surface temperatures, producing condensation, damp, and mould; a behavioural pathway distinct from the physical-fabric route `HEE → IEQ`.
- **Added** edge **Accessibility → Physical Health** — distance and travel time to services delay diagnosis and disrupt management of physical illness; also opens an indirect `Accessibility → PH → MH` sub-path.
- **Removed** edge **Climate → HEE** — it conflated regional heating *demand* with the dwelling's installed *efficiency*; the channel is retained through `Climate → IEQ` and `Climate → Fuel Poverty`. The edge is now documented in the excluded-edges table with its rationale.
- **Air Pollution → IEQ** was already present and is confirmed unchanged.

**Definition & rationale updates**

- **Accessibility** redefined to include the local availability of mental-health services (no new node).
- **Climate** broadened to cover coastal/geographic physical exposure — coastal-flood and storm-surge risk, wind-driven rain, and salt/wind weathering of the building fabric — folded into the existing node rather than added as a separate node.
- **Climate → IEQ** rationale extended with the wind-driven (driving) rain moisture-ingress mechanism.
- **Economic Capital → Policy Scheme Access** flagged for an orientation-sensitivity test; the direction is retained pending that check.
- **IEQ** kept aggregated in the main DAG, with a note that a decomposed cold/overheating sub-graph is maintained separately.

**Appearance**

- Node palette, legend, and domain filters recoloured and relabelled to match the project slide deck (Exposure, Outcome, Structural confounder, Environmental mediator, Social / structural mediator, Health mediator, Latent). The Outcome node now carries a hairline border so it stays legible on the dark canvas.

The graph now has **25 nodes and 88 directed edges**. Edge-by-edge evidence is maintained in `edge_table.tex`; the node schema in `node_table.tex`.

### v1.0.0 — baseline (commit `59449e5`)

Initial reviewed baseline: the interactive DAG for expert review, GitHub-Issues feedback integration, the adjustment-set / path-highlighting tools, and the Fuel Poverty mediator node with its edges and rationale.

---

## For expert reviewers

You can leave feedback in two ways, depending on the type of contribution.

### 1. React to existing suggestions

Each open issue represents a suggested change to the DAG (add an edge, remove an edge, reverse a direction, or general discussion). You can support or decline a suggestion by reacting on the issue body:

- 👍 if you support the proposed change
- 👎 if you decline (i.e. you think the DAG should stay as it is, or the proposal is wrong)

These reactions are counted automatically. The visualisation displays the running tally inside the side panel when you click a node or edge.

If you wish to elaborate on your vote, please add a comment below the issue. Reactions alone are recorded as anonymous tallies; comments are signed and useful for the workshop discussion.

### 2. File a new suggestion

Click any node or edge in the visualisation, then use the buttons in the side panel:

- **Comment on node / Comment** — open a general discussion about a node or edge.
- **Propose new edge** (node panel) — suggest a new directed edge involving this node.
- **Propose removal** (edge panel) — suggest that an edge be removed.
- **Propose reversal** (edge panel) — suggest that an edge be reversed in direction.

Each button opens a pre-filled GitHub Issue in a new tab. Please:

1. Complete the title where it ends in `: ` with a one-line summary.
2. Fill in the body sections (justification, mechanism, citation if you have one).
3. Submit the issue.

You'll need a GitHub account. Creating one takes about 60 seconds. Once signed in, you can react and comment on others' issues too.

### What happens to your feedback

All issues are reviewed by the project team before the in-person workshop. The workshop session functions as a final sign-off; the issues are intended to surface contested edges in advance so the limited workshop time can focus on them. The final DAG, together with a record of how each substantive comment was addressed, will appear in the methods section of the resulting paper.

---

## For the project maintainer

### Deploying

1. Replace the placeholders in `index.html`:
   ```js
   const GH_OWNER = 'YOUR_GITHUB_USERNAME';
   const GH_REPO  = 'dag-review';
   ```
2. Push to a public repository on GitHub.
3. In the repository settings, enable **Pages** with source `main` branch, root folder.
4. After a minute or two, the site will be available at `https://<owner>.github.io/<repo>/`.

### Issue labels

Create the following labels in the **Issues → Labels** tab (or accept the auto-assignment when issues are filed via the in-app buttons):

| Label          | Purpose                                              |
|----------------|------------------------------------------------------|
| `dag-review`   | Master label; required for the page to find an issue |
| `edge`         | Issue relates to a specific edge                     |
| `node`         | Issue relates to a specific node                     |
| `general`      | Issue is not tied to a specific node/edge            |
| `add-edge`     | Proposes adding an edge                              |
| `remove-edge`  | Proposes removing an edge                            |
| `reverse-edge` | Proposes reversing an edge direction                 |

The page lists every issue labelled `dag-review` regardless of state (open or closed), so resolved discussions remain visible as part of the audit trail.

### Issue title conventions

The page parses issue titles to associate them with nodes and edges. The required formats are:

- `[edge] <SOURCE> -> <TARGET>: <free text>` — for example `[edge] EC -> HEE: weak mechanism in UK context`
- `[node] <ID>: <free text>` — for example `[node] HEE: consider splitting into installation vs ongoing efficiency`
- `[general]: <free text>` — for issues not tied to a specific element

Node and edge IDs must match those used in the visualisation (e.g. `HEE`, `EC`, `MH`). Issues with titles that do not match these patterns will not be aggregated into the panel and will appear only in the GitHub issue list.

### Rate limits

The visualisation calls the GitHub public REST API without authentication. This is limited to 60 requests per IP per hour, which is comfortably above what a typical reviewer session generates (one request on page load). If the limit is exceeded, the page will show `feedback: offline` in the header but the rest of the visualisation will continue to work.

### How feedback is recorded for the paper

For the methods section, the audit trail can be reconstructed from:

- The list of all `dag-review` issues at submission time (downloadable via the GitHub API or `gh` CLI as JSON);
- The git history of any commits that modified `rawEdges` in `index.html` in response to feedback;
- A short summary table linking each substantive issue to the decision taken (accepted / accepted with modification / declined, with brief rationale).

A suggested aggregation query, using the `gh` CLI:

```bash
gh issue list --label dag-review --state all --limit 200 \
  --json number,title,state,reactions,createdAt,closedAt,labels \
  > dag-review-export.json
```

This produces a JSON file that can be cited as supplementary material and analysed in R.
