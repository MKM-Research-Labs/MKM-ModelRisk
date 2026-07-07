# MKM-ModelRisk — Product Valuation Model (Product) Specification

**Status:** Draft for review
**Audience:** Engineering, Model Risk Committee (MRC)
**Conceptual source:** *Model Risk Governance for Vendors*, Ch. 13 "Product Valuation Model"
**Relates to:** [User Guide](user_guide.md) · [Extraction & Build Project Plan](mkm_modelrisk_extraction_plan.md)

---

## Contents

1. [Purpose & motivation](#1-purpose--motivation)
2. [Concept](#2-concept)
3. [Domain model](#3-domain-model)
4. [Product identifier](#4-product-identifier)
5. [Aggregate, events & commands](#5-aggregate-events--commands)
6. [User experience](#6-user-experience)
7. [Monitoring](#7-monitoring)
8. [Controlled vocabularies](#8-controlled-vocabularies)
9. [Out of scope](#9-out-of-scope)
10. [Open questions](#10-open-questions)

---

## 1. Purpose & motivation

Today the platform's inventory treats a **model** as a single analytical
methodology — register it, validate it against the SR 26-2 questions, track its
assumptions and limitations. That governs the model *as built in a safe
environment*.

In banking operations, practitioners often use the terms "model" and "product"
interchangeably, because there is usually a one-to-one relationship between the
two. That simplification overlooks the difference between a model in development
and the same model running in production against live portfolios, real market
data, and finite compute.

This spec introduces the **Product Valuation Model (Product)**: a first-class
inventory concept that captures the *practical application* of models. A Product
defines a **product** and links how that product should be **risked and priced**
by binding together the three components that determine its behaviour in
production — an **Analytics Model**, a **Market Data Model**, and a
**Calculating Agent** — under a single Product banner.

This establishes an explicit **hierarchy**. The Product is the top-level,
client-facing artifact — it is what the client sees and what the business
transacts. The models beneath it are **engines**: reusable analytical and
market-data machinery that the Product wires together for a specific product. The
goal is to let the MRC govern and monitor at the level where production risk
actually materialises, not only at the level of the abstract engine.

## 2. Concept

> A **Product Valuation Model (Product)** is the *instance* of a model within a
> production environment, where it must interact with real market data,
> computational infrastructure, and business processes.

A sophisticated pricing model that performs flawlessly in development may behave
quite differently under production constraints, data-quality issues, and
compute limits. The same analytical model frequently supports **many** Products
across different products, markets, and platforms — so model-level monitoring
can mask risks that only appear at the Product level (e.g. a Black-Scholes model
that looks fine "on average" but misbehaves in a specific commodities Product).

A Product therefore pairs **one product** with a unique combination of three
components, each contributing its own risk characteristics:

| Component | Role in the hierarchy | What it is | Examples |
|---|---|---|---|
| **Analytics Model** | Engine | The core quantitative methodology that has gone through development & validation (i.e. an existing inventory model). | Bond/cashflow; Black-Scholes; SABR |
| **Market Data Model** | Engine | How market information is sourced, processed and transformed into model inputs: vendors, curve construction, proxies for missing points, update timing/frequency. | ICE direct; NSS curve fit; curve interpolation/extrapolation |
| **Calculating Agent** | Platform | A simple name telling the user **which environment the Product is calculated in**. Maintained as institution reference data. | Murex; Calypso; AM |

## 3. Domain model

The Product is a new **aggregate** alongside the existing model inventory and MRC
meeting aggregates. It is event-sourced and confirm-to-amend like everything
else on the platform.

### 3.1 Hierarchy & relationships

```
   CLIENT-FACING        ┌──────────────────────┐
   (what the client ────│         Product          │  defines a product;
    sees & transacts)   │  (Product-xxxx, banner)  │  links how it is risked & priced
                        └───────────┬──────────┘
                        binds exactly one of each:
          ┌──────────────────┬──────────────────┬──────────────────┐
   Analytics Model     Market Data Model    Calculating Agent
   (existing model,    (MDM-xxx)            (admin reference list,
    e.g. MKM-CR-001)                         e.g. Murex)
   └──── ENGINES (reusable machinery) ────┘   └─ PLATFORM (where it runs) ─┘
```

- The **Product sits at the top** of the hierarchy: it is the client-facing artifact.
  The Analytics Model and Market Data Model below it are reusable **engines**;
  the Calculating Agent is the **platform** the engines run on.
- A **Product** binds **exactly one** Analytics Model, **one** Market Data Model,
  and **one** Calculating Agent, against **one** Product.
- The **Analytics Model** reference points at an existing record in the **Model
  Inventory** — it is *not* duplicated. This is the lineage link: a Product inherits
  its analytical model's validation status, tier, assumptions, and limitations.
- One Analytics Model may be referenced by **many** Products (the one-to-many that
  motivates this whole feature).
- A **Market Data Model** is a reusable reference record (`MDM-xxx`); the
  **Calculating Agent** is an institution reference value maintained under Admin
  (see [§5](#5-aggregate-events--commands)). Both are defined once and reused
  across many Products.

### 3.2 Product record fields

| Field | Notes |
|---|---|
| **Product ID** | Stable identifier, e.g. `Product-0001` (mandatory). |
| **Product** | The product/instrument this Product values, e.g. *Government Bond*, *Equity Option* (mandatory). |
| **Product ID** | The product instance reference where one exists. |
| **Analytics Model** | Reference to an inventory model, e.g. `MKM-CR-001` (mandatory). |
| **Market Data Model** | Reference to an `MDM-xxx` record (mandatory). |
| **Calculating Agent** | Selected from the Admin reference list, e.g. *Murex* (mandatory). |
| **Product identifier** | Derived; see [§4](#4-product-identifier). |
| **Status** | Lifecycle: Proposed / Active / Suspended / Retired. |
| **Owner** | From the People directory. |
| **Monitoring approach** | Free text: how this Product is monitored (see [§7](#7-monitoring)). |
| **Monitoring results** | Free text: latest monitoring findings/observations. |
| **Notes** | Free text. |

A Product also carries the standard structured registers where they add value at the
production level — **Limitations** and **Assumptions** — mirroring how inventory
models work today. Monitoring is captured as the two narrative fields above
rather than a structured time-series (see [§7](#7-monitoring)).

## 4. Product identifier

Each Product renders a human-readable identifier in the form:

```
<AnalyticsModelID>.<MarketDataModelID>.<CalculatingAgent>
```

The Analytics Model leads, because it is the engine that defines how the product
is priced and risked; the Market Data Model feeds it; the Calculating Agent is
where it runs. A product that is a **Government Bond** plus an **Equity Option**
might be made up of these Products:

```
Bond_Pricer.NSSF_bond_curve.Murex
Black_Scholes.NSS_equity_vol.Murex
Black_Scholes.SABR_swaption_vol.Murex
```

Reading the first line: a particular bond pricing algorithm (Analytics Model),
fed by a specific bond-curve construction methodology (Market Data Model),
executed on the Murex platform (Calculating Agent). *(NSSF = Nelson-Siegel-
Svensson curve fit over a filtered subset of bonds.)* Each component introduces
its own assumptions, limitations, and failure modes that must be understood and
managed.

The identifier is **derived** from the three component references and is not
independently editable; changing a component changes the identifier (and is an
audited event).

## 5. Aggregate, events & commands

Products follow the platform's event-sourced, confirm-to-amend pattern: every
command opens a confirmation dialog, accepts an optional reason, and appends a
hash-chained event on confirmation. The Audit Trail *is* the change history.

### 5.1 Reference data (new)

- **Market Data Model** (`MDM-xxx`) — a reusable reference record: name,
  description, vendor/source, curve or construction method, update frequency.
- **Calculating Agent** — a new **Admin reference menu**, maintained alongside
  the existing Company / Division / Department lists (see [§6](#6-user-experience)).
  It is simply a name that tells the user which environment the Product is calculated
  in (e.g. *Murex*, *Calypso*, *AM*) — no further attributes. Once populated, the
  Product's Calculating Agent field renders as a dropdown sourced from this list,
  keeping the value consistent across Products.

### 5.2 Product aggregate events

| Event | Trigger |
|---|---|
| `ProductRegistered` | A Product is created with its product and three component bindings. |
| `ProductComponentRebound` | A component reference (Analytics / MDM / Agent) is changed. |
| `ProductFieldEdited` | A scalar field (owner, status, monitoring approach, monitoring results, notes) is edited. |
| `ProductLimitationAdded` / `…Removed` | Production-level limitation register. |
| `ProductAssumptionAdded` / `…Removed` | Production-level assumption register. |
| `ProductSuspended` / `ProductRetired` | Lifecycle transitions; retired Products are read-only. |

### 5.3 Validation rules

- All three component references and the product are mandatory at registration.
- The Analytics Model reference **must resolve** to a live inventory model.
- The combination (Product + Analytics + MDM + Agent) **should be unique** —
  duplicates are flagged at confirmation, not silently allowed.
- Retiring or removing an inventory model that is still referenced by an Active
  Product is **blocked** with a clear message listing the dependent Products.

## 6. User experience

A new top-level **Products** tab, modelled on the Model Inventory:

- **List** — summary cards (counts by status) and a table: Product ID, product,
  derived identifier, Analytics Model, Calculating Agent, owner, status.
- **Register a Product** — a card taking Product ID + product, then three dropdowns:
  **Analytics Model** (sourced from the Model Inventory), **Market Data Model**
  (from the MDM reference records), and **Calculating Agent** (from the Admin
  reference menu). Confirm to create.
- **Product detail** — header (identifier, product, status, owner) plus tabs:
  **Overview** (the bindings, each with an inline *rebind* link; plus the
  **Monitoring approach** and **Monitoring results** fields, inline-editable),
  **Limitations**, **Assumptions**, and **Audit**.
- **Cross-links** — the Analytics Model binding deep-links to that model's
  inventory record; conversely, an inventory model gains a **"Used by N Products"**
  panel listing the Products that reference it.

**Admin.** The reference-menus section gains a fourth list, **Calculating
Agent**, maintained exactly like Company / Division / Department.

Products may be added to an **MRC meeting's** scope alongside models, so the
committee can review a production instance directly.

## 7. Monitoring

Monitoring is captured on the Product record as two free-text fields rather than a
structured time-series tab:

- **Monitoring approach** — how this Product is monitored: what is watched, at what
  frequency, and against what expectation.
- **Monitoring results** — the latest findings/observations from that approach.

Per the handbook, the recommendation is to **start with the basics and build up**
once the activity is bedded in. Suggested content for the *approach* field:

| Basis | What it reveals |
|---|---|
| **Notional Outstanding** | Business growth, concentration risk, capacity limits; sudden spikes flag unvalidated new-product launches. |
| **Maturity Profile** | Model-appropriateness; e.g. a short-dated Product suddenly taking long-dated exposure signals "shoehorning". |
| **Key Sensitivities** | Delta and vega behaviour; instability or non-response to market moves flags underlying model problems. |
| **P&L backtest** | The strongest signal: hypothetical P&L (Taylor approximation from delta/vega and observed market moves) vs. actual P&L. Persistent unexplained difference = the model is missing or mis-capturing risk. |

> **The "shoehorning" risk this is designed to catch:** a barrier option valued
> on a plain Black-Scholes Product because it is the only available equity framework.
> It produces prices and sensitivities but misses the barrier risks that should
> drive hedging — visible at the Product level, invisible at the model level.

## 8. Controlled vocabularies

| Field | Values |
|---|---|
| Product status | Proposed, Active, Suspended, Retired |
| Market Data Model update frequency | Real-time, Intraday, Daily, Weekly, Ad-hoc |
| **Calculating Agent** | *Admin reference menu* (institution-maintained, e.g. Murex, Calypso, AM) — not a fixed vocabulary. |

(Existing vocabularies — tier, RAG, validation status — are inherited from the
referenced Analytics Model and are not redefined here.)

## 9. Out of scope

- **Computing actual valuations.** This platform governs and monitors Products; it
  does not price instruments or run the engines. Metrics are recorded from
  upstream systems.
- **Live feeds from Murex/Calypso/etc.** Initial release is manual/recorded
  entry; automated ingestion is a later phase.
- **Re-validating the analytics model.** Validation stays on the inventory model
  record; a Product inherits and references it.

## 10. Open questions

1. **Monitoring depth** — narrative approach/results fields are sufficient for
   v1. Do we later want to graduate the recurring measures (notional,
   sensitivities, P&L backtest) into a structured time-series with trends?
2. **Product-level risk rating** — do we want a composite rating for a Product, or does
   it simply surface its Analytics Model's rating plus monitoring health?
4. **Many-product Products** — the handbook example lists three identifiers under one
   product set; confirm whether a "product" can bundle instruments or is strictly
   one instrument per Product.
5. **Terminology guard** — elsewhere in the library "Product" is used for *Product,
   Valuation and Market data* (a banking data architecture). This spec uses
   *Product Valuation Model*. Confirm the platform standardises on the latter to
   avoid collision.

---

© 2022–2026 MKM Research Labs. All rights reserved.
