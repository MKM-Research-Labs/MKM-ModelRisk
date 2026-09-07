# Design & plan: Cluster — grouping a register by function

**Status:** Proposed 2026-09-07. Nothing built.
**Area:** `config/governance`, the reference store, all four registers, the list screens

## 1. What was asked

A new field, **Cluster**, on Models, Products, ML Applications and AI Systems. It
groups records by *function* — "Storm Generation", "Flood Simulation", "Instrument
Pricer" — and is deliberately not Type. Type says what a model *is* (Analytical,
Curve, Market Data) and drives Product bindings through its `binding_role`; a
Cluster says what a model is *for*, and drives nothing.

The Models screen then leads with the clusters. A reader sees a short list of
groups and expands one to reach its models, instead of one long table.

The clusters are defined per Division, in Admin.

## 2. Why this is cheap, and where the cost actually is

The estate already has every mechanism this needs, and three of them fit so
exactly that the feature is mostly configuration.

**A division-scoped admin list already exists, and it is `line_of_business`.**
`config/governance/_reference.py:153-156` defines a list whose items carry a name
and a `division`, and `MrcNav.lobsForDivision(div, ref)`
(`src/static/js/mrc_nav.js:94`) filters them by division on the client. A Cluster
is the same shape. This matters because it means "defined by Division" needs no
new storage: **not** a per-division event stream like the risk policy, and **not**
an MRC-ratified policy — one more reference list, whose items name their division.

**A record's division is already threaded to every field editor.**
`DetailShell.fieldEditor` passes `opts.division` into `inputControl`
(`src/static/js/detail_shell.js:108`), and `inputControl`
(`src/static/js/inventory.js:26`) already branches on field key to source options
from the division rather than the spec — that is how `materiality`, `complexity`
and `rag_rating` read their bands out of the division's risk policy. A
division-filtered Cluster dropdown is one more branch in that function. All four
detail screens pass division today (`inventory/detail_overview.js:230`,
`product/detail_edit.js:156`, `mlapp/detail_core.js:139`,
`aisystem/detail_core.js:106`).

**The grouped, expandable list already exists on the dashboard.**
`src/static/js/dashboard.js` draws a collapsed row that names what it spans, a
List/Hide toggle (`:126`), members indented beneath it (`_members`, `:147`) and
`_expanded` state keyed by group (`:45`). The CSS is written
(`src/static/css/app.css:251`). The Models list should look like that, not like a
new invention.

**And three of the four registers share one list engine.** `InventoryList` in
`src/static/js/inventory/list.js` is config-driven, and `createRecordList`
(`:167`) makes an instance per register — ML Applications
(`src/static/js/mlapp.js:96`) and AI Systems (`src/static/js/aisystem.js:95`) are
already instances. Grouping written once in `_renderTable` (`:131`) serves all
three.

So the real cost is in four places, and none of them is the storage:

| Where | Why |
|---|---|
| **Products is not on the shared engine** | `src/static/js/product.js:122-154` hand-rolls its `<tr>` strings and its `<thead>` literal. It has no filters, no sorting and no tiles. It cannot inherit grouping without being migrated first. |
| **Detail screens are hand-curated** | A field in config appears in the API payload and the generated PDFs but on **no screen** until its key is added to `OVERVIEW_LEFT` (`inventory/detail_core.js:31`) and the three equivalents. CLAUDE.md §4 says this; it is still true. |
| **`PRODUCT_EDITABLE_FIELDS` is hand-written** | The other three derive `EDITABLE_FIELDS` from the spec keys. Adding `cluster` to `PRODUCT_FIELD_SPECS` alone yields a field that renders and whose edit is refused with `field not editable: cluster` (`src/governance/product/_rules.py:124`). |
| **The completeness audit probes every non-exempt field** | At `DEFAULT_FIELD_CRITICALITY = 0.40` (`config/governance/_completeness.py:47`). See §6 — this is the one change that reaches the whole estate on the day it ships. |

**Database changes: none.** Reference lists have no projection table at all — the
`ReferenceData/global` stream is folded on every read
(`src/governance/reference/_store.py:20-25`). A record's fields live in a JSONB
`data` column that `rebuild_*_view` copies wholesale. No migration, no DDL, no
projection edit.

**Web API changes: none.** All four `/fields` handlers pass their spec dict
through `grouped_field_specs`, and `resolve_field` (`src/web/_helpers.py:159`)
promotes any field with a `reference` to a dropdown automatically.

## 3. The decision that shapes everything: where a Cluster lives

Three options were considered. The recommendation is the first.

### A. A reference list whose items carry a division — **recommended**

Modelled line-for-line on `line_of_business`. One list, `cluster`; each item is
`{value: "Storm Generation", division: "Analytics", description: …}`. Admin gets a
**Cluster** tab beside Line of Business.

- Reuses the whole add/edit/reorder/delete path, including `CollectionItemMoved`
  ordering, so the clusters appear in the order an administrator arranged them
  rather than alphabetically.
- Division filtering is client-side, exactly as `lobsForDivision` already does it.
- Two divisions may both define "Pricing" and mean different things; the item is
  distinct because it names its division.

### B. A per-division policy aggregate (the `RatifiedPolicy` pattern)

What the risk policy and the ML review policy do: one event stream per division,
`Proposed → Approved → Rejected`, ratified at that division's MRC.

Rejected. A Cluster decides nothing — not a rating, not a review cadence, not a
committee. Gating it behind a committee meeting puts a quorum between an
administrator and renaming a folder. The risk policy earns that ceremony because
changing it re-classifies signed-off models; a cluster rename moves nothing.

### C. A flat global list, no division

Cheapest, and wrong: the user asked for per-division, and a firm with a Ratings
division and an Analytics division will have two different "Pricing".

### The trap inside option A, and how to close it

`resolve_field` promotes a reference field to a dropdown **only when the list is
non-empty** (`src/web/_helpers.py:159`), and `reject_unknown_references` skips
enforcement against an empty list (`src/governance/reference/_validate.py:63`).
On day one no clusters exist, so a Cluster field would render as a **free-text
box** and accept anything — and the estate would acquire "Storm Generation",
"Storm generation" and "Storm Gen" as three groups.

There are no sensible defaults to seed (unlike model types, whose defaults exist
precisely so the field never degrades to free text). So the field must be
**suppressed until the division has at least one cluster**, rather than seeded.
That is step C2c.

The second half of the trap: `reject_unknown_references` validates against the
whole list, not the record's division, so nothing today would stop a model in
Analytics being assigned a Ratings cluster. Step C2d closes it.

## 4. Phases

Each step follows the house contract: **Goal** (one sentence), **Steps** (config
first, then domain, then API, then UI, then tests — that order is R1), **Verify**
(named tests and the screen to look at), **Done when** (one mechanical check).

Phases C1–C3 deliver the feature the user described, for Models. C4 extends it to
the other three registers. C5 is the estate-wide consequence and should not be
skipped.

---

### C1 — The Cluster list and its Admin tab

**Goal.** An administrator can define, rename, reorder and remove clusters under a
named division.

**Steps.**

- **a.** New module `config/governance/_cluster.py` — `CLUSTER_LIST = "cluster"`,
  `CLUSTER_REFERENCE_SPECS`, folded into `_reference.py` the way `_ml.py` and
  `_ai.py` already are (two lines: the name into `REFERENCE_LISTS` at `:101`, the
  spec into the `REFERENCE_SPECS.update(...)` block at `:283`). It goes in its own
  module because `_reference.py` is at 293 lines against R2's 300.
- **b.** No seeder. A cluster set is the institution's own and there is no
  defensible default; the field suppression in C2c is what an empty list buys
  instead.
- **c.** `src/static/js/reference.js:28` — `["cluster", "Cluster"]` in `_TABS`,
  placed after Line of Business. Nothing else: `_renderList` handles it, because
  the list is an ordinary two-field list.

**Shape.**

```python
CLUSTER_LIST = "cluster"
CLUSTER_REFERENCE_SPECS = {
    CLUSTER_LIST: {"label": "Cluster", "id_prefix": "CL", "display": "value",
                   "hint": "How this division groups its estate by function.",
                   "fields": [
        {"key": "value", "label": "Cluster", "type": "text", "required": True},
        {"key": "division", "label": "Division", "type": "text",
         "reference": "division", "required": True},
        {"key": "description", "label": "What it covers", "type": "textarea"},
    ]},
}
```

**Verify.** A new `tests/governance/test_cluster_list.py`: add two clusters under
different divisions, assert both come back from `get_reference_lists()`, assert
reorder emits `CollectionItemMoved`, assert an item with no division is refused.
Then the Admin → Cluster tab in the running app on 5016.

**Done when** `GET /api/reference` returns a `cluster` key and the tab adds a row.

---

### C2 — The field on all four records

**Goal.** Every record carries a Cluster, chosen from its own division's clusters.

**Steps.**

- **a. Config, four edits.** `"cluster": {"label": "Cluster", "type": "text",
  "group": "Organisation", "reference": "cluster", "strict_reference": True}` into
  `MODEL_FIELD_SPECS` (`_inventory.py:61`), `PRODUCT_FIELD_SPECS`
  (`_product.py:67`), `ML_APPLICATION_FIELD_SPECS` (`_ml_application.py:86`) and
  `AI_SYSTEM_FIELD_SPECS` (`_ai_system.py:89`) — beside `division` in each, since
  it is an organisational fact.
- **b. `PRODUCT_EDITABLE_FIELDS`** (`_product.py:115`) — add `"cluster"`. The
  other three derive theirs. This is the step that is silently missed.
- **c. Suppress the field where the division has no clusters.** In `inputControl`
  (`src/static/js/inventory.js:26`), source `cluster` options from
  `Clusters.forDivision(division)` — the same branch shape as
  `POLICY_DIMENSION_FIELD` above it — and where the division has none, render the
  row as a muted "No clusters defined for this division" rather than a text box.
  A small `Clusters` registry in `helpers.js`, loaded from `/api/reference` at
  startup, mirroring the existing `Policy` registry.
- **d. Division-aware strictness.** `reject_unknown_references`
  (`src/governance/reference/_validate.py:37`) checks against the whole list.
  Extend it so a spec may declare `"scoped_by": "division"`, and the allowed set
  narrows to items whose `division` matches the record's. This is genuinely new
  machinery, small, and it is what stops a model in one division being filed under
  another's cluster.
- **e. Detail screens, four hand edits.** `OVERVIEW_LEFT`
  (`inventory/detail_core.js:31`), `PRODUCT_OVERVIEW_ORG`
  (`product/detail_core.js:26`), `_LEFT` (`mlapp/detail_core.js:87`) and `_LEFT`
  (`aisystem/detail_core.js:39`).
- **f. Register forms.** Add `cluster` to the four `*_REGISTER_FIELDS` tuples.
  Three of the register forms are spec-driven and need nothing else; the **Models
  register overlay is hand-written HTML** (`src/templates/index.html:74-90` plus
  `_populateTypePicker` at `inventory.js:130`), so it needs a picker method of its
  own, populated from the nav's currently selected division.

**Verify.** `tests/governance/test_cluster_field.py` — a model in Analytics
accepts an Analytics cluster and is refused a Ratings one with a `DomainError`
naming the allowed set; a Product edit to `cluster` succeeds (the C2b regression);
`GET /api/models/fields` carries `cluster` as a `choice`. Then: register a model
in the app, set its cluster, reload, confirm it persisted.

**Done when** all four detail screens show a Cluster row and the audit is clean.

---

### C3 — The grouped Models list

**Goal.** The Models screen opens on clusters, and expanding one reveals its
models.

**Steps.**

- **a.** New `src/static/js/inventory/list_groups.js` — `_renderTable` grows a
  `_cfg.groupBy` branch, defaulting off, so a register that does not set it is
  byte-identical to today. Group rows carry the cluster name, its record count and
  a roll-up of what the reader needs at a glance (worst risk rating in the group,
  and how many are overdue); `_expanded` state per group, `List`/`Hide` toggle,
  members as indented rows. Own file because `list.js` is 176 lines and
  `list_filters.js` 196, both gated at 300.
- **b.** Registered as a `<script>` tag in `src/templates/index.html`. **A new
  script tag needs a server restart** — Jinja caches `index.html` with
  `debug=False` (CLAUDE.md §4).
- **c.** Records with no cluster go into an **Unclustered** group, rendered last
  and visually distinct. On the day this ships that is every record in the estate,
  so the empty state is the normal state until C5 runs. It must read as work to
  do, not as an error.
- **d.** Grouping is off when a filter or a search term is active — a reader who
  has typed a name wants the matching rows, not three collapsed groups they must
  open to find them. Sorting a column likewise flattens. Both are toggles back to
  the flat table, not separate code paths.
- **e.** Expansion state survives a re-render but not a reload; there is no
  precedent here for persisting UI state and none is needed.

**Verify.** Not unit-testable in the Python suite — this is browser JS. Verify in
the running app on 5016 against a restored scratch database, with clusters defined
and several models assigned: groups collapsed on load, counts correct, expand and
collapse, then a search term flattening the view. Screenshot both states.

**Done when** the Models screen loads collapsed and the counts sum to the
unfiltered total.

---

### C4 — The other three registers

**Goal.** ML Applications, AI Systems and Products group the same way.

**Steps.**

- **a.** ML Applications and AI Systems: set `groupBy: "cluster"` in their
  `createRecordList` config (`mlapp.js:96`, `aisystem.js:95`) and add a Cluster
  column. Two lines each — they are already instances of the engine.
- **b.** **Migrate Products onto `createRecordList`.** `product.js:122-154`
  becomes a config plus a column table, its `_summary()` tiles become
  `extraTiles`. This is the largest single piece of work in the plan and is worth
  doing on its own merits: Products is the only register with no filters, no
  sorting and no clickable tiles, and this is the third time that asymmetry has
  cost something.
- **c.** Then Products sets `groupBy` like the rest.

**Verify.** `tests/web/test_product_api.py` unchanged and green (the migration is
client-side only). Then all four screens in the app, side by side, confirming they
look the same — which has been the standing requirement for these registers.

**Done when** no register renders its own `<table>` markup.

---

### C5 — The estate, and the completeness audit

**Goal.** Existing records acquire clusters without the audit reporting the estate
as suddenly incomplete.

**Steps.**

- **a. Exempt `cluster` from completeness scoring** in the same commit as C2a —
  `EXEMPT_FIELDS` (`config/governance/_completeness.py:62`), with the reason
  written beside it, exactly as `monitoring_approach` was exempted while the
  review workflow was built. See §6.
- **b. A backfill script**, on the house template
  (`scripts/backfill_version_register.py`): dry-run by default, `--apply` to
  write, derives nothing it cannot justify, reports what it cannot fill rather
  than inventing it, writes through `update_model_field` and never SQL (R6), and
  **calls `rebuild_inventory_view()` at the end** — a backfill from a bare script
  leaves the read models stale. Rehearsed against a restored scratch database
  (R9).
  There is no honest derivation of a cluster from existing data, so this script's
  job is to apply a mapping the user supplies, not to guess one.
- **c. Remove the exemption** once the estate is assigned, so a new record without
  a cluster is a finding. That is a separate, deliberate commit — and the point at
  which the user should be asked, because it moves every score.

**Verify.** `tests/governance/test_completeness.py` — the estate's scores are
unchanged by C2a (the exemption holding), and a named test asserting `cluster` is
exempt *with its reason*, so removing the exemption is a deliberate act and not an
accident.

**Done when** the completeness report before and after C2 differs by nothing.

## 5. What this does not touch

Worth stating, because each looked like it might.

- **Type.** Untouched. A Cluster is orthogonal, and in particular nothing about
  `binding_role` or the Product bindings changes.
- **The MRC scope screens.** A committee sees the records in its org scope; a
  cluster does not change that scope. Grouping the MRC's model list by cluster is
  a reasonable later ask, not part of this.
- **The generated PDFs.** `report_blocks.field_groups` drives all four reports off
  the spec dicts, so Cluster appears in them automatically as an Organisation
  field. Grouping the *report* by cluster is a separate piece of work.
- **`MrcNav`.** The division/line-of-business selector stays as it is. Cluster is
  a grouping *within* the current scope, not a fourth level of it.

## 6. The one change that reaches the whole estate

`src/governance/completeness/_gaps.py:110` scores every field spec that is not in
`EXEMPT_FIELDS`, at `DEFAULT_FIELD_CRITICALITY = 0.40`. Adding `cluster` to four
spec dicts therefore raises a completeness finding against **every record in the
estate** the moment it merges — before a single cluster has been defined.

This has happened before and the precedent is written into the config:
`monitoring_approach` is exempt because it "lands as an empty field on every
existing model, and scoring it on the day the tab appears would drop every score
for a gap nobody has been asked to fill yet."

The same reasoning applies exactly. Exempt at C2a; un-exempt at C5c, deliberately,
once the estate has been given a chance to answer.

## 7. R2 headroom on the files this plan touches

The audit gates Python **and** `.js`/`.css` at 300 lines, and the gate at HEAD is
`PASS: 0 gated finding(s)` — so any finding this work produces is its own.

| File | Lines | Headroom | Plan |
|---|---|---|---|
| `config/governance/_reference.py` | 293 | **7** | 2 lines only; the spec goes in a new `_cluster.py` |
| `config/governance/_completeness.py` | 293 | **7** | 1 line in `EXEMPT_FIELDS` |
| `config/governance/_ai_system.py` | 271 | 29 | 1 field spec |
| `src/web/_helpers.py` | 265 | 35 | untouched |
| `config/governance/_inventory.py` | 264 | 36 | 1 field spec |
| `config/governance/_ml_application.py` | 255 | 45 | 1 field spec |
| `src/static/js/reference.js` | 242 | 58 | 1 tab |
| `src/static/js/inventory.js` | 218 | 82 | the `inputControl` branch + the register picker |
| `src/static/js/helpers.js` | 212 | 88 | the `Clusters` registry |
| `src/static/js/list_filters.js` | 196 | 104 | a Cluster filter |
| `src/static/js/inventory/list.js` | 176 | 124 | the `groupBy` hook only; grouping in `list_groups.js` |
| `config/governance/_product.py` | 173 | 127 | field spec + editable tuple |
| `src/static/js/product.js` | 155 | 145 | rewritten onto `createRecordList` (C4b) |

Two files are effectively full. Everything else has room.

## 8. Risks

1. **The audit finding on every record** (§6). Mitigated by the exemption, but
   only if C2a and C5a land in the same commit.
2. **Free-text clusters before the list is populated** (§3). Mitigated by
   suppressing the field rather than seeding a default set.
3. **Cross-division assignment.** Mitigated by C2d; without it, nothing stops it.
4. **"Cluster" collides with ML vocabulary.** An ML Application already has a
   `learning_task` of "Clustering" (`config/governance/_ml_training.py:89`). Two
   different meanings of the word on the same record. Not a blocker — the labels
   differ and the fields sit in different tabs — but it is worth deciding
   consciously rather than discovering on the screen (§9).
5. **The Products migration (C4b) is the only step that rewrites working code.**
   It is client-side and covered by no test. It should be verified in the app, not
   reasoned about.
6. **Detail screens are hand-curated.** The field will be invisible on any screen
   whose key array was missed. Four arrays, named in C2e.

## 9. Open decisions

These need the user, and the answers change what gets built.

1. **Is "Cluster" the right word on screen?** It is unambiguous against Type, but
   collides with the ML "Clustering" learning task. "Group" or "Function" are the
   alternatives. The stored field key should be `cluster` either way.
2. **May a record belong to more than one cluster?** The plan assumes one, which
   is what a grouped list needs — a record in two groups appears twice, and the
   counts stop summing to the total. Multi-valued is possible (`multichoice`
   survives `resolve_field`) but the grouped list would need a rule.
3. **Should the Cluster list be MRC-ratified?** The plan says no (§3B). If the
   answer is yes, the shape changes to `RatifiedPolicy` and roughly doubles.
4. **Do clusters nest?** "Flood Simulation" under "Catastrophe" is plausible and
   the plan assumes flat. Nesting is much more expensive on the list screen.
5. **When does the exemption come off** (C5c)? That is the moment the estate's
   completeness scores move, and it should be the user's call, not a consequence.

## 10. Recommended order

C1 and C2 together are a single day's work and deliver a usable field. C3 is the
feature the user actually asked for and is worth verifying in the app before C4
begins. C4b (Products) is the largest piece and is separable. C5b (the backfill)
needs the user's mapping and cannot start without it.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
