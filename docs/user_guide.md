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
21. [The Dashboard — do I need to respond?](#21-the-dashboard--do-i-need-to-respond)
22. [Feeding your ERM](#22-feeding-your-erm)

Appendix A. [Governance components, artefacts and workflows](#appendix-a--governance-components-artefacts-and-workflows) — a reference inventory for policy drafting and regulatory submissions.

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

The main tabs, left to right, are: **Dashboard**, **MRC**, **Models**, **Model
Chain**, **Products**, **ML Apps**, **Clients**, **Audit Trail**, **Documents**,
**Audit Reports**, and **Admin**.

You land on **Dashboard**, which answers one question — *does any of this need a
response from me?* On a fresh install it has nothing to report; it becomes useful
once there are models on the register, so it is described last, in section 21.

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

## 21. The Dashboard — do I need to respond?

This is the tab you land on, and it exists to answer one question in about four
seconds. Everything on it earns its place by helping answer that question;
anything that does not is left off.

The consequence is a rule the page keeps to: **no number appears without the state
it implies.** "14 open findings" tells you nothing you can act on. "14 open
findings, all with named owners and inside their deadlines — nothing for you" is
an answer.

### The four states

Everything the platform is owed sorts into exactly four states, used identically on
the cards, on the queue and in the API.

| On screen | State | What it means | Your response |
|---|---|---|---|
| **Breaches** | Escalate | A governance rule is broken that no owner can clear alone. | Yours. Take it to the committee. |
| **Needs you** | Act | Owed, and past the date somebody set for it. | Chase the named owner. |
| **Worth noting** | Monitor | Owed, not yet due, with a named owner. | Nothing today. Note it. |
| **With owners** | Clear | Open, in date, in somebody else's queue. | Nothing. |

The names in the first column, and the four labels, are yours to change —
`config/governance/_attention.py`, like every other vocabulary in the platform.

### The verdict

The top of the page is a sentence, not a score:

> **Yes — 27 items need your response.** 22 remediation steps are past their date,
> 4 records have findings past their remediation deadline, and 1 record is below
> the acceptable standard.

There is deliberately no single "model risk score". A composite number would
immediately raise the question of what it is made of, and the honest answer takes
the rest of the page. The platform makes the same argument about not deriving a
second risk rating beside the one your committee sets.

### What reaches you, and what does not

An item reaches you when one of three things is true.

1. **A date somebody set has passed** — a review past its next-review date, or a
   remediation step past its due date.
2. **A hard rule is broken.** Four of these, each chosen because an owner *cannot*
   quietly close it by filling in a field: the recorded reviewer is the record's
   own owner; a division is running on a risk policy its committee never ratified;
   the register cites a document the store cannot produce; a record carries no
   committee sign-off.
3. **A record is below the completeness standard its own division set**, or its
   findings have outlived the deadline their severity band allows.

Everything else that is open is *with an owner*, and the page says so rather than
counting it against you. That distinction is the whole value of the screen: it
turns a backlog into a queue with somebody else's name on it.

Note what is **not** here. A committee action is agreed without a target date —
progress is recorded as dated updates instead — so it is reported as outstanding
and never as late. Calling it overdue would put a deadline in front of you that no
committee ever set.

### Reading the queue

Each row ends in a named person and, where there is one, a date. A row that you
cannot hand to somebody is an observation, not an action.

Rows collapse where twenty of them would say the same thing. Overdue remediation
collapses **by owner** — "14 remediation steps are past their date · David K Kelly
· across 8 records · worst 147 d" — because the response to fourteen overdue steps
is a conversation with one person, not reading fourteen rows. **List** opens the
records behind a collapsed row; **Open** takes you to the record itself.

The page never writes. There is no acknowledge and no dismiss: clearing an item
from a dashboard would be a decision with no minute against it, and the whole
premise of the platform is that a response is recorded where it can be challenged.
Every row routes you to the record or the meeting instead.

### Direction

"Is this getting better?" is the second question, and today's figures cannot
answer it. Once a day the platform looks at what the completeness audit is
reporting and writes down what it saw — when each finding first appeared, when it
was last seen, and when it stopped appearing.

From that come three things: the trend line, the opened-versus-closed counts, and
the ability to say a finding has outlived its deadline. Until it has looked more
than once the panel says so, rather than drawing a flat line — a flat line and an
empty history look identical, and only one of them is true.

**Meeting the standard** is a count — how many records meet the threshold their own
division set, out of how many were audited. It is deliberately not a weighted
average of completeness scores: the audit publishes no estate-wide figure, and one
invented here would be a number nobody chose sitting on the front page of a
governance record. Read it beside **Below the standard**: an average in the
nineties with a tail of four is a different firm from one with a tail of none.

### How this relates to the completeness audit

They cannot disagree, by construction.

| | Completeness audit | Dashboard |
|---|---|---|
| Asks | Is each record complete, and how bad is each gap? | Does any of this need me? |
| Unit | One finding, per record | One response, per person |
| For | The committee, an assessor | You, and your ERM |
| Output | A signed PDF, defensible line by line | A sentence and a queue |

**The dashboard computes nothing the audit does not.** It reads the audit's own
findings, severity bands, deadlines and remediation wording unchanged. Where it
adds anything it is subtraction: four states, and everything inside its deadline
dropped out of your count. A committee member who has read the audit recognises
the row rather than having to reconcile it.

---

## 22. Feeding your ERM

Model risk rarely stops at this platform. Where a firm runs enterprise risk
management, model risk usually feeds two places in it: the **operational risk**
view, and **strategic direction**. The platform exposes a read-only API shaped
around those two consumers.

```
GET /api/erm/v1/model-risk             the panel: verdict, operational, direction, estate
GET /api/erm/v1/model-risk/attention   the queue: every outstanding obligation
GET /api/erm/v1/model-risk/estate      the position: counts by kind, tier, rating, division
```

Authentication is a shared token in the `X-ERM-Token` header. It is separate from
the ingest token on purpose: ingest *writes* the governance record and the ERM may
only read it.

**The ERM can never write.** There is no write endpoint at any version. If it
could change the record, the record would no longer be the thing your committee
signed.

Two things an integrator should know. Every enumerated field ships a fixed machine
value *and* your label — `state` beside `label`, `reason` beside `reason_label` —
so renaming your risk vocabulary never breaks a consumer. And items come back
individually, each carrying the `group` it would collapse under, so the ERM can
reproduce the console's rollup or list every record instead.

The full contract, with JSON Schemas and worked examples, is checked in at
[`contracts/erm/`](../contracts/erm/README.md). Hand that to whoever is building
the ERM side.

---

## Appendix A — Governance components, artefacts and workflows

The guide above walks you through the console screen by screen. This appendix is
the same platform described the other way round: an inventory of what it holds,
what it produces, what it enforces, and what it does **not** do.

It is written for a different reader — somebody drafting an institutional model
risk policy, preparing a regulatory submission, or answering a due-diligence
questionnaire — who needs to find, for a control they want to assert, the
mechanism that would evidence it. Read [A.25](#a25-not-built--do-not-assert)
before asserting anything: a policy clause that claims a control the estate cannot
evidence is worse than one that stays silent.

**Status date:** 2026-08-29.

**In this appendix.** *What is governed* — the organisational skeleton (A.1), the
five record types (A.2), the registers each one carries (A.3). *Workflows* —
registration and classification (A.4), risk rating (A.5), validation and review
(A.6), the committee (A.7), committee-ratified policy (A.8), lifecycle (A.9),
dependency and lineage (A.10), monitoring (A.11). *Artefacts* — document control
(A.12), the documents the institution issues (A.13), evidence packs (A.14).
*Assurance* — the completeness audit (A.15), framework coverage (A.16), review
programme (A.17), the response model (A.18), finding history (A.19). *Controls* —
the evidence architecture (A.20), identity and segregation of duties (A.21),
integration surfaces (A.22), controls over the software itself (A.23), what an
institution sets for itself (A.24). *Limits* — what is not built (A.25).
Controlled vocabularies are tabulated at A.26.

### Part I — What is governed

#### A.1 The organisational skeleton

Four structures exist before any model does. Everything else hangs off them, and
each is the answer to a "who" question a policy has to settle.

| Structure | What it is | Policy question it answers |
|---|---|---|
| **The institution** | A singleton. One deployment is one firm; its name, chair and meeting cadence are held once and stamped on every document issued. | Whose record is this? |
| **Division / Line of Business** | A two-level org tree. Line of Business belongs to a Division. Every governed record is allocated to a Division, optionally to a Line of Business. | Which part of the firm owns this? |
| **People** | A directory of named individuals with email and roles. An identity that is not in it cannot author a change to the record (§A.21). | Who is a real, recognised actor? |
| **Committees (MRC)** | One or more Model Risk Committees, each anchored at **Company**, **Division** or **Line of Business** level, each with its own frequency, roster, quorum rule and Terms of Reference. | Which committee is answerable for this record? |

**Committee coverage is resolved, not assigned.** A record's responsible committee
is derived from its Division / Line of Business against the committee anchored at
the narrowest matching level. A record cannot therefore fall outside committee
oversight by an administrator forgetting to route it, and a request for sign-off
knows where to go without anyone choosing.

**Quorum is enforced, not advisory.** Each committee records a minimum number of
voting members, and separately whether the chair and secretary are individually
required. A meeting cannot proceed to business until it is quorate, and the
rollcall that establishes quorum is the first standing agenda item.

**Roles are granted by the committee, not by an administrator.** Roles are
proposed on a person's record in the administration area and take effect only when
ratified at a meeting, under a standing agenda item for membership. The shipped
role vocabulary is: **owner**, **validator**, **committee**, **chair**,
**administrator**, **reader** — each carrying a written explanation of what it
grants, shown at the point of assignment.

---

#### A.2 The five governed record types

The platform deliberately keeps five distinct registers rather than forcing
everything into one "model" table. Each has fields the others cannot answer, and a
single register would have to leave them blank.

##### A.2.1 Model
A quantitative model the institution builds, buys or runs. Carries methodology,
source module, repository and codebase, vendor, version, and the full governance
apparatus below. This is the classical model-inventory record.

##### A.2.2 ML Application
The **use** of an off-the-shelf estimator — the record for "we fitted a gradient
boosting regressor to this problem", where the estimator is somebody else's and the
governable thing is the *application*: which estimator and version, why that one
rather than a simpler alternative, and the full training record (§A.4.3). It carries
the same field names as a Model wherever the question is the same, so estate-wide
queries count both.

##### A.2.3 AI System
A system built on a third-party foundation model. It carries what no model record
can answer: which foundation model and provider, whether the version is **pinned**,
where it is **hosted**, what **data is sent for inference** and under what
contractual basis, its **deployment pattern** (direct prompting / RAG / fine-tuned
/ agentic / multi-agent), where the **human oversight** sits, the **guardrails**
and **grounding** in place, output variability, the explainability approach, and
its **EU AI Act classification** with the reasoning behind it. Agentic systems
additionally enumerate the tools and APIs the agent may call.

##### A.2.4 Product
A commercial product priced by a combination of the above. A Product binds one
**Calculating Agent** (the pricing platform — an internal library, a third-party
engine) and an open-ended list of **components**, each naming what kind of
component it is and which record fills it. A component may be a Model, an ML
Application or an AI System. Several components may share a type — two curve models
is the ordinary case for structured credit, not an error.

A Product is rated, reviewed and signed off in its own right, but it does **not**
carry its own validation questionnaire: a product validates through its components,
and demanding a second copy of the evidence one link away would be restatement.

##### A.2.5 Client
An external counterparty the institution hands an evidence pack to. Carries the
client's own contact org tree (divisions → departments → contacts), its links to
Products and Models, and a **pack history** recording every pack ever generated —
both the *as-of* date the pack reflects and the *generated-at* moment it was
produced.

---

#### A.3 What every governed record carries

Beyond its scalar fields, each record carries a set of **registers** — repeating,
individually-identified rows rather than free prose. The distinction matters for
policy: a register can be counted, queried and challenged row by row; a paragraph
cannot.

##### A.3.1 The description registers — what the record *is*

| Register | Contents |
|---|---|
| **Assumptions** | Description, impact band, how it is monitored, mitigation. |
| **Limitations of use** | Description, impact band, the monitoring trigger that would show the limit is being breached, the compensating control. |
| **Model weaknesses** | Description, impact band. |
| **Validation questions** | The institution's questionnaire, one row per question, with the owner's status, rationale, evidence — and separately the reviewer's verdict and comment (§A.6.3). |
| **Version history** | Version, date, description, author, reference document, lifecycle stage of that version. |
| **Change history** | Version, date, author, change type, description. |
| **Dependencies** | Upstream / downstream links to other records, with a note. |
| **Data sources** | Which feeds the record pulls inputs from, drawn from an administered list that classifies each source as internal or external, with its sensitivity and whether it may leave the institution. |
| **Field lineage** | Provider field → consumer field, with types, units and a compatibility note. |
| **RACI roles** | Role, RACI code, assigned person, backup, description. Four roles are seeded at registration. |

##### A.3.2 The measurement registers — what was *found*

Held apart from the description registers on purpose. `benchmark_tests: Yes`
records that testing happened and nothing else — not what was tested, against what,
what it found, or when. A committee cannot challenge a Yes.

| Register | Contents |
|---|---|
| **Fairness assessments** | One row per attribute or group considered: how it was assessed, the metric, what it showed, the date. `Not measured` and `no disparity found` are different answers and are not collapsed. |
| **Evaluations** | One row per evaluation run: kind (held-out performance / benchmark against a baseline / adversarial or red-team / LLM-as-a-judge / human review / reproducibility check), what it was evaluated against, the metric, what it returned in prose, a verdict, and the date. The verdict may be blank — an exploratory red-team run has findings and no pass mark. |

Both are carried by Models, ML Applications and AI Systems under one name each, so
*"what has this firm actually measured"* is a single query rather than three.

##### A.3.3 The event registers — what *happened*

| Register | Contents |
|---|---|
| **Operational failure events** | Event date, what happened, remediation, and the full RACI: who was operationally responsible, the accountable owner, the committee consulted, and whether the client and senior management were informed. Each event is routed to the committee, which records that it has received it. |
| **Remediation steps** | Description, owner, priority, due date, status. |
| **Actions** | Committee-raised actions with an owner and a due date (§A.7.4). |

##### A.3.4 The committee's own registers

| Register | Contents |
|---|---|
| **Sign-off requests** | The queue: what has been asked of the committee, of what kind, targeted at which committee, its status, and the meeting and agenda item it landed on. |
| **Sign-off history** | The decisions: date, kind, outcome, the meeting that took it, the rating it moved from and to, the resulting next-review date, and — for an ownership change — the previous and new owner. |

These two are exempt from the read-only rule that applies to a hibernated record
(§A.9): a decision must be recordable even when it is the decision that hibernated
the record, and a reactivation is raised on a record that is hibernated at the time.

---

### Part II — Workflows

#### A.4 Registration and classification

##### A.4.1 Registration
A record is registered with a minimum set of fields and completed afterwards. The
minimum differs by type — a Model needs its identifier, name, division, owner and
classification; an ML Application needs its estimator and use case; an AI System
needs its deployment pattern and use case, because the framework clauses that bite
on it depend on that value.

Registration seeds the record: the institution's validation questionnaire is copied
onto it, and its four RACI roles are created. The questionnaire is **copied, not
referenced** — a record keeps the questions it was actually asked, even after the
institution later edits its question set.

##### A.4.2 Controlled classification
Several classification fields are **strict**: a record cannot be typed as something
nobody has defined, or name a vendor nobody has registered. Others are deliberately
open, because they hold names that predate the lists and rejecting those would block
every edit to an existing record. Which fields are strict is a configuration
decision, not a code one.

##### A.4.3 The training record (ML Applications)
An ML Application carries a **training record**, structured in six sections in the
order a fit is actually performed:

**A. Task and target · B. Training data · C. Split, preprocessing and validation ·
D. Fit record · E. Performance · F. Reproducibility**

Every enumeration it uses — learning task, missing-data treatment, categorical
encoding, scaling method, the point at which the scaler was fitted, split method,
cross-validation method, hyperparameter search method, determinism, primary metric,
naïve baseline — is an administered vocabulary the institution owns and can extend.

Training runs may be **captured automatically** from the producing codebase rather
than typed (§A.22.1), and the record marks which fields were captured that way. Each
run may carry its evidence artefacts: a **calibration** curve, a **convergence**
plot, a **segment analysis**. These are plots and tables rather than prose, on the
principle that a reliability curve *is* the calibration evidence, where a sentence
saying the model is well calibrated is only an assertion.

---

#### A.5 Risk rating

##### A.5.1 Three structural dimensions
Every governed record is rated on three axes, each with a written justification
demanded beside it:

- **Mission criticality** (three bands — the tier)
- **Materiality** (three bands)
- **Complexity** (three bands)

Plus an **overall rating rationale** in the owner's own words. The bands, their
names, their explanations and the grid below are all the institution's to set (§A.8.1).

##### A.5.2 The rating grid
Materiality × Complexity resolves to a **Red / Amber / Green** rating, on a
separate grid per criticality band. The criticality band fixes how quickly the grid
escalates: a mission-critical record reaches Red readily; a not-important record
stays Green until the top corner.

##### A.5.3 Owner-set, committee-ratified
The owner sets the classification. The rating derived from it is a **proposal**
until a committee approves it: a rating change is raised as a sign-off request,
routed to the record's responsible committee, tabled, decided and minuted. The
committee's decision is what sets the record's rating and its next review date.
The owner's view and the committee's view are allowed to disagree in the interim —
that disagreement is a designed state, not an error.

---

#### A.6 Validation and the review workflow

##### A.6.1 The questionnaire
The institution's validation question set is an administered list, seeded from a
recognised nine-question standard and freely reworded, extended or reduced. A
question carries a short topic label and the question text. Separate question sets
exist for Models, for ML Applications (ten questions, written against the failure
modes of a fitted estimator — leakage, out-of-sample performance, overfitting and
stability, explainability, drift) and for AI Systems (written against the AI risk
catalogue — provenance, grounding, oversight, egress, agent authority).

##### A.6.2 The review as a workflow
A review runs as **seven ordered stages**, each of which the reviewer gives an
interim approval to. Approving a stage moves the review on and sets the record's
review status, so *"where has this review got to"* is answered by work done rather
than by somebody remembering to update a dropdown.

| # | Stage | Status it sets |
|---|---|---|
| 1 | Preliminary documents | Documents reviewed |
| 2 | Assumptions | Assumptions agreed |
| 3 | The validation questions | Questions answered |
| 4 | Model weaknesses | Weaknesses agreed |
| 5 | Limitations of use | Limitations agreed |
| 6 | Monitoring approach | Monitoring agreed |
| 7 | Remediation | Remediation agreed |

Assumptions precede the questions because one of the questions asks whether the
assumptions are documented and justified: answering it means reading them.
Remediation is last before sign-off because the committee should see what the
review found outstanding, and what is being done about it, before it signs anything.

**An interim approval is not a lock.** Earlier stages stay open — a reviewer who
reaches the limitations and needs to reopen a question must be able to. What the
approval records is that the two parties agreed at that point, and who said so.

##### A.6.3 Why the review is happening, and what it must confirm
A review records its **trigger**: periodic, a new version, an owner change, or
committee-directed. What a reviewer should look at differs in each case, and the
trigger is recorded so the review can be read in context years later.

Before a review begins, the owner writes a **scope** — what has changed and what
they want looked at. A reviewer handed a record and no brief writes the review they
imagine is wanted.

Where the trigger is a **new version**, the owner must additionally confirm that the
three artefacts which go stale together have been brought up to date and loaded:
the record's documentation, its sensitivities, and its test evidence. Otherwise the
reviewer reads last version's write-up against this version's model.

##### A.6.4 The record of challenge
The review carries a **note thread**, scoped to the stage it was said under. A note
is either an ordinary remark or a **Challenge** — a stated objection, which stands
**Open** until a later note answers it. Neither state is stored on the challenge
row; both are derived, because storing them would mean editing a challenge to close
it.

- The thread is **append-only**. A correction is a new note, as it would be in
  minutes. Evidence that can be edited afterwards is not evidence.
- The author and their **side** — owner, reviewer or participant — are stamped from
  the signed-in identity against the record's own owner and reviewer fields. Never
  typed, never chosen from a dropdown, or *"who challenged whom"* would be a matter
  of what somebody selected.
- On the questionnaire, the owner's status and the reviewer's verdict are separate
  fields. A question can be **Addressed** by its owner and **Challenged** by its
  reviewer at the same time. That disagreement is the review doing its job, and the
  record has to be able to hold it.
- An open challenge is a stated reason the review is not finished.

##### A.6.5 Sign-off and the report
The reviewer signs off with a final commentary. The sign-off is append-only and
produces a **Model Review Report** (§A.13) — the document the committee receives when
it comes to approve the rating. The committee does not adjudicate the review; it
signs off the risk rating, and the report is the evidence in front of it when it
does. The report therefore carries the *argument*, not just the conclusion: both
sides of every question, the registers as agreed, and the record of challenge
verbatim under the stage it happened on.

##### A.6.6 Cycles
Starting a new review **records a new cycle rather than resetting**. The stage
register is append-only: stages agreed before the marker belong to the review that
was already signed off, and the previous cycle stays readable — its approvals, its
notes and its filed report are the history.

---

#### A.7 The committee

##### A.7.1 The standing agenda
Every meeting is seeded with the institution's standing running order. The shipped
order is:

1. **Rollcall and confirmation of quorum** — the meeting may proceed only once quorate.
2. **Sign-off of the previous meeting's minutes** — proposed by the chair.
3. **Review of outstanding actions** — every action still open across the committee, and ratification of the closures owners have requested.
4. **Review of record sign-offs** — the rating approvals queued for this meeting.
5. **Review of analyses** — confirmation to proceed, and any actions arising.
6. **Governance completeness audit** — run and review the audit for the records in scope for this committee, and record the committee's notes on the outcome.
7. **Committee membership and roles** — ratify proposed changes to who sits on the committee and what they are allowed to be.
8. **Any Other Business.**

The order is the institution's to edit; each meeting keeps the copy it was given, so
a change to the standing order never rewrites a meeting already held. What stays
fixed is each standing item's *kind*, which determines the working panel the meeting
draws for it. Outstanding actions are reviewed immediately after the minutes,
because the first thing a committee does once it has accepted the record is ask what
it is still owed.

##### A.7.2 Scope
A meeting has an explicit scope: the Models and the Products it is considering.
Papers are **tabled by reference** — the committee reviews the document the record
actually holds, never a copy of it, so a paper cannot drift from its source between
tabling and reading. The categories a committee may table are configurable; the
shipped set is sensitivity studies, analyses, test results and review reports.

##### A.7.3 Sign-off routing
One queue carries every kind of decision a committee ratifies. A request names its
**kind** and is routed to the record's responsible committee, where it waits as
Pending until a meeting of that committee is scheduled, at which point it is pulled
onto the agenda and marked Attached against the item it landed on. The kinds are:

| Kind | What is being asked |
|---|---|
| **rag** | Approve a proposed risk rating. |
| **retire** | Ratify a retirement (§A.9). |
| **reactivate** | Bring a hibernated record back. |
| **handoff** | Approve a declared handoff between records. |
| **owner** | Ratify a change of owner. The new owner takes the record immediately — somebody has to answer for it today — and the committee ratifies the appointment afterwards, so the request carries both names. |

Outcomes are **Approved** or **Rejected**, recorded against the meeting that took
the decision.

##### A.7.4 Actions
Actions have an owner, a due date and a status. An owner cannot close their own
action: they **request closure**, and the committee ratifies it under the standing
actions item. The status vocabulary is therefore three-valued — Open, Closure
requested, Closed.

##### A.7.5 Meeting lifecycle
A meeting is **Scheduled** or **Completed**. The agenda locks; minutes are filed;
closing the meeting sets it Completed, after which it cannot be amended. **Closing a
meeting schedules its successor** at the committee's own cadence, so a committee
that meets on a cycle always has its next date on the record rather than in
somebody's diary. The previous meeting's minutes cannot fail to be signed off,
because their sign-off is a standing item on the next agenda.

---

#### A.8 Committee-ratified policy

Two things are settings the institution writes down and a committee then stands
behind. Both are **per division**, because one division's standard cannot describe
another's work, and both would be worthless if an owner could change them the week
before an inspection. Both therefore run the same lifecycle:

> **Proposed** → a draft submitted for sign-off, carrying the whole policy
> **Approved** → the division's committee ratified it; it becomes the live policy
> **Rejected** → the draft is withdrawn or declined; the live policy stands

What records actually use is the **most recently approved** policy, or the firm-wide
default for a division that has never ratified its own. A draft drives nothing.

##### A.8.1 The risk policy
What a rating *means* in a division: the bands on each of the three dimensions with
their written explanations, the overall rating vocabulary, the Materiality ×
Complexity grid for each criticality band — and the audit parameters that division
sets for itself (§A.15.4). It is issued as a **Risk Categorisation Document** (§A.13).

A division running on an unratified policy is itself a reportable finding (§A.18).

##### A.8.2 The ML review policy
What a review of an ML Application must *contain*: which of the training-record
fields and which of the review questions are **in use** in that division, and which
are **mandatory**. It lets a division that does not fit neural networks stop being
asked neural-network questions, without any division being able to quietly drop the
questions it finds inconvenient — because the committee ratifies the list.

---

#### A.9 Lifecycle: retirement, reactivation, ownership

**Retirement is hibernation, not deletion.** A record is never removed. Retiring it
requires committee ratification, and a hibernated record becomes **read-only** — with
the deliberate exception of the committee's own two registers, so that the decision
which hibernated it, and any later request to bring it back, are still recordable
against it. A hibernated record is excluded from the estate's audit figures, because
reporting gaps against a record nobody is running is noise.

**Reactivation** is the mirror image: raised on the hibernated record, ratified by
the committee, minuted.

**A change of owner** takes effect immediately and is ratified afterwards. The
request carries both names, so the handover is on the record even before the
committee meets.

**Lifecycle stage** (development / validation / production / retired) and
**validation status** (initial / pending / validated / conditionally approved /
rejected) are separately tracked administered vocabularies — where a record is in
its life, and what the validation function has concluded about it, are different
facts.

---

#### A.10 Dependency, handoff and lineage

Three levels of granularity, deliberately separate.

##### A.10.1 The model chain
The directed graph of which record feeds which. It may be declared by owners one
dependency at a time, or pushed wholesale from the producing codebase (§A.22.1).
**The graph is enforced acyclic** at both entry points — the same invariant, one
implementation. A self-loop counts as a cycle.

##### A.10.2 Handoffs
Each edge of the chain can be governed in its own right: a **handoff** is declared
between a providing and a consuming record, reviewed, and approved by the committee
under the `handoff` sign-off kind. A handoff carries its own field-level register
and produces a **Model Handover Document** (§A.13).

##### A.10.3 Field lineage
Provider field → consumer field, with each side's type and units and a compatibility
note. This is where a unit mismatch or a silent type coercion between two governed
records becomes visible and challengeable. It is normally written by the ingest
pipe from the producing repository rather than typed by an owner, so its absence is
a pipeline finding rather than a governance one.

##### A.10.4 Data lineage
A pipeline **run manifest**, pushed from the producing repository: the steps, and
which runs executed them. Every step named in a run must exist in the step list —
validated at ingest, not assumed.

---

#### A.11 Ongoing monitoring

Two layers, and the distinction is worth preserving in policy.

**The standing approach.** Each record carries a narrative **monitoring approach**,
agreed as stage 6 of its review — how the record will be watched once it is in use,
in the owner's and reviewer's own words. It is deliberately prose rather than a
register of metrics and thresholds: an approach is agreed in sentences long before
anyone can name the numbers.

**The trigger on each limitation.** Every recorded limitation of use carries the
**monitoring trigger** that would show the limit is being breached, and the
compensating control. This is the operative half — a limitation with no trigger is
a disclaimer, not a control.

**The observed record.** Monitoring results are filed as **timestamped documents**
under a Monitoring category, so each observation is retained as its own dated entry
rather than overwriting the last. An **Ongoing Monitoring Report** (§A.13) states one
record's monitoring position: which portfolios it has been exercised against, and
the standing position on every weakness and limitation recorded for it. Where there
is no production activity, the document **says so explicitly** rather than going
quiet — an absent document and one recording "nothing yet" are very different things
to an assessor.

---

### Part III — Artefacts

#### A.12 Document control

##### A.12.1 Filing
Every document category is surfaced in exactly one place, so a document is never
listed twice. Where a document belongs is decided by *where the work that produced
it happened*, not by a general filing cabinet.

| Where | Categories |
|---|---|
| **Documentation** | Core Documentation, Sensitivity, Analysis, Monitoring |
| **Testing** | Overall test-results pack, plus one category per test type (unit, integration, benchmark), each offered beside the field it evidences |
| **Review** | The signed reports a review has issued — the issued document, not the reviewer's working papers, which stay beside the stage that produced them |
| **In context** | Event evidence and remediation evidence, attached beside the item they evidence |
| **Training** | Calibration, convergence and segment-analysis artefacts, filed beside the training field each evidences |
| **History** | Generated governance documents, rendered from the record as it stood when issued |

The committee is given the report, not the reviewer's drafts — only one of the two
is a document anybody should be tabling.

##### A.12.2 Institutional artefacts
Separate from records: what the **institution issues**. Filed per division, plus a
company-wide shelf for what belongs to the firm rather than to one division, plus a
dedicated shelf for the **control documentation** that evidences the AI mitigation
catalogue (§A.16.3) — kept apart because those documents carry mitigation references
and are read by the audit, which no other artefact is. Shipped artefact kinds:
Terms of Reference, Presentation, Policy, Guide, Template, Other.

##### A.12.3 File handling
An upload is metadata on the record plus bytes on disk. Allowed types are the
ordinary office and image formats plus LaTeX source, so a generated document can be
filed alongside its own auditable original. **Uploads are only ever stored and
served back, never executed.** Only a narrow list of types is served inline in the
browser — markup formats, including SVG, are excluded because an inline file runs in
the application's own origin.

---

#### A.13 Documents the institution issues

Every document below is generated from the record at the moment of issue, in one
shared house style, carrying the institution's own classification banner, author
line, legal notice and logo. A filed copy is therefore the record of what the
governed thing looked like *then* — the second time axis alongside the audit trail's
*when we were told*.

| Document | What it is |
|---|---|
| **Model Risk Document** | One record's full governance write-up: classification, rationale, registers, validation questions, documents, history. Issued per Model, per Product, per ML Application. |
| **Model Review Report** | What the reviewer signed and what the committee receives: both sides of every question, the registers as agreed, and the record of challenge verbatim (§A.6.5). |
| **Model Handover Document** | A governed handoff between two records: the fields crossing the boundary, their compatibility, and the review of it. |
| **Risk Categorisation Document** | A division's ratified risk policy: bands, definitions and the rating grid. |
| **Ongoing Monitoring Report** | One record's monitoring position (§A.11). |
| **Meeting Pack** | The committee's papers for one meeting: agenda, scope, tabled papers, sign-off queue, actions, decisions. |
| **Governance Completeness Audit** | The estate's gaps, ranked, with an instruction and a target date against each (§A.15). |
| **Model Risk Report** | The estate's governance record reproduced — the inverse of the audit. |
| **User Guide / Integration Guide** | Published as PDF, and the user guide additionally as an editable document so an institution's own people can mark it up. |
| **Coding-Rule Audit, Test Report, coverage and results artefacts** | The evidence of control over the software itself (§A.23). |

---

#### A.14 Evidence packs

Three assemblies, each answering a different "show me everything about" question.

| Pack | Scope |
|---|---|
| **Meeting pack** | One meeting's papers, as PDF. |
| **Product pack** | A product's own document plus the **full pack of every component it binds** — each component's governance document and its attachments, foldered by category, so the whole product is browsable without unzipping again. |
| **Client pack** | Everything handed to an external counterparty: the governance documents for every Product and Model linked to that client, plus the minutes of the most recent completed committee meetings, capped so a pack does not balloon over a long meeting history. |

Two properties are common to all three and are worth asserting in policy:

- **Every generated document in a pack is built at the moment of packing**, so a
  pack never carries a stale write-up.
- **Every pack carries a contents listing that says what was packed and what was
  recorded but unavailable.** A pack explains itself; it does not silently omit.

Client packs are recorded in the client's pack history with both their as-of date
and their generation moment, so *"what did we send them, and what did it say then"*
is answerable.

---

### Part IV — Assurance

#### A.15 The completeness audit

The inverse of the governance report. That document reproduces the record; this one
reports its **holes, ranked, with an instruction and a target date against each**.
A reader should be able to work top-down through the register and close the estate's
worst exposure first without reading anything else.

##### A.15.1 What it examines
Every Model, Product and ML Application on the register, excluding hibernated and
retired records. For each: every scalar field, every register, and every demanded
document category.

##### A.15.2 What counts as a gap
Four kinds, and the fourth is the one an assessor cares most about:

1. **A field is absent.**
2. **A register is empty**, where empty is not a legitimate steady state. Registers
   where empty *is* legitimate are exempt — an empty remediation list means nothing
   is outstanding, an empty events list means nothing has gone wrong, and scoring
   those would penalise the best-kept records.
3. **A demanded document category holds nothing.**
4. **A document is cited but cannot be produced.** The register is a claim; the file
   store is the fact. This scores *above* a document never uploaded at all: both
   leave the same hole, but a broken reference also asserts to a reader that the
   evidence exists — and nobody reading the register alone will catch it.

Plus **rule findings**, which are a different animal: a contradiction between
answers that are both present, which no completeness score can see. The shipped rule
is **reviewer independence** — a record whose peer reviewer is its own owner has
both fields filled in and would otherwise score as fully governed.

##### A.15.3 How a gap is scored
`criticality × tier weight × rating multiplier × event pressure × staleness`

| Factor | Effect |
|---|---|
| **Criticality** | What the missing thing is worth, before anything else. Anchored at both ends: 1.00 is a gap a validator would refuse to sign off around; 0.30 is worth recording but not chasing. |
| **Tier weight** | The institution's own statement of how much the record matters. An **untiered** record is treated as nearly top tier — the absent tier is itself the reason to look. |
| **Rating multiplier** | Taken from the division's ratified risk policy, so the audit escalates on exactly the rating the record shows rather than forming a second opinion. An **unrated** record escalates *above* the lowest band: a missing rating is not evidence of a healthy one. |
| **Event pressure** | Operational failure events in a rolling window. Capped, so a single bad year cannot dominate the ranking. |
| **Staleness** | Days past the next-review date. A record complete at its last review and unreviewed since is a weaker assurance than the same record reviewed last month. |

The result bands to **Critical / High / Medium / Low**, each carrying a target
number of working days to close. The register therefore doubles as a remediation
plan rather than needing one written after it.

Each finding carries a **recommended action phrased as an instruction to the named
owner**, because a finding an assessor cannot hand to somebody is an observation.
Where a finding also appears on the executive view (§A.18), the instruction travels
with the finding — so the dashboard cannot word it differently from the report the
committee signed.

##### A.15.4 Roll-up and thresholds
Each record gets a weighted completeness score and is reported as materially
incomplete once it falls below the division's **acceptable** threshold, with a lower
**conditional** threshold beneath it. Both thresholds, and several of the escalation
factors, sit on the division's ratified risk policy — because that is what its
committee already ratifies, and splitting the audit's basis across two places would
leave nobody able to say what a score was computed against.

##### A.15.5 Two design commitments to state in policy
- **Findings are never summarised away.** Every gap on every record appears in the
  per-record findings, and the summary counts reconcile to it. A completeness audit
  that quietly truncates its own register is the one document where an omission is
  indefensible.
- **The audit is committee business.** It is a standing agenda item, scoped to the
  records that committee oversees, and the committee's notes on the outcome are
  minuted.

---

#### A.16 Framework coverage

A section of the completeness audit, and the part an external assessor is handed:
one table per framework, every clause, what evidences it, and **how much of the
estate actually carries that evidence**.

##### A.16.1 The commitment that makes it credible
A clause is never reported as evidenced because the platform *can* hold the record.
It is evidenced because the estate *does* — the probe counts records, and a
capability nobody has populated reads as **Not evidenced**. An assessor is owed the
second number, not the first.

Ratings are **Evidenced / Partially evidenced / Not evidenced / Outside the
platform**. The last is used honestly: whether risk management is embedded in the
firm's decision-making, what budget and headcount were allocated — these are
organisational facts no system can hold, and saying so is better than a blank cell.

Where a clause has **no applicable population at all**, it reads Not evidenced with
the population said out loud. "Nothing needed it" is a claim the reader should see
and challenge, not one the report should make silently on the estate's behalf.

The clauses reading Not evidenced are **listed again, on their own, after the
tables**. A reader working only from a forty-row table reads the rows that are
green; the point of the section is the rows that are not.

##### A.16.2 Frameworks mapped
- **ISO 31000:2018** — clause by clause, 4 through 6.7.
- **COSO ERM (2017)** — by principle.
- **BCBS 239 (2013)**.
- **FINOS AI Governance Framework** — both catalogues (§A.16.3).
- **EU AI Act** — each AI System carries its Annex III classification and the
  reasoning; "Not assessed" is the honest default and is itself the finding.

The audit cites **SR 26-2 (superseding SR 11-7) and PRA SS1/23** as the basis for
its scope. That citation is configuration: an institution re-pointing the audit at
its own framework changes the citation with it.

##### A.16.3 The AI framework, and why it is two catalogues
The AI framework is carried as two separate catalogues that are deliberately not
merged:

- The **risk catalogue** — what the institution is exposed to (hallucination,
  foundation-model versioning, non-determinism, provider availability, alignment,
  bias, explainability, overreach, drift, multi-agent trust boundaries, information
  leakage).
- The **mitigation catalogue** — the controls it has in place, evidenced by
  **tagged control documentation on the dedicated shelf** (§A.12.2).

Keeping them apart means nobody can mistake *"we are exposed to prompt injection"*
for *"here is our prompt-injection control"*, which is exactly what merging them
would invite.

Population rules are applied so the numbers mean something: an AI-specific clause is
scored over AI Systems only, and clauses about agent authority are narrowed again to
agentic systems — scoring "does the agent exceed its authority" against a
direct-prompting summariser would manufacture a gap nobody can close.

---

#### A.17 Review-programme reporting

Reviewing an entire estate is a programme with its own timetable, not something an
owner can finish this afternoon. Scored as completeness it would mark the whole
estate incomplete on the day the workflow was introduced and hold it there for
months — a new bar applied backwards, which reads as decay rather than as the
backlog it is.

The review is therefore **reported separately** rather than scored: how many records
have a review under way, how far each has got, how many stages have been agreed, how
many are signed off, and what is standing in the way. *"None started yet"* becomes a
plan with a number against it rather than a failure with a number against it.

Progress reads forward from the current cycle's marker, so last year's approvals do
not flatter this one.

---

#### A.18 The response model (executive view)

The completeness audit asks whether each record is complete. The executive view
answers the question one level up: **of everything already known, what does a chief
risk officer have to do something about?**

##### A.18.1 Four states
A reader at that level has four available responses, so every item resolves to one
of four. The machine values are frozen so an integration survives a rename; the
words beside them are the institution's.

| State | Card | The response |
|---|---|---|
| **Escalate** | Breaches | Yours. Take it to the committee. |
| **Act** | Needs you | Chase the named owner. |
| **Monitor** | Worth noting | Nothing today. Note it. |
| **Clear** | With owners | Nothing. |

Only the first two reach the executive. Everything else is with an owner, and the
page says so rather than counting it against the reader.

##### A.18.2 One record, one item
A record contributes **at most one item — the worst obligation standing against
it**. Without that rule, a badly-kept record appears three times and the count
measures how many ways one record is behind rather than how many records are.
Remediation steps and committee actions are the exception: each is a separate
commitment by a named person, so two overdue steps on one record are two people who
have not done what they said they would. Divisions produce an item of their own
where their risk policy has never been ratified.

##### A.18.3 The reasons, worst first
Reviewer is the record's own owner · Evidence cited but not held · No committee
sign-off · Review overdue · Below the acceptable standard · Findings past their
remediation deadline · Review falls due within the horizon · Open findings with
their owner. Alongside these, at committee and division level: committee action
still open, remediation overdue or due, risk policy never ratified.

##### A.18.4 No derived second opinion
The view derives no finding of its own. Three of its record-level reasons are an
audit gap under another name, and review currency is read from the same
classification the register already shows. A record the register calls Overdue and
the executive view called something else would be a control failure of its own.

The headline is **one sentence, not a score**. A composite index would immediately
raise the question of what it is made of, and the honest answer takes the rest of
the page.

The queue is capped; when the cap bites the true total is still reported and the
truncation is declared, because a capped list that says nothing about the cap reads
as *"that is all there is"*.

---

#### A.19 Finding history and trend

The audit is computed fresh each run and has no memory of its own. A scheduled
observer therefore records what it saw, daily. That gives three things a policy can
rely on:

- **The age of a finding** — when it first appeared, not merely that it is open now.
- **A trend line** over a full governance cycle, so a committee sees direction and
  not just position.
- **Opened-and-closed counts** for a period, retained well past the longest
  remediation target.

---

### Part V — Controls

#### A.20 The evidence architecture

This is the property that distinguishes the record from a database with a log
beside it, and it is the foundation any assertion about auditability rests on.

**Every change is an event.** Nothing is overwritten and nothing is deleted. Events
are grouped into streams, one per governed record. Within a stream the sequence is
one-based and gap-free, and a uniqueness constraint makes two concurrent writes to
the same position impossible.

**Immutability is enforced at the database grant level** — the application's own
role cannot update or delete. It is not a convention the code observes.

**The log is hash-chained.** Each event carries a SHA-256 over its own fields plus
the previous event's hash in the same stream. Recomputing the chain detects any
after-the-fact mutation, including one made with privileges the application does not
have. Chain verification is available per stream.

**Every screen is a projection**, rebuilt from the log. The log is the record; the
views are derived and can be discarded and rebuilt.

**Every event carries its actor and, where given, the reason.** Attribution is not
optional metadata.

**Bi-temporality.** Two time axes are retained and are different questions: *when
the institution was told* (the event's recorded time) and *what the record looked
like as of a date* (the as-of a document or pack was rendered against). Both are
kept on every issued document and on every client pack.

**Practical consequence for policy:** every state the institution has ever asserted
about a governed record can be reconstructed and attributed, and a prior assertion
cannot be quietly improved.

---

#### A.21 Identity, authorship and segregation of duties

**Known actors.** A change must be authored by somebody the institution has
registered in its People directory, matched on name or email. An unregistered
identity is refused. Two categories pass without being people: the platform's own
actor for first-run seeding, and **machine producers**, whose identifiers are
prefixed so the audit trail never mistakes an ingested payload for a person's work.
The rule stands down while no people are registered at all, so a fresh installation
cannot lock itself out; the first person added closes it.

Enforcement is configurable at three levels — **protected databases only** (the
default), **always** (what a hardened deployment sets), or **never** (a break-glass
setting for a migration, which leaves the record open to any identity and should be
temporary).

**Segregation of duties.** A record's peer reviewer may not be its own owner. This
is enforced at the write on **model records** — the check runs on both fields, since a
model with a distinct reviewer can be put in breach just as easily by moving the
ownership onto them — *and* reported by the audit across the audited estate. Only the
write that **creates** a breach is refused: a record already in breach stays editable
in every other respect, so no existing record is ever locked shut by the rule arriving
and its owner can still correct everything else about it. It is also configurable off
for an institution mid-migration whose estate cannot yet satisfy it, with the breaches
still reported throughout. ML Applications and AI Systems are audited against the rule
but are not yet write-enforced.

**Roles** (§A.1) are held on the person's record, granted by the committee, and are
the institution's vocabulary to re-set.

**A caution to carry into policy drafting.** The identity presented to the
application is currently taken at face value: authentication is the deployment's
responsibility, not the application's. §A.25 states this plainly; do not draft a
clause asserting authenticated identity without confirming what the deployment
actually enforces in front of it.

---

#### A.22 Integration surfaces

Two, with deliberately opposite privileges and separate credentials — a single
credential for both would collapse the distinction.

##### A.22.1 Ingest — machine-produced evidence in
Producing codebases push governance artefacts to a **frozen, versioned,
language-agnostic contract** published as JSON Schemas with worked examples. The
accepted artefacts are: model inventory, model chain, data lineage, field lineage,
ML training run, and document metadata.

Every request is an **envelope**: a provenance block plus the payload. Provenance —
source repository, commit, producer name and version, generation time — is stamped
onto every stored event, giving a reproducible link from a governed artefact back to
the exact scan that produced it.

The envelope is **strict** (unknown top-level keys are rejected, to catch producer
mistakes); payloads are **permissive** (only structural and identifying keys are
required, so a producer adding descriptive fields never breaks ingestion).

**Cross-reference integrity is validated server-side at ingest**, not left to the
schemas, because it spans artefacts: chain links must resolve to known records,
adjacency must be consistent, the graph must be acyclic, every lineage field's
pipeline step must resolve to a step in the current manifest, and every run must
name steps that exist.

##### A.22.2 ERM — governance position out
A **read-only by contract** feed, versioned in its path from the first release,
shaped around two consumers: an operational-risk function that needs what has
actually failed and which controls are not holding, and a strategic view that needs
how much of the estate meets the standard its divisions set and which way that is
moving.

**There is no write endpoint at any version.** If the enterprise risk system could
change the governance record, the record would no longer be the thing the committee
signed. Every enumerated field carries both a frozen machine value and the
institution's label, so renaming a vocabulary never breaks a consumer.

---

#### A.23 Controls over the software itself

The platform applies a gated rule set to its own source and publishes the evidence
as a report alongside the governance reports. This matters for a policy that has to
say something about the control environment around the tooling.

| Rule | Requirement |
|---|---|
| **R1** | No hardcoded parameters outside the configuration package — every institutional judgement is data, not code. |
| **R2** | No source file longer than 300 lines (400 for tests). |
| **R3** | ≥99% test coverage, verified at each stage. |
| **R4** | No functions in package initialisers. |
| **R5** | Every source file carries the canonical copyright header. |
| **R6** | **Zero tolerance**: no data-store access, SQL or driver import outside the single database package. |
| **R7** | Front-end assets live in their designated directories only. |
| **R8** | No duplication; shared logic is extracted, and existing copies are migrated. |
| **R9** | Testing is against a restored backup, never the live record. |
| **R10** | Every visual parameter comes from the central theme configuration. |

Duplication is measured and capped. The audit exits non-zero on any gated finding
and is published as a **Coding-Rule Audit** PDF, alongside the test report, the
coverage report and machine-readable results.

**R1 is the one with governance significance**, not just engineering hygiene: it is
what makes every threshold, weight, band, vocabulary and question in this document
an institutional setting rather than a vendor's opinion baked into code.

---

#### A.24 What an adopting institution sets for itself

Everything in this list is data the institution owns. None of it requires a change
to the software, and none of it migrates existing records when changed — the stored
value is stable and only the displayed label moves.

| Area | What is set |
|---|---|
| **Organisation** | Institution name, divisions, lines of business, people, roles. |
| **Committees** | How many, at what level, cadence, roster, quorum rule, Terms of Reference, standing agenda. |
| **Risk vocabulary** | The three dimensions' band names and explanations, the rating vocabulary, and the rating grid per criticality band. |
| **Audit calibration** | What each missing thing is worth, the escalation factors, the severity bands, the remediation targets, and the acceptable / conditional thresholds — per division, ratified by that division's committee. |
| **Questionnaires** | The validation question set for models, for ML applications and for AI systems: reword, drop, add. |
| **Review policy** | Which review items are in use and which are mandatory, per division. |
| **Classification lists** | Model types, vendors, codebases and repositories, calculating agents, data sources with their sensitivity and egress rules, estimators, features, foundation models. |
| **Status vocabularies** | Lifecycle stage, validation status, impact, priority, remediation status, question status, version lifecycle, and every training enumeration. |
| **Document identity** | Classification banner, author line, legal notice, logo, and the whole visual style of every issued document. |
| **Framework mapping** | Which frameworks the coverage section reports against, their clauses and their citations. |
| **Enforcement posture** | Known-actor enforcement, reviewer-independence enforcement, review horizons, retention periods. |

Two mechanical rules worth stating in policy, because they are what make the
vocabulary safe to change:

- A vocabulary entry stores a **stable value** and displays a **label**. Renaming
  edits the label and moves nothing in the estate.
- The stored value is **immutable once the entry exists**, because records already
  carry it and changing it would orphan every one of them. The migration path is to
  add a new entry, not to rename in place on a live estate.

---

### Part VI — Limits

#### A.25 Not built — do not assert

A policy clause that asserts a control the estate cannot evidence is worse than no
clause. The following are known limits as at the status date.

**Authentication.** The identity presented to the application is trusted verbatim.
The known-actor rule (§A.21) constrains *which* identities may author, but the
application does not itself authenticate. Any assertion about authenticated identity
must rest on what the deployment enforces in front of the application, and should be
drafted against that, not against this platform.

**Role-based authorisation.** Roles are recorded and committee-ratified, but they
are not yet enforced as permissions: the known-actor and reviewer-independence rules
are the enforced controls. Do not draft a clause asserting that role X cannot
perform action Y.

**Machine-actor scoping.** Ingest actors are distinguishable in the trail but are
not yet restricted to append-only operations.

**AI Systems are not yet in the completeness findings register.** They are counted
in framework coverage, but the ranked gap register covers Models, Products and ML
Applications. A clause promising a single ranked remediation register across the
whole estate would currently overstate it.

**Risk treatment options are not recorded.** A remediation step records what will be
done, but not which treatment option was chosen — accept, reduce, transfer, avoid —
nor the residual risk left after it, nor who accepted that residual and until when.
This is a live gap the ISO coverage table reports against itself.

**Organisational context is not recorded.** Internal and external context, and the
scope of the risk management activity itself, have no record. The coverage tables
report these as Not evidenced.

**Framework self-review is not recorded.** Division policies are ratified but not
re-reviewed on a cycle, and no record links a change in the framework to the finding
that prompted it.

**Nothing here detects drift.** The platform holds the governance cycle around
drift — the feeds, the monitoring approach, the review schedule — but does not
observe model behaviour in production.

**Monitoring reports exercise, not exceptions**, wherever the institution has no
production portfolios onboarded. The documents say so explicitly; a policy should
not claim more.

**Test evidence in the audit is a declaration plus an artefact.** The completeness
audit scores whether testing is declared and whether an evidence pack exists; the
evaluation register (§A.3.2) is where a measured result lives, and it is populated by
people rather than derived.

---

### Part VII — Reference tables

#### A.26 Controlled vocabularies

Every list below is administered by the institution and can be reworded, extended or
reduced. The values shown are what ships.

**Risk and rating.** Overall rating: Green / Amber / Red. Materiality, Complexity,
Impact, Priority: Low / Medium / High. Mission criticality: three bands
(mission critical / important / not important).

**Lifecycle.** Lifecycle stage: Development / Validation / Production / Retired.
Validation status: Initial / Pending / Validated / Conditionally Approved /
Rejected. Product status: Proposed / Active / Suspended / Retired. Client status:
Active / Prospect / Inactive / Retired.

**Review.** Trigger: Periodic / New version / Owner change / Committee directed.
Status: Not started, then one per stage agreed, then Signed off. Reviewer verdict on
a question: Not reviewed / Accepted / Challenged. Note kind: Note / Challenge.
Challenge state (derived): Open / Resolved. Note author side (derived): Owner /
Reviewer / Participant. Frequency: Monthly / Quarterly / Semi-annual / Annual.

**Committee.** Meeting status: Scheduled / Completed. Agenda item status: Pending /
Completed / Escalated / Rejected. Participant status: Invited / Attended / Apologies
/ Declined. Action status: Open / Closure requested / Closed. Sign-off request
status: Pending / Attached / Completed / Rejected / Withdrawn. Sign-off outcome:
Approved / Rejected. Sign-off kind: rating / retire / reactivate / handoff / owner.
Committee level: Company / Division / Line of Business.

**Registers.** Remediation status: Open / In Progress / Closed. Dependency
direction: upstream / downstream. Data source kind: Internal / External. Data
sensitivity: Public / Internal / Confidential / (and above). Data egress: whether a
source may leave the institution. RACI: Responsible / Accountable / Consulted /
Informed.

**Measurement.** Evaluation kind: Held-out performance / Benchmark against a
baseline / Adversarial or red team / LLM-as-a-judge / Human review / Reproducibility
check. Evaluation verdict: Passed / Passed with caveats / Failed / Inconclusive, or
blank where no verdict was reached.

**AI systems.** Hosting: Third-party hosted API / Private cloud / On-premise /
Embedded in a vendor product. Deployment pattern: Direct prompting /
Retrieval-augmented / Fine-tuned / Agentic / Multi-agent. Data sent for inference:
No data leaves the firm / Internal non-sensitive / Confidential business data /
Personal data / Regulated client data. Human oversight: Human makes the decision /
Human reviews before action / Human reviews after the fact / Human on request only /
Fully autonomous. Version policy: Pinned to a named version / Pinned, reviewed on a
cycle / Tracks the provider's latest. EU AI Act class: Not assessed / Minimal /
Limited / High (Annex III) / Prohibited.

**Assurance.** Coverage rating: Evidenced / Partially evidenced / Not evidenced /
Outside the platform. Severity band: Critical / High / Medium / Low. Response state:
Escalate / Act / Monitor / Clear.

**Artefacts.** Terms of Reference / Presentation / Policy / Guide / Template / Other.


---

© 2022-2026 MKM Research Labs. Licensed under the MIT License; see [`LICENSE`](../LICENSE).
