# ML review policy — the institution decides what it is asking for

**Scope: ML Applications only.** Models are untouched.

## The problem

The ML review asks for a lot. A train carries 51 typed fields across six numbered
sub-tabs, and the Review tab asks nine questions on top. Every one of them is a
reasonable thing to want; asking for all of them at once, of somebody who has just
been handed the console, is how a governance tool gets abandoned.

The list is not wrong. What is wrong is that **we** decided it. An institution
rolling this across a data estate has its own view of what a review must contain,
and that view will differ by institution and move over time.

So: the catalogue stays, and the institution says which of it applies.

## The shape

One Admin tab. Every reviewable item on it, each with two ticks:

| Tick | Meaning |
|---|---|
| **In use** | the item appears on the ML Application's screens at all |
| **Mandatory** | the item must be filled before the review can complete |

Two ticks, not one three-state control, because they are two different questions and
an adopter will set them at different times: switch things on first, tighten later.
`mandatory` implies `in_use` — ticking mandatory ticks in use, and un-ticking in use
clears mandatory. Nothing else about the record changes.

### One mechanism, two catalogues

The items come from two places, and the policy does not care which:

- **Training fields** — the keys of `TRAINING_FIELD_SPECS`, grouped by their A–F
  section. Defined in code; an institution chooses among them, it does not add to
  them.
- **Review questions** — rows of the `ml_application_questions` reference list.
  Already institution-owned: rows can be added and removed in Admin today.

A single policy keyed by item id covers both. Building it twice is how the four
copies of `_grouped_specs` happened.

## Decisions

1. **Default: everything in use, nothing mandatory.** This is the settled position
   from T6 ("nothing is mandatory") and it means an existing estate sees no change
   on the day this ships. An institution tightens deliberately, from a screen that
   shows it what it is tightening.

2. **MRC-ratified**, on the same footing as `risk_policy`. What a review must
   contain is a governance standard, not a form preference: an institution that can
   quietly drop a mandatory item the week before an inspection has not got a
   standard at all. So the Admin tab edits a *draft*, and the draft becomes the live
   policy only when the committee approves it. Proposed → Approved / Rejected, the
   lifecycle `risk_policy` already runs.

3. **A field that is switched off keeps its data.** Un-ticking hides a field; it
   does not erase what a train already recorded, and re-ticking shows it again.
   Governance records are append-only and a policy change is not a deletion.

4. **Completeness counts the policy, not the catalogue.** `filled / total` becomes
   `filled / in-use`, so the progress a screen reports is progress against what the
   institution actually asked for. Mandatory gaps are counted and reported
   *separately* — progress and permission are different questions.

5. **The gate is on completion, never on recording.** A train can always be created
   and edited with mandatory fields blank; what is refused is *finishing the
   review*. A barrier to writing evidence down is a barrier to evidence.

## Phases

**P1 — the policy.** `config/governance/_ml_review_policy.py` (catalogue assembly +
defaults) and an aggregate under `src/governance/ml_review_policy/`, following
`risk_policy`'s Proposed → Approved / Rejected lifecycle per decision 2. Read helper
`review_policy()` returns the LIVE policy — the most recently approved one, or the
defaults where nothing has been ratified — resolved so an unset item is answered
without a write. The pending draft is read separately by the admin editor, exactly
as a risk policy's is. Domain tests first.

**P2 — the Admin tab.** Items grouped by source and section, two checkboxes each,
count of in-use / mandatory per group. Mandatory implies in-use, enforced in the
rules, not only the UI.

**P3 — the ML App screens.** Training and Review tabs list only in-use items;
mandatory ones carry a left red rule. Both tab badges count against the policy.

**P4 — the gates.** Refuse *mark review complete* and refuse *raise MRC sign-off*
while a mandatory item is blank, naming what is missing. Both refusals are domain
rules, so the API and any script hit the same wall.

**P5 — the dashboard.** The ML Apps tiles gain the estate-level view: how many
records have every mandatory item filled, and how many do not. `createRecordList` is
shared with Models, so this arrives as a config-declared extra tile, not a branch
inside the shared builder.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
