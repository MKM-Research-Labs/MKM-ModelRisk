# MKM-ModelRisk — User Guide

A step-by-step walkthrough of the governance console: from an empty instance to a
fully-linked inventory of models and products, a model chain with reviewed
handoffs, an MRC committee with Terms of Reference and a quorate roster, risk
ratings, a committee meeting that signs models off, and a client pack that
aggregates it all.

Follow it top-to-bottom the first time — later steps depend on data created in
earlier ones (a product needs models and a calculating agent; a committee chair
needs a person; a meeting needs a committee). For installation, see the
[README](../README.md).

---

## Contents

1. [Core concepts](#1-core-concepts)
2. [The tabs, and setting yourself up](#2-the-tabs-and-setting-yourself-up)
3. [Define the Company](#3-define-the-company)
4. [Divisions and Lines of Business](#4-divisions-and-lines-of-business)
5. [Add People](#5-add-people)
6. [Model Types and Calculating Agents](#6-model-types-and-calculating-agents)
7. [Define an MRC — roster, quorum and ToR](#7-define-an-mrc--roster-quorum-and-tor)
8. [Build Models](#8-build-models)
9. [Risk rating explained](#9-risk-rating-explained)
10. [Validation questions](#10-validation-questions)
11. [The Model Chain and handoffs](#11-the-model-chain-and-handoffs)
12. [Build Products](#12-build-products)
13. [Request MRC sign-off](#13-request-mrc-sign-off)
14. [Run an MRC meeting](#14-run-an-mrc-meeting)
15. [Meeting lifecycle: finalise, close, succession](#15-meeting-lifecycle-finalise-close-succession)
16. [Actions and decisions that link to models](#16-actions-and-decisions-that-link-to-models)
17. [Clients and client packs](#17-clients-and-client-packs)
18. [Documents and Audit Reports](#18-documents-and-audit-reports)
19. [How everything links](#19-how-everything-links)
20. [The audit trail](#20-the-audit-trail)

---

## 1. Core concepts

A few ideas underpin every screen.

**One institution, an org tree.** The console runs for a single firm. "Company"
is not a list you add to — it is a singleton (a name and a logo). Divisions and
Lines of Business sit beneath it, and everything hangs off that
Company → Division → Line of Business tree.

**The org-scope selector.** The header carries a scope selector for the current
Company / Division / Line of Business. It scopes what the lists show and it
**fixes the Division / Line of Business of anything you register** while it is
selected — so you set the scope once in the header rather than re-typing it on
every form.

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
tamper-evident, hash-chained log rather than overwriting state; the screens are
projections rebuilt from that log. Consequences you can rely on: the full history
of every model, product and meeting is preserved, nothing is ever truly deleted,
and the **Audit Trail** tab does not *describe* the changes — it *is* the changes.

**Derived, not duplicated.** Many links are computed, not typed. A model's
responsible committee, a product's committee (via its bindings), a meeting's
Division / Line of Business / Chair — all derived. You set the *anchors* (org tier,
bindings, roster) and the system resolves the rest.

---

## 2. The tabs, and setting yourself up

There is **no separate admin role** today — every authenticated user can administer
everything. Access is controlled at the perimeter (an SSO proxy) and the console
reads your identity from a trusted request header. Running locally without a proxy,
you are `david.kelly@mkmresearchlabs.com` by default.

**What to do:**

1. Open the console (locally: `python model.py`, then the host/port from
   `config/web.py`, default `http://127.0.0.1:5015`).
2. Set the **Acting as** field in the header to your name or email — this is the
   actor stamped on every change you make.
3. Set the **org-scope selector** in the header to the Company (and, later,
   Division / Line of Business) you are working in.

The main tabs, left to right, are: **MRC**, **Models**, **Model Chain**,
**Products**, **Clients**, **Audit Trail**, **Documents**, **Audit Reports**, and
**Admin**.

Click **Admin**. Its sub-tabs are **Company**, **Division**, **Line of Business**,
**MRC**, **Calc Agent**, **Data Source**, **People**, **Model Type**, **Vendor**,
**Risk** and **Misc**. All the setup in sections 3–7 happens here.

---

## 3. Define the Company

**Admin → Company.** This is a single-record editor, not a list.

1. **Company name** — click **edit**, type your institution's name (e.g. *Sterling
   Bank plc*), **Save**, confirm. This name appears in the console header and on
   every PDF report.
2. **Logo** — choose a PNG/JPEG and click **Upload logo**. It is embedded in the
   Meeting Pack, Model Risk Report and client-pack PDFs. (Logo upload is immediate,
   no confirm dialog.)

### What your PDFs say — Admin → Misc

The wording every generated PDF carries is yours, not the platform's. **Admin →
Misc** holds it, and each field is edited in place (**edit** → type → **Save** →
confirm) like any other setting:

| Field | Where it appears |
|---|---|
| **Classification banner** | Title page (in red) and the centre of every page footer — e.g. *CONFIDENTIAL — PROPRIETARY*, *OFFICIAL-SENSITIVE* |
| **Prepared by (document author)** | The author line on the title page, beneath the date and version |
| **Legal notice** | The block at the foot of the title page. Leave a blank line between paragraphs; each becomes its own paragraph in the PDF |

The legal notice covers the **contents** of the document — the models, methodology
and calculations it describes. It says nothing about the software that generated
it, which is MIT-licensed (see `LICENSE`). Until you change them, these fields
carry MKM Research Labs' shipped wording, so **set them before you publish
documents outside your institution**. Saving a field empty drops that line from
your documents altogether — for an institution that classifies nothing, or that
files its legal notice elsewhere.

Changes apply to every document generated afterwards: Meeting Packs, Model Risk
Reports, model and product documents, completeness audits, risk-categorisation
documents and client packs. PDFs already generated and stored are unchanged.

This sub-tab also holds **Document model types** — the comma-separated tag
taxonomy offered on the top-level Documents tab.

---

## 4. Divisions and Lines of Business

The org tree scopes committees, people, models and products. Create Divisions
first, then Lines of Business (a Line of Business must belong to a Division).

**Admin → Division:** type a Division name (e.g. *Markets*, *Treasury*) in the
**Division** field, **Add**, confirm. Repeat for each.

**Admin → Line of Business:** type a **Line of Business** name (e.g. *Rates
Trading*), pick its **Division** from the dropdown, **Add**, confirm. Repeat (e.g.
*Equity Derivatives* under Markets, *Funding and Liquidity* under Treasury).

Each row has **Edit** and **Remove** on the right (both confirm-to-amend).

---

## 5. Add People

People are the directory used for committee chairs and secretaries, model and
product owners, peer reviewers and remediation owners. **Create them before
committees and models** so those dropdowns are populated.

**Admin → People.** For each person:

| Field | Required | Notes |
|---|---|---|
| **Name** | yes | Full name — this is what shows in dropdowns |
| **Email** | no | |
| **Division** | no | Which Division they belong to (leave blank for firm-wide) |
| **Line of Business** | no | Which Line of Business, if narrower than a Division |

A person's Division / Line of Business anchor them to the org tree; leaving both
blank makes them firm-wide. This anchoring is what determines whether they are
eligible to chair, or sit on, a committee in a given scope. Each row has **Edit**
and **Remove**.

Example spread: *David K Kelly* (CRO) → firm-wide; *Priya Anand* (Head of Rates) →
Line of Business *Rates Trading*; *Marcus Reid* (Treasurer) → Division *Treasury*.

---

## 6. Model Types and Calculating Agents

Two small reference lists that Models and Products depend on — set them up before
building either.

**Admin → Model Type.** Each model type carries a machine-readable **Binding role**
that products use when they bind a model as a component:

| Field | Required | Notes |
|---|---|---|
| **Type** | yes | The label shown in the model **Type** dropdown (e.g. *Analytical Model*, *Curve Model*, *Market Data Model*, *Other*) |
| **Binding role** | yes | `Analytics`, `Market Data`, or `Neither` — product component slots filter on this role, **not** on the type name |

So a product's *Market Data* component accepts any model whose type has the
**Market Data** binding role, and its *Analytics* component accepts any model with
the **Analytics** role. Naming a new type differently does not break bindings — the
role does the work.

**Admin → Calc Agent.** A Calculating Agent is the pricing/booking platform a
**product** runs on (e.g. *Murex*, *Calypso*). Type a **Value** → **Add** → confirm.
Products bind to one, so create them before building products.

---

## 7. Define an MRC — roster, quorum and ToR

An MRC (Model Risk Committee) is anchored to an org tier, exactly like a person.
That anchoring drives which models and products it is responsible for, and its
**roster** and **quorum rules** drive whether its meetings can proceed.

**Admin → MRC.** Fill the add form:

| Field | Required | Notes |
|---|---|---|
| **MRC ID** | yes | Unique code, e.g. `MRC-AM` |
| **Name** | yes | Human-readable, e.g. *Asset Management MRC* |
| **Level** | yes | `Company`, `Division`, or `Line of Business` |
| **Division / Line of Business** | no | The specific unit it covers (n/a for Company). The scope picker reacts to the Level. |
| **Frequency** | no | `Monthly`, `Quarterly`, `Semi-annual`, `Annual` — also sets the interval to the auto-scheduled next meeting |

Click **Add committee**, confirm, then **click the committee row** to open its
detail panel and complete it:

- **Membership** — set the **Chair**, **Secretary**, **Voting members** and
  **Non-voting members** (all chosen from People in scope). This roster is carried
  onto every meeting as its participants list.
- **Quorum** — **Requires chair** (default *Yes*), **Requires secretary** (default
  *Yes*), **Min voting members** (default *2*). A meeting cannot proceed to
  sign-offs, or be closed, until it is quorate against these rules.
- **Terms of Reference** — choose a file and click **Upload ToR**. A download link
  (with a **Replace…** option) then appears. The ToR is also surfaced on the MRC
  tab and included in client packs.

**What Level means (the coverage rule):**

- **Company** — covers the whole inventory (the backstop).
- **Division** — covers everything in that division and its lines of business.
- **Line of Business** — covers only that line of business's models.

When a model needs a committee, the system picks the **most specific** active
committee that covers it: Line of Business, then Division, then Company. Archived
committees never match.

**Archive / Unarchive:** the committee detail panel has an **Archive committee**
toggle. Committees are never deleted — archiving keeps history and any meetings
already bound to it, while removing it from pickers and future matching.

---

## 8. Build Models

**Models tab → + Register model.** With the header org-scope set, the modal
(*Register a model*) needs:

| Field | Required | Notes |
|---|---|---|
| **Model ID** | yes | e.g. `MKM-CR-001` |
| **Name** | yes | e.g. *Retail Credit Scoring* |
| **Type** | no | Dropdown from your **Model Type** list |
| **Division / Line of Business** | — | Read-only, fixed by the header org-scope selector |
| **Model Owner** | yes | Dropdown from People |

Because Division / Line of Business come from the header scope, set that scope
correctly *before* registering — it is what links the model to its MRC (section 19).
A model registered at Company scope can only match a Company-level committee.

On registration the platform automatically seeds the **nine SR 26-2 validation
questions** against the model, each starting *Not Addressed*.

Click a model row to open its **detail view**. The header shows the name, its
`id · version · category`, tier badge, next-review date and — on the right — the
**Owner** RAG badge. The detail tabs, in order, are:

**Overview · Versions · Limitations · Dependencies · RACI ·
Validation & Assumptions · Risk Rating · MRC linkage · Docs · Danger ·
Audit.**

- **Overview** — a **Summary** band (the description) then two columns: **Model
  Details** (Division, Line of Business, Repository location, Codebase, Type, Short
  name, Methodology and rationale, Source module, Materiality, Complexity, Tier and
  rationales) and **Governance** (the responsible MRC, RAG rating, Owner and role,
  Lifecycle stage, Review status, Peer reviewer, Validation date, MRC status, Next
  review). Fill any field via its inline **edit** link.
- **Versions** — the version register (Version, Date, Description, Author, Reference
  document, Lifecycle) plus the **Change history** register.
- **Limitations** — two registers: **Model weaknesses** (Description, Impact) and
  **Limitations** (Description, Impact, Monitoring trigger, Compensating control).
- **Dependencies** — declare this model's edges in the model chain: **Direction**
  (upstream / downstream), **Related model**, and a note. These declarations build
  the Model Chain (section 11).
- **RACI** — the responsibility matrix: Role, RACI (Responsible / Accountable /
  Consulted / Informed), Assigned to, Backup, Description.
- **Validation & Assumptions** — the nine SR 26-2 questions (section 10) plus the
  **Assumptions** register (Description, Impact, Monitoring, Mitigation).
- **Risk Rating** — see section 9. **Remediation** sits at the foot of this tab:
  remediation steps (Description, Owner, Priority (Low/Medium/High), Due date,
  Status (Open / In Progress / Closed)) with the **Supporting documents** panel that
  files the evidence closing them. The heading carries the open-step count.
- **MRC linkage** — the meeting decisions and actions tagged to this model
  (section 16), read-only here.
- **Docs** — item-specific documents on per-category sub-tabs (**Core Documentation ·
  Sensitivity · Analysis · Testing · Monitoring · History**), plus **Model Risk
  Document (PDF)** and **Client pack (ZIP)** generation for this model. The
  **Testing** sub-tab is evidence-driven: upload the overall **Test results** pack
  and the **Unit tests**, **Integration tests** and **Benchmark tests** results into
  their panels. (The old Yes/No flags are gone; the record is the attached evidence.)
- **Danger** — **Request retire…** (hibernate) or **Request reactivate…**. Both go
  to the responsible committee as a sign-off item to ratify (section 13); they are
  not immediate.
- **Audit** — this model's own change history.

---

## 9. Risk rating explained

Open a model's **Risk Rating** tab. There is **one** governed rating — the tier
heatmap — deliberately not a competing second score.

### The RAG heatmap: Materiality × Complexity, by Tier

Your model's **Tier** selects one of three 3×3 grids, and the (**Materiality**,
**Complexity**) cell gives a **Green / Amber / Red**. The tab draws the grid
captioned *"Tier n heatmap — {label}"* (Tier 1 *Mission critical*, Tier 2
*Important*, Tier 3 *Not important*), with your current cell outlined and marked
**YOU**, and a headline **HEATMAP RATING** band in the cell's colour. It appears
once both Materiality and Complexity are set. Higher tiers escalate to Red faster.
For example:

**Tier 1 (mission critical):**

| Materiality (down) / Complexity (across) | Low | Medium | High |
|---|---|---|---|
| **High** | Amber | Red | Red |
| **Medium** | Green | Amber | Red |
| **Low** | Green | Green | Amber |

**Tier 3** is mostly Green; **Tier 2** sits in between.

### Owner vs Table, and sign-off

The Overview shows **two RAG badges** side by side: the **Owner**-set `RAG rating`
field and the computed **Table** (heatmap) RAG. When they diverge, that is the
signal the rating needs MRC sign-off. The Risk Rating tab also shows the **sign-off
state** — *Pending MRC sign-off*, *MRC signed off — {RAG}* (with a **Revoke
sign-off…** control), or a prompt to request one — and a **Sign-off history** table
(Date, Outcome, From, To, Meeting, Next review, Note).

> **No composite score.** Unlike some earlier drafts, there is no second 0–100%
> "health" score. The one rating the committee sets and reviews is the model's risk
> statement. (The percentage you may see on the **Validation & Assumptions** tab is
> validation *coverage*, not a risk score.) A rolling **operational-events** count
> is shown on **products** only, not on models.

To raise the rating for approval, use **Request MRC sign-off…** (section 13).

---

## 10. Validation questions

Every model is seeded on registration with **nine SR 26-2 validation questions**
(the Ronseal test, accuracy and stability, resource usage, override controls, data
quality, assumptions, limitations, benchmarking, independent validation). SR 26-2
supersedes SR 11-7; the questions are unchanged.

**Model detail → Validation & Assumptions tab.** The questions render as a table
(**#**, **Question**, **Status**, **Rationale**). For each, set a **Status**
(`Addressed`, `Partially Addressed`, `Not Addressed`, `Not Applicable`) and a
**rationale**, then **Save**. Summary cards count Addressed / Partially / Not
Addressed / N/A, and a coverage bar shows progress. The same tab carries the
**Assumptions** register beneath the questions.

---

## 11. The Model Chain and handoffs

**Model Chain tab.** The chain is the *"string of pearls"* — a directed graph
derived automatically from what each model declares on its **Dependencies** tab
(section 8). Declarations are cycle-checked, so the chain stays acyclic. Three
sub-tabs:

- **Chain** — the models that sit in the chain, drawn producer → consumer.
- **Terminal** — terminal outputs: models with no downstream consumer.
- **Hibernated** — retired models, kept for history.

Beneath the graph, a **Handoffs** table lists every edge with its **Status** (an
edge starts *Draft*), a field-lineage summary, and a **Define handoff** /
**Edit handoff** button.

**Define a handoff** to open the handoff panel (*Handoff — {from} → {to}*). Each
handoff carries:

- a **Compatibility note** (textarea + **Save note**) — the MRC's plain-language
  read on whether the two models fit together;
- a **Field lineage** table mapping each **Provider** field to a **Consumer**
  field. Add a mapping with **Field / Type / Units** on each side plus a **Note**,
  then **Add mapping**;
- an MRC **compatibility sign-off** — *Not yet submitted*, *Pending MRC sign-off*,
  or *approved* — raised with **Request MRC sign-off…** and ratified as a `handoff`
  sign-off in a meeting (section 14).

A **Handover document** can be downloaded for the edge.

> **Ingested lineage (for producer systems).** Lineage can also be pushed in from a
> producing repository through a token-gated, schema-validated ingest API — a whole
> model chain, field-level report lineage (BCBS 239 Principle 3), or a full data
> manifest. That is an integration path rather than a screen; declared dependencies
> and handoffs above are the manual equivalent.

---

## 12. Build Products

A Product is a live pricing/booking configuration. **Prerequisites:** its
Calculating Agent must exist (Admin → Calc Agent), and the models it will bind as
components must exist in the inventory.

**Products tab → + Register Product.** Registration is deliberately light — you
name the product and its platform, then bind its models afterwards:

| Field | Required |
|---|---|
| **Product ID** | yes |
| **Product** (name) | yes |
| **Calculating Agent** | yes |

Status starts at **Proposed**. Open the product's detail view; its tabs are:

**Overview · Components · Limitations · Assumptions · Remediation · Events · RACI ·
Risk Rating · MRC · Docs · Danger · Audit.**

- **Components** — bind the models the product pulls in. Each component has a
  **Type** (from your Model Type list, so its binding role decides eligibility), a
  **Model** (from the inventory) and a **Role in product**. A product is *not*
  limited to a fixed "analytics + market-data" pair — bind as many as it needs. The
  classic shape is one Analytics-role model and one Market-Data-role model.
- **Overview** — Components and Calculating Agent binding, plus Product details,
  Organisation, Classification (Tier / Materiality / Complexity), Monitoring
  approach, and Governance & review (Status, Owner, MRC sign-off, review dates,
  Notes). The scalar **Calculating Agent** binding is changed with a **rebind** link
  (which preserves lineage and re-validates), not a plain edit.
- **Risk Rating** — the same tier heatmap as a model, **plus** a rolling
  **Events (past 365 days)** card fed by the Events tab.
- **Events** — operational-failure events (date, what happened, remediation, and
  RACI attribution). These feed the risk window and flow up to the committee.
- **MRC** — the committee responsible for this product (derived from its bindings)
  and the latest meeting MRC status.
- **Danger** — **Retire Product…** (retired products become read-only).

Editable status values are **Proposed / Active / Suspended / Retired**. A product's
RAG rating is set directly on the product; the authoritative MRC position is the
committee's meeting decision, surfaced in the **MRC status** row.

---

## 13. Request MRC sign-off

Sign-off is how a committee ratifies a decision. Sign-off items come in four
**kinds**: **rag** (approve a RAG rating), **retire** and **reactivate**
(hibernate / restore a subject), and **handoff** (approve a chain edge's
compatibility).

**To raise a request:**

- **A model's RAG** — on the model **Risk Rating** tab, set the proposed RAG and
  click **Request MRC sign-off…**. The change is *proposed*, not applied — it only
  takes effect when the committee approves.
- **Retire / reactivate a model** — from the model **Danger** tab (**Request
  retire… / Request reactivate…**).
- **A handoff** — from the handoff panel (section 11).
- **A product** — a product's RAG is set directly, but a sign-off can still be
  routed to its covering committee where your process requires ratification.

Every request is:

1. **Routed** to the responsible committee automatically — a model via its
   division / line of business, a product or handoff via its subject's org.
2. **Attached** immediately to that committee's next **Scheduled** meeting if one
   exists; otherwise **queued (Pending)** and drained onto the agenda the moment
   such a meeting is scheduled.

The request state (`Pending → Attached → Completed`, or `Rejected`) shows on the
Risk Rating / handoff panel. If no committee covers the subject you are told to
configure one first. A global **Request MRC sign-off** dialog (with a **Meeting**
picker) is also available to queue an item directly.

---

## 14. Run an MRC meeting

**MRC tab.** Pick a committee. Its cards show **MRC** (name · level · scope),
**Chair**, **Frequency**, and a Terms-of-Reference download when one is uploaded,
plus a meeting summary (Total / Scheduled / Completed).

**Schedule a meeting.** Fill **Meeting ID**, **Title**, **Date** (required), and
optionally **Time** and **Location**; the committee is set from your selection and
status defaults to **Scheduled**. Scheduling also **drains any queued sign-off
requests** for that committee onto the new agenda.

**Open a meeting** (double-click its row). The info bar shows read-only chips
derived from the committee — **MRC**, **Division**, **Line of Business**, **Chair**
— and editable chips **Date**, **Time**, **Location** and **Status** (this is how
you would move a meeting's status inline).

On the left is a persistent **Participants** panel: the committee roster, an
attendance status per person (`Invited / Attended / Apologies / Declined`), a live
**Quorum met / not met** badge (with what it still *Needs*), and an **Add guest**
control. **A meeting that is not quorate cannot proceed to sign-offs or be closed.**

The meeting has four tabs:

### Agenda

Meetings open with a **standing agenda** (Rollcall & Confirmation of Quorum →
Sign-off of the previous minutes → Review model sign-off → Review model analysis →
Any Other Business), each with its own confirm control. Add your own items with
**Add agenda item** (Title required; optional Description and Presenter). You can
**Finalise agenda for distribution…** to lock it and produce a **Distribution pack
(ZIP)**; **Unlock** reopens it. An **Operational events for review** sub-section
lets the committee receive product events raised since last time.

### Signoff

Two sections, each with **Models / Products / Handoffs** sub-tabs:

- **Approvals — MRC sign-offs.** Every routed sign-off item appears here with its
  subject and its ask (e.g. *→ Amber* for a rag item, *Retire · hibernate*,
  *Reactivate*, or a handoff compatibility approval). For a rag item you can set a
  **Next review** date. Two actions: **Approve** and **Reject**.
  - **Approve** carries out the decision for its kind — snaps a model's RAG to the
    proposed value and stamps the MRC sign-off date and meeting; hibernates or
    restores for retire / reactivate; records compatibility for a handoff — writes a
    **sign-off history** entry, **auto-generates a minute**, and marks both the
    request and the agenda item **Completed**. (Approval requires the meeting to be
    quorate.)
  - **Reject** changes nothing on the subject; it records the decision and marks the
    request and item **Rejected**.
  - *Escalation to another committee exists in the model and the API, but there is
    no button for it in the current UI.*
- **Analysis.** A scope picker of inventory models / products / handoffs
  **in scope** for the meeting, **pre-filtered to the committee's remit**. Tick
  subjects and **Save selection…**. For each, record an **Outcome** (*Pending* or
  *Reviewed — agreed to proceed*), a **Discussion note**, and any **Follow-on
  remediation** (Remediation, Owner, Due date). In-scope subjects' open remediation
  appears in the Meeting Pack PDF.

### Actions

Add actions (bulk-add supported): **Action** (required), **Owner**, **Target
date**, **Status** (`Open / Closed`), and an optional **Model** link. Actions
tagged to a model surface on that model's **MRC linkage** tab (section 16).

### Minutes

Add minutes: an optional **Agenda item** to attach to, **Title** (required),
**Presenter**, an optional **Related model / product**, and the minute **text**.
Sign-off and standing-item minutes are written automatically as decisions are made,
so most of the record assembles itself.

---

## 15. Meeting lifecycle: finalise, close, succession

- **Finalise for distribution.** From the Agenda tab, **Finalise agenda for
  distribution…** locks the agenda and offers **↓ Distribution pack (ZIP)** — the
  agenda PDF plus every uploaded agenda / analysis paper. **Unlock** reopens it.
- **Close the meeting.** **Close meeting…** (top of the meeting) becomes available
  only once the meeting is **quorate** and **every agenda item is resolved**; until
  then it is disabled and tells you what is blocking (quorum, or open items).
  Closing renders and files the **minutes PDF**, and stamps the status
  **Completed**.
- **Automatic successor.** Closing a meeting **auto-schedules the next one** an
  interval ahead — Monthly = 1 month, Quarterly = 3, Semi-annual = 6, Annual = 12
  (default 3) — carrying the committee binding and standing agenda, and tabling the
  just-filed minutes on the successor's minutes-sign-off item. The cadence never has
  to be re-set up by hand.
- **Meeting Pack PDF.** **↓ Meeting Pack PDF** (top right of an open meeting)
  renders the company logo and name, the meeting info line, Participants, Agenda,
  Minutes, Actions, and a per-model **open remediation** section for each in-scope
  model. After close, **↓ Minutes** downloads the filed minutes.

> PDF generation requires the `tectonic` LaTeX engine on the server. Without it,
> those endpoints return an error instead of a PDF.

---

## 16. Actions and decisions that link to models

Meeting **actions** (and, in the data model, decisions) carry an optional **Model**
field. When you tag one to a model it **automatically surfaces on that model's
detail view** — the model's **MRC linkage** tab lists every meeting item pointing at
it, credited with the source meeting (title, ID, date). This is read-only on the
model side: the meeting is the system of record; the model simply reflects it.

So the workflow is: raise the action **in the meeting**, tag the model, and it shows
up under that model automatically — no double entry.

---

## 17. Clients and client packs

The **Clients** tab treats the client as the point of aggregation: one relationship
record, linked to the specific models and products that client relies on, and one
self-describing evidence pack generated on demand — so you answer a client's
model-risk questions once, from one place. *(This area is in early development; the
records and pack generation exist, with the surrounding workflow still maturing.)*

**Register a client.** The list shows ID / Client / Sector / Status; registration
needs only a **New client name**. Open the client to complete it:

- **Company** — Client name, Legal entity, Sector, **Relationship owner** (from
  People), Notes, **Status** (`Active / Prospect / Inactive / Retired`).
- **Divisions / Departments / Contacts** — the client's own internal structure and
  key people.
- **Links** — **Link the Products and Models this client's pack should cover.** Pick
  a **Type** (Product / Model), the subject, and an optional note.
- **Pack history** — every pack you have generated, with timestamps and downloads.

**Generate a client pack.** **Generate client pack…** opens a preview
(*Client pack — preview*) listing what will be included — model documentation and
evidence, any supplementary documents you add, recent MRC minutes, operational-event
write-ups, the MRC Terms of Reference, and the **Governance Completeness (gaps)
audit** — plus any warnings. **Generate & retain** builds and files it. The pack is
a ZIP that carries, for every linked model / product: a freshly rendered Model Risk
Document and its attached evidence, the completeness audit, recent completed-meeting
minutes (up to five), the operational-event write-ups, and the committee ToR — with
a **CONTENTS.txt** manifest that stamps as-of and generated-at and states exactly
what was packed and what was recorded but unavailable. Because the PDFs are built at
the moment of packing, a pack never carries a stale write-up.

---

## 18. Documents and Audit Reports

**Documents.** A governance-wide library independent of any single model. Upload a
file with an optional description; the table lists Name, Description, Date Added and
Size, with **Download** and **Delete**. Use it for institution-level policies and
papers. (Models and products also have their own **Docs** tab for item-specific
files, and the per-model Docs tab carries the nine document categories.)

**Audit Reports.** Click **Generate reports** to produce the whole set on demand.
The tab then divides what it produced between two sub-tabs, because it is read by
two audiences that share nothing but that button:

- **User** — what the institution publishes about its own estate, and the guides
  that come with the console: the **Model Risk Report** (the portfolio profile, the
  inventory table, then a full dossier per model — classification, methodology,
  governance, validation questions and evidence, assumptions, limitations,
  weaknesses, remediation, dependencies, change history, MRC sign-offs and attached
  documents), the **Governance Completeness Audit**, the **User Guide** (this
  document, also as an editable Word file) and the **Integration Guide**.
- **Code** — the coding-rule evidence, in rule order: one report per rule,
  **R1–R10**, the JSON-file audit and the consolidated **coding-rule audit**; then,
  arriving in the background because the test suite takes about a minute, the
  coverage (browsable HTML and Cobertura XML), the JUnit results and the
  **Test Report**.

Each report card offers **View** / **Download** / **Open**. Files are written under
`uploads/audit/`.

> The per-meeting **Meeting Pack** is generated from the meeting itself
> (section 15), not from this tab.

---

## 19. How everything links

The whole point is that nothing floats free. The chain, top to bottom:

- **Company** (singleton: name + logo)
  - **Division** then **Line of Business** — the org tree (Admin)
    - **People** — anchored by Division / Line of Business; become chairs,
      secretaries, members, owners
    - **Model Type** (with binding role) and **Calculating Agent** — the reference
      lists models and products draw on
    - **MRC committee** — anchored by Level + scope; carries a roster, quorum rules
      and a ToR; covers the models in its scope
    - **Model** — scoped by the header org selector
      - Risk rating: Materiality × Complexity × Tier → RAG (Owner vs Table)
      - Validation (9 × SR 26-2), Dependencies, RACI, Remediation
      - matches an MRC (Line of Business, else Division, else Company)
      - sign-off request (rag / retire / reactivate) → committee meeting → ratified
    - **Model Chain** — derived from every model's declared Dependencies
      - **Handoff** per edge: field lineage + compatibility note → handoff sign-off
    - **Product** — registered on a Calculating Agent, bound to model **Components**
      - inherits its MRC via its bindings' org
      - operational events feed its risk window and the committee
  - **MRC meeting** (of a committee)
    - Participants (the roster) + live quorum
    - Agenda (standing + added) → finalise / distribution pack
    - Signoff → Approvals (Approve / Reject) and Analysis (scope + outcomes)
    - Actions tagged to a Model, which then appear on that Model's MRC linkage
    - Close → minutes PDF + auto-scheduled successor
  - **Client** — linked to the Products and Models it relies on → aggregated pack

**Recommended build order** (each step feeds the next):

1. **Company** name and logo.
2. **Divisions**, then **Lines of Business**.
3. **People** (needed for chairs, secretaries and owners).
4. **Model Types** (with binding roles) and **Calculating Agents**.
5. **MRC committee** — roster, quorum and ToR (members picked from People).
6. **Models** — with the header scope set so they match a committee; set
   Materiality / Complexity / Tier for a RAG; answer validation questions; declare
   dependencies.
7. **Handoffs** — define the field lineage and compatibility note on each chain edge.
8. **Products** — register on a calc agent, then bind model components.
9. **Request sign-off** on a model RAG, a retire / reactivate, or a handoff.
10. **Schedule an MRC meeting** — the queued sign-offs drain onto the agenda.
11. **Run the meeting** — confirm quorum, approve sign-offs, review analyses, record
    actions, then **close** it (a successor is scheduled automatically).
12. **Clients** — link products / models and generate the aggregated client pack.

---

## 20. The audit trail

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
