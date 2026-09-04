<!--
Copyright (c) 2022-2026 MKM Research Labs. Licensed under the MIT License; see LICENSE.
-->
# Porting: sign-off subject kinds on the MRC agenda

**Written for a Claude working on the Moody's fork.** The fork has diverged and runs on
**Microsoft SQL Server**, so the instruction "apply this change" is not enough — what
follows separates the part that is portable code from the part that is storage, and says
precisely which is which. The short version: **this change is code-only. There is no
schema migration, on either engine.** Do not write one.

Read [`../mssql-immutability.md`](../mssql-immutability.md) first if you have not — it is
the other half of the SQL Server story.

---

## 1. The defect, in one paragraph

An owner proposes a risk rating on an ML Application; the request is queued on the record,
routed to the committee covering its division, and attached to that committee's next
scheduled meeting as an agenda item. All of that worked. But the console decides which
agenda items are *decisions the committee must take* (as against its running order) by
looking for a **subject field** on the item — and its list of those fields named only
models, products and handoffs. An ML Application item carries `subject_ml_application_id`,
matched nothing, and so appeared on **no Approvals tab at all**: it fell through to the
plain agenda with no Approve/Reject control on it. The same stale list in the meeting-pack
builder put it in the running-order table instead of the sign-offs table. AI Systems had
the identical omission.

A second failure followed from the first. Because the committee could not decide the item,
meetings closed with the request still `Attached`. Superseding an open request removes its
agenda item from the meeting — and a **closed** meeting refuses amendment, so the removal
raised and the whole supersession failed. The owner then got `400 meeting is closed and
cannot be amended` on **every subsequent proposal**, permanently. That is the symptom most
likely to be reported: *"clicking MRC Approval does nothing / errors."*

## 2. Is the fork affected?

Almost certainly, if it carries ML Applications or AI Systems at all. Check three things
before porting anything — the fork may have solved it differently, and a blind port would
then be a regression:

1. `grep -rn "subject_model_id" <fork>/src/static/js/mrc/` — does the console's subject
   list name `subject_ml_application_id` and `subject_ai_system_id`?
2. `grep -rn "subject_model_id" <fork>/src/governance/mrc/` — same question for the pack.
3. Does the fork's supersession path guard on meeting status before removing an agenda
   item? Look for the caller of the agenda-item removal inside the "supersede open
   requests" routine.

Anything already true is **not new functionality** and must not be migrated.

## 3. What changed here

Four files. Nothing outside them.

| File | Change |
|---|---|
| `src/governance/mrc/_pack_signoffs.py` | **New.** Holds `SUBJECT_FIELDS` (the five subject fields) plus `subject_of()` and `signoff_ask()`, split out of `pack.py`. |
| `src/governance/mrc/pack.py` | Imports those two back under their old private names; net effect is the wider field list. (The split was forced by the 300-line rule, not by this fix.) |
| `src/static/js/mrc/detail_signoff.js` | `SUBJECT_KINDS` table replaces two hardcoded chains; two new Approvals sub-tabs, **ML Apps** and **AI Systems**. |
| `src/web/_signoff_routing.py` | `_supersede_open_requests` skips the agenda removal when the meeting is closed. |

### 3a. The subject vocabulary

The full list, which must agree in all three places (Python pack, JS console, and the
`Subject` adapters in `src/web/_signoff_subject.py`):

```
subject_model_id  subject_product_id  subject_handoff_id
subject_ml_application_id  subject_ai_system_id
```

The console's table also carries the tab label per kind, because a tab is what the user
was missing:

```js
const SUBJECT_KINDS = [
  { kind: "model",          field: "subject_model_id",          label: "model" },
  { kind: "product",        field: "subject_product_id",        label: "product" },
  { kind: "handoff",        field: "subject_handoff_id",        label: "handoff" },
  { kind: "ml_application", field: "subject_ml_application_id", label: "ML Application" },
  { kind: "ai_system",      field: "subject_ai_system_id",      label: "AI System" },
];
```

**Each kind gets its own tab.** Do not fold ML Applications or AI Systems in under Models:
they are separate records the committee decides on separately, and a rating argued over an
ML Application is not a model rating.

A test now asserts the three lists cannot drift
(`tests/web/test_ml_application_signoff.py::test_every_subject_the_routing_knows_is_a_subject_the_pack_knows`).
Port that test even if the fork's rendering differs — it is what stops the next record
type repeating this.

### 3b. The closed-meeting guard

```python
if agenda_item_id and meeting_id and _meeting_is_open(meeting_id, config):
    withdraw_agenda_item(ctx, meeting_id, agenda_item_id, config=config)
```

`_meeting_is_open` reads the meeting and compares its status to `CLOSED_MEETING_STATUS`
(`"Completed"`, from `config/governance/_mrc.py`). The request is still marked `Withdrawn`
either way; only the removal from the sealed meeting is skipped.

## 4. Database impact: none — and why that is not a guess

Agenda items are **not rows and not columns**. They live inside the meeting aggregate's
JSON document, in two places:

- `events.payload` (`JSONB` on PostgreSQL) — the append-only log, the system of record;
- `mrc_meeting_view.data` (`JSONB`) — the rebuildable projection, whose only typed columns
  are `meeting_id`, `data`, `status`, `version`, `updated_at`.

See `src/database/migrations/0004_mrc_meeting_view.sql`. `subject_ml_application_id` is a
key inside `data->'agenda'`, so widening the set of recognised keys touches no DDL. On SQL
Server, where the fork presumably maps `JSONB` to `NVARCHAR(MAX)` with `ISJSON`, the same
holds for the same reason.

**Therefore:** no `ALTER TABLE`, no new index, no backfill script, no projection version
bump. If a proposed migration plan for the fork contains a schema step for this change,
that step is wrong.

Two SQL-Server-specific things that *do* need care, but are pre-existing rather than
introduced here:

- **Rebuilding the projection is a full replay** of the meeting stream. If the fork's
  rebuild deletes and re-inserts `mrc_meeting_view`, that runs under the `DENY` regime in
  `mssql-immutability.md` — the view is writable, the log is not. Do not "fix" a rebuild
  failure by loosening the log's permissions.
- **JSON key comparison is case-sensitive** in `JSON_VALUE`/`OPENJSON` under a
  case-insensitive database collation only for the *values*, not the *paths*. If the fork
  queries agenda items in T-SQL anywhere (this codebase does not — R6 keeps SQL inside
  `src/database/`), the path `$.subject_ml_application_id` must match exactly.

## 5. Records already stranded in an existing estate

Any ML Application or AI System whose request was attached to a meeting that has since
closed is stuck at `Attached` and will refuse new proposals until this ships. **No data
repair is needed** — once the guard is in, the owner's next proposal supersedes the
stranded request to `Withdrawn` on its own and attaches the new one to the next scheduled
meeting. The sealed meeting keeps the item it was given, which is correct: it is a record
of what was tabled, not of what was decided.

To find them first (read-only; `data` is the projection, so this is safe on production):

```sql
-- PostgreSQL
SELECT ml_application_id, r->>'item_id', r->>'status', r->>'meeting_id'
FROM   ml_application_view v,
       jsonb_array_elements(v.data->'signoff_requests') r
WHERE  r->>'status' IN ('Pending', 'Attached');
```

```sql
-- SQL Server equivalent
SELECT v.ml_application_id, r.item_id, r.status, r.meeting_id
FROM   ml_application_view v
CROSS APPLY OPENJSON(v.data, '$.signoff_requests')
       WITH (item_id NVARCHAR(50), status NVARCHAR(50), meeting_id NVARCHAR(50)) r
WHERE  r.status IN ('Pending', 'Attached');
```

Cross-check each `meeting_id` against `mrc_meeting_view.status`: a `Attached` request whose
meeting is `Completed` is a stranded one.

## 6. Verifying the port

Against a **restored copy**, never the live estate (rule R9):

1. Register or pick an ML Application whose division has a committee, and schedule a
   meeting for that committee.
2. `POST /api/ml-applications/<id>/request-signoff {"proposed_rag": "Amber"}` → **201**.
3. `GET /api/meetings/<next scheduled>` → the agenda carries an item with
   `subject_ml_application_id` set and `status: "Pending"`.
4. Open that meeting → **Signoff** tab → the sub-tabs read
   `Models (n) Products (n) Handoffs (n) ML Apps (n) AI Systems (n) …`, and the ML Apps tab
   shows the row with **Approve** / **Reject**.
5. Mark the meeting `Completed` without deciding the item, schedule the next one, and raise
   a second proposal → **201**, the first request is `Withdrawn`, and the closed meeting
   still holds its item.
6. Repeat 1–4 for an AI System.

Steps 3 and 5 are API-level and are the ones that matter; step 4 is what the user actually
reported.
