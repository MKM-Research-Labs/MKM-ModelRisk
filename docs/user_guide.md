# MKM-ModelRisk — User Guide

A step-by-step walkthrough of the governance console: from an empty instance to a
fully-linked inventory of models and products, an MRC committee with Terms of
Reference, risk ratings, and a committee meeting that signs models off.

Follow it top-to-bottom the first time — later steps depend on data created in
earlier ones (a product needs models; a committee chair needs a person; a meeting
needs a committee). For installation, see the [README](../README.md).

---

## Contents

1. [Core concepts](#1-core-concepts)
2. [Set yourself up as admin](#2-set-yourself-up-as-admin)
3. [Define the Company](#3-define-the-company)
4. [Divisions and Lines of Business](#4-divisions-and-lines-of-business)
5. [Add People](#5-add-people)
6. [Add Calculating Agents](#6-add-calculating-agents)
7. [Define an MRC and upload its ToR](#7-define-an-mrc-and-upload-its-tor)
8. [Build Models](#8-build-models)
9. [Risk rating explained](#9-risk-rating-explained)
10. [Validation questions](#10-validation-questions)
11. [Build Products](#11-build-products)
12. [Request MRC sign-off](#12-request-mrc-sign-off)
13. [Run an MRC meeting](#13-run-an-mrc-meeting)
14. [Decisions and Actions](#14-decisions-and-actions)
15. [Meeting Pack PDF](#15-meeting-pack-pdf)
16. [Documents, Bibliography, Reports](#16-documents-bibliography-reports)
17. [How everything links](#17-how-everything-links)
18. [The audit trail](#18-the-audit-trail)

---

## 1. Core concepts

A few ideas underpin every screen.

**One institution.** The console runs for a single firm. "Company" is not a list
you add to — it is a singleton (a name and a logo). Divisions and Lines of Business sit
beneath it, and everything hangs off that Company -> Division -> Line of Business tree.

**Identity ("Acting as").** The console does not log you in — in production your
SSO identifies you at the perimeter. Locally, the **Acting as** field in the header
carries your identity, and whatever it says is recorded as the author of every
change you make. Set it to your name or email before you start.

**Confirm-to-amend.** Nothing changes silently. Every action that writes data —
register, edit, add, remove, archive, schedule — first opens a **Confirm change**
dialog with an optional **Reason** box, and only commits when you click
**Confirm and record**. On success you see the toast *"Change recorded in the audit
trail."* This guide will not repeat "then confirm" every time — assume it.

**Immutable, event-sourced audit.** Under the hood each change is appended to a
tamper-evident log rather than overwriting state; the screens are projections
rebuilt from that log. Consequences you can rely on: the full history of every
model, product and meeting is preserved, nothing is ever truly deleted, and the
**Audit Trail** tab does not *describe* the changes — it *is* the changes.

**Derived, not duplicated.** Many links are computed, not typed. A model's
responsible committee, a product's committee (via its analytics model), a meeting's
Division / Line of Business / Chair — all derived. You set the *anchors* (org tier,
bindings) and the system resolves the rest.

---

## 2. Set yourself up as admin

There is **no separate admin role** today — every authenticated user can administer
everything. Access is controlled at the perimeter (an SSO proxy) and the console
reads your identity from a trusted request header. Running locally without a proxy,
you are `david.kelly@mkmresearchlabs.com` by default.

**What to do:**

1. Open the console (locally: `python model.py`, then the host/port from
   `config/web.py`, default `http://127.0.0.1:5015`).
2. Set the **Acting as** field in the header to your name or email — this is the
   actor stamped on every change you make.
3. The main tabs are: **Model Inventory, Products, MRC, Documents, Bibliography,
   Audit Trail, Audit Reports, Admin**.
4. Click **Admin**. Its sub-tabs are **Company, Division, Line of Business, MRC, Calc
   Agent, People**. All setup below happens here.

---

## 3. Define the Company

**Admin -> Company.**

1. **Company name** — click **edit**, type your institution's name (e.g. *Sterling
   Bank plc*), **Save**, confirm. This name appears in the console header and on
   every PDF report.
2. **Logo** — choose a PNG/JPEG and click **Upload logo**. It is embedded in the
   Meeting Pack and Model Risk Report PDFs. (Logo upload is immediate, no confirm
   dialog.)

---

## 4. Divisions and Lines of Business

The org tree scopes committees, people and models. Create Divisions first, then
Lines of Business (a Line of Business must belong to a Division).

**Admin -> Division:** type a Division name (e.g. *Markets*, *Treasury*), **Add**,
confirm. Repeat for each.

**Admin -> Line of Business:** type a Line of Business name (e.g. *Rates Trading*), pick its
**Division** from the dropdown, **Add**, confirm. Repeat (e.g. *Equity Derivatives*
under Markets, *Funding and Liquidity* under Treasury).

Each row has **Edit** and **Remove** on the right (both confirm-to-amend).

---

## 5. Add People

People are the directory used for committee chairs, model and product owners, peer
reviewers, and meeting roles. **Create them before committees and models** so those
dropdowns are populated.

**Admin -> People.** For each person:

| Field | Required | Notes |
|---|---|---|
| **Name** | yes | Full name — this is what shows in dropdowns |
| **Email** | no | |
| **Org level** | yes | `Company`, `Division`, or `Line of Business` |
| **Division / Line of Business** | no | Which specific unit — leave blank for Company-level |

The **Org level** plus **Division / Line of Business** anchor a person to the org tree. A
Company-level person is firm-wide; a Line of Business-level person is scoped to one
line of business. This anchoring is what determines whether they are eligible to sit on a
given committee or own a model in that scope.

Example spread: *David K Kelly* (CRO) -> Company; *Priya Anand* (Head of Rates) ->
Line of Business / Rates Trading; *Marcus Reid* (Treasurer) -> Division / Treasury.

---

## 6. Add Calculating Agents

A Calculating Agent is the pricing/booking platform a **product** runs on (e.g.
*Murex*, *Calypso*). Products bind to one, so create them before building products.

**Admin -> Calc Agent** -> type a **Value** -> **Add** -> confirm.

---

## 7. Define an MRC and upload its ToR

An MRC (Model Risk Committee) is anchored to an org tier, exactly like a person.
That anchoring drives which models and products it is responsible for.

**Admin -> MRC.** Fill the add form:

| Field | Required | Notes |
|---|---|---|
| **MRC ID** | yes | Unique code, e.g. `MRC-AM` |
| **Name** | yes | Human-readable, e.g. *Asset Management MRC* |
| **Level** | yes | `Company`, `Division`, or `Line of Business` |
| **Division / Line of Business** | no | The specific unit it covers (n/a for Company). The scope picker reacts to the Level. |
| **Chair** | no | Dropdown of **People** (add the person first) |
| **Frequency** | no | `Monthly`, `Quarterly`, `Semi-annual`, `Annual` |

Click **Add committee**, confirm.

**What Level means (the coverage rule):**

- **Company** — covers the whole inventory (the backstop).
- **Division** — covers everything in that division and its lines of business.
- **Line of Business** — covers only that line of business's models.

When a model needs a committee, the system picks the **most specific** active
committee that covers it: Line of Business, then Division, then Company. Archived
committees never match.

**Upload the Terms of Reference (ToR):**

1. In the MRC sub-tab, **click the committee row** to open its detail panel.
2. Find the **Terms of Reference** section.
3. Choose a file and click **Upload ToR**. A download link (with a **Replace**
   option) then appears. The ToR is also downloadable from the MRC meetings tab.

**Archive / Unarchive:** the committee detail panel has an **Archive committee**
toggle. Committees are never deleted — archiving keeps history and any meetings
already bound to it, while removing it from pickers and future matching.

---

## 8. Build Models

**Model Inventory tab -> + Register model.**

At registration you only need:

| Field | Required |
|---|---|
| **Model ID** | yes |
| **Name** | yes |
| **Type** | no (`Analytical Model`, `Market Data Model`, `Other`) |
| **Division** / **Line of Business** | no (dropdowns from your org tree) |

Set **Division/Line of Business** at registration or soon after — this is what links the
model to its MRC (section 17). A model with no org tier can only match a
Company-level committee. **Type** matters for products: an *analytics model*
binding accepts non-Market-Data models; a *market data model* binding accepts only
`Market Data Model` type.

On registration the platform automatically seeds the **nine SR 26-2 validation
questions** against the model, each starting *Not Addressed*.

Click a model row to open its **detail view**, then fill the rest via inline
**edit** links. Key fields, grouped:

- **Classification:** short name, description, category, **Tier** (1 = mission
  critical, 2 = important, 3 = not important), **Materiality** (Low/Medium/High),
  **Complexity** (Low/Medium/High).
- **Governance:** **Owner** (People), peer reviewer, lifecycle stage, validation
  status, version, **RAG rating**, review frequency.
- **Review dates:** last review, next review, MRC sign-off, recertification,
  validation date.
- **Testing:** unit / integration / benchmark tests (Yes/No).

Detail tabs: **Overview, Remediation, Versions, Limitations, Assumptions, Changes,
Validation, Events, Risk, Decisions, Actions, Docs, Audit, Danger**. Each
collection has its own add / edit / remove.

---

## 9. Risk rating explained

Open a model's **Risk** tab. Risk rating has **two independent parts.**

### (a) The RAG heatmap: Materiality x Complexity, by Tier

This is the owner-facing rating and it is a lookup. Your model's **Tier** selects
one of three 3x3 grids, and the (**Materiality**, **Complexity**) cell gives a
**Green / Amber / Red**. It only appears once *both* materiality and complexity are
set. Higher tiers escalate to Red faster. For example:

**Tier 1 (mission critical):**

| Materiality (down) / Complexity (across) | Low | Medium | High |
|---|---|---|---|
| **High** | Amber | Red | Red |
| **Medium** | Green | Amber | Red |
| **Low** | Green | Green | Amber |

**Tier 3 (not important)** is mostly Green; **Tier 2** sits in between. The grid is
drawn on the Risk tab with your current cell highlighted.

The Overview shows **two RAG badges** side by side: the owner-set `RAG rating` field
and the **computed heatmap RAG**. When they diverge, that is the signal the rating
needs MRC sign-off (section 12).

### (b) The composite health score

Separately, an operational-health score (0-100%) is computed from five weighted
signals:

| Signal | Weight | Measures |
|---|---|---|
| Validation coverage | 30% | Validation questions marked *Addressed* out of 9 |
| Remediation health | 25% | Remediation steps *Closed* out of total |
| Review currency | 20% | Is the next review date still in the future? |
| Assumption risk | 15% | Fewer High-impact assumptions is better |
| Limitation risk | 10% | Fewer High-impact limitations is better |

Thresholds: **>= 75% Acceptable**, **50-75% Conditional**, **< 50% Unacceptable**.
The Risk tab breaks this down bar by bar and shows a count of operational failure
events in the last 365 days.

In short: the **heatmap** answers *"how risky is this model?"* (materiality x
complexity x tier); the **composite** answers *"how healthy is our governance of
it?"* (validation, remediation, reviews).

---

## 10. Validation questions

Every model is seeded on registration with **nine SR 26-2 validation questions**
(the Ronseal test, accuracy and stability, resource usage, override controls, data
quality, assumptions, limitations, benchmarking, independent validation).

**Model detail -> Validation tab.** For each question set a **Status**
(`Addressed`, `Partially Addressed`, `Not Addressed`, `Not Applicable`) and a
**rationale**, then **Save**. The count of *Addressed* answers drives the
validation-coverage component of the composite score, and the tab shows progress
(e.g. *Validation (6/9)*).

---

## 11. Build Products

A Product is a live pricing/booking configuration built from three components.
**Prerequisites:** its analytics model and market-data model must exist in the
inventory (the analytics model must be **live**, i.e. not retired), and its
calculating agent must exist in Admin -> Calc Agent.

**Products tab -> Register a Product.** All of these are required:

| Field | References |
|---|---|
| **Product ID** | — |
| **Product** (name) | — |
| **Analytics Model** | a live, non-Market-Data model |
| **Market Data Model** | a `Market Data Model`-type model |
| **Calculating Agent** | the Calc Agent list |

The three bindings form the product's **derived identifier**
(`AnalyticsModel.MarketDataModel.CalcAgent`), which must be unique across live
products. Status starts at **Proposed**.

In the product detail view:

- **Components** are shown with a **rebind** link — you change a binding via
  *rebind*, not a normal edit, which preserves lineage and re-validates.
- Editable fields: **RAG rating**, status (`Proposed / Active / Suspended /
  Retired`), **Owner** (People), notes, review dates, monitoring approach and
  results.
- The **MRC** section shows which committee is responsible **and via which model**.
- Tabs: **Overview, Limitations, Assumptions, Remediation, Docs, Audit, Danger**
  (retire).

---

## 12. Request MRC sign-off

Sign-off is how a **RAG rating becomes official** — a committee approves it. It
works the same way for models and products.

**To raise a request** (model **Risk** tab, or product **Overview**): set a RAG
rating, then click **Request MRC sign-off**. The request is:

1. **Routed** to the responsible committee automatically — a model via its
   division/line of business, a product via its analytics model's division/line of business.
2. **Attached** immediately to that committee's next **Scheduled** meeting agenda
   if one exists; otherwise **queued (Pending)** and drained onto the agenda the
   moment such a meeting is scheduled.

The request state (`Pending` -> `Attached` -> `Completed`) shows on the Risk /
Overview panel. If no committee covers the subject you are told to configure one
first.

---

## 13. Run an MRC meeting

**MRC tab.** Pick a committee (the schedule form is hidden until at least one
committee exists). Its card shows chair, frequency, level/scope, and a ToR download
link.

**Schedule a meeting:** fill **Meeting ID**, **Title**, **Date** (required), and
optionally **Time** and **Location**. The committee is set from your selection and
status defaults to **Scheduled**. Scheduling a meeting also **drains any queued
sign-off requests** for that committee onto the agenda.

**Open a meeting** (double-click its row). The header shows:

- **Row 1 (read-only, derived from the committee):** MRC, Division, Line of Business,
  Chair.
- **Row 2:** Date, Time, Location (fixed at scheduling, read-only) and **Status**
  (editable inline — this is how you move a meeting `Scheduled -> Completed`).

Meeting tabs: **Agenda, Minutes, Participants, Models, Decisions, Actions,
Documents.**

### Agenda

Each item is a two-row card: Title and Description on top; Presenter, Status and any
sign-off details below. Add items with the **Add agenda item** form (Title
required; optional Description, Presenter, Status, Subject model, Proposed RAG).

**Sign-off agenda items** (those carrying a subject model/product plus a proposed
RAG) show two extra actions while **Pending**:

- **approve sign-off** — snaps the subject's RAG rating to the proposed value,
  stamps the **MRC sign-off date and meeting** on it, writes a **sign-off history**
  entry, marks the queued request **Completed**, and completes the agenda item. The
  comment you type in the confirm dialog is saved as the sign-off note.
- **escalate** — opens a picker to choose **another MRC**; the item is copied onto
  that committee's next Scheduled meeting and the original is marked **Escalated**.

### Minutes, Participants, Models

- **Minutes** — bulk-add several rows at once (Title required, Presenter, text).
- **Participants** — added one at a time: Name, Role, Organisation, Status
  (`Invited / Attended / Apologies / Declined`).
- **Models** — a multi-select of inventory models "in scope" for the meeting,
  **pre-filtered to the committee's remit** (a Line of Business-level MRC shows only that
  line of business's models; toggle **Show all models** to override). Tick the models and
  **Save selection**. In-scope models' open remediation steps appear in the Meeting
  Pack PDF.

---

## 14. Decisions and Actions

**Yes, decisions and actions link to models.** Both collections have an optional
**Model** field (a dropdown of the inventory):

- **Decisions:** Decision (required), Date, **Model**.
- **Actions:** Action (required), Owner, Target date, Status (`Open / Closed`),
  **Model**.

Add them on the meeting's **Decisions** and **Actions** tabs (bulk-add supported).
When you link one to a model, it **automatically surfaces on that model's detail
view** — the model's own **Decisions** and **Actions** tabs list every meeting item
pointing at it, credited with the source meeting (title, ID, date). This is
read-only on the model side: the meeting is the system of record; the model simply
reflects it.

So the workflow is: raise the decision or action **in the meeting**, tag the model,
and it shows up under that model automatically — no double entry.

---

## 15. Meeting Pack PDF

From an open meeting, click **Meeting Pack PDF** (top right). It renders a PDF
containing the company logo and name, the meeting info line, **Participants**,
**Agenda**, **Minutes**, **Decisions**, **Actions**, and a per-model **open
remediation** section for each in-scope model.

Requires the `tectonic` LaTeX engine on the server (`brew install tectonic`). If it
is not installed the endpoint returns an error instead of a PDF.

---

## 16. Documents, Bibliography, Reports

**Documents.** A governance-wide library independent of any single model. Upload a
file with an optional description; the table lists name, description, date added and
size, with download and delete. Use it for institution-level policies and papers.
(Models and products also have their own **Docs** tab for item-specific files.)

**Bibliography.** A reference list — author(s), year, title, journal / publisher,
category, URL — with a category filter and per-row Edit / Del. **Export BibTeX**
downloads the whole bibliography as a `.bib` file.

**Audit Reports.** Several PDFs are produced on demand (all require `tectonic`):
the **Model Risk Report** (the portfolio profile, the inventory table, and then a
full dossier per model — classification, methodology, governance, validation
questions and evidence, assumptions, limitations, weaknesses, remediation,
dependencies, change history, MRC sign-offs and attached documents; also on the
Model Inventory tab), the per-meeting **Meeting Pack**, the **Coding-Rule Audit**,
and **this User Guide**. Open the **Audit Reports** tab, click **Generate reports**,
then **View** or **Download** each; files are written to `uploads/audit/`.

---

## 17. How everything links

The whole point is that nothing floats free. The chain, top to bottom:

- **Company** (singleton: name + logo)
  - **Division** then **Line of Business** — the org tree (Admin)
    - **People** — anchored by Org level + scope; become chairs / owners / roles
    - **MRC committee** — anchored by Level + scope, carries a ToR; covers the
      models in its scope
    - **Model** — tagged with Division/Line of Business
      - Risk rating: Materiality x Complexity x Tier -> RAG
      - Validation (9 x SR 26-2) and Owner feed the composite health score
      - matches an MRC (Line of Business, else Division, else Company)
      - sign-off request -> committee meeting -> approved RAG
    - **Product** — binds Analytics Model + Market Data Model + Calc Agent
      - inherits its MRC via the Analytics Model's org
      - sign-off request -> committee meeting -> approved RAG
- **MRC meeting** (of a committee)
  - Agenda (including routed sign-off items -> approve / escalate)
  - Models in scope (filtered to the committee's remit)
  - Decisions / Actions tagged to a Model, which then appear on that Model's detail

**Recommended build order** (each step feeds the next):

1. **Company** name and logo.
2. **Divisions**, then **Lines of Business**.
3. **People** (needed for chairs and owners).
4. **Calculating Agents** (needed for products).
5. **MRC committee** and **ToR** (chair picks from People).
6. **Models** — set Division/Line of Business so they match a committee; set
   Materiality / Complexity / Tier for a RAG; answer validation questions.
7. **Products** — bind to existing models plus a calc agent.
8. **Request sign-off** on a model or product.
9. **Schedule an MRC meeting** — the queued sign-off drains onto the agenda.
10. **Run the meeting** — approve sign-offs, record minutes, tag decisions/actions
    to models, save models-in-scope, download the Meeting Pack PDF.

---

## 18. The audit trail

Because every change is an append-only event, you get a complete, tamper-evident
history for free:

- **Audit Trail tab** — the full event log across the whole instance, most recent
  first, with the actor, the reason, and per-field before/after values.
- **Per-record Audit tab** — on any model or product detail, its own change
  history.

This is why the console insists on confirm-to-amend with a reason: the audit trail
is a first-class governance artefact, not a side-effect. It cannot be edited or
cleared from the application.

---

© 2022-2026 MKM Research Labs. Licensed under the MIT License; see [`LICENSE`](../LICENSE).
