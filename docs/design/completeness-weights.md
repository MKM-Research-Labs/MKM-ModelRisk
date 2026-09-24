# Design: completeness criticality weights become the division's own

**Status:** Built — agreed and complete 2026-09-24 (tasks 1–4; task 5's cases landed with
the code they test; the editor verified on the scratch estate)
**Area:** Completeness audit / Risk policy / MRC

## Decision

The criticality weights — what a missing field, collection or documentation
category is *worth* before escalation — move onto the division's risk policy, in
the `audit` section its MRC already ratifies. The firm-wide tables in
`config/governance/_completeness.py` stay as the seed and the fallback.

Until now the audit was half-configurable: *how much the record's risk position
matters* (tier weight, rating multiplier, event pressure, staleness) was the
division's to set, but *how much a missing field matters* was the platform's.

```python
policy["audit"]["field_weights"]      = {"tier": 0.80, ...}
policy["audit"]["collection_weights"] = {"validation_questions": 1.00, ...}
policy["audit"]["doc_weights"]        = {"Core Documentation": 1.00, ...}
```

**Absent key = firm-wide value**, exactly as `acceptable_at` works. A division that
overrides `"tier": 0.80` gets 0.80 for tier and the firm-wide value for everything
else. Only the division's *live* (approved) policy is read — the audit takes it from
the risk envelope (`risk["audit_policy"]`, `model_inventory/risk.py`), so a draft
changes nothing until the committee approves it.

## What checking the original note against the code changed

The note this design came from (screenshots, 2026-09-24) had the shape right and
five details wrong:

1. **The denominator.** `_rules.py:_carried()` reads the same three tables to total
   what a record *holds*. Changing only the gap functions would weigh the missing
   at one scale and the held at another, and every completeness figure for an
   overriding division would be wrong. Both sides read through one resolver.
2. **`scan.py` needs no change.** The audit section already reaches `audit_entity()`
   on the risk envelope.
3. **The validator refuses nested sections.** `_validate_audit` accepts only the flat
   numeric keys of `AUDIT_POLICY_DEFAULTS`; it is extended, not merely appended to.
4. **The report does not yet print each division's basis.** `_method.py` prints the
   firm-wide tables for everyone. That becomes false for an overriding division, so
   printing the overrides is a task of its own (3) — it is also the mitigation the
   note relied on.
5. **The range.** The note said both 0.00–2.00 and a floor of 0.10. The bounds are
   0.10–2.00, in `config/` (R1).

Found on the way: `broken_doc_escalation` was offered per division in the editor and
accepted by the validator, but `_gaps.py` multiplied by the firm-wide constant, so a
division's value was silently ignored. It is read from the policy now.

Found while building the editor: the weight table still held `analytics_model` and
`market_data_model`, fields no record carries, so the audit never scores them. What a
division may weight is therefore drawn from the record specs, not from the tables.

## Tasks

| # | Task | Files | After | Est. |
|---|---|---|---|---|
| 1 | One resolver for criticality; gap functions **and** `_carried()` read through it; `audit_entity()` passes the audit policy to both | `completeness/_weights.py` (new), `_gaps.py`, `_rules.py` | — | 1 h |
| 2 | The three sections on the policy: empty in `default_policy()`; validated — recognised names only, values within bounds | `config/governance/_completeness_weights.py` (new), `risk_policy/_defaults.py`, `commands.py` | — | 45 min |
| 3 | The report states each division's overrides beside the firm-wide tables | `completeness/_method.py` (or a companion) | 1, 2 | 1.5 h |
| 4 | Weight editor in Admin → Risk → Audit: three tables of label / firm-wide value / input, blank = firm-wide, saving into the same draft | `static/js/risk_policy_weights.js` (new), `risk_policy_draw.js`, `index.html`, a config endpoint | 2 | 2.5 h |
| 5 | Tests: override moves a gap's criticality **and** the ratio; no override is identical to today; validator refusals; draft inert, approved live; report prints overrides | `tests/governance/test_completeness_weights.py` (new) | 1–3 | 1.5 h |
| 6 | Verify on 5016 against the scratch DB; `python -m audit` and `pytest` | — | all | 1 h |

About eight hours. 1 and 2 together; 3, 4 and 5 in parallel; 6 last. Backward
compatible from the start — until a division sets a weight every audit is identical —
so backend and UI can ship separately with no flag. No data migration: a policy
approved before this change has no weights section and reads through to the config.

**R2 watch.** `config/governance/__init__.py` is at 300 lines, so the new names are
imported from their own module rather than re-exported. `_rules.py` is at 258.

## Risk

A division that sets weights low enough to trivialise a real gap. Mitigated by the
0.10 floor (nothing can be zeroed out) and by task 3: a committee that has softened
its own weights is visible in the report every other committee reads.

## Not in scope — phase 2

Per-division exempt lists, severity bands and SLA days. Bands are harder than they
look: `SEVERITY_BANDS` fixes the band order the report tallies by
(`report_sections.py`), and the dashboard's past-SLA test reads `sla_days` off each
finding, so per-division bands would put two scales in one report. Rule specs
(reviewer independence) stay in config.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
