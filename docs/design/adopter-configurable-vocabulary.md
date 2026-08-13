# Design: what an adopting institution must be able to rename

**Status:** Tier 1 built (2026-08-08 to 08-10); Tier 2 outstanding
**Area:** config/governance, risk policy, completeness audit

## Why this exists

A division renamed its Complexity dimension to Problematic. The name reached the
Admin editor and the model's Risk tab, and stopped there: the Risk Tables panel
still described "one Materiality × Complexity table", the Risk Categorisation PDF
headed its sections with the platform's names, and the Model Risk Document
labelled the field from its spec. Each had the word written into the source, so
each kept printing it at exactly the moment the new one mattered. Fixed in
`53b4690`.

The lesson generalises: **a closed set of words shown to a user is the adopting
institution's, not the platform's.** This is the survey of everything still on the
wrong side of that line, so the next one is found deliberately rather than by an
adopter noticing.

## The shape that works

The risk dimensions are now right, and are the pattern to copy:

- The **names** live in the division's approved policy, nowhere else.
- `TIER_LABELS`, `VALID_RAG_RATINGS`, `VALID_MATERIALITY`, `VALID_COMPLEXITY` and
  `RISK_HEATMAP_BY_TIER` are **no longer read at runtime** — they survive only in
  `risk_policy/_defaults.py`, seeding a division's first policy.
- Every surface asks: `Policy.dimensionName` in the console,
  `risk_policy/naming.py` on the server, both falling back to the humanised
  dimension key rather than to a word somebody typed.
- What is *structural* stays in config: which field carries which dimension
  (`RISK_DIMENSION_FIELDS`), and the fact that there are three of them.

## The trap, and how it was resolved

The dimensions were straightforward because a record stores a **band name** and the
label lives in the policy. Most of what follows stores the displayed word itself —
a model's `lifecycle_stage` is literally `"Production"`.

So each item needs a deliberate choice:

1. **Stable key + label** (the dimension pattern) — records store a key, screens
   resolve the label. Clean, but a migration for existing records.
2. **Rename migrates the data** — as `_renameInGrid` moves a scale's assignments
   onto its new name when a band is renamed.

Choosing neither is worse than leaving the value hardcoded: records end up holding
a value that is no longer in the list, and every filter and count quietly
disagrees with the record.

**What was done (2026-08-10):** option 1, with the key seeded to the word records
already carried — so `"Production"` is both the stored value and the starting label.
That gives the stable key without a migration: nothing in the estate had to be
rewritten, and renaming edits the label alone. The stored value is immutable once an
entry exists, enforced in the domain, because records already carry it.

## Tier 1 — vocabulary an adopter will hit — **BUILT**

All of the below are now admin lists, each seeded with the shipped words and edited
under Admin. The status vocabularies store a stable value and show a label, so a
rename moves nothing on record; the questionnaire and the standing agenda are copied
onto each record when it is created, so editing them changes only what comes next.
Editing either of those two is confirm-to-amend.

| What | Now edited at | Shape |
|---|---|---|
| **The nine questions** | Admin → Review | Seeded from SR 26-2, copied onto each model at registration; a model keeps the questions it was asked. Confirm-to-amend. |
| **The standing agenda** | Admin → Agenda | Seeded from the shipped order, copied onto each meeting when scheduled. The item's `kind` stays fixed — it drives the panel a meeting draws. Confirm-to-amend. |
| **Lifecycle stages** | Admin → Vocabulary | Stable value + label. |
| **Validation statuses** | Admin → Vocabulary | Stable value + label. |
| **Impact / Priority / Remediation status** | Admin → Vocabulary | Stable value + label, three lists. |
| **Validation-question statuses** | Admin → Vocabulary | Stable value + label. The completeness audit still matches the stored "Addressed", so renaming what a reviewer sees cannot change whether the estate looks complete. |

Every list is reorderable, and order is an event (`CollectionItemMoved`) rather than
a position field, so there is no second copy of it to fall out of step.

## Tier 2 — numbers that are policy, not platform — **PART BUILT**

The completeness audit's thresholds and escalation factors are done: they sit on the
division's risk policy (Admin → Risk → Audit), ratified by the same MRC, with the
firm-wide values as the fallback. Everything else below is still a fixed constant.

**The completeness audit's scoring basis** (`_completeness_scoring.py`, `_completeness.py`)
is the largest single item: `TIER_WEIGHTS`, `RAG_MULTIPLIERS`, `UNRATED_MULTIPLIER`,
`EVENT_PRESSURE_PER_EVENT` / `_CAP`, `STALENESS_STEPS`, `SEVERITY_BANDS`,
`REMEDIATION_SLA_DAYS`, `BROKEN_DOC_ESCALATION`, `COMPLETENESS_ACCEPTABLE_AT` /
`_CONDITIONAL_AT`, and the per-field, per-collection and per-document criticality
weights. Between them they decide every completeness score and every remediation
deadline in the estate — the thing a regulator asks to see the basis for. A
rating's escalation multiplier already comes from the risk policy, so the pattern
is half-built.

`AUDIT_BASIS` ("SR 26-2 … PRA SS1/23") is printed in the audit report; a non-UK
adopter cites something else.

Also here: **cadence** (`VALID_REVIEW_FREQUENCIES`, `VALID_MRC_FREQUENCIES`,
`MEETING_INTERVAL_MONTHS`, and `REVIEW_DUE_SOON_DAYS` / `REVIEW_UPCOMING_DAYS` —
what counts as "due soon" colours the Models list); **document categories** (a
filing taxonomy); **RACI defaults**; **participant statuses**; **client
vocabulary**; and `PORTFOLIO_FILES` with the monitoring statements, which are
still one estate's own file names.

## Leave alone — structure, not vocabulary

`VALID_SIGNOFF_KINDS`, `VALID_MRC_LEVELS`, `VALID_BINDING_ROLES`,
`VALID_DEPENDENCY_DIRECTIONS`, `VALID_SIGNOFF_OUTCOME`, `VALID_NOTE_KINDS`, the
`CLOSED_*` markers, `TIER_MIN` / `TIER_MAX`, and the three risk dimensions
themselves. These describe how the platform works, not what an institution calls
things; making them editable would let an adopter break the machinery.

## What was done, and what remains

1. ~~The nine questions~~ — Admin → Review.
2. ~~The completeness scoring~~ — Admin → Risk → Audit, per division.
3. ~~The small vocabularies~~ — Admin → Vocabulary, plus Admin → Agenda for the
   standing agenda. The key-versus-rename question was settled by seeding each
   stable value to the word records already carried, so no migration was needed.

**Remaining:** cadence (review and MRC frequencies, the "due soon" window), document
categories, RACI defaults, participant statuses, the client vocabulary, and the
monitoring estate's file names and statements.

## How to stop it recurring

The question to ask of any new constant: *if an adopter renamed this, would
anything keep printing the old word?* If yes, it belongs behind a policy or an
admin list, and every surface must ask rather than spell it out. An audit rule
flagging new `VALID_*` constants used directly as display strings would make that
mechanical — worth considering once the tiers above are cleared, not before.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
