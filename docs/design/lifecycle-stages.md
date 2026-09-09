# Design & plan: Lifecycle stages — a firm-wide catalogue, divisions choose from it

**Status:** Proposed 2026-09-09, revised the same day after the user's decision on §9
(the catalogue). **Steps 1-3 built 2026-09-09** (§6); steps 4-5 not started. The
backfill has NOT been run against the live estate — see §6a for what it found there. Written after
the user observed that Lifecycle stage is hardcoded and so is not user-defined via
Admin.
**Area:** `config/governance/_inventory.py`, three registers' rules, two new ratified
policies, the Admin editor, the MRC Approvals tab, one backfill.

## 1. What was asked

> "Lifecycle stage is hard coded and thus is not user-defined via the Admin. Can you
> complete analysis and propose a migration solution. With lifecycle changes will
> trigger a MRC approval."

Decisions taken before writing this (asked and answered 2026-09-09):

| Question | Answer |
|---|---|
| What does the MRC approve? | **The vocabulary itself** — adding, removing, renaming or reordering a stage. Not each record's stage move. |
| When does a change take effect? | **On approval.** A draft drives nothing until the committee ratifies it. |
| Firm-wide or per division? | **Per division** — divisions choose, but from a firm-wide catalogue. |
| Who owns the words themselves? | **A firm-wide catalogue, ratified by the Company-level MRC.** A division ratifies which catalogue stages it uses and in what order; it cannot coin a new one alone. |

So the stage vocabulary becomes what the risk policy, the ML review policy and the
functional groups already are — a small document a committee signs off — in two layers.
A record's stage move stays an ordinary field edit, validated against its division's
live list.

## 2. The finding is real, and it is worse than "hardcoded"

The stages are not simply hardcoded. They are hardcoded **and** admin-editable, in two
different places that no longer agree — which is worse than either alone, because the
console offers a choice the domain then refuses.

- `config/governance/_inventory.py:53` — `VALID_LIFECYCLE_STAGES`, the shipped five.
- `config/governance/_inventory.py:152` — the field spec carries both
  `options: VALID_LIFECYCLE_STAGES` **and** `reference: LIFECYCLE_STAGE_LIST`.
- `config/governance/_inventory.py:284` — `FIELD_CHOICES` is derived from `options`,
  i.e. from the frozen tuple, and `src/governance/model_inventory/_rules.py:83` is what
  validates a write against it.
- `src/web/_helpers.py:150` — `resolve_field` *replaces* those options with the admin
  list's values whenever that list has any. The dropdown is the admin list.

The two paths part company the moment an administrator adds a stage. Demonstrated
against the disposable test database (probe written, run, deleted):

```
POST /api/reference/collections/lifecycle_stage  {"value": "Decommissioning", ...}   201
GET  /api/models/fields          -> lifecycle_stage.options includes "Decommissioning"
POST /api/models/M9/field        {"field": "lifecycle_stage", "value": "Decommissioning"}
  400 {'error': 'lifecycle_stage must be one of: Pre Development, Development,
                 Validation, Production, Retired'}
```

The existing test `tests/web/test_status_vocabularies.py::test_a_stage_the_institution_adds_is_offered`
asserts the dropdown offers it. Nothing asserted it could be *saved*, which is why this
had stood. **Closed by step 1** — what follows is the analysis as it was found. The config file's own comment at `_inventory.py:49-52` predicts this exact
failure; it was written as a warning and never closed.

`docs/design/adopter-configurable-vocabulary.md:70` lists Lifecycle stages as **BUILT**.
That is half true — the label is adopter-controlled, the vocabulary is not — and the
row needs correcting whatever else is done here.

### The other direction

Removing a shipped stage in Admin takes it off every dropdown but the domain still
accepts it over the API and through ingest, and existing records keep it. So the list
an administrator curates is advisory in both directions.

### Every other place a stage is written down

| Where | What | Consequence |
|---|---|---|
| `config/governance/_ml_application.py:171` | same `options` + `reference` pair | identical drift on ML Applications |
| `config/governance/_ai_system.py:201` | same pair | identical drift on AI Systems |
| `src/static/js/inventory/list.js:26` | `LIFECYCLE_STAGES` — a **four**-item copy, missing "Pre Development" | stale duplicate; used at `list_filters.js:123` as the pre-load fallback for the register's filter |
| `scripts/seed_demo.py`, `scripts/_ef001_data.py` | literal stages in seed data | fine — seeds, not logic |
| `contracts/ingest/v1/examples/model_inventory.example.json` | `"Development"` | example only; ingest writes go through the same domain rules |

**Nothing in `src/` branches on a stage's value.** No rule says "if Production, then…".
That is the single most important fact in this analysis: the stage is inert data the
estate carries and reports on, so making the vocabulary adopter-defined has no
behavioural blast radius. Contrast `model_type`, whose `binding_role` the Product
bindings genuinely read.

`config/theme_status.py:54`'s `"lifecycle"` colour map is the **version** lifecycle
(`version_lifecycle`), not this field. Model stages have no badge colours, so an added
stage needs none.

### A gate blind spot

`audit/hardcoding.py` (R1) scans `.py` for all-caps *numeric* constants and infra
literals only. A string vocabulary — in Python or in `.js` — is invisible to it. The
audit could not have caught this and will not catch the next one.

## 3. What already exists to build on

Three per-division policies already run the exact lifecycle asked for, over one shared
implementation in `src/governance/ratified_policy.py` (180 lines):

```
<Name>Proposed  → a draft submitted for sign-off (carries the whole policy)
<Name>Approved  → the committee ratified it; it becomes the LIVE policy
<Name>Rejected  → withdrawn or declined; the live policy stands
```

`RatifiedPolicy` takes `default` (what a scope that has ratified nothing runs on) and
`validate` (what makes a policy valid) and provides everything else. Functional groups
is the closest analogue — a ratified **vocabulary** backing a record field — and it
contributes four reusable pieces:

- `src/governance/functional_groups/_store.py` — the reads (`live`, `draft`, names).
- `src/governance/functional_groups/commands.py` — propose / approve / reject and
  `_reject_removals_in_use`: a draft that would orphan records is refused at propose
  time, not at the meeting.
- `src/web/_ratified_policy_api.py` — the approve/reject routes and the registry
  payload, already written once for three policies.
- `src/static/js/helpers.js:221` `Groups` + `inventory.js:36` `inputControl` — the
  client-side per-division registry and the one hook where a field's options vary by the
  record's division. `rag_rating` uses the same hook already.

Routing needs nothing new either: `committee_at_levels(("Company",), None, None, refs)`
in `src/governance/mrc/projection.py:195` already resolves the institution-wide
committee, and the meeting AOB panel that ratifies a functional-group draft
(`mrc/detail_agenda_signoffs.js:92`) is the shape the catalogue's sign-off takes.

## 4. Target design — two layers

### 4.1 The catalogue — firm-wide, Company MRC

`LifecycleStageCatalogue`: a **singleton** ratified policy holding the institution's
whole stage vocabulary as an ordered list of `{value, label, description}`.

- **`value` is the stable key and it stays global.** Records already carry the word —
  `"Production"` is literally what is stored — and the 2026-08-10 decision recorded in
  `adopter-configurable-vocabulary.md` was to seed the key to that word so nothing has
  to be migrated. That property must survive. Values are immutable once they exist.
- **`label` is what every screen shows, everywhere.** A rename edits the label and moves
  nothing on record — exactly as today. Deliberately *not* per-division: one firm-wide
  word per stage is most of the point of having a catalogue, and a division that
  relabelled "Production" would defeat cross-division reporting at the display layer
  while pretending not to. Omitted rather than forgotten; it can be added later without
  moving any data.
- **`description` is what the stage means** — the thing the committee is actually
  ratifying, and the thing an auditor asks for. There is nowhere to record it today.
- The default is the **shipped five**, moved out of `VALID_LIFECYCLE_STAGES` into
  `config/governance/_lifecycle_stages.py`. An institution that has ratified nothing
  behaves exactly as it does today.

`RatifiedPolicy` keys on `division` throughout — parameter names and refusal wording
("a {noun} must belong to a division"). A singleton needs one small, honest change:
rename that parameter to `scope` and add a `scope_noun` field (default `"division"`) used
in the messages, so the catalogue says *"the lifecycle stage catalogue has no proposed
version awaiting sign-off"* rather than *"global has no…"*. The three existing policies
keep their own public `division=` signatures; only their internal delegation lines move
(about nine lines across three `commands.py` files). `"global"` is the established
singleton id — `MRCSettings` and `ReferenceData` both use it.

### 4.2 The division's list — which stages it uses

`LifecycleStages`: a per-division ratified policy holding an **ordered list of catalogue
values** — not a second copy of the words. Its `validate` refuses any value not in the
live catalogue.

**The default is the whole catalogue, in catalogue order.** This is the load-bearing
choice: a division that has ratified nothing offers every stage, which is precisely
today's behaviour. It makes the migration free — *no per-division backfill is needed at
all* — and it means the feature can ship before a single committee has met.

`stages_for(division)` = the division's ratified subset intersected with the live
catalogue, or the whole catalogue when the division has ratified nothing. The
intersection gives a clean invariant: **a value dropped from the catalogue disappears
from every division at once**, with no division left naming a stage that no longer
exists.

### 4.3 Validation, and the two removal rules

`src/governance/lifecycle_stages/_validate.py` gets
`reject_unknown_lifecycle_stage(value, division)`, called from the three aggregates'
`_validate_field` beside `reject_unknown_functional_group`. Blank passes — a model
registers without a stage today, deliberately (`ml_application/_rules.py:100`). The
field drops out of `FIELD_CHOICES` in all three configs.

Removing a stage records still hold is refused **at propose time**, at both layers,
reusing the shape of `functional_groups.commands._reject_removals_in_use` across all
four registers:

- **Catalogue**: refused if *any* live record in the estate holds the value.
- **Division**: refused if any live record *in that division* holds it.

A record whose stage is not in its target division's list cannot be moved there — the
move is refused naming the stage in the way, consistent with
`reject_division_move_while_grouped`. (Alternative considered: allow it and mark the
record off-policy. Rejected — it makes the register quietly wrong rather than loudly
blocked.)

### 4.4 Where each is ratified

The catalogue's draft surfaces as AOB on a **Company-level** committee's meeting; a
division's draft on that division's meeting, exactly as the functional-group draft does
now. One wrinkle to build for: `_aobPending` (`detail_agenda_signoffs.js:52`) keys on
`meeting.data.division`, and `derive_org_scope` (`projection.py:137`) gives a
Company-level meeting **no** division — so today a Company-level meeting surfaces no
ratification AOB at all. The catalogue panel's predicate is the committee's `level`,
read from the `mrc` reference list the console already loads, not the absence of a
division.

## 5. What does NOT change

- **A record's stage move stays an ordinary field edit.** Per §1 the committee ratifies
  the vocabulary, not each move. `_change.py:199` keeps `lifecycle_stage` as a
  **Bounded** change (movement inside an approved envelope) — a classification that
  reads better once the envelope is literally a document a committee approved. If gating
  individual moves is ever wanted, the hook is `set_record_field`
  (`src/web/_owner_ratification.py:94`), which already does exactly this for `owner`.
- The stored values. Nothing in the estate moves.
- The completeness audit (`_completeness.py:115`), the change register, the dashboards
  and every export — all read the stored value.

## 6. Migration, in five steps

Each step is independently mergeable and leaves the tree green.

**Step 1 — close the drift — BUILT 2026-09-09.**
`live_choice_values` in `src/governance/reference/_validate.py` is now the one rule both
sides use: a choice field whose `reference` names a list with entries takes its allowed
values from that list, and keeps its shipped options only while the list is empty. The
three aggregates' `_validate_field` call it in place of reading `FIELD_CHOICES`. The
console's promise and the domain's answer agree from here on, and every later step is a
change of *where the list comes from*, not of whether it is honoured.

Two departures from what this step originally proposed, both found in the writing:

- **`reject_unknown_references` was not reused.** It compares a stored value against the
  list's *display* field, and a status vocabulary displays `label` while records store
  `value` — so it would have refused every write the moment anybody renamed a stage. It
  also treats an empty list as unenforced, which on a fresh database opens the field to
  free text (§7's first trap). `live_choice_values` reads under `value_key` and falls
  back to the shipped words, which is exactly what `resolve_field` does.
- **`validation_status` was fixed with it.** It is the same shape and carried the same
  defect; the affected pairs are `lifecycle_stage` and `validation_status` across all
  three registers. Excluding it would have taken extra code.

`model_inventory/_rules.py`'s docstring claimed "No I/O happens here", which stopped
being true when the risk fields began reading the division's ratified policy. Corrected
in the same commit rather than left standing over code that reads the admin list.

**Step 2 — `scope` on `RatifiedPolicy`, then the catalogue — BUILT 2026-09-09.**
`RatifiedPolicy` keys on `scope`, and `scope_noun=None` marks a singleton: its refusals
then read *"there is no proposed lifecycle stage catalogue awaiting sign-off"* rather
than naming the fixed id it is stored under. The three existing policies pass
`scope=division` and are otherwise untouched — their 81 tests were green without
modification, which is the whole test of a behaviour-neutral rename.

Then `config/governance/_lifecycle_stages.py` (the catalogue's shape, its default, and
its keys) and `src/governance/lifecycle_stage_catalogue/` (store + commands), tested and
reading nothing yet. Two checks look outside the catalogue, both at propose time: a
stage records hold cannot be removed, and a stored **value** cannot be renamed — the
second is not in functional groups, which mints ids nobody types, and is needed here
because the value IS the key and a rename would orphan every record in the stage.

**Step 3 — backfill the catalogue — BUILT 2026-09-09, NOT YET RUN.**
`scripts/backfill_lifecycle_catalogue.py` builds the first catalogue from *the current
global reference list* — not from the shipped tuple — so an adopter who has already
renamed "Production" to "Live", or added a stage, keeps it. Dry run by default, `--apply`
to write, and it prints the database it resolved to before doing either.

It ratifies **without a meeting**, deliberately: what it carries over is the vocabulary
already in force across the estate, and asking a committee to ratify the status quo
before the feature works at all is ceremony. The event names the backfill as its author,
so the trail says plainly that no sitting agreed it; what a committee ratifies is the
first change *after* this.

Quiet when there is nothing to do — an already-ratified catalogue, an outstanding draft
(a committee mid-decision, which it must not settle underneath), an unseeded list, or a
list that still matches the words the catalogue already defaults to. **No per-division
backfill**: §4.2's default covers every division that has ratified nothing, which on day
one is all of them.

### 6a. What the dry run found on the live estate

Run read-only against `mkm_modelrisk` on 2026-09-09 (nothing written):

```
   Demo               Development   Validation   Production   Retired
 + Pre Development
```

Two facts nobody had written down, and both matter:

- The estate has added a stage — **"Demo"** — which before step 1 was offered on every
  dropdown and refused on save. Step 1 makes it saveable.
- **"Pre Development" has been removed from the admin list, but records are still in
  it.** So the backfill carries it back into the catalogue, because a catalogue that
  omitted it could not be proposed at all — the domain refuses to drop a stage records
  hold.

That last point has a consequence worth deciding before the backfill is run for real:
carrying the stage back in **re-offers it on every dropdown**, undoing what looks like a
deliberate removal. Step 4 resolves it properly — the catalogue may hold a stage that no
division's ratified subset offers, which is exactly the shape this needs — but until
step 4 exists there is no such subset. Options: run the backfill after step 4; or move
those records to another stage first; or accept the stage reappearing for the interval.

**Step 4 — switch the readers.**
`src/governance/lifecycle_stages/` (the per-division layer); three `_validate_field`s
call `reject_unknown_lifecycle_stage`; `lifecycle_stage` leaves `FIELD_CHOICES`; the
field spec's `options` becomes the catalogue default and the console overrides per
division through a `Stages` registry beside `Groups` (`helpers.js`) and the one
`inputControl` hook (`inventory.js:36`). Delete `inventory/list.js:26`'s stale four-item
copy and read the filter's values from the registry. Retire the global `lifecycle_stage`
reference list **last**, once nothing reads it, leaving `STATUS_VOCABULARIES` to the six
lists that remain firm-wide.

**Step 5 — the committee surfaces.**
The Admin editor (`lifecycle_stages.js`, shaped on `functional_groups.js`, with the
catalogue and the per-division subset as two panes), the two AOB ratification panels,
and the row in the MRC pack. Then correct `adopter-configurable-vocabulary.md:70` and
add the stages to `docs/user_guide.md`.

## 7. Traps

- **`resolve_field` falls back to a free-text box when a reference list is empty**
  (`_helpers.py:150`, and the warning in `_functional_groups.py`). That is how an estate
  acquires "Production", "production" and "Prod". Keep the field spec's static options
  as the catalogue default rather than emptying them the way `functional_group` does.
- **Order is part of what is ratified**, at both layers. Every dropdown offers the list
  in order and "Pre Development" is first for a reason (`_inventory.py:46`).
- **The label/value split must survive.** A rename edits `label`; `value` is immutable
  once an entry exists. Today the domain enforces that on the reference item
  (`test_the_stored_value_cannot_be_edited`); the catalogue's `validate` has to enforce
  the same, or a committee could approve a draft that orphans every record in a stage.
- **A Company-level meeting has no division** (§4.4). Anything keyed on
  `meeting.data.division` will silently never fire for the catalogue.
- **R2 headroom.** `_inventory.py` is at 288 lines and `_reference.py` at 293; both are
  edited here. Moving the stage vocabulary into its own
  `config/governance/_lifecycle_stages.py` takes lines *out* of both, which is the
  natural seam rather than a splitting exercise. `api_mrc/signoff.py` (295) and
  `_signoff_routing.py` (284) are untouched under §1's decisions.
- **`kill -HUP` does not reload Python** (CLAUDE.md §4). Restart `dev_app.sh` when
  verifying on 5016.

## 8. Tests

- ~~The drift, both directions: a stage the institution adds **saves**; a stage it
  removed is refused (the two tests that would have caught this).~~ **Done in step 1**,
  with five more: the registration path, `validation_status`, the unseeded fallback, and
  one apiece for ML Applications and AI Systems.
- ~~A draft drives nothing, at both layers~~ / ~~a proposal dropping a stage records
  hold is refused, naming them~~ / ~~the singleton's refusal names no scope~~ —
  **done in step 2** (16 tests), with the value-immutability rule and the
  label-rename-moves-nothing case.
- ~~The catalogue backfill is idempotent and preserves an adopter's renamed labels.~~
  **Done in step 3** (9 tests), including the draft it must not walk over and the stage
  the estate holds but the list has dropped.
- ~~`RatifiedPolicy`'s three existing policies are unchanged by the `scope` rename.~~
  **Done in step 2** — their 81 tests passed unmodified.

Still to write, with step 4:

- A division may not ratify a stage that is not in the catalogue.
- A division that has ratified nothing offers the whole catalogue, and registers, edits
  and reports exactly as today (the default path — the migration-free guarantee).
- A stage dropped from the catalogue leaves every division's list at once, including a
  division that had ratified a subset naming it.
- A division move carrying a stage the target does not use is refused.

And on every step: `python -m audit` reads `PASS: 0 gated finding(s)`, and `pytest` is
green, on the merged tree before the push.

## 9. Settled

The question this document was first written with — whether a division could coin its
own stage values — is answered: it cannot. The catalogue is firm-wide and the Company
MRC owns additions to it; a division ratifies which of those stages it uses and in what
order. Two divisions can no longer coin "Decommissioning" and "Decommissioned" for the
same thing, and an estate-wide count of a stage means one thing everywhere.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
