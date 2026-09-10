# Expert review — primary record

Source material for the expert-review section of `HEE-MH-paper-1` (thesis Ch4).
Everything here is evidence; nothing here is generated. Cite it from the paper
and, where the paper makes a claim about the review process, it should be
checkable against one of these files.

## Contents

| File | What it is |
|---|---|
| `DAG_Review_Workshop.pptx` | The 18-slide deck used on 22 June 2026. Slide 6 carries the stage-1 tallies; slide 7 is the DAG figure the paper's Figure 1 reproduces; slide 8 lists the seven identifying assumptions; slide 18 is the node-role reference. **Speaker notes carry the issue-number mapping**, and several slides carry text typed live during the session. |
| `workshop_transcript_2026-06-22.vtt` | Teams transcript, 1 h 26 m 50 s. Names are auto-transcribed and some are wrong (Chun Sang → "Shen Sung/Chen Sang", Gesche → "Geisha/Daijia/Keisha/Aisha", Niloofar → "Nalu/Nagoor/Nay Lu", Jonathon → "John"). `~CentralHse.305.(6).Bartlett` is the room microphone — Phil Symonds. |
| `workshop_transcript_2026-06-22_readable.txt` | Same transcript, de-duplicated and merged into speaker turns with timestamps. Use this one for reading and quoting. |
| `dag-review-issues.json` | Full GitHub issue export, `csauyong/dag-review`, all states, retrieved 10 Sep 2026. Issues #1–#2 are the author's own smoke tests (20 May) and are **not** review comments; #3–#12 are the ten substantive proposals. |
| `invited_reviewers_email_list.png` | The invitation recipient list — eight invited reviewers, supervisors in copy. |

## The record in brief

- **Invited:** 8 reviewers across 5 institutions (UCL, Manchester, Swansea, Exeter, Tampere).
- **Attended the workshop:** 5 — Jonathon Taylor, Gesche Huebner, Niloofar Shoari, Ricci Yue, Minnie Ashdown. Minnie Ashdown was not on the original invitation list.
- **Filed written proposals:** 3 — `kalsarikannit80` (Jonathon Taylor, 7 issues, 10 June), `amymizen` (Amy Mizen, 1 issue, 19 June), `nshoari` (Niloofar Shoari, 2 issues, 14 July).
- **Stage 1** (pre-workshop, GitHub): 8 proposals, 6 nodes flagged, 2 reviewers. All answered 21 June, the day before the workshop.
- **Stage 2** (workshop, 22 June): 26 substantive interventions from the 5 attendees; 9 produced a change to the graph, a node definition, or the analysis plan.
- **Stage 3** (post-workshop, from 24 June): 2 proposals, both from `nshoari` on 14 July. **Both are still open and unanswered** — close them before the paper claims every proposal was resolved.

## Regenerating the issue export

    gh issue list --label dag-review --state all --limit 200 \
      --json number,title,state,reactions,createdAt,closedAt,labels \
      > dag-review-export.json

or, unauthenticated:

    curl -sS "https://api.github.com/repos/csauyong/dag-review/issues?state=all&per_page=100" \
      -o dag-review-issues.json

## Caution

The transcript is an unredacted recording of a live meeting and the email list
contains personal addresses. Neither should be published as supplementary
material without the participants' consent. The citable supplement is the issue
export, which is already public.
