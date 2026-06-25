# MKM-ModelRisk — PVM Implementation Project Plan

**Status:** Draft for review — 2026-06-25
**Scope source:** [`pvm_spec.md`](pvm_spec.md)
**Relates to:** [User Guide](user_guide.md) · [Extraction & Build Project Plan](mkm_modelrisk_extraction_plan.md) · [Coding rules](rules/coding_rules.md)

---

## 1. Summary

The Product Valuation Model (PVM) introduces a **third top-level governance domain**
alongside the Model Inventory and MRC Meetings. A PVM is a first-class,
event-sourced aggregate that binds **one Product** to **one Analytics Model**
(an existing inventory model), **one Market Data Model**, and **one Calculating
Agent**, and governs that production instance — its lifecycle, limitations,
assumptions, and monitoring.

This is a material expansion: a new aggregate + projection + migration, two new
reference types, a new top-level UI tab with its own detail view, cross-aggregate
lineage (a model "Used by N PVMs", and a retire-block), and MRC-scope integration.
It is, however, **highly leverageable** — most of it reuses patterns the platform
already has.

### What reuses existing machinery (low risk)

| PVM need | Reuse |
|---|---|
| Event-sourced aggregate + projection + migration | mirror `src/governance/model_inventory/` + a `pvm_view` migration |
| Confirm-to-amend, actor + reason, hash chain | `src/command/dispatch.py`, `src/database/` |
| Limitations / Assumptions registers | the generic collections engine (`src/governance/collections.py`) via `PVM_COLLECTION_SPECS` |
| Calculating Agent (value-only menu) | the reference engine — add a list to `config/governance/_reference.py` |
| Market Data Model (`MDM-xxx`, multi-field) | the reference engine — a multi-field list (like `people`) |
| Reference fields → dropdowns in the register form | the existing `reference_options()` resolution (as Company already does) |
| List + register-modal + detail tabs UI | mirror `inventory.js` / `inventory_detail.js` / `inventory_collections.js` |

### What is genuinely new (the work to design carefully)

1. The **PVM aggregate** itself (component bindings, derived identifier, lifecycle).
2. **Cross-aggregate lineage** — the trickiest part:
   - an inventory model **cannot be retired** while **any non-retired PVM** still
     uses it — every dependent PVM must be retired first;
   - an inventory model gains a **"Used by N PVMs"** panel.
   This couples `model_inventory` to the PVM read model. It must be done through a
   single query function in the PVM domain that the inventory command calls — never
   ad-hoc SQL (rule R6).

---

## 2. Decisions to confirm (resolving spec §10)

The plan assumes these defaults; please confirm or redirect before Phase 2.

| # | Question | Recommended v1 decision |
|---|---|---|
| 1 | Monitoring depth | **Two narrative fields** (`monitoring_approach`, `monitoring_results`). Structured time-series (notional, sensitivities, P&L backtest) is a **later phase**. |
| 2 | PVM risk rating | **No separate composite.** The PVM detail **surfaces its Analytics Model's** tier/RAG/risk rating (via the lineage link) plus a manual monitoring-health note. |
| 3 | Product cardinality | **One instrument per PVM** for v1; bundling multiple instruments under one product is out of scope. |
| 4 | Terminology | Standardise on **Product Valuation Model**; add a one-line guard in the docs against the "Product, Valuation & Market data" meaning. |
| 5 | Identifier | Derived, non-editable: `<AnalyticsModelID>.<MarketDataModelID>.<CalculatingAgent>`; a rebind is an audited event that changes it. |

---

## 3. Domain & data model

### 3.1 New reference types (Phase 1)

Added to `config/governance/_reference.py` (`REFERENCE_LISTS` + `REFERENCE_SPECS`):

- **`calculating_agent`** — `id_prefix: CA`, fields: `value` (only). A simple menu.
- **`market_data_model`** — `id_prefix: MDM`, display `name`, fields:
  `name*`, `description`, `vendor`, `method`, `update_frequency` (choice).

Both appear as **Admin sub-tabs** (the Admin tab already renders one sub-tab per
reference list — Company / Division / Department / MRC / People → add **MDM** and
**Calculating Agent**). Once populated they become **dropdowns** in the PVM
register form, exactly as Company does today.

### 3.2 PVM aggregate (Phase 2)

`config/governance/_pvm.py`:

- `PVM_FIELD_SPECS` — scalar fields per spec §3.2: `product*`, `product_id`,
  `analytics_model*` (reference → inventory models), `market_data_model*`
  (reference → `market_data_model`), `calculating_agent*` (reference →
  `calculating_agent`), `status` (choice), `owner` (reference → people),
  `monitoring_approach`, `monitoring_results`, `notes`.
- `PVM_REGISTER_FIELDS` — the minimum for the register modal: `product` + the three
  bindings (PVM ID + product are mandatory; bindings mandatory).
- `VALID_PVM_STATUS = (Proposed, Active, Suspended, Retired)`.
- `VALID_MDM_FREQUENCY = (Real-time, Intraday, Daily, Weekly, Ad-hoc)`.
- `PVM_COLLECTION_SPECS` — `limitations`, `assumptions` (reuse the shapes from the
  inventory collections).

Derived identifier built in the domain (not stored as an editable field):
`f"{analytics_model}.{market_data_model}.{calculating_agent}"`.

### 3.3 Events (spec §5.2)

`PvmRegistered`, `PvmComponentRebound`, `PvmFieldEdited`, `PvmLimitationAdded/Removed`,
`PvmAssumptionAdded/Removed`, `PvmSuspended`, `PvmRetired`. Folded by
`src/governance/pvm/_store.py`; projected into `pvm_view` (a new migration).

### 3.4 Validation rules (spec §5.3)

- All three bindings + product mandatory at registration.
- Analytics Model reference **must resolve** to a live (non-retired) inventory model.
- `(product, analytics, mdm, agent)` combination should be **unique** — flagged at
  confirmation (a `DomainError` the confirm dialog surfaces).
- An inventory model **cannot be retired** while **any non-retired PVM** references
  it. All dependent PVMs must be **retired first**; the block message names them.
  (A PVM that is itself Retired no longer blocks.)

---

## 4. Work breakdown (phased)

Each phase is independently shippable and ends **green**: ≥99% coverage (R3), audit
clean (`python -m audit`), all coding rules R1–R8.

### Phase 0 — Decisions & scaffolding
- Confirm §2 decisions.
- Add the controlled vocabularies to `config/governance/_pvm.py` (constants only).
- **Deliverable:** locked data model. **Tests:** config import/contract tests.

### Phase 1 — Reference data: Calculating Agent + Market Data Model
- Extend `REFERENCE_LISTS` / `REFERENCE_SPECS`; the reference engine, API, and the
  Admin sub-tabs pick them up automatically.
- **Files:** `config/governance/_reference.py`; minor Admin sub-tab order.
- **Tests:** reference add/update/remove for both lists; MDM `update_frequency`
  choice validation; the new lists appear in `/api/reference`.

### Phase 2 — PVM aggregate (domain core)
- `src/governance/pvm/`: `_store.py` (fold → state), `commands.py`
  (register / rebind / edit-field / add-remove collection item / suspend / retire),
  `_rules.py` (the §5.3 validation, derived identifier, uniqueness), `__init__.py`.
- `src/database/migrations/000N_pvm_view.sql` (projection table + app-role grants;
  immutability unchanged).
- A `rebuild_pvm_view` projector mirroring the inventory projector.
- **Tests:** every event/command, the derived identifier, the validation rules,
  uniqueness, the resolve-to-live-model rule. (No web yet.)

### Phase 3 — PVM HTTP API
- `src/web/api_pvm.py` (blueprint, `url_prefix="/api/pvms"`): list, fields/specs
  (resolving reference dropdowns via `reference_options()`), register, rebind,
  edit-field, collection add/remove, suspend, retire, and a `used-by/<model_id>`
  lineage query. Register in `app.py`.
- **Tests:** every route incl. confirm-to-amend (409 without `confirmed`), the
  reference-dropdown enrichment, and the blocked-retire path.

### Phase 4 — PVMs UI tab
- New top-level **PVMs** tab modelled on the inventory: `pvm.js` (list + summary
  cards + **"+ Register PVM"** modal with product + three dropdowns), `pvm_detail.js`
  (header with derived identifier; Overview with inline rebind + monitoring fields;
  Limitations / Assumptions via the shared `Collections` renderer; Audit).
  Nav button + panel + script tags in `index.html`; `TABS` entry in `main.js`.
  Assets under `src/static/js/` (R7).
- **Tests:** e2e — register a PVM, open it, rebind a component, edit monitoring, add
  a limitation; smoke covers the new tab.

### Phase 5 — Cross-aggregate lineage
- Inventory model detail gains a **"Used by N PVMs"** panel (calls the
  `used-by` query); the Analytics-Model binding deep-links to the inventory record.
- Wire the **retire-block**: `model_inventory`'s retire command calls a PVM domain
  query (`dependent_pvms_for_model` — every non-retired PVM referencing the model)
  and raises `DomainError` listing them. The model can only be retired once that
  list is empty (i.e. all dependent PVMs are themselves retired).
- **Tests:** retire blocked while any non-retired PVM references the model; allowed
  once all such PVMs are retired (or rebound away); the used-by panel count.

### Phase 6 — MRC scope + reporting
- Allow **PVMs in an MRC meeting's `models_in_scope`** (or a parallel `pvms_in_scope`)
  so the committee reviews production instances; reflect in the Meeting Pack PDF.
- Optionally add a **PVM register** to the Audit Reports tab (a PVM inventory PDF).
- **Tests:** meeting-scope add; pack rendering with a PVM; report generation.

### Phase 7 — Docs & finalisation
- Update the **User Guide** (new PVMs section + Admin MDM/Agent + the lineage panel),
  which auto-publishes to the Audit Reports tab as a PDF.
- Update the README capability list. Tidy `pvm_spec.md` open questions to "resolved".
- **Deliverable:** docs current; full suite + e2e + audit green.

---

## 5. Risks & dependencies

| Risk | Mitigation |
|---|---|
| **Cross-aggregate coupling** (retire-block, used-by) touches existing inventory code | Expose a single PVM-domain query; the inventory command calls it. No SQL outside `src/database` (R6). One clearly-scoped change to the existing retire command, covered by tests. |
| **Derived identifier drift** on rebind | Identifier is computed, never stored editable; a rebind emits `PvmComponentRebound` (audited) and recomputes. |
| **Uniqueness check** races | Enforced in the command against the current projection at confirmation; acceptable at this scale (same pattern as the single-company rule). |
| **Migration ordering** | New `pvm_view` migration is additive and numbered after the latest; app-role grants mirror existing views. |
| **Scope creep** (monitoring time-series, multi-instrument products) | Explicitly deferred in §2; v1 is narrative monitoring + single instrument. |

---

## 6. Definition of done (per phase and overall)

- Coding rules **R1–R8** all green; `python -m audit` reports **0 gated findings**.
- **≥99% coverage** maintained at every phase (target 100%, as today).
- **e2e** covers the PVM register → detail → rebind → collection flows and the new tab.
- The **retire-block** and **used-by** lineage are demonstrated by tests.
- **User Guide** updated and published as a PDF in the Audit Reports tab.

---

## 7. Sequencing note

Phases 1–4 deliver a **standalone, usable PVM module** (define MDMs/agents, register
and govern PVMs). Phase 5 adds the lineage that makes the one-Analytics-Model →
many-PVMs relationship safe, which is the feature's core motivation. Phases 6–7 are
committee integration and polish. The plan can stop cleanly after any phase.

---

© 2022–2026 MKM Research Labs. All rights reserved.
