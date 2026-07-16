# MKM-ModelRisk — Product Implementation Project Plan

**Status:** Draft for review — 2026-06-25
**Scope source:** [`product_spec.md`](product_spec.md)
**Relates to:** [User Guide](user_guide.md) · [Extraction & Build Project Plan](mkm_modelrisk_extraction_plan.md) · [Coding rules](rules/coding_rules.md)

---

## 1. Summary

The Product Valuation Model (Product) introduces a **third top-level governance domain**
alongside the Model Inventory and MRC Meetings. A Product is a first-class,
event-sourced aggregate that binds **one Product** to **one Analytics Model**
(an existing inventory model), **one Market Data Model**, and **one Calculating
Agent**, and governs that production instance — its lifecycle, limitations,
assumptions, and monitoring.

This is a material expansion: a new aggregate + projection + migration, two new
reference types, a new top-level UI tab with its own detail view, cross-aggregate
lineage (a model "Used by N Products", and a retire-block), and MRC-scope integration.
It is, however, **highly leverageable** — most of it reuses patterns the platform
already has.

### What reuses existing machinery (low risk)

| Product need | Reuse |
|---|---|
| Event-sourced aggregate + projection + migration | mirror `src/governance/model_inventory/` + a `product_view` migration |
| Confirm-to-amend, actor + reason, hash chain | `src/command/dispatch.py`, `src/database/` |
| Limitations / Assumptions registers | the generic collections engine (`src/governance/collections.py`) via `PRODUCT_COLLECTION_SPECS` |
| Calculating Agent (value-only menu) | the reference engine — add a list to `config/governance/_reference.py` |
| Market Data Model (`MDM-xxx`, multi-field) | the reference engine — a multi-field list (like `people`) |
| Reference fields → dropdowns in the register form | the existing `reference_options()` resolution (as Company already does) |
| List + register-modal + detail tabs UI | mirror `inventory.js` / `inventory_detail.js` / `inventory_collections.js` |

### What is genuinely new (the work to design carefully)

1. The **Product aggregate** itself (component bindings, derived identifier, lifecycle).
2. **Cross-aggregate lineage** — the trickiest part:
   - an inventory model **cannot be retired** while **any non-retired Product** still
     uses it — every dependent Product must be retired first;
   - an inventory model gains a **"Used by N Products"** panel.
   This couples `model_inventory` to the Product read model. It must be done through a
   single query function in the Product domain that the inventory command calls — never
   ad-hoc SQL (rule R6).

---

## 2. Decisions to confirm (resolving spec §10)

The plan assumes these defaults; please confirm or redirect before Phase 2.

| # | Question | Recommended v1 decision |
|---|---|---|
| 1 | Monitoring depth | **Two narrative fields** (`monitoring_approach`, `monitoring_results`). Structured time-series (notional, sensitivities, P&L backtest) is a **later phase**. |
| 2 | Product risk rating | **No separate composite.** The Product detail **surfaces its Analytics Model's** tier/RAG/risk rating (via the lineage link) plus a manual monitoring-health note. |
| 3 | Product cardinality | **One instrument per Product** for v1; bundling multiple instruments under one product is out of scope. |
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
**Calculating Agent**). Once populated they become **dropdowns** in the Product
register form, exactly as Company does today.

### 3.2 Product aggregate (Phase 2)

`config/governance/_product.py`:

- `PRODUCT_FIELD_SPECS` — scalar fields per spec §3.2: `product*`, `product_id`,
  `analytics_model*` (reference → inventory models), `market_data_model*`
  (reference → `market_data_model`), `calculating_agent*` (reference →
  `calculating_agent`), `status` (choice), `owner` (reference → people),
  `monitoring_approach`, `monitoring_results`, `notes`.
- `PRODUCT_REGISTER_FIELDS` — the minimum for the register modal: `product` + the three
  bindings (Product ID + product are mandatory; bindings mandatory).
- `VALID_PRODUCT_STATUS = (Proposed, Active, Suspended, Retired)`.
- `VALID_MDM_FREQUENCY = (Real-time, Intraday, Daily, Weekly, Ad-hoc)`.
- `PRODUCT_COLLECTION_SPECS` — `limitations`, `assumptions` (reuse the shapes from the
  inventory collections).

Derived identifier built in the domain (not stored as an editable field):
`f"{analytics_model}.{market_data_model}.{calculating_agent}"`.

### 3.3 Events (spec §5.2)

`ProductRegistered`, `ProductComponentRebound`, `ProductFieldEdited`, `ProductLimitationAdded/Removed`,
`ProductAssumptionAdded/Removed`, `ProductSuspended`, `ProductRetired`. Folded by
`src/governance/product/_store.py`; projected into `product_view` (a new migration).

### 3.4 Validation rules (spec §5.3)

- All three bindings + product mandatory at registration.
- Analytics Model reference **must resolve** to a live (non-retired) inventory model.
- `(product, analytics, mdm, agent)` combination should be **unique** — flagged at
  confirmation (a `DomainError` the confirm dialog surfaces).
- An inventory model **cannot be retired** while **any non-retired Product** references
  it. All dependent Products must be **retired first**; the block message names them.
  (A Product that is itself Retired no longer blocks.)

---

## 4. Work breakdown (phased)

Each phase is independently shippable and ends **green**: ≥99% coverage (R3), audit
clean (`python -m audit`), all coding rules R1–R8.

### Phase 0 — Decisions & scaffolding
- Confirm §2 decisions.
- Add the controlled vocabularies to `config/governance/_product.py` (constants only).
- **Deliverable:** locked data model. **Tests:** config import/contract tests.

### Phase 1 — Reference data: Calculating Agent + Market Data Model
- Extend `REFERENCE_LISTS` / `REFERENCE_SPECS`; the reference engine, API, and the
  Admin sub-tabs pick them up automatically.
- **Files:** `config/governance/_reference.py`; minor Admin sub-tab order.
- **Tests:** reference add/update/remove for both lists; MDM `update_frequency`
  choice validation; the new lists appear in `/api/reference`.

### Phase 2 — Product aggregate (domain core)
- `src/governance/product/`: `_store.py` (fold → state), `commands.py`
  (register / rebind / edit-field / add-remove collection item / suspend / retire),
  `_rules.py` (the §5.3 validation, derived identifier, uniqueness), `__init__.py`.
- `src/database/migrations/000N_product_view.sql` (projection table + app-role grants;
  immutability unchanged).
- A `rebuild_product_view` projector mirroring the inventory projector.
- **Tests:** every event/command, the derived identifier, the validation rules,
  uniqueness, the resolve-to-live-model rule. (No web yet.)

### Phase 3 — Product HTTP API
- `src/web/api_product.py` (blueprint, `url_prefix="/api/products"`): list, fields/specs
  (resolving reference dropdowns via `reference_options()`), register, rebind,
  edit-field, collection add/remove, suspend, retire, and a `used-by/<model_id>`
  lineage query. Register in `app.py`.
- **Tests:** every route incl. confirm-to-amend (409 without `confirmed`), the
  reference-dropdown enrichment, and the blocked-retire path.

### Phase 4 — Products UI tab
- New top-level **Products** tab modelled on the inventory: `product.js` (list + summary
  cards + **"+ Register Product"** modal with product + three dropdowns), `product_detail.js`
  (header with derived identifier; Overview with inline rebind + monitoring fields;
  Limitations / Assumptions via the shared `Collections` renderer; Audit).
  Nav button + panel + script tags in `index.html`; `TABS` entry in `main.js`.
  Assets under `src/static/js/` (R7).
- **Tests:** e2e — register a Product, open it, rebind a component, edit monitoring, add
  a limitation; smoke covers the new tab.

### Phase 5 — Cross-aggregate lineage
- Inventory model detail gains a **"Used by N Products"** panel (calls the
  `used-by` query); the Analytics-Model binding deep-links to the inventory record.
- Wire the **retire-block**: `model_inventory`'s retire command calls a Product domain
  query (`dependent_pvms_for_model` — every non-retired Product referencing the model)
  and raises `DomainError` listing them. The model can only be retired once that
  list is empty (i.e. all dependent Products are themselves retired).
- **Tests:** retire blocked while any non-retired Product references the model; allowed
  once all such Products are retired (or rebound away); the used-by panel count.

### Phase 6 — MRC scope + reporting
- Allow **Products in an MRC meeting's `models_in_scope`** (or a parallel `products_in_scope`)
  so the committee reviews production instances; reflect in the Meeting Pack PDF.
- Optionally add a **Product register** to the Audit Reports tab (a Product inventory PDF).
- **Tests:** meeting-scope add; pack rendering with a Product; report generation.

### Phase 7 — Docs & finalisation
- Update the **User Guide** (new Products section + Admin MDM/Agent + the lineage panel),
  which auto-publishes to the Audit Reports tab as a PDF.
- Update the README capability list. Tidy `product_spec.md` open questions to "resolved".
- **Deliverable:** docs current; full suite + e2e + audit green.

---

## 5. Risks & dependencies

| Risk | Mitigation |
|---|---|
| **Cross-aggregate coupling** (retire-block, used-by) touches existing inventory code | Expose a single Product-domain query; the inventory command calls it. No SQL outside `src/database` (R6). One clearly-scoped change to the existing retire command, covered by tests. |
| **Derived identifier drift** on rebind | Identifier is computed, never stored editable; a rebind emits `ProductComponentRebound` (audited) and recomputes. |
| **Uniqueness check** races | Enforced in the command against the current projection at confirmation; acceptable at this scale (same pattern as the single-company rule). |
| **Migration ordering** | New `product_view` migration is additive and numbered after the latest; app-role grants mirror existing views. |
| **Scope creep** (monitoring time-series, multi-instrument products) | Explicitly deferred in §2; v1 is narrative monitoring + single instrument. |

---

## 6. Definition of done (per phase and overall)

- Coding rules **R1–R8** all green; `python -m audit` reports **0 gated findings**.
- **≥99% coverage** maintained at every phase (target 100%, as today).
- **e2e** covers the Product register → detail → rebind → collection flows and the new tab.
- The **retire-block** and **used-by** lineage are demonstrated by tests.
- **User Guide** updated and published as a PDF in the Audit Reports tab.

---

## 7. Sequencing note

Phases 1–4 deliver a **standalone, usable Product module** (define MDMs/agents, register
and govern Products). Phase 5 adds the lineage that makes the one-Analytics-Model →
many-Products relationship safe, which is the feature's core motivation. Phases 6–7 are
committee integration and polish. The plan can stop cleanly after any phase.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
