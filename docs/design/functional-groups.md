# Design & plan: Functional Groups — grouping a register by function

**Status:** Proposed 2026-09-07, revised the same day after the user's decisions
(§9). Nothing built.
**Area:** a new MRC-ratified per-division policy, all four registers, the list
screens

## 1. What was asked

A new field, **Functional Group**, on Models, Products, ML Applications and AI
Systems. It groups records by *function* — "Storm Generation", "Flood Simulation",
"Instrument Pricer" — and is deliberately not Type. Type says what a model *is*
(Analytical, Curve, Market Data) and drives Product bindings through its
`binding_role`; a Functional Group says what a model is *for*.

The Models screen then leads with the groups. A reader sees a short list of them
and expands one to reach its models, instead of one long table.

The groups are defined per Division, in Admin, and **the list is ratified by that
division's MRC**. A record belongs to exactly one group, and groups do not nest.

## 2. The decision that shapes everything: MRC ratification

Making the list MRC-ratified takes this off the cheap path and onto the deliberate
one, and it is worth being explicit about what that costs and buys.

A **reference list** (Type, Vendor, Codebase, the status vocabularies) is edited in
Admin and takes effect immediately. Adding one is a config change: no storage, no
API, no lifecycle. `line_of_business` is already exactly the shape a Functional
Group would need — a named item that carries a division — so that route would have
been perhaps a day's work.

A **ratified policy** is a different mechanism entirely. `RatifiedPolicy`
(`src/governance/ratified_policy.py:69`) is one event stream per division,
`Proposed → Approved → Rejected`, where the draft drives nothing and the last
approved version is what records use. Two things already run on it — the risk
policy and the ML review policy — and its docstring says why:

> both are worthless if an owner can change them the week before an inspection

That is the argument for ratifying the group list too. If an administrator can
silently re-cut the functional groups, then "these four models are the Flood
Simulation stack" is an assertion nobody stands behind, and a regulator asking who
agreed the estate is carved up this way has no answer. Ratified, the carve-up is a
committee decision with a date and a meeting id on it.

**What it costs:** a new governance package, an API, an Admin editor, a sign-off
block on the meeting agenda, and a client-side registry — roughly the shape of
`ml_review_policy`, which is 264 lines of Python across three files plus 184 lines
of editor. Call it three to four times the reference-list route.

**What it buys, beyond the governance:** the options no longer come from
`resolve_field`, and that removes the worst trap in the first draft of this plan. A
reference-backed field degrades to a **free-text box** when its list is empty
(`src/web/_helpers.py:159`), and strictness is not enforced against an empty list
either (`src/governance/reference/_validate.py:63`) — so on day one the estate
could have acquired "Storm Generation", "Storm generation" and "Storm Gen" as three
groups. A policy-backed field has no such fallback: it renders an empty dropdown
until the MRC has ratified a list, which is the honest state of affairs.

### Store the id, show the name

The policy carries `{id, name, description}` per group and a **record stores the
id** (`FG-003`), not the name.

This is the "stable key + label" pattern that `docs/design/adopter-configurable-vocabulary.md`
identifies as correct and records as expensive, because every existing status
vocabulary had records already carrying the displayed word. **Here it is free:**
`functional_group` is a brand-new field, no record carries anything yet, so there
is nothing to migrate. Taking the cheap option now would mean paying for it later.

It matters more than usual under ratification. Renaming a group needs a committee
sitting, so renames will be rare and consequential — and if records stored the
name, the sitting that approved "Flood Simulation" → "Inundation Modelling" would
silently orphan every model in it. Storing the id means a ratified rename moves
nothing on record and every screen updates at once.

**Removal is the case that genuinely orphans records**, and the answer is to catch
it before the committee ever sees it: refuse a proposal that drops a group still in
use, naming the records that hold it. `RatifiedPolicy.propose` already validates
before appending (`ratified_policy.py:143`), so the draft never reaches an agenda
in a state the committee would have to reject on a technicality.

## 3. Why the rest of it is cheap

Three mechanisms in the tree fit this exactly, and they are why only the
ratification half is new work.

**Per-division field validation already exists, in all four registers.** Each
register's `_rules.py` has an identical `_validate_field(field, value, division)`
and a `_POLICY_CHOICE_FIELDS` table mapping a field to a function that extracts its
allowed values from the division's policy (`model_inventory/_rules.py:51`,
`product/_rules.py:55`, `ml_application/_rules.py:47`, `ai_system/_rules.py:52`).
That is how `materiality`, `complexity` and `rag_rating` are checked against the
division's risk bands. `functional_group` is one more entry, reading a different
policy. The division is already threaded in, including the case where the division
itself is the field being edited (`model_inventory/_rules.py:113`).

**Per-division options already reach the browser the same way.** `Policy` in
`src/static/js/helpers.js:86` loads every division's live risk policy once at
startup (`main.js:131`) and resolves by the record's division; `inputControl`
(`src/static/js/inventory.js:26`) branches on field key to source its options from
that rather than the field spec; and `DetailShell.fieldEditor` passes the record's
division into it (`src/static/js/detail_shell.js:108`), which all four detail
screens already do. A Functional Group dropdown is a second registry beside
`Policy` and one more branch in `inputControl`.

**The grouped, expandable list already exists on the dashboard.**
`src/static/js/dashboard.js` draws a collapsed row that names what it spans, a
List/Hide toggle (`:126`), members indented beneath it (`_members`, `:147`) and
`_expanded` state keyed by group (`:45`). The CSS is written
(`src/static/css/app.css:251`). The Models list should look like that rather than
like a new invention.

**And three of the four registers share one list engine.** `InventoryList`
(`src/static/js/inventory/list.js`) is config-driven and `createRecordList`
(`:167`) makes an instance per register; ML Applications (`mlapp.js:96`) and AI
Systems (`aisystem.js:95`) are already instances. Grouping written once in
`_renderTable` (`:131`) serves all three.

**Database changes: none.** A policy is an event stream, and `RatifiedPolicy` folds
it on read with no projection table — the same as the risk policy and the ML review
policy, neither of which has a migration. A record's fields live in a JSONB `data`
column that `rebuild_*_view` copies wholesale. No DDL, no projection edit, no
backfill of existing rows.

**The four `/fields` endpoints: no change.** They pass their spec dict through
`grouped_field_specs`, and a `choice` field with empty static options survives that
untouched — exactly as `materiality` does.

## 4. Where the work actually is

| Where | Why |
|---|---|
| **The ratification loop is all new** | A governance package, an API, an Admin editor and a meeting sign-off block. Modelled on `ml_review_policy`, which is the smaller of the two existing consumers. |
| **Products is not on the shared list engine** | `src/static/js/product.js:122-154` hand-rolls its `<tr>` strings and its `<thead>` literal. It has no filters, no sorting and no tiles. It cannot inherit grouping without being migrated first. |
| **Detail screens are hand-curated** | A field in config appears in the API payload and the generated PDFs but on **no screen** until its key is added to `OVERVIEW_LEFT` (`inventory/detail_core.js:31`) and the three equivalents. CLAUDE.md §4 says this; it is still true. |
| **`PRODUCT_EDITABLE_FIELDS` is hand-written** | The other three derive `EDITABLE_FIELDS` from the spec keys. Adding `functional_group` to `PRODUCT_FIELD_SPECS` alone yields a field that renders and whose edit is refused with `field not editable: functional_group` (`src/governance/product/_rules.py:124`). |

## 5. Phases

Each step follows the house contract: **Goal** (one sentence), **Steps** (config
first, then domain, then API, then UI, then tests — that order is R1), **Verify**
(named tests and the screen to look at), **Done when** (one mechanical check).

**F1–F3 are one closed loop and only mean something together**: until a division's
MRC has ratified a list, there is nothing for a record to be assigned to. Nothing
is visible on a register until F4.

---

### F1 — The policy: store, commands, API, and the field's server side — **BUILT**

**Goal.** A division can have an ordered list of functional groups, proposed and
ratified through the same lifecycle as its risk policy, and a record can be filed
under one of its own division's groups.

**Scope note (2026-09-07).** F1 was first written as the policy alone, with the
field's server half in F4. That could not be tested: F1's central safety check is
that a group still in use cannot be removed, and nothing can be in use until a
record can hold one. Rather than ship an untested guard, the field's **server**
side moved into F1 — the four field specs, `PRODUCT_EDITABLE_FIELDS`, and the
domain validation. The field is on no screen (F4 still owns every UI edit), so
nothing is half-delivered to a user; what moved is only what the guard needs to be
provable.

**Steps.**

- **a. Config** — new `config/governance/_functional_groups.py`:
  `FUNCTIONAL_GROUPS_AGGREGATE = "FunctionalGroups"`, `FUNCTIONAL_GROUPS_NOUN`,
  `FUNCTIONAL_GROUP_ID_PREFIX = "FG"`, and `default_functional_groups()` returning
  an **empty list**. Its own module, not `_reference.py`, which has 7 lines of
  headroom against R2.
- **b. Domain** — new `src/governance/functional_groups/`, three files mirroring
  `src/governance/ml_review_policy/` exactly: `_store.py` holding
  `POLICY = RatifiedPolicy(...)` plus `load`/`live`/`groups_for`, `commands.py`
  holding `propose_functional_groups` / `approve` / `reject` with the validator,
  and `__init__.py`.
- **c. Validation, at propose time.** A group needs a non-empty `id` and `name`;
  ids are unique within the division and never reused; a name is unique within the
  division, because two groups a reader cannot tell apart are not two groups. Then
  the estate check: **refuse a proposal that removes a group any record still
  holds**, listing them. That check needs a read of the four registers, so it lives
  in `commands.py` around `POLICY.propose` rather than in the `validate` callable,
  which sees only the policy.
- **d. API** — new `src/web/api_functional_groups.py`, five endpoints mirroring
  `api_ml_review_policy.py` (112 lines): `GET /api/functional-groups` (the registry
  — every division's live list plus its `state`, which is what the console loads at
  startup), `GET /api/functional-groups/<division>` (live + draft + state + how many
  records hold each group, so the editor can show what a removal would cost before
  it is attempted), and `POST .../propose|approve|reject`. Registered in
  `src/web/app.py`.
- **e. The field, server side** (moved from F4, see the scope note): the four field
  specs, `"functional_group"` added to the hand-written `PRODUCT_EDITABLE_FIELDS`,
  and a `reject_unknown_functional_group` branch in each register's
  `_validate_field`. The rule is written once in
  `src/governance/functional_groups/_validate.py` and called from all four, because
  four copies of a rule is how the `/fields` handlers came to disagree.

**Shape.**

```python
# The policy payload for one division.
[{"id": "FG-001", "name": "Storm Generation",
  "description": "Hazard generation for windstorm and surge."},
 {"id": "FG-002", "name": "Flood Simulation", "description": ""}]
```

**Verify.** `tests/governance/test_functional_groups.py` (26),
`tests/governance/test_functional_group_field.py` (25, each case run against all
four registers) and `tests/web/test_functional_groups_api.py` (7).

**Done when** `GET /api/functional-groups` returns a keyed registry and the suite
and audit are green. **Done 2026-09-07.**

**What it also turned up.** Three of the four registers derive their editable-field
tuple from the spec keys and Products writes its out by hand, so the field rendered
everywhere and Product edits were refused — the trap §4 predicted, caught by a check
rather than by a screen. And the ratification API was about to become a third copy
of the same approve/reject pair and registry body, so those moved to
`src/web/_ratified_policy_api.py` and the risk and ML review policies were migrated
onto it in the same change (R8: 25 clones back to 24, none of them in the new code).

---

### F2 — Admin → Functional Groups — **BUILT**

**Goal.** An administrator can draft a division's list and see that it is waiting
on the MRC.

**Steps.**

- **a.** New `src/static/js/functional_groups.js`, modelled on
  `src/static/js/ml_review_policy.js` (184 lines) rather than the risk editor,
  which is the more elaborate of the two: a division selector across the top, then
  add / rename / describe / reorder / remove rows. Every edit auto-saves as a draft
  via `POST .../propose`, exactly as `RiskEditor._save` does
  (`risk_policy.js:55`).
- **b.** The seed / draft / approved banner, the same one the Risk editor carries.
  This is the control that stopped a whole class of confusion last time: an admin
  edit that is still a draft otherwise looks like it never arrived.
- **c.** `src/static/js/reference.js:28` — `["functional_groups", "Functional
  Groups"]` in `_TABS`, and a branch in `_renderBody` beside the `risk` and
  `ml_review_policy` ones (`:108`, `:114`), because this is an editor and not a
  plain list.
- **d.** A `<script>` tag in `src/templates/index.html`. **A new script tag needs a
  server restart** — Jinja caches `index.html` with `debug=False` (CLAUDE.md §4).

**Verify.** In the running app on 5016 against a restored scratch database.

**Done 2026-09-07**, verified against the real PhysicalRisk estate: added Storm
Generation / Flood Simulation / Instrument Pricer, ids minted server-side
(FG-001..003), banner *draft*; approved through the API; filed the live model
MKM-BRF-001 under FG-001; reload showed **Approved**, "1 record" beside that group
and its Remove withheld; reordering moved a group without disturbing its id; and
renaming FG-001 to "Storm & Surge Generation" put the change in the **draft** with
the live list unchanged and the model **still filed as FG-001** — the store-the-id
design demonstrated on a real record rather than argued for.

**What it also turned up.** The app had **no `:disabled` styling at all**. The
withheld Remove was genuinely inert and looked identical to a live button, which
reads as a broken screen rather than as a guard — and the gap was never this
screen's: the identity dialog's Confirm and the report generators disable buttons
the same way. One shared rule in `app.css` covers all of them.

---

### F3 — Ratification at the division's MRC — **BUILT**

**Goal.** The committee approves the draft and the list goes live.

**Steps.**

- **a.** The draft surfaces as a one-off item under **AOB** on the division's
  scheduled meeting, exactly as the risk categorisation does
  (`mrc/detail_agenda_standing.js:77` calls `_categorisationAob`, defined in
  `mrc/detail_core.js:203`). Approve → live; Reject → the draft is withdrawn and
  the live list stands.
- **b.** `mrc/detail_core.js` is at 240 lines against R2's 300 and already holds
  `_categorisationAob` and `_decidePolicy`. A second sign-off block goes in a new
  `mrc/detail_agenda_signoffs.js` — and the honest move is to take the
  categorisation one with it, since one AOB item carrying two ratifications is one
  subject, and leaving one behind guarantees they drift.
- **c.** The meeting loads the division's functional-group state alongside its
  categorisation (`detail_core.js:65`).

**Shape.** `FunctionalGroupsApproved` carries `{policy, meeting_id}`, so "the
committee agreed this carve-up" names the sitting.

**Verify.** `tests/web/test_functional_groups_api.py` covers the endpoint; the
agenda block is browser JS and was verified in the app.

**Done 2026-09-07**, against the real PhysicalRisk estate on the scheduled meeting
MRC-PR-Q2: the pending draft appeared under AOB as "Functional groups sign-off —
PhysicalRisk" listing all three groups; the risk-categorisation block stayed
correctly absent (that division's categorisation is already approved, so there was
nothing to ratify); Approve made the list live, cleared the draft, recorded
`approved_at`, and removed the block. The event log carries
`FunctionalGroupsApproved ... meeting=MRC-PR-Q2` — "which sitting agreed this" is
answerable, which is the whole point of ratifying it. The model MKM-BRF-001 stayed
filed as FG-001 across the rename going live.

**No visual**: the browser pane was hidden on the user's side for this phase, so
the page did not paint and every screenshot came back blank. Verified through the
DOM and the event log instead.

**Structure.** The categorisation block moved out of `mrc/detail_core.js` with the
new one, into `mrc/detail_agenda_signoffs.js` — one agenda item carrying two
ratifications is one subject, and the shell had no room for the second. The shell
drops 240 → 202 lines. Both blocks share `_aobPanel`, so a third ratification is a
few lines rather than a third copy.

---

### F4 — The field on all four records — **BUILT**

**Goal.** Every record carries one Functional Group, chosen from its own division's
ratified list.

**Steps.** Its server side landed in F1 (see that phase's scope note); what is left
is every screen.

- **d. Client registry.** A `Groups` object in `src/static/js/helpers.js` beside
  `Policy`, loaded from `/api/functional-groups` in the same `Promise.all` at
  `main.js:131`. It answers `optionsFor(division)` (`{value: id, label: name}`) and
  `nameFor(id, division)`.
- **e. `inputControl`** (`src/static/js/inventory.js:26`) — one more branch,
  submitting the **id** and showing the **name**, which is the shape the function
  already uses for the `tier` band picker (`:40`).
- **f. Detail screens, four hand edits.** `OVERVIEW_LEFT`
  (`inventory/detail_core.js:31`), `PRODUCT_OVERVIEW_ORG`
  (`product/detail_core.js:26`), `_LEFT` (`mlapp/detail_core.js:87`) and `_RIGHT`
  (`aisystem/detail_core.js:39`). Displaying the value resolves the id through
  `Groups.nameFor`.
- **g. Register forms.** Add `functional_group` to the four `*_REGISTER_FIELDS`
  tuples. Three of the register forms are spec-driven and need nothing else; the
  **Models register overlay is hand-written HTML** (`src/templates/index.html:74-90`
  plus `_populateTypePicker` at `inventory.js:130`), so it needs a picker method of
  its own, populated from the division the nav currently has selected.

**Verify.** The domain half is `tests/governance/test_functional_group_field.py`
(landed in F1). The screens are browser JS and were verified in the app.

**Done 2026-09-07**, all four screens against the restored estate: a Model showed
"Storm & Surge Generation" for its stored FG-001 and was refiled to Flood
Simulation through the picker, which moved the Admin editor's count with it; an ML
Application and a Product showed the row unfiled and editable; an AI System
registered for the check showed "Instrument Pricer" for FG-003. The picker offers
NAMES and submits IDS, in the order the committee ratified, and a division whose
MRC has ratified nothing gets a disabled control saying so rather than an empty
dropdown that looks broken.

Displaying it is one branch in `DetailShell.fieldValue`, which all four screens
already share — so the id → name resolution is written once rather than four
times.

**Register forms deferred — deliberately, and this is a scope cut.** Step (g)
assumed the field could join the four `*_REGISTER_FIELDS` tuples. It cannot, not
cheaply: on three of the four registers `division` is chosen *in the same form*, so
a group picker there needs a division → group cascade, and the spec-driven register
forms render every field once from a flat list with no notion of one field
depending on another. Building that is real work that was not costed here, and it
buys only the convenience of filing at registration — the field is fully editable
on the detail screen the moment the record exists. Doing it for the Models overlay
alone (where the division comes from the nav, so no cascade arises) would have left
the four registers inconsistent, which is the thing this codebase keeps paying to
undo. Left for its own step if wanted.

**No visual**: the browser pane stayed hidden, so nothing painted. Verified through
the DOM.

**A probe that lied.** The first check reported the Functional Group row on the ML
Application and the Product both reading "Flood Simulation" — a value only the
*model* had. A bare `getElementById("row-functional_group")` had returned the row
from the model panel still in the document, which is precisely what
`DetailShell.fieldEditor` documents and guards against. Scoping the lookup to the
visible panel gave the right answer. Worth recording because the wrong answer
looked like a working feature.

---

### F5 — The grouped Models list — **BUILT**

**Goal.** The Models screen opens on functional groups, and expanding one reveals
its models.

**Steps.**

- **a.** New `src/static/js/inventory/list_groups.js` — `_renderTable` grows a
  `_cfg.groupBy` branch, defaulting off, so a register that does not set it renders
  exactly as today. Group rows carry the group name, its record count and a roll-up
  of what a reader needs at a glance (worst risk rating in the group, how many are
  overdue); `_expanded` state per group; members as indented rows. Its own file
  because `list.js` is 176 lines and `list_filters.js` 196, both gated at 300.
- **b.** Group order is the **ratified policy's order**, not alphabetical. A
  committee that arranged the list arranged it for a reason.
- **c.** Records with no group go into an **Ungrouped** bucket, rendered last and
  visually distinct. On the day this ships that is every record, so the empty state
  is the normal state until F7. It must read as work to do, not as an error. So
  must a division whose MRC has ratified nothing — there the grouped view should
  say so and fall back to the flat table rather than showing one enormous Ungrouped
  bucket.
- **d.** Grouping is off when a filter or a search term is active — a reader who
  has typed a name wants the matching rows, not three collapsed groups they must
  open to find them. Sorting a column likewise flattens. Both are toggles back to
  the flat table, not a second code path.
- **e.** Expansion state survives a re-render but not a reload. There is no
  precedent for persisting UI state here and none is needed.

**Verify.** Browser JS, so verified in the running app on 5016 against the restored
estate.

**Done 2026-09-07.** The Models screen opens on **four rows instead of
twenty-four**: Storm & Surge Generation (2), Instrument Pricer (1), Flood
Simulation (1), Ungrouped (20) — in the order PhysicalRisk's committee ratified,
not alphabetical, with Ungrouped last. Counts sum to the unfiltered total.
Expanding shows the members indented; the toggle flips Show/Hide; a search term
flattens to plain rows and clearing it regroups **with the open group still open**;
sorting by Name sorts *within* the group; a member row still opens the record.
AI Systems groups the same way from one config line. ML Applications, which has
nothing filed, falls back to the flat table under "No ML Applications have been
filed under a functional group yet."

**One deliberate change from the plan.** Step (d) said sorting a column should
flatten the view, as a filter does. It should not, and does not: sorting is how a
reader browses *within* the structure, and throwing the structure away at the first
header click makes the grouped view something you leave by accident and cannot
easily get back to. Sorting now sorts within each group; only a search or filter
flattens, because there the reader is looking for a specific record rather than
browsing.

**The group key is the division AND the id**, never the id alone — ids are minted
per division, so PhysicalRisk's FG-001 and Analytics' FG-001 would otherwise be
drawn as one group. Where the visible set spans divisions the group row names its
division too, since two divisions may both have a "Pricing" and mean different
things.

---

### F6 — The other three registers — **BUILT**

**Goal.** ML Applications, AI Systems and Products group the same way.

**Steps.**

- **a.** ML Applications and AI Systems: set `groupBy: "functional_group"` in their
  `createRecordList` config (`mlapp.js:96`, `aisystem.js:95`) and add a column. Two
  lines each — they are already instances of the engine.
- **b.** **Migrate Products onto `createRecordList`.** `product.js:122-154` becomes
  a config plus a column table, and its `_summary()` tiles become `extraTiles`.
  This is the largest single piece of work in the plan and is worth doing on its
  own merits: Products is the only register with no filters, no sorting and no
  clickable tiles, and this is the third time that asymmetry has cost something.
- **c.** Then Products sets `groupBy` like the rest.

**Verify.** `tests/web/test_product_api.py` unchanged and green — the migration is
client-side only. Then all four screens in the app.

**Done 2026-09-07.** Products is on `createRecordList`: tiles, filters, sorting and
functional-group headings for the first time. It keeps its own columns (Identifier
and Components are facts no model has) and its own status counts through
`extraTiles`, where they belong — Active/Proposed/Suspended mean nothing on a
model. **No register renders its own `<table>` markup any more.** (a and c landed
with F5, which set `groupBy` on all three engine registers at once.)

**One thing the migration needed.** The shared filter assumed every register has a
`lifecycle_stage`; a Product is Active or Suspended and has none, so it would have
been offered a model's stages and matched no record. The field the filter reads is
now `_cfg.statusField`, with `_cfg.statusFilterLabel` beside it — spelled out
rather than derived, because "All lifecycle stage" and "All status" both read
wrong. Products offers Proposed / Active / Suspended / Retired under "All
statuses"; the other three are unchanged under "All lifecycle".

**And one regression it caused, found by looking.** Adding Criticality and Risk
Rating narrowed the Status column until "Proposed" broke across two lines inside
its pill and read as damage. `productStatusBadge` now sets `white-space: nowrap`.
No test would have caught that — only the screen.

---

### F7 — Assigning the estate — **BUILT** (awaiting your mapping)

**Goal.** Existing records acquire groups.

**Steps.**

- **a.** A backfill script on the house template
  (`scripts/backfill_version_register.py`): dry-run by default, `--apply` to write,
  writing through `update_model_field` and never SQL (R6), and **calling
  `rebuild_inventory_view()` at the end** — a backfill from a bare script leaves
  the read models stale. Rehearsed against a restored scratch database (R9).
- **b.** There is no honest derivation of a functional group from existing data, so
  the script applies a mapping you supply and reports what it cannot place rather
  than guessing. It cannot start until the divisions have ratified their lists, so
  this phase genuinely follows F3 rather than merely being scheduled after it.

**Verify.** `tests/test_backfill_functional_groups.py` (14), plus a rehearsal
against the restored scratch database.

**Built 2026-09-07.** `scripts/backfill_functional_groups.py` takes a two-column
CSV of `record_id,group` and does exactly that, covering all four registers.
`group` is the group's NAME as its division ratified it — matched
case-insensitively — or its id, for anyone reading them off the Admin screen.
Resolution is per the RECORD's division, so a name only another division uses
cannot reach across.

Every mapping row comes back with a verdict, including the ones it will not touch,
because a backfill whose refusals you cannot read is one you have to run to
understand: `file`, `already`, `filed-elsewhere`, `no-such-group`, `no-groups`,
`unknown`, `refused`. Dry by default; `--apply` writes; `--refile` is what moves a
record somebody already filed elsewhere, and it has to be asked for — the decision
made on the screen outranks the mapping.

Rehearsed on scratch: filed three, skipped the one already filed elsewhere, was a
no-op on re-run, and `--refile` then moved it. The group counts came back changed
through the API, which is the check that matters — it proves the read models were
rebuilt and not just the event log written.

**Still awaiting the mapping**, which is the one thing that cannot be derived. The
rehearsal also showed why the format takes names: a mapping row saying "Storm
Generation" correctly failed after the committee had ratified the group as "Storm &
Surge Generation".

## 6. Two holes worth knowing about

**Moving a record between divisions — CLOSED in F1, and worse than described.**
The plan first called this an orphan: `decide_update_field` re-validates only the
field being edited (`model_inventory/_rules.py:101`), so changing `division` would
leave `functional_group` pointing at a group the new division does not define.

Writing the tests showed it is not an orphan at all. **Ids are minted per division**,
so PhysicalRisk and Analytics both have an `FG-001` and they are different groups. A
record carried across with its group still set does not end up holding a dangling
reference a screen could show as ungrouped — it silently acquires the new division's
group of the same number, and nothing about the record looks wrong while it is
counted, filtered and reported under a group nobody filed it in.

So this was not a decision to defer. F1 refuses a division change while a group is
set (`reject_division_move_while_grouped`), telling the caller to clear it first.
That is one extra edit on a rare and consequential change, and being asked where the
record now files is the right thing to be asked. The equivalent hole for
`materiality` and `complexity` is still open — those resolve against the risk policy
by *name*, so a move leaves a band name the new division may not define. Out of
scope here, but now the better documented of the two.

**The completeness audit will report every record as incomplete.**
`src/governance/completeness/_gaps.py:110` scores every field spec not in
`EXEMPT_FIELDS`, at `DEFAULT_FIELD_CRITICALITY = 0.40`
(`config/governance/_completeness.py:47`), so adding `functional_group` to four
spec dicts raises a finding against the whole estate the moment F4 merges. You said
you would work through it, so this plan does **not** exempt the field — it is noted
here only so the number moving is expected rather than alarming, and so nobody
later reads it as a regression.

## 7. What this does not touch

- **Type.** Untouched. A Functional Group is orthogonal, and in particular nothing
  about `binding_role` or the Product bindings changes.
- **`MrcNav`.** The division / line-of-business selector stays as it is. A
  Functional Group is a grouping *within* the current scope, not a fourth level of
  it.
- **The MRC scope screens.** A committee sees the records in its org scope, and a
  group does not change that scope. Grouping the MRC's model list is a reasonable
  later ask, not part of this.
- **The generated PDFs.** `report_blocks.field_groups` drives all four reports off
  the spec dicts, so the field appears in them automatically as an Organisation
  field — carrying the id unless the report resolves it, which is a small step to
  remember in F4. Grouping the *report* is separate work.
- **Re-classification.** The risk policy flags records signed off under a
  superseded categorisation (`needs_reclassification`). Nothing equivalent is
  needed here: with stable ids a rename moves nothing, and a removal is refused
  while records still hold it.

## 8. R2 headroom on the files this plan touches

The audit gates Python **and** `.js`/`.css` at 300 lines, and the gate at HEAD is
`PASS: 0 gated finding(s)` — so any finding this work produces is its own.

| File | Lines | Headroom | Plan |
|---|---|---|---|
| `config/governance/_reference.py` | 293 | **7** | untouched — the config goes in a new `_functional_groups.py` |
| `config/governance/_completeness.py` | 293 | **7** | untouched (§6) |
| `config/governance/_ai_system.py` | 271 | 29 | 1 field spec |
| `config/governance/_inventory.py` | 264 | 36 | 1 field spec |
| `config/governance/_ml_application.py` | 255 | 45 | 1 field spec |
| `src/static/js/reference.js` | 242 | 58 | 1 tab + 1 branch |
| `src/static/js/mrc/detail_core.js` | 240 | 60 | the AOB blocks move out to a new file (F3b) |
| `src/static/js/inventory.js` | 218 | 82 | the `inputControl` branch + the register picker |
| `src/static/js/helpers.js` | 212 | 88 | the `Groups` registry |
| `src/static/js/mrc/detail_agenda_standing.js` | 197 | 103 | one call |
| `src/static/js/inventory/list_filters.js` | 196 | 104 | a Functional Group filter |
| `src/static/js/inventory/list.js` | 176 | 124 | the `groupBy` hook only; grouping in `list_groups.js` |
| `config/governance/_product.py` | 173 | 127 | field spec + editable tuple |
| `src/static/js/product.js` | 155 | 145 | rewritten onto `createRecordList` (F6b) |

New files carry no legacy: `_functional_groups.py`, the three in
`src/governance/functional_groups/`, `api_functional_groups.py`,
`functional_groups.js`, `inventory/list_groups.js`,
`mrc/detail_agenda_signoffs.js`. Two existing files are effectively full and
neither needs touching.

## 9. Decisions taken

Settled by the user on 2026-09-07, and the plan above reflects them:

1. **"Functional Group", not "Cluster."** Field key `functional_group`. This also
   clears the collision with an ML Application's `learning_task` of "Clustering"
   (`config/governance/_ml_training.py:89`), which would have put two meanings of
   the same word on one record.
2. **One group per record.** Single-valued, which is what a grouped list needs — a
   record in two groups appears twice and the counts stop summing to the total.
3. **The list is MRC-ratified.** §2. This is the decision that set the shape.
4. **One level. No nesting.**
5. **No completeness exemption.** §6 — the user is working through the finding.

## 10. What remains open

- ~~The division-change hole~~ — closed in F1 by refusing the move while a group
  is set (§6). The same hole for the risk fields is untouched and still open.
- **Who may propose a list.** The plan assumes Admin, as the Risk and ML Review
  editors do. If proposing should be restricted further, that is a `config/permissions.py`
  question and should be settled before F2.

## 11. Recommended order

F1 is self-contained backend work and is the largest single new package. F2 and F3
close the ratification loop and only mean anything together — nothing is visible on
a record until all three land. F4 is where the feature reaches the registers, and
F5 is the screen the user actually described; both are worth verifying in the
running app before F6 begins. F6b (Products) is the biggest rewrite and is cleanly
separable. F7 needs your mapping and a ratified list, so it cannot start early.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
