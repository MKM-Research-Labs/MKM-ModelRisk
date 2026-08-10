# MKM-ModelRisk — Platform Capability Brief

**Purpose of this document.** Source material for a regulator-facing proposal. It
describes, factually and in detail, what the MKM-ModelRisk platform does, how its
controls work, what evidence it produces, and — explicitly — what it does not yet do.
It is written to be pasted into a drafting session and turned into a submission; it is
not itself the submission.

**Status date:** 2026-08-07. Everything below reflects the state of the codebase on
that date. Sections marked **[NOT BUILT]** or **[PARTIAL]** are design-agreed but not
delivered, and must not be presented as capability.

**Before submission, verify §21 (Claims requiring verification).** Two things in the
platform's own vocabulary — a regulatory citation and the strength of its identity
control — need a human decision before they go in front of an examiner.

---

## Contents

1. [One-paragraph summary](#1-one-paragraph-summary)
2. [The problem it addresses](#2-the-problem-it-addresses)
3. [Design principles](#3-design-principles)
4. [The governance skeleton: organisation, people, committees](#4-the-governance-skeleton-organisation-people-committees)
5. [The model inventory](#5-the-model-inventory)
6. [Risk classification and rating](#6-risk-classification-and-rating)
7. [Validation: the nine questions and the review workflow](#7-validation-the-nine-questions-and-the-review-workflow)
8. [The model chain, handoffs and field lineage](#8-the-model-chain-handoffs-and-field-lineage)
9. [Products and operational events](#9-products-and-operational-events)
10. [The Model Risk Committee](#10-the-model-risk-committee)
11. [The completeness audit](#11-the-completeness-audit)
12. [Reporting: the evidence the platform produces](#12-reporting-the-evidence-the-platform-produces)
13. [Clients and client packs](#13-clients-and-client-packs)
14. [The evidence architecture](#14-the-evidence-architecture)
15. [Identity, authorship and permissions](#15-identity-authorship-and-permissions)
16. [Integration: the ingest contract](#16-integration-the-ingest-contract)
17. [Controls over the software itself](#17-controls-over-the-software-itself)
18. [Deployment and operations](#18-deployment-and-operations)
19. [Configurability — what an adopting institution changes](#19-configurability--what-an-adopting-institution-changes)
20. [Regulatory mapping](#20-regulatory-mapping)
21. [Claims requiring verification, and known limitations](#21-claims-requiring-verification-and-known-limitations)

---

## 1. One-paragraph summary

MKM-ModelRisk is a model-agnostic model-risk-governance platform. It holds an
institution's model inventory and runs the governance lifecycle around it: risk
classification, independent validation and challenge, the dependency chain between
models and its field-level handoffs, the products those models price, Model Risk
Committee meetings and their sign-offs, document control, and committee reporting.
Its distinguishing property is that the audit trail is the system of record rather
than a log written beside one: every change is an event appended to a hash-chained,
insert-only PostgreSQL store, and every screen is a projection rebuilt from that
store. Nothing is overwritten, nothing is deleted, and every state the institution
has ever asserted about a model can be reconstructed and attributed.

---

## 2. The problem it addresses

Model risk frameworks fail examination in a small number of recurring ways:

- **The inventory is a spreadsheet.** It is complete on the day it is compiled and
  decays thereafter; there is no record of who changed what, when, or why.
- **Validation is a document, not a process.** The report exists; the challenge that
  produced it does not. "Was this model effectively challenged?" cannot be answered
  from the file.
- **Committee governance is minuted, not enforced.** Quorum, segregation, and the
  link from a decision to the model it governs live in Word documents and people's
  memories.
- **Dependencies are undocumented.** A model consumes another model's output; nobody
  has written down which field feeds which, or who agreed the two are compatible.
- **Evidence is assembled under deadline.** When the examiner asks, a team spends
  three weeks reconstructing a position from email.

The platform's design responds to each of these directly: the inventory is
event-sourced; validation is a workflow whose challenge record is part of the
deliverable; committee rules are enforced in software (a non-quorate meeting cannot
sign anything off); dependencies are declared, field-mapped and committee-approved;
and the evidence pack is generated on demand from live state.

---

## 3. Design principles

Five ideas run through every screen. They are worth stating in a proposal because
they are what an examiner is actually being asked to accept.

**3.1 The audit trail is the record, not a description of it.** State is not stored
and then logged. State is *derived* from an append-only event log. The Audit Trail
screen does not describe the changes — it *is* the changes.

**3.2 Confirm-to-amend.** Every write — register, edit, add, remove, archive,
schedule — opens a confirmation dialog with a reason box and commits only on
explicit confirmation. Actor and reason are stamped on the event. This is a
deliberate friction: it makes the reason field a habit rather than an exception.

**3.3 Derived, not duplicated.** Links are computed, not typed. A model's responsible
committee is derived from its position in the org tree; a product's committee from
its model bindings; a meeting's chair and scope from its committee. The institution
sets the anchors; the platform resolves the relationships. There is no second place
for a fact to be wrong.

**3.4 Permissions come from the governance record, not a parallel user store.** The
domain already knows who is a real person (the People register), who owns a model
(the model's owner field), and who sits on the committee that governs it (the MRC
roster). Rights derive from those facts, so entitlements are themselves auditable and
committee-ratifiable. There is no shadow user table.

**3.5 The institution's framework, not the vendor's.** Risk vocabulary, rating bands,
heatmaps, completeness weights, document categories, remediation SLAs, the
classification banner and legal notice on every PDF, and the standard the audit cites
are all configuration. An adopting institution re-points them at its own framework
without code changes.

---

## 4. The governance skeleton: organisation, people, committees

**4.1 One institution, one org tree.** Company is a singleton (name and logo).
Divisions sit beneath it; Lines of Business beneath Divisions. Everything —
people, committees, models, products — hangs off that tree. A header scope selector
both filters what is shown and fixes the organisational placement of anything
registered while it is active.

**4.2 People.** A single directory of named individuals, each optionally anchored to
a Division or Line of Business (blank = firm-wide). People become committee chairs
and secretaries, model and product owners, peer reviewers, remediation owners and
RACI assignees. Their org anchoring determines eligibility to chair or sit on a
committee in a given scope.

**4.3 Model Risk Committees.** A committee is anchored to an org tier — Company,
Division, or Line of Business — and carries:

- a **roster**: chair, secretary, voting members, non-voting members, all drawn from
  People in scope;
- **quorum rules**: requires-chair (default yes), requires-secretary (default yes),
  minimum voting members (default 2);
- a **Terms of Reference** document, uploaded and version-controlled;
- a **frequency** (Monthly / Quarterly / Semi-annual / Annual), which also sets the
  interval at which successor meetings are auto-scheduled.

**4.4 The coverage rule.** When a subject needs a committee, the platform selects the
**most specific active committee that covers it**: Line of Business, then Division,
then Company as backstop. Archived committees never match. Committees are never
deleted — archiving preserves history and any meetings already bound to them.

This is the mechanism that makes committee responsibility a property of the
institution's structure rather than an assignment somebody remembers to make.

---

## 5. The model inventory

**5.1 Registration.** A model is registered with an ID, name, type, owner, and its
Division / Line of Business (fixed by the header scope, which is what binds it to a
committee). On registration the platform **automatically seeds the nine validation
questions** (see §7), each at *Not Addressed*. A model therefore enters the estate
with its validation gaps already declared rather than invisible.

**5.2 The model record.** Each model carries structured registers, all event-sourced:

| Area | Contents |
|---|---|
| **Overview** | Description, repository location, codebase, type, short name, methodology and rationale, source module, materiality, complexity, tier and the rationale for each |
| **Governance** | Responsible MRC, RAG rating, owner and role, lifecycle stage, review status, peer reviewer, validation date, MRC status, next review date |
| **Remediation** | Steps with description, owner, priority, due date, status (Open / In Progress / Closed) |
| **Versions** | Version register (version, date, description, author, reference document, lifecycle) plus a change-history register |
| **Weaknesses** | Description and impact |
| **Limitations** | Description, impact, monitoring trigger, compensating control |
| **Assumptions** | Description, impact, monitoring, mitigation |
| **Dependencies** | Declared upstream / downstream edges to other models, cycle-checked |
| **RACI** | Role, RACI classification, assigned to, backup, description |
| **Testing** | Evidence-driven: unit, integration and benchmark test results uploaded as documents rather than asserted as flags |
| **Documents** | Nine categories: Core Documentation, Sensitivity, Analysis, Monitoring, History, Test Results, Event Evidence, Remediation Evidence, Review |
| **MRC linkage** | Read-only view of every meeting decision and action tagged to this model |
| **Audit** | This model's own complete change history |

**5.3 Retirement is hibernation, and it is ratified.** A model is never deleted.
"Request retire…" raises a sign-off item to the responsible committee; the model
hibernates only when the committee approves. Reactivation follows the same path. A
hibernated model leaves the active estate — and leaves every portfolio figure derived
from it — while its history remains intact and its position in the chain is preserved
under a Hibernated view.

**5.4 Generated documents are filed, not merely rendered.** A Model Risk Document is
rendered from the inventory *as it stood at the moment of issue* and filed under the
History category. This gives a second time axis alongside the audit trail: the audit
trail records when the institution was told something; the filed document records
what the model looked like when a given statement was issued.

---

## 6. Risk classification and rating

**6.1 Three structural dimensions.** Every model and product is classified on
**Materiality**, **Complexity** and **Mission Criticality** (historically "Tier",
1–3: Mission critical / Important / Not important). Each carries a required
justification — the owner picks the band, and the framework asks for the reason.

**6.2 One governed rating.** Mission Criticality selects one of three 3×3 grids; the
(Materiality, Complexity) cell yields a Red / Amber / Green rating. Higher criticality
escalates to Red faster. The default Tier 1 grid, for example:

| Materiality ↓ / Complexity → | Low | Medium | High |
|---|---|---|---|
| **High** | Amber | Red | Red |
| **Medium** | Green | Amber | Red |
| **Low** | Green | Green | Amber |

There is deliberately **no competing composite score**. The one rating the committee
sets and reviews is the model's risk statement.

**6.3 Owner vs table.** Two ratings are shown side by side: the rating the owner has
asserted, and the rating the heatmap computes. Divergence between them is the signal
that the rating needs committee attention. This is a designed disagreement, not a
data-quality defect.

**6.4 Sign-off binds to a cell, not to a model.** An MRC sign-off covers the specific
(materiality, complexity, criticality) cell that was approved. Moving the model to a
different cell ends the cover — the model reverts to un-signed-off rather than
carrying an approval that was granted for a different risk position.

**6.5 Risk policy is per-division and committee-ratified.** The bands themselves —
their names, colours, explanations and scores, and the grid that maps them to ratings
— are an administered policy held per division. A policy is **drafted** by an
administrator and **approved** by the MRC; the draft/approved distinction is the gate,
and only an approved policy is in force. The three dimensions are structural; what
each band means is the institution's to define.

---

## 7. Validation: the nine questions and the review workflow

**7.1 The nine questions.** Every model is seeded on registration with nine
validation questions:

1. **Ronseal test** — does the model do what it says on the tin?
2. **Accuracy & stability** — does it provide timely, accurate and stable results?
3. **Resource usage** — does it consume excessive computational resources?
4. **Override controls** — are there controls over manual overrides?
5. **Data quality** — is the input data accurate, complete and appropriate?
6. **Assumptions** — are the model's assumptions documented and justified?
7. **Limitations** — are the model's limitations understood and monitored?
8. **Benchmarking** — has it been benchmarked against credible alternatives?
9. **Independent validation** — has it been independently validated?

Each is answered with a status (*Addressed / Partially Addressed / Not Addressed /
Not Applicable*) and a written rationale. Coverage is counted and displayed, but is
explicitly *coverage*, not a risk score.

**7.2 The review as a five-stage workflow.** [PARTIAL — see build state below]
A model review runs as a single workflow with five ordered stages, each carrying its
own state, the reviewer's interim approval, and who approved it and when:

| # | Stage | Content |
|---|---|---|
| 1 | Preliminary documents | The pack the reviewer works from; marked received and read |
| 2 | The nine questions | Owner's status and rationale; reviewer's verdict and comment |
| 3 | Model weaknesses | Weaknesses register, owner-proposed, reviewer-agreed |
| 4 | Limitations of use | Limitations register, same pattern |
| 5 | Monitoring approach | Narrative description of how the model will be monitored |

The model's review status is set by the work done — *Documents reviewed*, *Questions
answered*, *Weaknesses agreed*, *Limitations agreed*, *Monitoring agreed* — not by
somebody updating a dropdown. Interim approval is not a lock: earlier stages stay
reopenable, and reopening is itself a recorded act.

**7.3 Two-sided questions.** Each of the nine questions carries an owner side
(status, rationale, evidence) and a **reviewer side**: verdict (*Accepted /
Challenged / Not reviewed*), comment, and a stamped reviewed-by and reviewed-at. A
question can be *Addressed* by its owner and *Challenged* by its reviewer at the same
time. Holding that disagreement is the point.

**7.4 The record of challenge is the deliverable.** Per stage, an append-only thread
between owner and reviewer:

- **No edit, no delete** — not by the author, not for a typo. A correction is a new
  note. The console never offers the affordance.
- **Attributed and stamped** — named identity, role (Owner / Reviewer / Participant,
  *derived* from the signed-in identity against the model's owner and reviewer, never
  chosen from a dropdown), and timestamp.
- A note may be marked a **Challenge**, which is Open until a later note answers it.
  Both states are derived; no row is edited to carry them.
- Challenges are **printed verbatim in the review report**, under the stage they
  arose in — so the report can state "six challenges raised on the nine questions,
  six resolved, two changed a status" rather than leaving a reader to infer rigour
  from a wall of text.
- **An open challenge blocks sign-off.** A reviewer who signs off over one must say
  so in a note; it is never silent.

This is the platform's direct answer to "was this model effectively challenged?" —
the documentation answers it on its own, without a person to narrate it.

**7.5 Review triggers.** A review is not only a calendar event. Valid triggers are
*Periodic*, *New version*, *Owner change*, and *MRC directed*. A new version puts a
"has the documentation been brought up to date?" checklist in front of the owner,
because a new version is the case where the write-up, the sensitivities and the test
evidence all go stale at once.

**7.6 Build state.** Delivered: the review tab and stage rail, per-stage interim
approval and status, the reviewer's verdict on each of the nine questions, the review
brief, and the append-only challenge record under the stage it happened on.
**[NOT BUILT]**: the final reviewer sign-off gate, generation and filing of the Model
Review Report PDF, and the mechanism for tabling that report to the MRC as a received
paper. The vocabulary for the signed-off state exists; the sign-off does not. A
proposal must not claim the signed review report today.

---

## 8. The model chain, handoffs and field lineage

**8.1 The chain.** Each model declares its upstream and downstream dependencies. From
those declarations the platform derives a directed, **cycle-checked** graph — the
"string of pearls" — presented in three views: **Chain** (models with edges, drawn
producer → consumer), **Terminal** (models with no downstream consumer, i.e. the
estate's actual outputs), and **Hibernated** (retired models, kept for history).

**8.2 Every edge is a governed handoff.** An edge is not merely an arrow. Each
carries:

- a **field lineage table** mapping each provider field to a consumer field, with
  type and units on both sides and a note — the actual data contract between two
  models;
- a **compatibility note**: the plain-language statement of whether the two models fit
  together;
- an **MRC compatibility sign-off**, raised as a `handoff` sign-off item and ratified
  in a meeting. An edge starts *Draft*.

A **handover document** can be generated for any edge.

**8.3 Why this matters to an examiner.** Model-chain risk — a model consuming another
model's output under assumptions that no longer hold — is normally undocumented
because no artefact naturally owns it. Here the edge is a first-class governed object
with a named owner of the question, a field-level contract, and a committee decision
attached to it.

---

## 9. Products and operational events

A **Product** is a live pricing or booking configuration: the point where models meet
the business.

- A product is registered against a **Calculating Agent** (the pricing/booking
  platform — e.g. Murex, Calypso) and then **binds model components**. Eligibility is
  driven by each model type's machine-readable **binding role** (Analytics / Market
  Data / Neither), not by the type's name, so an institution can name its types as it
  wishes without breaking bindings. A product is not limited to a fixed
  analytics-plus-market-data pair.
- It carries its own limitations, assumptions, remediation, RACI, classification and
  risk rating (the same heatmap as a model).
- **Operational events** — real production failures, with date, what happened,
  remediation and RACI attribution — are recorded against the product. A rolling
  365-day event count feeds the product's risk view **and** escalates its completeness
  severity (§11), and events flow up to the committee as agenda items to be received.
- A product inherits its responsible committee from its bindings' organisation.
- Status runs Proposed / Active / Suspended / Retired; retired products become
  read-only.

The design point: operational failure is not a separate incident system. It is a
governance input that changes how hard the platform pushes on a model's evidence.

---

## 10. The Model Risk Committee

The committee machinery is where the platform enforces process rather than recording
it.

**10.1 Scheduling.** A meeting is scheduled against a committee with an ID, title,
date and optionally time and location. Scheduling **drains any queued sign-off
requests** for that committee onto the new agenda automatically.

**10.2 Participants and quorum.** The committee roster is carried onto the meeting as
its participants, each with an attendance status (Invited / Attended / Apologies /
Declined), plus any added guests. A live quorum badge shows *met* or *not met* and
what it still needs. **A meeting that is not quorate cannot approve a sign-off and
cannot be closed.** This is enforced, not advised.

**10.3 Standing agenda.** Meetings open with a standing agenda — rollcall and
confirmation of quorum, sign-off of the previous minutes, review of model sign-offs,
review of model analysis, any other business — each with its own confirm control.
Institution-specific items are added alongside. The agenda can be **finalised for
distribution**, which locks it and produces a distribution pack (ZIP: the agenda PDF
plus every uploaded agenda and analysis paper). Unlocking reopens it, as a recorded
act.

**10.4 Sign-off.** Sign-off items come in four kinds and are routed to the
responsible committee automatically:

| Kind | What it ratifies |
|---|---|
| `rag` | A proposed risk rating for a model |
| `retire` | Hibernation of a model |
| `reactivate` | Restoration of a hibernated model |
| `handoff` | The compatibility of a chain edge |

A request is attached immediately to the committee's next scheduled meeting if one
exists, and otherwise **queued and drained onto the agenda the moment such a meeting
is scheduled**. State runs *Pending → Attached → Completed*, or *Rejected*. If no
committee covers the subject, the request is refused and the user is told to
configure one — an uncovered model cannot quietly bypass governance.

**Approval carries out the decision.** For a rag item it snaps the model's rating to
the proposed value and stamps the sign-off date and meeting; for retire/reactivate it
hibernates or restores; for a handoff it records compatibility. It also writes a
sign-off history entry, **auto-generates a minute**, and marks both the request and
the agenda item Completed. Rejection changes nothing on the subject and records the
decision. Approval requires quorum.

Critically: **a proposed rating is proposed, not applied.** The change takes effect
only on committee approval. There is no path by which an owner's assertion becomes
the governed position without the committee.

**10.5 Analysis.** Separately from approvals, the meeting reviews a scope of
inventory models, products and handoffs **pre-filtered to the committee's remit**.
Each selected subject gets an outcome, a discussion note, and any follow-on
remediation (with owner and due date). In-scope subjects' open remediation is printed
in the Meeting Pack.

**10.6 Actions and minutes.** Actions carry an owner, target date, status and an
optional model link; an action tagged to a model **surfaces automatically on that
model's MRC linkage tab**, credited to its source meeting. The meeting is the system
of record; the model reflects it. There is no double entry. Minutes are added
manually where needed, but sign-off and standing-item minutes are written
automatically as decisions are made, so most of the record assembles itself.

**10.7 Close, and succession.** *Close meeting* becomes available only once the
meeting is quorate **and** every agenda item is resolved; until then the control is
disabled and names what is blocking it. Closing renders and files the **minutes PDF**
and stamps the meeting Completed. It then **auto-schedules the successor** at the
committee's frequency interval, carrying the committee binding and the standing
agenda, and tabling the just-filed minutes on the successor's minutes-sign-off item.
A closed meeting is locked.

The consequence worth putting in front of a regulator: the committee cadence cannot
lapse through inattention, and the previous meeting's minutes cannot fail to be
tabled at the next one.

---

## 11. The completeness audit

The platform grades its own governance record. This is the engine behind the
Governance Completeness Audit report and the client pack's gap section.

**11.1 What it detects.** For every model and product, three kinds of gap:

- **field gaps** — a required field not recorded;
- **collection gaps** — an empty register, or a partially-completed one (e.g. three
  of nine validation questions still unanswered);
- **document gaps** — a required document category with nothing uploaded, or — scored
  higher — a **broken reference**: a document recorded on the register whose file is
  not in the store. A broken reference escalates by a factor of 1.15, on the reasoning
  that an inventory overstating its own coverage is a more serious finding than a
  visible hole, and one nobody reading the register alone would catch.

**11.2 How severity is scored.** Each gap's severity is its intrinsic criticality
multiplied by four escalation factors:

```
severity = criticality × tier_weight × rating_multiplier × event_pressure × staleness
```

| Factor | Default behaviour |
|---|---|
| **tier_weight** | Tier 1 = 1.00, Tier 2 = 0.80, Tier 3 = 0.60. **Untiered = 0.90** — an absent tier escalates rather than damps, because the missing classification is itself the reason to look. |
| **rating_multiplier** | Red 1.25, Amber 1.10, Green 1.00. **Unrated = 1.15**, above Green: a missing rating is not evidence of a healthy one. Taken from the division's approved risk policy, so the audit escalates on exactly the rating the Risk tab shows rather than forming a second opinion. |
| **event_pressure** | +0.05 per operational event in the rolling window, capped at 1.25, so a single bad year cannot dominate the ranking. |
| **staleness** | Stepped escalation by how far past its next review date the record has run. A record not yet due, or with no review scheduled, is not escalated here — the absent date is already its own gap, and charging twice would double-count. |

Severity bands and target remediation windows: **Critical** (≥1.00, 30 working days),
**High** (≥0.60, 60), **Medium** (≥0.35, 90), **Low** (180).

**11.3 Every finding is defensible line by line.** Each gap carries its own factors,
not just the product. The register prints `0.90 × 1.00 × 1.25 × 1.15 × 1.10 = 1.42,
Critical` — not an unexplained 1.42. The scoring module performs no I/O, so the
arithmetic an auditor is asked to trust is unit-testable in isolation from the report
that prints it.

**11.4 Every finding is actionable.** Each carries an instruction addressed to a named
owner — "Record *next review date* on the model record", "Upload a document under
*Core Documentation*", "Re-upload under *Test Results*: the record cites a file that
is not in the document store and cannot be produced" — plus its SLA. A finding
somebody cannot be handed is an observation, not a finding.

**11.5 Weighted completeness.** A record's score is the share of the criticality it
was asked to carry that it actually holds. Unweighted percentages flatter a record
that has filled in its cheap fields and left the expensive ones blank. A record is
reported as **materially incomplete below 0.85**, and **conditional below 0.60**.

**11.6 The audit basis is configurable** and is printed on the report, so an adopting
institution changes the citation when it re-points the weights at its own framework.

---

## 12. Reporting: the evidence the platform produces

All generated on demand from live state. PDF rendering uses a LaTeX engine
(`tectonic`) in a shared house style; the classification banner, document author and
legal notice on every page are the institution's configuration.

| Artefact | Contents |
|---|---|
| **Model Risk Document** | Per model: classification, methodology, governance, the nine validation questions with evidence, assumptions, limitations, weaknesses, remediation, dependencies, change history, MRC sign-offs, attached documents. Filed under History on issue. |
| **Model Risk Report** | The portfolio-level report: risk profile across the estate, the inventory table, then a full dossier per model. |
| **Governance Completeness Audit** | The gap register: every finding, its factors, its severity band, its SLA and its instruction, worst first. |
| **Meeting Pack** | Per meeting: company branding, meeting info, participants, agenda, minutes, actions, and per-model open remediation for every in-scope model. |
| **Distribution pack (ZIP)** | The finalised agenda PDF plus every uploaded agenda and analysis paper. |
| **Minutes** | Rendered and filed automatically on meeting close. |
| **Handover document** | Per chain edge: the field lineage and compatibility position. |
| **Monitoring document** | What the models have been exercised against, and the standing position on every recorded weakness and limitation of use. |
| **Risk categorisation document** | The division's approved risk policy: bands, definitions and the rating grid. |
| **Client pack (ZIP)** | See §13. |
| **Model Review Report** | **[NOT BUILT]** — designed; would carry the five stages, both sides of every question, the registers, the monitoring narrative, the challenge record verbatim and the reviewer's attestation. |

An in-app **Audit Reports** tab generates the coding-rule audit reports, the Model
Risk Report, the Governance Completeness Audit, the test-suite coverage report and
the test report, each viewable and downloadable.

---

## 13. Clients and client packs

**[PARTIAL — records and pack generation exist; the surrounding workflow is still
maturing.]**

The Clients area treats a client as a point of aggregation: one relationship record,
linked to the specific models and products that client relies on, and one
self-describing evidence pack generated on demand — so a client's model-risk due
diligence is answered once, from one place.

A generated pack contains, for every linked model and product: a **freshly rendered**
Model Risk Document and its attached evidence, the completeness audit, recent
completed-meeting minutes, operational-event write-ups, and the committee's Terms of
Reference — with a `CONTENTS.txt` manifest stamping as-of and generated-at, and
stating exactly what was packed **and what was recorded but unavailable**. Because
the PDFs are built at the moment of packing, a pack never carries a stale write-up;
because the manifest declares absences, it never silently omits.

Every generated pack is retained with its timestamp, so what was sent to whom, and
when, is itself part of the record.

---

## 14. The evidence architecture

This section is the technical core of any regulatory submission.

**14.1 Event sourcing / CQRS.** The system of record is an append-only `events`
table. Events are grouped into streams keyed by `(aggregate_type, aggregate_id)`.
Within a stream, `stream_seq` is a 1-based, gap-free counter, and a UNIQUE constraint
makes two concurrent appends to the same position impossible. Every screen is a
**projection** — a read model rebuilt from the log. Projections can be dropped and
rebuilt at any time without loss, because they contain no truth of their own.

**14.2 Immutability enforced at the database grant level.** The runtime application
role (`mkm_app`) holds `SELECT` and `INSERT` only. It cannot `UPDATE`, `DELETE` or
`TRUNCATE`. This is not an application convention that a bug could bypass — the
database refuses. Schema migration runs under a separate owner role.

**14.3 Tamper evidence.** Each event carries `event_hash` = SHA-256 over its own
fields *and the previous event's hash in the same stream*:

```
hash = SHA256( aggregate_type | aggregate_id | stream_seq | event_type
             | canonical_json(payload) | actor | reason | recorded_at | prev_hash )
```

The payload is canonically encoded (sorted keys, fixed separators) so the hash is
reproducible. `verify_chain` recomputes the chain; **any after-the-fact mutation of a
stored event — including one made with privileged database access outside the
application entirely — is detectable.** This is the control that answers "what if
someone with DBA rights edits the record?"

**14.4 What every event carries.** Aggregate type and id, sequence, event type,
payload, **actor**, **reason**, UTC timestamp, previous hash and own hash. The
before/after values of every changed field are recoverable, and are displayed
per-field on the Audit Trail.

**14.5 What this delivers.**

- The complete history of every model, product, meeting and decision is preserved.
- Nothing is ever truly deleted — retirement is hibernation, archiving is archiving.
- Any historical state can be reconstructed: what the institution believed about a
  model on any past date, and who told it.
- The audit trail **cannot be edited or cleared from the application**, and
  out-of-band editing is detectable.
- There are two independent time axes: the event log ("when we were told") and the
  filed generated documents ("what we said, at the time we said it").

**14.6 Single sanctioned data path.** All database access goes through one module
(`src/database/`), mechanically enforced (see §17, rule R6). No SQL, driver import or
connection exists anywhere else in the codebase. There is exactly one place where the
event store's guarantees can be reasoned about — and exactly one place an examiner or
internal auditor needs to read to verify them.

---

## 15. Identity, authorship and permissions

**This section must be presented honestly. It is the platform's weakest area and an
examiner will find it.**

**15.1 What exists today.**

- **Authentication is perimeter-delegated.** The platform has no login. It reads the
  acting user from a trusted request header (`X-Auth-Request-User`) supplied by the
  institution's SSO proxy, and records that identity as the actor on every event.
  This is a legitimate architecture *behind a properly configured proxy*.
- **Known-actor enforcement (delivered 2026-08-07).** A change must be authored by
  somebody registered in the People directory, matched on name or email. Refusal is
  an HTTP 403 naming the actor and the remedy. The platform's own actor and machine
  producers (`ingest:*`) pass. An empty People list stands the rule down so a fresh
  install can register its first person. Policy is configuration:
  `protected` (the production estate only — the default), `always` (a hardened
  deployment), or `never` (a documented, temporary break-glass). The same check covers
  document-upload paths, which call their commands directly.

**15.2 What does not exist. [NOT BUILT]**

- **Role-based authorisation.** Every authenticated, registered actor can currently
  register models, edit any field, approve MRC sign-offs, ratify risk policy, close
  meetings and retire models. There is a deliberate, documented enforcement seam
  (`authorize()` in the single command dispatcher, which every mutating command
  already passes through), but it currently enforces only the known-actor rule.
- **Segregation of duties.** The negative controls — an owner cannot approve their own
  model; a validator cannot validate a model they own; an administrator cannot ratify
  the policy they drafted; a chair cannot be sole approver of their own tabled paper
  — are designed but not built.
- **Header verification.** The known-actor rule narrows *who* can author to a
  registered person, but does not verify that the caller **is** that person. Anyone
  who can address the application can send a registered name. Closing that gap
  requires the proxy to authenticate and strip the header — an infrastructure
  decision, not an application one.

**15.3 The delivery plan.** Six phases, sequenced so nothing is enforced before it can
be satisfied: **P1** know who is real *(delivered)*; **P2** roles as data on the
People record, assigned by event so entitlements are audited; **P3** authorise in
report-only mode for a period of real use, so the log says exactly what would break;
**P4** enforce, with 403s naming the missing role; **P5** segregation of duties;
**P6** scope machine actors to append-only.

**15.4 How to present this.** The defensible framing is that the platform makes every
decision attributable and reconstructable *today*, and that the entitlement layer is
scoped, sequenced and enforced at a single architectural choke point rather than
scattered across endpoints. The undefensible framing is any claim that segregation of
duties is in place. It is not.

**15.5 Open decisions worth naming in a submission** (they will be asked about):
whether the SSO header is trusted in production; how events authored by unknown
actors before P1 are surfaced and explained rather than silently trusted; whether
role assignment itself requires MRC ratification; and whether there is a named,
time-boxed, loudly-audited break-glass path for when the committee cannot convene.

---

## 16. Integration: the ingest contract

The platform can act as a collector as well as a console. Producing systems POST
schema-validated artefacts to a token-gated ingest API, against frozen,
language-agnostic JSON Schemas that any stack can code to:

| Artefact | Contents |
|---|---|
| `model_inventory` | Inventory plus the model chain |
| `data_lineage` | A pipeline run manifest |
| `field_lineage` | Report → section → field registry (BCBS 239 Principle 3) |
| `document` | Model-document upload metadata |

Every request is an **envelope**: a provenance block plus the payload. Provenance
carries the source repository, the exact **commit hash**, the producer name and
version, and generation timestamp — and is stamped onto every stored event. The
result is a reproducible link from a governed artefact back to the exact scan of the
exact code revision that produced it.

For an institution whose models live in code, this is the mechanism by which the
governance record stays synchronised with reality rather than being re-typed.

---

## 17. Controls over the software itself

A model-risk platform is itself a piece of software an examiner may ask about. The
codebase is held to nine mechanically-enforced coding rules, audited by a command
that exits non-zero on any gated finding:

| Rule | Control |
|---|---|
| **R1** | No hardcoded parameters outside `config/` — every threshold, weight and vocabulary item is inspectable configuration, not buried in logic |
| **R2** | No source file longer than 300 lines |
| **R3** | ≥99% test coverage, verified at each stage and gated |
| **R4** | No logic in `__init__.py` |
| **R5** | Canonical copyright/licence header on every source file, generated from one source of truth |
| **R6** | **Zero tolerance** — no SQL, driver import or connection outside `src/database/` |
| **R7** | Front-end assets confined to `src/static` and `src/templates`; no embedded JavaScript |
| **R8** | No duplicated logic; shared behaviour is extracted |
| **R9** | Test and verify against a restored backup, never the live database |

Test coverage is enforced at ≥99% across roughly 750 unit and integration tests, with
a separate Playwright end-to-end browser suite. Unit and e2e suites derive their own
disposable databases and are guarded so they cannot reach live data.

**R1 is worth highlighting in a proposal**: it is the rule that makes "show me your
risk weights" a matter of reading a configuration file rather than auditing source
code.

---

## 18. Deployment and operations

- **Runs entirely on-premises.** PostgreSQL 16 and Python 3.13. No cloud dependency,
  no external service calls, no telemetry. Institution data never leaves the
  institution.
- **A Flask application** served by any WSGI server, with a dependency-free
  vanilla-JavaScript console — no front-end build chain, no third-party runtime
  JavaScript.
- **Documents** are stored on disk with their metadata in the event stream; the
  completeness audit checks that every recorded document is actually retrievable, so
  the two cannot silently diverge.
- **Backups** are taken hourly, with scripted restore, and restore-to-scratch
  guardrails that make restoring over the live estate a deliberate act rather than an
  accident.
- **Licensing.** The platform is MIT-licensed. Third-party dependencies and their
  licences are enumerated in a maintained manifest. The legal notice on generated
  documents covers the *contents* — the models and calculations described — and is
  the institution's own text, distinct from the software licence.

---

## 19. Configurability — what an adopting institution changes

Everything in this list is configuration, not code. It is the answer to "is this your
framework or ours?"

- **Risk vocabulary and bands** — names, colours, explanations and scores for
  Materiality, Complexity and Mission Criticality, per division, MRC-ratified.
- **The rating grid** — which (materiality, complexity) cell yields which rating in
  each criticality band.
- **Completeness weights** — per-field, per-collection and per-document-category
  criticality; tier weights; rating multipliers; event pressure; staleness steps;
  severity bands; remediation SLAs; exemptions.
- **The audit basis citation** printed on the completeness report.
- **Model types and their binding roles**; calculating agents; data sources; vendors.
- **Document categories and their tag taxonomy.**
- **Committee structure, levels, quorum rules and frequencies.**
- **Classification banner, document author and legal notice** on every generated PDF.
- **The known-actor enforcement mode.**
- **The command-to-role permission map** (as the role model is delivered).

---

## 20. Regulatory mapping

Indicative mapping of platform capability to common supervisory expectations. **Each
citation should be confirmed against the current text of the relevant standard before
submission — see §21.**

| Expectation | How the platform addresses it |
|---|---|
| **Complete, maintained model inventory** | Event-sourced inventory with mandatory classification, org placement and ownership; hibernation rather than deletion; completeness audit that scores and ranks what is missing |
| **Risk-based tiering proportionate to model materiality** | Materiality × Complexity × Mission Criticality with mandatory per-dimension justification; per-division, committee-approved policy; tiering drives audit escalation and review cadence |
| **Independent validation and effective challenge** | Five-stage review workflow with a distinct reviewer side on every validation question; append-only, attributed challenge record that blocks sign-off while open and is printed verbatim **[report generation NOT BUILT]** |
| **Documented assumptions and limitations, with monitoring** | Dedicated registers for assumptions, limitations (with monitoring trigger and compensating control) and weaknesses; monitoring approach as a review stage; standing monitoring document |
| **Ongoing monitoring and benchmarking** | Benchmarking is a seeded validation question requiring evidence; test evidence is uploaded artefacts, not assertions; operational events feed the rolling risk window |
| **Governance, policies and controls; board and committee oversight** | Committee structure anchored to the org tree with automatic coverage resolution; enforced quorum; standing agenda; auto-scheduled successor meetings; committee-ratified risk policy |
| **Segregation of duties** | **[NOT BUILT]** — designed as negative controls at a single enforcement point; §15 |
| **Change management and versioning** | Version register and change history per model; every change an attributed event with a reason; material version change is a review trigger |
| **Data quality and lineage (BCBS 239)** | Data quality is a seeded validation question; field-level provider→consumer lineage on every chain edge; field-lineage and data-lineage ingest artefacts with commit-level provenance |
| **Audit trail and record retention** | Append-only, hash-chained store; insert-only database grants; nothing deletable from the application; out-of-band tampering detectable |
| **Third-party / vendor model governance** | Vendor reference list; models registered irrespective of provenance; calculating-agent bindings on products |
| **Evidence production on demand** | Model Risk Document, Model Risk Report, Meeting Pack, minutes, completeness audit, handover documents, client packs — all generated from live state with as-of stamping |

---

## 21. Claims requiring verification, and known limitations

**Include this content in internal review before submission. Removing it does not
make the issues go away; a regulator will find them, and finding them stated is a
materially better outcome than finding them concealed.**

### 21.1 Verify before citing

- **"SR 26-2, superseding SR 11-7."** The platform's own vocabulary describes its
  nine validation questions and its completeness audit basis as
  *"SR 26-2 (superseding SR 11-7) and PRA SS1/23"*. **Confirm this citation against
  the current published supervisory guidance before it appears in a regulatory
  submission**, including the exact designation and the effective date. If the
  designation is wrong or not yet in force, the substance is unaffected — the nine
  questions and the framework do not change — but the citation must be corrected in
  `config/governance/_completeness_scoring.py` (`AUDIT_BASIS`) and in the question
  seed, since it prints on generated reports.
- **PRA SS1/23** is cited in the same string; confirm applicability to the
  institution and jurisdiction the proposal addresses.

### 21.2 Not built — do not claim

- Reviewer sign-off, the Model Review Report PDF, and tabling that report to the MRC.
- Role-based authorisation and segregation of duties (§15).
- Escalation of a sign-off to a higher-tier committee (present in the data model and
  API, no user-interface control).
- Machine-actor scoping to append-only.

### 21.3 Known weaknesses to disclose

- **The identity header is trusted verbatim.** The platform records whatever
  identity the perimeter supplies. Its integrity therefore depends entirely on the
  SSO proxy authenticating and stripping that header. This is an infrastructure
  control, and the proposal should state which component provides it in the
  institution's deployment.
- **Events authored before known-actor enforcement.** The log is append-only, so
  historical events authored by unregistered identities remain. The proposed
  treatment is to surface them on the audit trail as "unrecognised actor" so they can
  be explained rather than silently trusted. That surfacing is **[NOT BUILT]**.
- **PDF generation depends on an external LaTeX engine.** Without `tectonic`
  installed, report endpoints return an error rather than a document. This is an
  operational prerequisite, not a defect, but it belongs in a deployment section.
- **Clients and client packs are in early development.** Records and pack generation
  work; the surrounding workflow is maturing.

### 21.4 Framing note

The strongest case this platform makes is not feature breadth — it is that the
**evidence architecture is structurally sound**: append-only, hash-chained,
insert-only at the grant level, single data path, everything attributed, nothing
deletable, all reports generated from live state. That claim survives scrutiny. The
entitlement layer is the immature part, it is scoped and sequenced, and it is enforced
at one architectural choke point rather than scattered. A proposal that leads with the
first and is candid about the second is considerably more credible than one that
blurs them.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
