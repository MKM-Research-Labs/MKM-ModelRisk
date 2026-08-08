# Design: what an adopting institution must be able to rename

**Status:** Survey — 2026-08-08, nothing built from it yet
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

## The trap, before anything is built

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

## Tier 1 — vocabulary an adopter will hit

| What | Where | Note |
|---|---|---|
| **The nine questions** | `SR262_QUESTIONS` (`_inventory.py`), seeded at registration | An adopter with its own questionnaire, or another regulator's, cannot change the wording or the count. Seed-only — existing models keep what they were given — so it behaves like the reference lists that are already admin-editable. The centre of the review workflow. |
| **The standing agenda** | `STANDING_AGENDA` (`_mrc.py`), seeded onto every meeting | A committee's own running order, in code. `kind` drives bespoke per-item UI, so what is editable is the title, the description, and which optional items appear — not the kinds. |
| **Lifecycle stages** | `VALID_LIFECYCLE_STAGES` — Development / Validation / Production / Retired | Field value and a Models-list filter. Stored verbatim; needs the migration choice above. |
| **Validation statuses** | `VALID_VALIDATION_STATUSES` — Initial / Pending / Validated | As above. |
| **Impact / Priority / Remediation status** | `VALID_IMPACT`, `VALID_PRIORITY`, `VALID_REMEDIATION_STATUS` | On assumptions, limitations, weaknesses and remediation. The same class as the risk bands; left behind when risk moved to policy. |
| **Validation-question statuses** | `VALID_VQ_STATUSES` | The completeness audit keys off "Addressed", but already names it in `COLLECTION_ANSWERED` rather than inlining it — so the renaming path is open. |

## Tier 2 — numbers that are policy, not platform

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

## Suggested order

1. **The nine questions** — self-contained, seed-only, no migration, highest
   adopter value.
2. **The completeness scoring** — largest, and the one with a regulatory audience.
3. **The small vocabularies as one batch**, once the key-versus-rename decision is
   made, so they all follow the same rule.

## How to stop it recurring

The question to ask of any new constant: *if an adopter renamed this, would
anything keep printing the old word?* If yes, it belongs behind a policy or an
admin list, and every surface must ask rather than spell it out. An audit rule
flagging new `VALID_*` constants used directly as display strings would make that
mechanical — worth considering once the tiers above are cleared, not before.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
