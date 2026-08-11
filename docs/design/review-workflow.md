# Design: the model review as a workflow, ending in a signed report

**Status:** Built — agreed 2026-08-06, complete on main 2026-08-08
**Area:** Model inventory / Review & Validation / MRC

## Decision

A model review is **one Review tab running as a five-stage workflow**, ending in a
reviewer sign-off that files a **Model Review Report** PDF. The MRC **receives**
that report as a tabled paper; what the MRC actually signs off is the **risk
rating**, as it does today. The review does not go to the committee for approval.

The record of **challenge between owner and reviewer is part of the deliverable**,
not a convenience. It is append-only, attributed, and printed verbatim in the
report — because "was this model effectively challenged?" is a question the
documentation has to answer on its own.

## The five stages

One inner rail on the Review tab. Each stage carries its own state — *Not started /
In progress / Agreed* — with who agreed and when. Agreement is what moves the review
along; it is recorded per stage, not per row.

| # | Stage | Content | Data |
|---|---|---|---|
| 1 | Preliminary documents | The pack the reviewer works from; reviewer marks it received and read | New `Review` document category |
| 2 | The nine questions | Owner's status + rationale; reviewer's verdict and comment | `validation_questions` + reviewer fields |
| 3 | Model weaknesses | Weaknesses register, owner-proposed, reviewer-agreed | `model_weaknesses` (moves here) |
| 4 | Limitations of use | Limitations register, same pattern | `limitations` (moves here) |
| 5 | Monitoring approach | Narrative description of how the model will be monitored | New free-text field |
| ✓ | Sign-off | Final commentary, the gate, the report | New `review_signoffs` |

Stage 5 is deliberately a **textual description** for now, not a register of metrics
and thresholds. If monitoring later needs to be structured, it becomes a register
without disturbing the workflow around it.

Earlier stages stay revisitable — a reviewer who reaches stage 4 and needs to reopen
a question must be able to. Reopening an agreed stage is itself a recorded act.

## The nine questions, two-sided

Each of the nine SR 26-2 questions (`config/governance/_inventory.py`) gains a
reviewer side alongside the owner's existing status / rationale / evidence:

- `reviewer_verdict` — Accepted / Challenged / Not reviewed
- `reviewer_comment`
- `reviewed_by`, `reviewed_at` — stamped, not typed

## The thread is evidence

Per stage, an append-only thread between owner and reviewer.

- **No edit, no delete** — not by the author, not for a typo. A correction is a new
  note. The event store gives this; the console must never offer the affordance.
- **Attributed and stamped** — named identity, role (owner / reviewer), timestamp.
- **A note may be marked a Challenge**, which is Open or Resolved, with the resolving
  note pointing back at it. This is what lets the report state *"6 challenges raised
  on the nine questions, 6 resolved, 2 changed a status"* rather than leaving a
  reader to infer rigour from a wall of text.
- **Printed verbatim** in the report, under the stage it belongs to.
- **An open challenge blocks sign-off.** A reviewer who signs off over one must say
  so in a note; it is never silent.

It is a record of exchange, not a messaging product: no notifications, no presence,
refresh-based. Building it as chat would promise something the platform does not do.

## Sign-off, and what the MRC gets

1. The reviewer writes the **final commentary** and signs off. Blocked while any
   stage is unagreed or any challenge is open; the button names what is outstanding,
   as the meeting-close button already does.
2. Sign-off **generates the Model Review Report** through the shared LaTeX house
   style and files it against the model — the same shape as closing a meeting
   generating and filing its minutes. It carries the five stages, both sides of every
   question, the registers, the monitoring narrative, the challenge record and the
   attestation. The filed PDF is the record of what was agreed on that date.
3. The report's category joins `MRC_REVIEWABLE_CATEGORIES`, so it can be **tabled**
   against the model's agenda item through the existing mechanism — the committee
   reads the document the model holds, never a copy of it.
4. The MRC **receives** it and signs off the **risk rating**. Receipt is minuted.
   There is no MRC approve/reject of the review itself, and no new sign-off kind.

**Open rule:** whether a RAG sign-off request should be *blocked* until the model has
a current signed review. Recommended, not yet decided.

## Re-review

A signed review completes a cycle. A new cycle is started by one of three triggers:

1. **The model owner** — explicitly, and particularly when ownership has changed.
2. **A material version change** — a new version marked material prompts one.
3. **MRC direction** — the committee can direct a re-review.

Starting a cycle resets the stage states as a recorded act. The filed reports and the
append-only sign-offs are the history of previous cycles.

## Consequences

- **The Assumptions tab.** With weaknesses and limitations moving into Review, that
  tab holds assumptions alone — which is what makes renaming it *Assumptions*
  honest. Registers get exactly one editing home.
- **Retire the stored `review_status` ladder.** Its options (*Not Started, First
  Meeting, Full Review, …*) are an informal version of this workflow, it is already
  exempt from the completeness audit as "derived", and a genuinely computed review
  status (Overdue / Due Soon / On Track, from `next_review_date`) already exists
  under the same name. The stage rail answers "where is this review up to".
- **The review header** — reviewer, validation status, and the review dates — moves
  off the Overview onto the Review tab, leaving a one-line summary on Overview.
- **Completeness audit.** The monitoring narrative is a new scored field; a
  *Challenged* question is a candidate new finding. Leave the existing "Addressed"
  bar alone so no model's score moves the day this ships.
- **Products** mirror models for several of these registers and will drift unless
  they follow.

## Build order

All six steps are done. Kept below as the record of how it was staged.

1. Review tab shell — stage rail, stage states, and the moves (questions, weaknesses,
   limitations in; Assumptions tab left clean).
2. Reviewer verdict on the nine questions; per-stage agreement.
3. Monitoring narrative.
4. Threads, challenge marking, preliminary documents.
5. Sign-off: commentary, gate, report generation, filing.
6. MRC: tabled paper, receipt in the minutes, re-review triggers.

Steps 1–2 are the visible restructure and can ship alone. Steps 5–6 carry the new
domain rules.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
