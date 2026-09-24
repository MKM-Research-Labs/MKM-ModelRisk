# MKM-ModelRisk — Platform Capability Brief

**Purpose of this document.** Source material for a regulator-facing proposal. It
describes, factually and in detail, what the MKM-ModelRisk platform does, how its
controls work, what evidence it produces, and — explicitly — what it does not yet do.
It is written to be pasted into a drafting session and turned into a submission; it is
not itself the submission.

**Status date:** 2026-08-29. Everything below reflects the state of the codebase on
that date. Sections marked **[NOT BUILT]** or **[PARTIAL]** are design-agreed but not
delivered, and must not be presented as capability.

**Before submission, verify §24 (Claims requiring verification).** Two things in the
platform's own vocabulary — a regulatory citation and the strength of its identity
control — need a human decision before they go in front of an examiner.

**What changed since the 2026-08-07 revision of this brief.** The estate is no longer
models and products alone: **ML Applications** and **AI Systems** are first-class
governed records (§6), each with its own questionnaire and its own field set. The
**review workflow is complete** — seven stages, a sign-off gate that an open challenge
blocks, and the Model Review Report generated and filed (§8); the previous revision
correctly recorded that sign-off and the report were not built, and that is no longer
the case. **Framework coverage** now reports the estate clause by clause against ISO
31000, COSO ERM, BCBS 239, the FINOS AI Governance Framework and the EU AI Act (§13).
An **executive response view** answers "what do I have to do something about"
(§14), backed by a daily observer that ages findings and carries a trend (§14.5). An
**ERM feed** publishes the governance position to enterprise risk, read-only by
contract (§19.2). **Reviewer independence is now enforced at the write** — the first
segregation-of-duties control to be delivered (§18). And **roles are now data on the
People record, ratified by the committee** rather than assigned by an administrator,
though they are still not enforced as permissions.

---

## Contents

1. [One-paragraph summary](#1-one-paragraph-summary)
2. [The problem it addresses](#2-the-problem-it-addresses)
3. [Design principles](#3-design-principles)
4. [The governance skeleton: organisation, people, committees](#4-the-governance-skeleton-organisation-people-committees)
5. [The model inventory](#5-the-model-inventory)
6. [The wider estate: ML Applications, AI Systems, Products](#6-the-wider-estate-ml-applications-ai-systems-products)
7. [Risk classification and rating](#7-risk-classification-and-rating)
8. [Validation: the questionnaires and the review workflow](#8-validation-the-questionnaires-and-the-review-workflow)
9. [The model chain, handoffs and field lineage](#9-the-model-chain-handoffs-and-field-lineage)
10. [Operational events, measurement and monitoring](#10-operational-events-measurement-and-monitoring)
11. [The Model Risk Committee](#11-the-model-risk-committee)
12. [The completeness audit](#12-the-completeness-audit)
13. [Framework coverage](#13-framework-coverage)
14. [The executive response model](#14-the-executive-response-model)
15. [Reporting: the evidence the platform produces](#15-reporting-the-evidence-the-platform-produces)
16. [Clients and client packs](#16-clients-and-client-packs)
17. [The evidence architecture](#17-the-evidence-architecture)
18. [Identity, authorship and permissions](#18-identity-authorship-and-permissions)
19. [Integration: ingest and the ERM feed](#19-integration-ingest-and-the-erm-feed)
20. [Controls over the software itself](#20-controls-over-the-software-itself)
21. [Deployment and operations](#21-deployment-and-operations)
22. [Configurability — what an adopting institution changes](#22-configurability--what-an-adopting-institution-changes)
23. [Regulatory mapping](#23-regulatory-mapping)
24. [Claims requiring verification, and known limitations](#24-claims-requiring-verification-and-known-limitations)

A companion reference — [Governance components, artefacts and workflows](governance_components_reference.md),
also published as Appendix A of the user guide — inventories the same platform as a
policy author needs it: every record type, register, workflow, vocabulary and issued
document, organised so a control to be asserted can be traced to the mechanism that
evidences it.

---

## 1. One-paragraph summary

MKM-ModelRisk is a model-agnostic model-risk-governance platform. It holds an
institution's inventory of models, machine-learning applications and AI systems, and
runs the governance lifecycle around them: risk classification, independent validation
and challenge, the dependency chain between models and its field-level handoffs, the
products those models price, Model Risk Committee meetings and their sign-offs,
document control, committee reporting, and a graded audit of its own completeness
against the institution's framework and against ISO 31000, COSO ERM, BCBS 239, the
FINOS AI Governance Framework and the EU AI Act. Its distinguishing property is that
the audit trail is the system of record rather than a log written beside one: every
change is an event appended to a hash-chained, insert-only PostgreSQL store, and every
screen is a projection rebuilt from that store. Nothing is overwritten, nothing is
deleted, and every state the institution has ever asserted about a model can be
reconstructed and attributed.

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
- **The estate outgrows the register.** Fitted estimators and systems built on
  third-party foundation models are governed, if at all, in a separate spreadsheet
  with a different vocabulary — so "what does this firm run, and how much of it is
  under governance" has no single answer.
- **Evidence is assembled under deadline.** When the examiner asks, a team spends
  three weeks reconstructing a position from email.

The platform's design responds to each of these directly: the inventory is
event-sourced; validation is a workflow whose challenge record is part of the
deliverable; committee rules are enforced in software (a non-quorate meeting cannot
sign anything off); dependencies are declared, field-mapped and committee-approved;
models, ML applications and AI systems share one register, one rating scheme and one
audit; and the evidence pack is generated on demand from live state.

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

**3.3 Derived, not duplicated.** Links are computed, not typed. A record's responsible
committee is derived from its position in the org tree; a meeting's chair and scope
from its committee; a challenge's Open or Resolved state from whether a later note
answers it; a note's author side from the signed-in identity against the record's own
owner and reviewer. The institution sets the anchors; the platform resolves the
relationships. There is no second place for a fact to be wrong.

**3.4 Permissions come from the governance record, not a parallel user store.** The
domain already knows who is a real person (the People register), who owns a model
(the model's owner field), and who sits on the committee that governs it (the MRC
roster). Rights derive from those facts, so entitlements are themselves auditable and
committee-ratifiable. There is no shadow user table.

**3.5 The institution's framework, not the vendor's.** Risk vocabulary, rating bands,
heatmaps, completeness weights, validation questionnaires, document categories,
remediation SLAs, the framework clauses the audit reports against, the classification
banner and legal notice on every PDF, and the standard the audit cites are all
configuration. An adopting institution re-points them at its own framework without
code changes.

---

## 4. The governance skeleton: organisation, people, committees

**4.1 One institution, one org tree.** Company is a singleton (name and logo).
Divisions sit beneath it; Lines of Business beneath Divisions. Everything —
people, committees, models, ML applications, AI systems, products — hangs off that
tree. A header scope selector both filters what is shown and fixes the organisational
placement of anything registered while it is active.

**4.2 People.** A single directory of named individuals, each optionally anchored to
a Division or Line of Business (blank = firm-wide). People become committee chairs
and secretaries, record owners, peer reviewers, remediation owners and RACI assignees.
Their org anchoring determines eligibility to chair or sit on a committee in a given
scope.

**4.3 Roles are committee-granted, not administrator-assigned.** A person's record
carries the roles they hold, from a configurable vocabulary that ships as **owner,
validator, committee, chair, administrator, reader** — each with a written explanation
of what it grants, shown beside the choice at the point of assignment. Roles are
**proposed** in the administration area and take effect only when **ratified at a
meeting**, under a standing agenda item for committee membership (§11.3). What a
person is allowed to be is therefore a committee decision on the record, not a
configuration change somebody made. See §18 for what roles do and do not yet enforce.

**4.4 Model Risk Committees.** A committee is anchored to an org tier — Company,
Division, or Line of Business — and carries:

- a **roster**: chair, secretary, voting members, non-voting members, all drawn from
  People in scope;
- **quorum rules**: requires-chair (default yes), requires-secretary (default yes),
  minimum voting members (default 2);
- a **Terms of Reference** document, uploaded and version-controlled;
- a **frequency** (Monthly / Quarterly / Semi-annual / Annual), which also sets the
  interval at which successor meetings are auto-scheduled.

**4.5 The coverage rule.** When a subject needs a committee, the platform selects the
**most specific active committee that covers it**: Line of Business, then Division,
then Company as backstop. Archived committees never match. Committees are never
deleted — archiving preserves history and any meetings already bound to them.

This is the mechanism that makes committee responsibility a property of the
institution's structure rather than an assignment somebody remembers to make.

---

## 5. The model inventory

**5.1 Registration.** A model is registered with an ID, name, type, owner, and its
Division / Line of Business (fixed by the header scope, which is what binds it to a
committee). On registration the platform **automatically seeds the institution's
validation questions** (see §8), each at *Not Addressed*, and creates the model's four
RACI roles. A model therefore enters the estate with its validation gaps already
declared rather than invisible.

The questionnaire is **copied onto the record, not referenced**. A model keeps the
questions it was actually asked, even after the institution later rewords or extends
its question set — so a review read three years later is read against the standard
that applied at the time.

**5.2 Controlled classification.** Type and vendor are **strict**: a model cannot be
typed as something nobody has defined in the administration area, or name a vendor
nobody has registered. Other reference-backed fields — owner, division — stay open,
because they hold names that predate the lists and rejecting those would block every
edit to an existing record. Which fields are strict is configuration.

**5.3 The model record.** Each model carries structured registers, all event-sourced:

| Area | Contents |
|---|---|
| **Overview** | Description, repository location, codebase, type, short name, methodology and rationale, source module, materiality, complexity, tier and the rationale for each |
| **Governance** | Responsible MRC, RAG rating, owner and role, lifecycle stage, review status, peer reviewer, validation status and date, MRC sign-off meeting and date, next review date, recertification date |
| **Remediation** | Steps with description, owner, priority, due date, status (Open / In Progress / Closed) |
| **Versions** | Version register (version, date, description, author, reference document, lifecycle) plus a change-history register |
| **Weaknesses** | Description and impact |
| **Limitations** | Description, impact, monitoring trigger, compensating control |
| **Assumptions** | Description, impact, monitoring, mitigation |
| **Dependencies** | Declared upstream / downstream edges to other models, cycle-checked |
| **Data sources** | The feeds the model pulls inputs from, drawn from an administered list that classifies each as internal or external and records its sensitivity and whether it may leave the institution |
| **Field lineage** | Provider field → consumer field with types, units and a compatibility note |
| **Fairness and evaluations** | What was *measured*, one row per protected attribute considered and one per evaluation run (§10.2) |
| **RACI** | Role, RACI classification, assigned to, backup, description |
| **Testing** | Evidence-driven: unit, integration and benchmark test results uploaded as documents beside the field each evidences, rather than asserted as flags alone |
| **Documents** | Filed by category, each surfaced in exactly one place (§15.1) |
| **Review** | The review workflow's own registers: stage approvals, the challenge thread, and the sign-off history (§8) |
| **MRC linkage** | Read-only view of every meeting decision and action tagged to this model |
| **Audit** | This model's own complete change history |

**5.4 Retirement is hibernation, and it is ratified.** A model is never deleted.
"Request retire…" raises a sign-off item to the responsible committee; the model
hibernates only when the committee approves. Reactivation follows the same path. A
hibernated model leaves the active estate — and leaves every portfolio and audit
figure derived from it — while its history remains intact and its position in the
chain is preserved under a Hibernated view. A hibernated record is **read-only with
one deliberate exception**: the committee's own two registers stay writable, so the
decision that hibernated it, and any later request to bring it back, are still
recordable against it.

**5.5 A change of owner takes effect immediately and is ratified afterwards.**
Somebody has to answer for the model today. The sign-off request carries both the
previous and the new owner, so the handover is on the record before the committee
meets, and the committee ratifies the appointment.

**5.6 Generated documents are filed, not merely rendered.** A Model Risk Document is
rendered from the inventory *as it stood at the moment of issue* and filed under the
History category. This gives a second time axis alongside the audit trail: the audit
trail records when the institution was told something; the filed document records
what the model looked like when a given statement was issued.

---

## 6. The wider estate: ML Applications, AI Systems, Products

An institution's model estate is no longer only quantitative models, and a register
that forces everything into one shape leaves the interesting fields blank. The
platform keeps **four governed record types plus the client relationship**, sharing
one rating scheme, one committee structure, one audit and one event log — but each
carrying the fields only it can answer.

**6.1 ML Application** — the governed **use** of an off-the-shelf estimator. The
record for "we fitted a gradient-boosting regressor to this problem", where the
estimator is somebody else's and the governable thing is the application: which
estimator and version, why that one rather than a simpler alternative, the use case
and what it is explicitly not for. It carries the same field names as a model wherever
the question is the same, so estate-wide queries count both.

It additionally carries a **training record** in six sections, in the order a fit is
actually performed — *task and target, training data, split and preprocessing and
validation, fit record, performance, reproducibility*. Every enumeration it uses
(learning task, missing-data treatment, categorical encoding, scaling method and the
point at which the scaler was fitted, split and cross-validation method, search
method, determinism, primary metric, naïve baseline) is an administered vocabulary the
institution owns and can extend. Training runs may be **captured automatically from
the producing codebase** rather than typed (§19.1), and the record marks which fields
were captured that way. Each run carries its evidence artefacts — a calibration curve,
a convergence plot, a segment analysis — on the reasoning that a reliability curve
*is* the calibration evidence, where a sentence saying the model is well calibrated is
only an assertion.

Its questionnaire is its own: ten questions written against the failure modes of a
fitted estimator — algorithm choice, training data representativeness, **data
leakage**, out-of-sample performance, benchmarking against a baseline a reviewer would
recognise, overfitting and stability, explainability, drift, and misinterpretation by
a consumer. Not one of the classical nine is answerable in the same terms.

**6.2 AI System** — a system built on a third-party foundation model. It carries what
no model record can answer:

| Field | Why it is a field and not prose |
|---|---|
| **Foundation model, provider, pinned version, version policy** | Whether the underlying model can change under the firm's feet has to be a query, not a paragraph. Version policy runs *Pinned to a named version / Pinned, reviewed on a cycle / Tracks the provider's latest*. |
| **Hosting** | Third-party hosted API / private cloud / on-premise / embedded in a vendor product. |
| **Deployment pattern** | Direct prompting / retrieval-augmented / fine-tuned / **agentic** / **multi-agent**. Several framework clauses bite only on particular values, so "is anything in the estate agentic" is answerable. |
| **Data sent for inference, and the contractual basis** | Ordered by how much it would matter if it leaked: no data leaves the firm / internal non-sensitive / confidential business data / personal data / regulated client data. |
| **Human oversight** | Human makes the decision / reviews before action / reviews after the fact / on request only / fully autonomous. |
| **Guardrails, grounding, output variability, explainability approach** | The controls, and how the system's non-determinism is bounded. |
| **EU AI Act classification and the reasoning** | *Not assessed* is the honest default and is not a class — it is the absence of the assessment, which is itself the finding. |
| **Tools and APIs** | Enumerated for agentic systems: what the agent may call. |

Its questionnaire is again its own, written against the AI risk catalogue —
provenance, grounding, oversight, egress, agent authority.

Beyond those fields, an AI System keeps **four running records** that a model has no
equivalent of, because a model does not change underneath you and does not answer
differently to the same question twice.

**Configuration snapshots.** Each version of the configuration the system has run
under, immutable once taken — which is what makes a snapshot evidence of what the
system *was* rather than a note about it. It covers the twelve fields that decide
reproducibility, and deliberately excludes the governance half: an owner or a review
date changes for reasons that have nothing to do with how the system behaves.

**The variability envelope.** A generative system answers the same input differently
each time; the governance question is how much it moves and whether that was
accepted. Scores from repeated runs go in raw and the envelope is computed from them
— a caller handing over a finished range has already decided the question the
measurement exists to ask. Two refusals are the substance of the control rather than
friction around it: **fewer than twenty runs is refused rather than narrowed**,
because a tight range from three agreeing runs is the most flattering reading of the
least evidence; and an envelope needs a snapshot behind it, because one with no
configuration attached is a number nobody can reproduce. An envelope whose
configuration has since moved is marked **stale**, never deleted — stale is a
finding, a missing envelope is a gap, and the two must not read alike.

**Trigger thresholds.** The bar each of four properties is judged against —
correctness, consistency, robustness, predictability — and the fallback when it
breaks, from *continue and note* to *suspend the system*. The fallback is required:
a threshold with no stated consequence is a number on a screen. Every property is
listed whether or not a bar is set, because a property with no threshold is the gap
worth seeing, and a table of only what was configured would hide precisely that. One
event per property, so "we tightened correctness" stays distinguishable from "we
restated all four".

**Release manifests.** What each release contained, sealed at the time and classified
against the same four-tier change engine the whole estate uses (Administrative,
Bounded, Measurement, Material). Sealed, not saved: a second seal under the same name
is refused, because a manifest that could be revised afterwards is a note about the
release rather than a record of it.

Which **regulatory regimes** apply is derived from where the system is used and what
it does, never ticked. That question has a right answer given those facts, and a
checkbox somebody ticked is an assertion nobody can check.

**6.3 Product** — a live pricing or booking configuration: the point where the estate
meets the business. A product binds one **Calculating Agent** (the pricing platform —
an internal library, a third-party engine) and an **open-ended list of components**.
Each component row names what kind of thing it is — **Model, ML Application or AI
System** — and which record fills it. Several components may share a type: two curve
models is the ordinary case for structured credit, not an error, and a fixed
analytics-plus-market-data pair could not describe a structured product without
inventing a slot for every shape.

A product carries its own limitations, assumptions, remediation, RACI, classification
and risk rating on the same grid as a model, and inherits its responsible committee
from its organisation. Status runs Proposed / Active / Suspended / Retired.

A product deliberately carries **no validation questionnaire of its own**: it
validates through its components, and demanding a second copy of evidence that exists
one link away would score it against a restatement. For the same reason the audit
demands of a product only what only a product can answer — what it *is*, and how its
use is watched.

**6.4 Client** — an external counterparty the institution hands an evidence pack to.
See §16.

**6.5 What this buys.** One rating scheme, one committee route, one completeness
audit and one event log across the whole estate. "How much of what this firm runs is
under governance" is one query rather than three registers with three vocabularies.
The caveat is stated in §12.1 and §24: AI Systems are counted in framework coverage
but are not yet in the ranked completeness findings register.

---

## 7. Risk classification and rating

**7.1 Three structural dimensions.** Every governed record is classified on
**Materiality**, **Complexity** and **Mission Criticality** (historically "Tier",
1–3: Mission critical / Important / Not important). Each carries a required
justification — the owner picks the band, and the framework asks for the reason — plus
an overall rating rationale in the owner's own words.

**7.2 One governed rating.** Mission Criticality selects one of three 3×3 grids; the
(Materiality, Complexity) cell yields a Red / Amber / Green rating. Higher criticality
escalates to Red faster. The default Tier 1 grid, for example:

| Materiality ↓ / Complexity → | Low | Medium | High |
|---|---|---|---|
| **High** | Amber | Red | Red |
| **Medium** | Green | Amber | Red |
| **Low** | Green | Green | Amber |

There is deliberately **no competing composite score**. The one rating the committee
sets and reviews is the record's risk statement.

**7.3 Owner vs table.** Two ratings are shown side by side: the rating the owner has
asserted, and the rating the heatmap computes. Divergence between them is the signal
that the rating needs committee attention. This is a designed disagreement, not a
data-quality defect.

**7.4 Sign-off binds to a cell, not to a record.** An MRC sign-off covers the specific
(materiality, complexity, criticality) cell that was approved. Moving the record to a
different cell ends the cover — it reverts to un-signed-off rather than carrying an
approval that was granted for a different risk position.

**7.5 Risk policy is per-division and committee-ratified.** The bands themselves —
their names, colours, explanations and scores, and the grid that maps them to ratings
— are an administered policy held per division. A policy is **drafted** by an
administrator and **approved** by the MRC; the draft/approved distinction is the gate,
and only an approved policy is in force. The three dimensions are structural; what
each band means is the institution's to define.

The division's policy also carries **the audit's own calibration** for that division
(§12.4) — because that is what its committee already ratifies, and splitting the
audit's basis across two places would leave nobody able to say what a score was
computed against.

**7.6 A second ratified policy: what a review must contain.** Alongside the risk
policy, each division ratifies an **ML review policy**: which of the training-record
fields and which of the review questions are *in use* in that division, and which are
*mandatory*. It lets a division that does not fit neural networks stop being asked
neural-network questions, without any division being able to quietly drop the
questions it finds inconvenient — because the committee ratifies the list. Both
policies run the same lifecycle: **Proposed → Approved → Rejected**, with the most
recently approved version live and a draft driving nothing.

**A division running on an unratified policy is itself a reportable finding** and
appears on the executive view (§14.3).

---

## 8. Validation: the questionnaires and the review workflow

**8.1 The questionnaire is the institution's.** Every record is seeded on registration
with the question set for its kind. The model set ships as the nine classical
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

ML Applications and AI Systems carry their own sets (§6.1, §6.2). All three are
**administered lists**: an adopter under a different regulator, or with its own house
standard, rewords a question, drops what does not apply and adds its own. Each is
answered with a status (*Addressed / Partially Addressed / Not Addressed / Not
Applicable*) and a written rationale. Coverage is counted and displayed, but is
explicitly *coverage*, not a risk score.

**8.2 The review as a seven-stage workflow.** A review runs as a single workflow with
seven ordered stages, each carrying its own state, the reviewer's interim approval,
and who approved it and when:

| # | Stage | Content | Status it sets |
|---|---|---|---|
| 1 | Preliminary documents | The pack the reviewer works from; marked received and read | Documents reviewed |
| 2 | Assumptions | Assumptions register, owner-proposed, reviewer-agreed | Assumptions agreed |
| 3 | The validation questions | Owner's status and rationale; reviewer's verdict and comment | Questions answered |
| 4 | Model weaknesses | Weaknesses register, same pattern | Weaknesses agreed |
| 5 | Limitations of use | Limitations register, same pattern | Limitations agreed |
| 6 | Monitoring approach | Narrative description of how the record will be monitored | Monitoring agreed |
| 7 | Remediation | What the review found outstanding, and what is being done | Remediation agreed |

Assumptions come **before** the questions because the sixth question asks whether the
assumptions are documented and justified: answering it means reading them. Remediation
comes **last, before sign-off**, because the committee should see what the review found
outstanding, and what is being done about it, before it signs anything off.

The review status is set by the work done, not by somebody updating a dropdown.
Interim approval is not a lock: earlier stages stay reopenable — a reviewer who
reaches the limitations and needs to reopen a question must be able to — and reopening
is itself a recorded act.

**8.3 Two-sided questions.** Each question carries an owner side (status, rationale,
evidence) and a **reviewer side**: verdict (*Accepted / Challenged / Not reviewed*),
comment, and a stamped reviewed-by and reviewed-at. A question can be *Addressed* by
its owner and *Challenged* by its reviewer at the same time. Holding that disagreement
is the point.

**8.4 The record of challenge is the deliverable.** Per stage, an append-only thread
between owner and reviewer:

- **No edit, no delete** — not by the author, not for a typo. A correction is a new
  note. The console never offers the affordance.
- **Attributed and stamped** — named identity, role (Owner / Reviewer / Participant,
  *derived* from the signed-in identity against the record's owner and reviewer fields,
  never chosen from a dropdown), and timestamp.
- A note may be marked a **Challenge**, which is Open until a later note answers it.
  Both states are derived; no row is ever edited to carry them, because a challenge
  that could be closed by editing it would not be evidence of anything.
- Challenges are **printed verbatim in the review report**, under the stage they
  arose in — so the report can state "six challenges raised on the nine questions,
  six resolved, two changed a status" rather than leaving a reader to infer rigour
  from a wall of text.
- **An open challenge blocks sign-off.** The console's sign-off control names exactly
  what is blocking it, and the endpoint refuses for exactly the same reasons — a
  reviewer who means to sign off over a challenge has to answer it first, in writing,
  rather than signing past it in silence.

This is the platform's direct answer to "was this model effectively challenged?" —
the documentation answers it on its own, without a person to narrate it.

**8.5 Why this review, and what a new version must confirm.** A review is not only a
calendar event. Valid triggers are *Periodic*, *New version*, *Owner change*, and *MRC
directed*, and the trigger is recorded so a review can be read in context years later.
Before a review begins the owner writes a **scope** — what has changed and what they
want looked at, because a reviewer handed a record and no brief writes the review they
imagine is wanted. Where the trigger is a new version, the owner must additionally
confirm that the three artefacts which go stale together have been brought up to date
and loaded: the documentation, the sensitivities and the test evidence. Otherwise the
reviewer reads last version's write-up against this version's model.

**8.6 Sign-off, and the report the committee receives.** The reviewer signs off with a
final commentary. The sign-off is append-only, gated on every stage being agreed and
no challenge standing open, and it **generates and files the Model Review Report** at
the moment of signing — the same shape as closing a meeting generating and filing its
minutes.

That report is what the MRC receives when it signs off the risk rating. **The
committee does not adjudicate the review**; it approves the rating, and the report is
the evidence in front of it. The report therefore carries the *argument*, not just the
conclusion: both sides of every question, the registers as agreed, the monitoring
narrative, and the record of challenge verbatim under the stage it happened on. It is
filed under a category the committee can table (§11.4), so a meeting reviews the
document the record actually holds rather than a copy of it.

**8.7 Cycles.** Starting a new review **records a new cycle rather than resetting**.
The stage register is append-only: stages agreed before the marker belong to the
review that was already signed off, and the previous cycle stays readable — its
approvals, its notes and its filed report are the history. Progress is reported
forward from the current cycle's marker, so last year's approvals do not flatter this
one (§12.6).

**8.8 Build state.** The workflow is complete: stages, interim approvals, the
reviewer's verdict on every question, the review brief and its trigger checklist, the
append-only challenge record, the sign-off gate, and the generated and filed Model
Review Report. The previous revision of this brief recorded sign-off and the report as
**[NOT BUILT]**; that is no longer the case, and a proposal may now claim the signed
review report.

---

## 9. The model chain, handoffs and field lineage

**9.1 The chain.** Each model declares its upstream and downstream dependencies, or a
producing codebase pushes the whole graph (§19.1). From those declarations the
platform derives a directed, **cycle-checked** graph — the "string of pearls" —
presented in three views: **Chain** (models with edges, drawn producer → consumer),
**Terminal** (models with no downstream consumer, i.e. the estate's actual outputs),
and **Hibernated** (retired models, kept for history). The acyclicity invariant is
enforced at both entry points by one implementation, tested once.

**9.2 Every edge is a governed handoff.** An edge is not merely an arrow. Each
carries:

- a **field lineage table** mapping each provider field to a consumer field, with
  type and units on both sides and a note — the actual data contract between two
  models, and where a unit mismatch or a silent type coercion becomes visible and
  challengeable;
- a **compatibility note**: the plain-language statement of whether the two models fit
  together;
- an **MRC compatibility sign-off**, raised as a `handoff` sign-off item and ratified
  in a meeting. An edge starts *Draft*.

A **handover document** can be generated for any edge.

**9.3 Data lineage.** Separately from the field-level contract, a **pipeline run
manifest** is pushed from the producing repository: the steps, and which runs executed
them. Every step named in a run must exist in the step list — validated at ingest, not
assumed.

**9.4 Why this matters to an examiner.** Model-chain risk — a model consuming another
model's output under assumptions that no longer hold — is normally undocumented
because no artefact naturally owns it. Here the edge is a first-class governed object
with a named owner of the question, a field-level contract, and a committee decision
attached to it.

---

## 10. Operational events, measurement and monitoring

**10.1 Operational events.** Real production failures, with date, what happened, the
remediation, and full RACI attribution — who was operationally responsible, the
accountable owner, the committee consulted, and whether the client and senior
management were informed. A rolling 365-day event count feeds the record's risk view
**and** escalates its completeness severity (§12.3), and events flow up to the
committee as items to be received, with the committee's receipt recorded on the event.

The design point: operational failure is not a separate incident system. It is a
governance input that changes how hard the platform pushes on a record's evidence.

**10.2 What was measured, as distinct from what was declared.** Two registers are held
apart from the descriptive ones, on every model, ML application and AI system:

- **Fairness assessments** — one row per protected attribute or group considered: how
  it was assessed, the metric, what it showed, the date. The attribute is free text on
  purpose: which characteristics are protected is a matter of law and differs by
  jurisdiction. *Not measured* and *no disparity above the threshold* are different
  answers and are not collapsed into a boolean.
- **Evaluations** — one row per evaluation run: kind (*held-out performance /
  benchmark against a baseline / adversarial or red team / LLM-as-a-judge / human
  review / reproducibility check*), what it was evaluated against, the metric, what it
  returned in prose, a verdict, and the date. The verdict may be blank, because an
  exploratory red-team run has findings and no pass mark.

The reasoning is worth stating in a submission. `benchmark_tests: Yes` records that
testing happened and nothing else — not what was tested, against what, what it found,
or when. **A committee cannot challenge a Yes.** Nor can it challenge "we assess for
bias" — only "we measured demographic parity across age bands in July and it held
within five percentage points". Because both registers are carried under one name
across all three record types, *"what has this firm actually measured"* is one query.

**10.3 Ongoing monitoring, in three layers.**

- **The standing approach** — a narrative on each record, agreed as stage 6 of its
  review: how it will be watched once in use, in the owner's and reviewer's own words.
  Deliberately prose rather than a register of metrics and thresholds, because an
  approach is agreed in sentences long before anyone can name the numbers.
- **The trigger on each limitation** — every recorded limitation of use carries the
  monitoring trigger that would show the limit is being breached, and the compensating
  control. This is the operative half: a limitation with no trigger is a disclaimer,
  not a control.
- **The observed record** — monitoring results are filed as **timestamped documents**,
  so each observation is retained as its own dated entry rather than overwriting the
  last. An **Ongoing Monitoring Report** states a record's monitoring position: which
  portfolios it has been exercised against, and the standing position on every
  weakness and limitation recorded for it.

Where the institution has no production portfolios onboarded, the monitoring document
**says so explicitly** rather than going quiet — an absent document and one recording
"nothing yet" are very different things to an assessor. See §24 for what this means
for a claim about ongoing monitoring.

---

## 11. The Model Risk Committee

The committee machinery is where the platform enforces process rather than recording
it.

**11.1 Scheduling.** A meeting is scheduled against a committee with an ID, title,
date and optionally time and location. Scheduling **drains any queued sign-off
requests** for that committee onto the new agenda automatically.

**11.2 Participants and quorum.** The committee roster is carried onto the meeting as
its participants, each with an attendance status (Invited / Attended / Apologies /
Declined), plus any added guests. A live quorum badge shows *met* or *not met* and
what it still needs. **A meeting that is not quorate cannot approve a sign-off and
cannot be closed.** This is enforced, not advised.

**11.3 The standing agenda.** Meetings open with the institution's standing running
order. The shipped order is:

1. **Rollcall and confirmation of quorum** — the meeting may proceed only once quorate.
2. **Sign-off of the previous minutes** — proposed by the chair.
3. **Review of outstanding actions** — every action still open across this committee,
   and ratification of the closures owners have requested. It sits here because the
   first thing a committee does once it has accepted the record is ask what it is
   still owed.
4. **Review of record sign-offs** — the rating approvals queued for this meeting.
5. **Review of analyses** — confirmation to proceed, and any actions arising.
6. **Governance completeness audit** — run and review the audit for the records in
   scope for this committee, and minute the committee's notes on the outcome.
7. **Committee membership and roles** — ratify proposed changes to who sits on this
   committee and the roles they hold (§4.3).
8. **Any Other Business.**

Institution-specific items are added alongside, and the running order itself is the
institution's to edit — **each meeting keeps the copy it was given**, so a change to
the standing order never rewrites a meeting already held. What stays fixed is each
item's kind, which determines the working panel the meeting draws for it. The agenda
can be **finalised for distribution**, which locks it and produces a distribution pack
(ZIP: the agenda PDF plus every uploaded agenda and analysis paper). Unlocking reopens
it, as a recorded act.

**11.4 Sign-off.** Sign-off items come in five kinds and are routed to the responsible
committee automatically:

| Kind | What it ratifies |
|---|---|
| `rag` | A proposed risk rating |
| `retire` | Hibernation of a record |
| `reactivate` | Restoration of a hibernated record |
| `handoff` | The compatibility of a chain edge |
| `owner` | A change of owner (which has already taken effect — §5.5) |

A request is attached immediately to the committee's next scheduled meeting if one
exists, and otherwise **queued and drained onto the agenda the moment such a meeting
is scheduled**. State runs *Pending → Attached → Completed*, or *Rejected* or
*Withdrawn*. If no committee covers the subject, the request is refused and the user
is told to configure one — an uncovered record cannot quietly bypass governance.

Papers are **tabled by reference**: the committee reviews the document the record
actually holds, never a copy of it, so a paper cannot drift from its source between
tabling and reading. The categories a committee may table are configurable and ship as
sensitivity studies, analyses, test results and **review reports** (§8.6).

**Approval carries out the decision.** For a rag item it snaps the rating to the
proposed value and stamps the sign-off date and meeting; for retire/reactivate it
hibernates or restores; for a handoff it records compatibility; for an owner change it
ratifies the appointment. It also writes a sign-off history entry, **auto-generates a
minute**, and marks both the request and the agenda item Completed. Rejection changes
nothing on the subject and records the decision. Approval requires quorum.

Critically: **a proposed rating is proposed, not applied.** The change takes effect
only on committee approval. There is no path by which an owner's assertion becomes
the governed position without the committee.

**11.5 Analysis.** Separately from approvals, the meeting reviews a scope of models,
products and handoffs **pre-filtered to the committee's remit**. Each selected subject
gets an outcome, a discussion note, and any follow-on remediation (with owner and due
date). In-scope subjects' open remediation is printed in the Meeting Pack.

**11.6 Actions and minutes.** Actions carry an owner, target date, status and an
optional record link; an action tagged to a model **surfaces automatically on that
model's MRC linkage tab**, credited to its source meeting. The meeting is the system
of record; the model reflects it. There is no double entry.

**An owner cannot close their own action.** They *request closure*, and the committee
ratifies it under the standing actions item — so the status vocabulary is three-valued:
*Open / Closure requested / Closed*. Minutes are added manually where needed, but
sign-off and standing-item minutes are written automatically as decisions are made, so
most of the record assembles itself.

**11.7 Close, and succession.** *Close meeting* becomes available only once the
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

## 12. The completeness audit

The platform grades its own governance record. This is the engine behind the
Governance Completeness Audit report, the committee's standing audit item, the
executive response view and the client pack's gap section.

**12.1 What it examines.** Every **model, product and ML Application** on the
register, excluding hibernated and retired records — which are out of the estate and
out of every figure, because reporting gaps against records nobody is running is
noise. ML Applications are audited on the same terms as everything else: an estate
half of which is ML, audited on the other half, reports a gap picture that is wrong in
the direction that flatters, with nothing on the page to say so. **AI Systems are not
yet in this register** — they are counted in framework coverage (§13) but do not yet
produce ranked findings. See §24.

**12.2 What counts as a gap.** Four kinds, and the fourth is the one an assessor cares
most about:

- **field gaps** — a required field not recorded;
- **collection gaps** — an empty register, or a partially-completed one (e.g. three
  of nine validation questions still unanswered). Registers where empty is a
  *legitimate steady state* are exempt: an empty remediation list means nothing is
  outstanding and an empty events list means nothing has gone wrong, and scoring
  those would penalise the best-kept records;
- **document gaps** — a required document category with nothing uploaded, or — scored
  higher — a **broken reference**: a document recorded on the register whose file is
  not in the store. The register is a claim; the file store is the fact. A broken
  reference escalates by a factor of 1.15, on the reasoning that an inventory
  overstating its own coverage is a more serious finding than a visible hole, and one
  nobody reading the register alone would catch;
- **rule findings** — a contradiction between answers that are *both present*, which
  no completeness score can see. The shipped rule is **reviewer independence**: a
  record whose peer reviewer is its own owner has both fields filled in and would
  otherwise score as fully governed. It is the first record an external assessor
  pulls, so an audit that cannot raise it reports the estate as better governed than
  it is.

**12.3 How severity is scored.** Each gap's severity is its intrinsic criticality
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
**High** (≥0.60, 60), **Medium** (≥0.35, 90), **Low** (180). The bands are calibrated
against the *escalation* range rather than the raw criticality scale, so that a
high-criticality gap on a routine Tier 2 Green record reads High rather than Critical.
Set too low, every finding on a badly-kept record bands Critical together and the
register stops saying what to do first — which is the one thing an audit reader needs
from it.

**12.4 Calibration is the division's, ratified by its committee.** The acceptable and
conditional thresholds, the untiered weight, the unrated multiplier, the event
pressure and its cap, and the broken-document escalation all sit on the division's
**ratified risk policy** (§7.5), not in code and not in an administrator's hands.

**12.5 Every finding is defensible line by line, and actionable.** Each gap carries
its own factors, not just the product. The register prints
`0.90 × 1.00 × 1.25 × 1.15 × 1.10 = 1.42, Critical` — not an unexplained 1.42. The
scoring module performs no I/O, so the arithmetic an auditor is asked to trust is
unit-testable in isolation from the report that prints it.

Each carries an instruction addressed to a named owner — "Record *next review date* on
the model record", "Upload a document under *Core Documentation*", "Re-upload under
*Test Results*: the record cites a file that is not in the document store and cannot be
produced", "Name a peer reviewer other than the owner, or record why the owner's
review is treated as independent" — plus its SLA. A finding somebody cannot be handed
is an observation, not a finding.

**12.6 The review programme is reported, not scored.** Reviewing an entire estate is a
programme with its own timetable. Scored as completeness it would mark every record
incomplete on the day the workflow shipped and hold it there for months — a new bar
applied backwards, which reads as decay rather than as the backlog it is. The review
is therefore reported in its own section: how many records have a review under way,
how far each has got, how many stages have been agreed, how many are signed off, and
what is standing in the way. *"None started yet"* becomes a plan with a number against
it rather than a failure with a number against it.

**12.7 Weighted completeness.** A record's score is the share of the criticality it
was asked to carry that it actually holds. Unweighted percentages flatter a record
that has filled in its cheap fields and left the expensive ones blank. A record is
reported as **materially incomplete** below the division's acceptable threshold
(default 0.85), and **conditional** below its lower threshold (default 0.60).

**12.8 Findings are never summarised away.** Every gap on every record appears in the
per-record findings, and the counts in the summary reconcile to it. A completeness
audit that quietly truncates its own register is the one document where an omission is
indefensible.

**12.9 The audit basis is configurable** and is printed on the report, so an adopting
institution changes the citation when it re-points the weights at its own framework.

---

## 13. Framework coverage

A section of the completeness audit, and the part an external assessor is handed: one
table per framework, every clause, what evidences it, and **how much of the estate
actually carries that evidence**.

**13.1 The commitment that makes it credible.** A clause is never reported as
evidenced because the platform *can* hold the record. It is evidenced because the
estate *does* — the probe counts records, and a capability nobody has populated reads
as **Not evidenced**. An assessor is owed the second number, not the first.

Ratings are **Evidenced / Partially evidenced / Not evidenced / Outside the platform**.
The last is used honestly: whether risk management is embedded in the firm's
decision-making, and what budget and headcount were allocated, are organisational
facts no system can hold, and saying so is better than a blank cell — a reader meeting
a blank learns nothing, where a reader meeting *"no ratified appetite threshold
exists"* learns the finding.

Where a clause has **no applicable population at all**, it reads Not evidenced with
the population said out loud. "Nothing needed it" is a claim the reader should see and
challenge, not one the report should make silently on the estate's behalf.

The clauses reading Not evidenced are **listed again, on their own, after the tables**.
A reader working only from a forty-row table reads the rows that are green; the point
of the section is the rows that are not.

**13.2 Frameworks mapped.**

| Framework | Treatment |
|---|---|
| **ISO 31000:2018** | Clause by clause, 4 through 6.7. |
| **COSO ERM (2017)** | By principle. |
| **BCBS 239 (2013)** | Data aggregation and lineage. |
| **FINOS AI Governance Framework** | Both catalogues — see §13.3. |
| **EU AI Act** | Each AI System carries its Annex III classification and the reasoning; *Not assessed* is the default and is itself the finding. |

**13.3 The AI framework is carried as two catalogues, deliberately not merged.** The
**risk catalogue** is what the institution is exposed to — hallucination and inaccurate
output, foundation-model versioning, non-determinism, provider availability,
alignment, bias and discrimination, explainability, model overreach, data quality and
drift, multi-agent trust boundaries, information leakage. The **mitigation catalogue**
is the controls it has in place, evidenced by **tagged control documentation on a
dedicated shelf** (§15.2). Keeping them apart means nobody can mistake *"we are
exposed to prompt injection"* for *"here is our prompt-injection control"*, which is
exactly what merging them would invite.

Population rules are applied so the numbers mean something. An AI-specific clause is
scored over **AI Systems only** — counting "is a foundation model version pinned"
across an estate of regression models would report a number that means nothing, and
would drag the row toward zero as the model inventory grows. Clauses about agent
authority are narrowed again to **agentic systems**: scoring "does the agent exceed its
authority" against a direct-prompting summariser would manufacture a gap nobody can
close and nobody should try to. Conversely, **bias is scored across the whole estate**,
not over AI Systems alone — a model that ranks retail applicants raises it exactly as
a generative system does.

**13.4 The mapping is configuration.** The clause list, its citations and its wording
are data; the arithmetic that says "17 of 20 records carry this" does not move. An
adopter re-points the audit at its own framework by editing the clause table.

---

## 14. The executive response model

The completeness audit asks whether each record is complete. This view answers the
question one level up: **of everything the audit and the committee registers already
know, what does a chief risk officer have to do something about?**

**14.1 Four states.** A reader at that level has four available responses, so every
item resolves to one of four. The machine values are frozen — the ERM integration
(§19.2) is written against them — while the words beside them are the institution's
to re-set like every other vocabulary.

| State | Card | The response |
|---|---|---|
| **Escalate** | Breaches | Yours. Take it to the committee. |
| **Act** | Needs you | Chase the named owner. |
| **Monitor** | Worth noting | Nothing today. Note it. |
| **Clear** | With owners | Nothing. |

Only the first two reach the executive. Everything else is with an owner, and the page
says so rather than counting it against the reader.

**14.2 One record, one item.** A record contributes **at most one item — the worst
obligation standing against it**. Without that rule a badly-kept record appears three
times and the count measures how many ways one record is behind rather than how many
records are. Remediation steps and committee actions are the exception: each is a
separate commitment by a named person, so two overdue steps on one record are two
people who have not done what they said they would.

**14.3 The reasons, worst first.** Reviewer is the record's own owner · Evidence cited
but not held · No committee sign-off · Review overdue · Below the acceptable standard
· Findings past their remediation deadline · Review falls due within the horizon ·
Open findings with their owner. Alongside these, at committee and division level:
committee action still open, remediation overdue or due, and **risk policy never
ratified** — a division-level item in its own right, because an unratified policy
belongs to a division rather than to a record.

**14.4 No derived second opinion.** The view derives no finding of its own. Three of
its record-level reasons are an audit gap under another name, and review currency is
read from the same classification the register already shows. A record the register
calls Overdue and this view called something else would be a control failure of its
own. Where a reason comes from an audit gap, **the instruction travels with the gap**,
so the dashboard cannot word a finding differently from the report a committee signed.

The headline is **one sentence, not a score**. A composite index would immediately
raise the question of what it is made of, and the honest answer takes the rest of the
page — the same argument the platform already makes about not deriving a second rating
beside the one the committee sets. The queue is capped; when the cap bites the true
total is still reported and the truncation is declared, because a capped list that says
nothing about the cap reads as *"that is all there is"*.

**14.5 Finding history and trend.** The audit is computed fresh each run and has no
memory of its own, so a scheduled observer records what it saw, daily. That gives three
things: **the age of a finding** — when it first appeared, not merely that it is open
now; a **trend line** over a full governance cycle, so a committee sees direction and
not just position; and **opened-and-closed counts** for a period, retained well past
the longest remediation target. The observer can be turned off by an adopter who does
not want the history; nothing else depends on it.

---

## 15. Reporting: the evidence the platform produces

All generated on demand from live state. PDF rendering uses a LaTeX engine
(`tectonic`) in a shared house style; the classification banner, document author,
legal notice and logo on every page are the institution's configuration.

**15.1 Document control.** Every document category is surfaced in **exactly one
place**, so a document is never listed twice. Where a document belongs is decided by
*where the work that produced it happened*: testing evidence sits beside the test
field it evidences, training artefacts beside the training field, event and
remediation evidence beside the item they evidence, the reviewer's working papers
beside the stage that produced them — and the **signed report apart from all of them**,
because the committee is given the report, not the drafts, and only one of the two is
a document anybody should be tabling.

**15.2 Institutional artefacts.** Separate from records: what the institution
*issues*. Filed per division, plus a company-wide shelf for what belongs to the firm
rather than to one division, plus a dedicated shelf for the **control documentation
that evidences the AI mitigation catalogue** (§13.3) — kept apart because those
documents carry mitigation references and are read by the audit, which no other
artefact is, and mixing them into the general shelf would leave the audit guessing
which of an institution's policies it was entitled to count. Shipped kinds: Terms of
Reference, Presentation, Policy, Guide, Template, Other.

**15.3 File handling.** An upload is metadata on the record plus bytes on disk.
Allowed types are the ordinary office and image formats plus LaTeX source, so a
generated document can be filed alongside its own auditable original. **Uploads are
only ever stored and served back, never executed.** Only a narrow list of types is
served inline in the browser — markup formats, including SVG, are excluded, because an
inline file runs in the application's own origin.

**15.4 The documents themselves.**

| Artefact | Contents |
|---|---|
| **Model Risk Document** | Per record: classification, methodology, governance, the validation questions with evidence, assumptions, limitations, weaknesses, remediation, dependencies, change history, MRC sign-offs, attached documents. Issued per Model, per Product and per ML Application. Filed under History on issue. |
| **Model Review Report** | What the reviewer signed and what the committee receives: both sides of every question, the registers as agreed, the monitoring narrative, and the challenge record verbatim under the stage it arose in. Generated and filed at the moment of sign-off. |
| **Model Risk Report** | The portfolio-level report: risk profile across the estate, the inventory table, then a full dossier per record. |
| **Governance Completeness Audit** | The gap register: every finding, its factors, its severity band, its SLA and its instruction, worst first — plus the framework-coverage tables (§13) and the review-programme section (§12.6). |
| **Meeting Pack** | Per meeting: branding, meeting info, participants, agenda, minutes, actions, and per-record open remediation for every in-scope subject. |
| **Distribution pack (ZIP)** | The finalised agenda PDF plus every uploaded agenda and analysis paper. |
| **Minutes** | Rendered and filed automatically on meeting close. |
| **Handover document** | Per chain edge: the field lineage and compatibility position. |
| **Ongoing Monitoring Report** | What the record has been exercised against, and the standing position on every recorded weakness and limitation of use. |
| **Risk categorisation document** | The division's approved risk policy: bands, definitions and the rating grid. |
| **Product pack (ZIP)** | A product's own document plus the full pack of every component it binds, foldered so the whole product is browsable without unzipping again. |
| **Client pack (ZIP)** | See §16. |
| **User Guide and Integration Guide** | Published as PDFs in the same house style, the user guide additionally as an editable Word document so an institution's own people can mark it up rather than maintaining a diverging second copy. |

An in-app **Audit Reports** tab generates these alongside the coding-rule audit
reports, the test report and the coverage report, each viewable and downloadable, and
split into a governance set and an engineering set so the two audiences are not made
to read each other's evidence.

---

## 16. Clients and client packs

**[PARTIAL — records and pack generation exist; the surrounding workflow is still
maturing.]**

The Clients area treats a client as a point of aggregation: one relationship record
with its own contact org tree (divisions → departments → contacts), linked to the
specific models and products that client relies on, and one self-describing evidence
pack generated on demand — so a client's model-risk due diligence is answered once,
from one place.

A generated pack contains, for every linked model and product: a **freshly rendered**
Model Risk Document and its attached evidence, the completeness audit, recent
completed-meeting minutes, operational-event write-ups, and the committee's Terms of
Reference — with a `CONTENTS.txt` manifest stamping as-of and generated-at, and
stating exactly what was packed **and what was recorded but unavailable**. Because
the PDFs are built at the moment of packing, a pack never carries a stale write-up;
because the manifest declares absences, it never silently omits.

Every generated pack is retained with **both its as-of date and its generation
moment**, so what was sent to whom, when, and what it said at the time, is itself part
of the record.

---

## 17. The evidence architecture

This section is the technical core of any regulatory submission.

**17.1 Event sourcing / CQRS.** The system of record is an append-only `events`
table. Events are grouped into streams keyed by `(aggregate_type, aggregate_id)`.
Within a stream, `stream_seq` is a 1-based, gap-free counter, and a UNIQUE constraint
makes two concurrent appends to the same position impossible. Every screen is a
**projection** — a read model rebuilt from the log. Projections can be dropped and
rebuilt at any time without loss, because they contain no truth of their own.

**17.2 Immutability enforced at the database grant level.** The runtime application
role (`mkm_app`) holds `SELECT` and `INSERT` only. It cannot `UPDATE`, `DELETE` or
`TRUNCATE`. This is not an application convention that a bug could bypass — the
database refuses. Schema migration runs under a separate owner role.

**17.3 Tamper evidence.** Each event carries `event_hash` = SHA-256 over its own
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

**17.4 What every event carries.** Aggregate type and id, sequence, event type,
payload, **actor**, **reason**, UTC timestamp, previous hash and own hash. The
before/after values of every changed field are recoverable, and are displayed
per-field on the Audit Trail.

**17.5 Append-only within the record, not only within the log.** Several registers are
append-only *by domain rule* as well as by storage: the review's challenge thread, its
stage approvals and its sign-offs. A stage approved twice — reopened, re-agreed —
leaves both rows standing. Evidence that can be tidied afterwards is not evidence, and
this is what lets the review report state what was said rather than what survived.

**17.6 What this delivers.**

- The complete history of every record, meeting and decision is preserved.
- Nothing is ever truly deleted — retirement is hibernation, archiving is archiving.
- Any historical state can be reconstructed: what the institution believed about a
  record on any past date, and who told it.
- The audit trail **cannot be edited or cleared from the application**, and
  out-of-band editing is detectable.
- There are two independent time axes: the event log ("when we were told") and the
  filed generated documents and packs ("what we said, at the time we said it").

**17.7 Single sanctioned data path.** All database access goes through one module
(`src/database/`), mechanically enforced (see §20, rule R6). No SQL, driver import or
connection exists anywhere else in the codebase. There is exactly one place where the
event store's guarantees can be reasoned about — and exactly one place an examiner or
internal auditor needs to read to verify them.

---

## 18. Identity, authorship and permissions

**This section must be presented honestly. It remains the platform's weakest area and
an examiner will find it.**

**18.1 What exists today.**

- **Authentication is perimeter-delegated.** The platform has no login. It reads the
  acting user from a trusted request header (`X-Auth-Request-User`) supplied by the
  institution's SSO proxy, and records that identity as the actor on every event.
  This is a legitimate architecture *behind a properly configured proxy*.
- **Known-actor enforcement.** A change must be authored by somebody registered in
  the People directory, matched on name or email. Refusal is an HTTP 403 naming the
  actor and the remedy. The platform's own actor and machine producers (`ingest:*`)
  pass. An empty People list stands the rule down so a fresh install can register its
  first person. Policy is configuration: `protected` (the production estate only — the
  default), `always` (a hardened deployment), or `never` (a documented, temporary
  break-glass). The same check covers document-upload paths, which call their commands
  directly.
- **Roles are data on the People record, granted by the committee.** A person carries
  the roles they hold from a configurable vocabulary, each with a written explanation
  of what it grants. Roles are *proposed* in the administration area and take effect
  only when **ratified at a meeting** under the standing membership item, and the
  ratifying meeting is stamped on the record. Entitlement is therefore itself an
  auditable committee decision. **What roles do not yet do is gate anything** — see
  18.2.
- **Reviewer independence is enforced at the write, on model records.** A model's
  peer reviewer may not be its own owner, and the check runs on *both* fields — a
  model with a distinct reviewer can be put in breach just as easily by moving the
  ownership onto them, and a rule enforced on one side of a pair is not enforced. This
  is the first of the negative controls to be delivered, and it is delivered in the
  defensible order: **only the write that creates the breach is refused**. A record
  already in breach stays editable in every other respect — the audit reports it
  (§12.2), and locking the record would leave its owner unable to correct anything
  else about it. The rule can be stood down for an institution mid-migration whose
  estate cannot yet satisfy it, with the breaches still reported throughout.
  Write-enforcement covers **every record type a review can be signed off on** — a
  model, an ML Application and an AI System alike. It covered models alone until
  2026-09-06, while the audit raised the same finding against all three: the audit was
  right and the write path was not.

**18.2 What does not exist. [NOT BUILT]**

- **Role-based authorisation.** Roles are recorded and ratified, but they are not
  enforced: every authenticated, registered actor can currently register records, edit
  any field, approve MRC sign-offs, ratify risk policy, close meetings and retire
  records. There is a deliberate, documented enforcement seam (`authorize()` in the
  single command dispatcher, which every mutating command already passes through), and
  it currently enforces only the known-actor rule.
- **The remaining segregation-of-duties controls.** An owner cannot approve their own
  model; a validator cannot validate a model they own; an administrator cannot ratify
  the policy they drafted; a chair cannot be sole approver of their own tabled paper.
  Reviewer independence (18.1) is delivered; these are designed and are not.
- **Header verification.** The known-actor rule narrows *who* can author to a
  registered person, but does not verify that the caller **is** that person. Anyone
  who can address the application can send a registered name. Closing that gap
  requires the proxy to authenticate and strip the header — an infrastructure
  decision, not an application one.
- **Machine-actor scoping.** Ingest actors are distinguishable in the trail but are
  not yet restricted to append-only operations.

**18.3 The delivery plan.** Six phases, sequenced so nothing is enforced before it can
be satisfied: **P1** know who is real *(delivered)*; **P2** roles as data on the
People record, assigned by event so entitlements are audited *(delivered, and
strengthened beyond the original design by routing the grant through committee
ratification)*; **P3** authorise in report-only mode for a period of real use, so the
log says exactly what would break; **P4** enforce, with 403s naming the missing role;
**P5** segregation of duties *(reviewer independence delivered ahead of sequence; the
rest outstanding)*; **P6** scope machine actors to append-only.

**18.4 How to present this.** The defensible framing is that the platform makes every
decision attributable and reconstructable *today*; that entitlement is held as
committee-ratified data rather than as an administrator's setting; that one
segregation control is enforced and reported; and that the rest is scoped, sequenced
and enforced at a single architectural choke point rather than scattered across
endpoints. The undefensible framing is any claim that segregation of duties is
generally in place. One control is. The others are not.

**18.5 Open decisions worth naming in a submission** (they will be asked about):
whether the SSO header is trusted in production; how events authored by unknown
actors before known-actor enforcement are surfaced and explained rather than silently
trusted; and whether there is a named, time-boxed, loudly-audited break-glass path for
when the committee cannot convene. (Whether role assignment itself requires MRC
ratification was an open question in the previous revision; it has been answered —
it does.)

---

## 19. Integration: ingest and the ERM feed

Two surfaces, with deliberately opposite privileges and **separate credentials**. One
writes the governance record; one may only read it. A single credential for both would
collapse that distinction.

### 19.1 Ingest — machine-produced evidence in

The platform can act as a collector as well as a console. Producing systems POST
schema-validated artefacts to a token-gated ingest API, against frozen,
language-agnostic JSON Schemas that any stack can code to:

| Artefact | Contents |
|---|---|
| `model_inventory` | Inventory plus the model chain |
| `model_chain` | The dependency graph on its own |
| `data_lineage` | A pipeline run manifest |
| `field_lineage` | Report → section → field registry (BCBS 239 Principle 3) |
| `ml_training_run` | A captured training run for an ML Application (§6.1) |
| `document` | Model-document upload metadata |

Every request is an **envelope**: a provenance block plus the payload. Provenance
carries the source repository, the exact **commit hash**, the producer name and
version, and generation timestamp — and is stamped onto every stored event. The
result is a reproducible link from a governed artefact back to the exact scan of the
exact code revision that produced it.

The envelope is **strict** — unknown top-level keys are rejected, to catch producer
mistakes. Payloads are **permissive** — only structural and identifying keys are
required, so a producer adding descriptive fields never breaks ingestion.

**Cross-reference integrity is validated server-side at ingest**, not left to the
schemas, because it spans artefacts: chain links must resolve to known records,
up/downstream adjacency must be consistent, the graph must be acyclic, every lineage
field's pipeline step must resolve to a step in the current manifest, and every run
must name steps that exist.

For an institution whose models live in code, this is the mechanism by which the
governance record stays synchronised with reality rather than being re-typed.

### 19.2 The ERM feed — governance position out

Model risk does not stop at this platform: it feeds the firm's enterprise risk
management. A versioned, token-gated read API publishes the governance position,
shaped around two named consumers rather than around how the platform happens to store
things — an operational-risk function that needs what has actually failed and which
controls are not holding, and a strategic view that needs how much of the estate meets
the standard its divisions set, and which way that is moving.

**There is no write endpoint at any version.** If the enterprise risk system could
change the governance record, the record would no longer be the thing the committee
signed. Two properties matter to an integrator: every enumerated field carries both a
frozen machine value *and* the institution's label, so renaming a risk vocabulary
never breaks a consumer; and items are returned individually, each carrying the group
it would collapse under, so the ERM can reproduce the console's roll-up or list every
record instead. The path is versioned from the first release rather than from the first
breaking change, because an ERM integration outlives refactors and an adopter cannot
redeploy their ERM because something was renamed.

---

## 20. Controls over the software itself

A model-risk platform is itself a piece of software an examiner may ask about. The
codebase is held to ten mechanically-enforced coding rules, audited by a command
that exits non-zero on any gated finding:

| Rule | Control |
|---|---|
| **R1** | No hardcoded parameters outside `config/` — every threshold, weight and vocabulary item is inspectable configuration, not buried in logic |
| **R2** | No source file longer than 300 lines (400 for tests) |
| **R3** | ≥99% test coverage, verified at each stage and gated |
| **R4** | No logic in `__init__.py` |
| **R5** | Canonical copyright/licence header on every source file, generated from one source of truth |
| **R6** | **Zero tolerance** — no SQL, driver import or connection outside `src/database/` |
| **R7** | Front-end assets confined to `src/static` and `src/templates`; no embedded JavaScript |
| **R8** | No duplicated logic; shared behaviour is extracted, and existing copies are migrated |
| **R9** | Test and verify against a restored backup, never the live database |
| **R10** | Every visual parameter — colour, scale, typeface — comes from one theme configuration, so a generated report and the screen it came from cannot disagree |

Duplication is measured and capped. Test coverage is enforced at ≥99% across roughly
1,700 unit and integration tests, with a separate Playwright end-to-end browser suite.
Unit and end-to-end suites derive their own disposable databases and are guarded so
they cannot reach live data. The audit publishes its findings as a PDF alongside the
governance reports, with the test report, the coverage report and machine-readable
results.

**R1 is worth highlighting in a proposal**: it is the rule that makes "show me your
risk weights" a matter of reading a configuration file rather than auditing source
code — and it is what makes every threshold, band, vocabulary, questionnaire and
framework clause in this document an institutional setting rather than a vendor's
opinion compiled into a binary.

---

## 21. Deployment and operations

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
- **The finding-history observer** runs in-application on a daily cycle (§14.5) and can
  be disabled.
- **Licensing.** The platform is MIT-licensed. Third-party dependencies and their
  licences are enumerated in a maintained manifest. The legal notice on generated
  documents covers the *contents* — the models and calculations described — and is
  the institution's own text, distinct from the software licence.

---

## 22. Configurability — what an adopting institution changes

Everything in this list is configuration, not code. It is the answer to "is this your
framework or ours?"

- **Risk vocabulary and bands** — names, colours, explanations and scores for
  Materiality, Complexity and Mission Criticality, per division, MRC-ratified.
- **The rating grid** — which (materiality, complexity) cell yields which rating in
  each criticality band.
- **The validation questionnaires** — the model set, the ML Application set and the AI
  System set: reword, drop, add.
- **What a review must contain** — which review items are in use and which are
  mandatory, per division, MRC-ratified.
- **Completeness weights** — per-field, per-collection and per-document-category
  criticality; tier weights; rating multipliers; event pressure; staleness steps;
  severity bands; remediation SLAs; exemptions — with the division-level subset
  ratified by its committee.
- **The framework clause tables** — which frameworks the coverage section reports
  against, their clauses, citations and wording.
- **The audit basis citation** printed on the completeness report.
- **The standing agenda** — the running order every meeting is seeded with.
- **Roles** — the vocabulary of what a person may be, and the explanation shown beside
  each.
- **Classification lists** — model types and their binding roles; calculating agents;
  data sources with their sensitivity and egress rules; vendors; codebases and
  repositories; estimators; features; foundation models.
- **Status vocabularies** — lifecycle stage, validation status, impact, priority,
  remediation status, question status, version lifecycle, and every training
  enumeration. Each stores a stable value and displays a label: renaming edits the
  label and moves nothing in the estate, and the stored value is immutable once the
  entry exists, so a live estate is migrated rather than renamed under.
- **Document categories, artefact kinds and their tag taxonomy.**
- **Committee structure, levels, quorum rules and frequencies.**
- **Classification banner, document author, legal notice, logo** and the whole visual
  style of every generated PDF.
- **The known-actor and reviewer-independence enforcement modes**, review horizons and
  retention periods.
- **The command-to-role permission map** (as the role model is delivered).

---

## 23. Regulatory mapping

Indicative mapping of platform capability to common supervisory expectations. **Each
citation should be confirmed against the current text of the relevant standard before
submission — see §24.**

| Expectation | How the platform addresses it |
|---|---|
| **Complete, maintained model inventory** | Event-sourced register covering models, ML applications, AI systems and products under one rating scheme; mandatory classification, org placement and ownership; hibernation rather than deletion; completeness audit that scores and ranks what is missing |
| **Risk-based tiering proportionate to model materiality** | Materiality × Complexity × Mission Criticality with mandatory per-dimension justification; per-division, committee-approved policy; tiering drives audit escalation and review cadence |
| **Independent validation and effective challenge** | Seven-stage review workflow with a distinct reviewer side on every validation question; append-only, attributed challenge record that blocks sign-off while open and is printed verbatim in the generated Model Review Report; reviewer independence enforced at the write and reported by the audit |
| **Documented assumptions and limitations, with monitoring** | Dedicated registers for assumptions, limitations (with monitoring trigger and compensating control) and weaknesses, each an agreed stage of the review; monitoring approach as a review stage; standing monitoring document |
| **Ongoing monitoring and benchmarking** | Benchmarking is a seeded validation question requiring evidence; test evidence is uploaded artefacts; a dedicated evaluations register records what was measured, against what, and what it returned; monitoring results are timestamped documents; operational events feed the rolling risk window |
| **Bias, fairness and consumer outcomes** | A fairness register, one row per attribute considered, recording how it was assessed and what it showed — scored across the whole estate, not only AI systems |
| **AI and third-party foundation models** | A dedicated record type carrying provider, pinned version and version policy, hosting, deployment pattern, inference-data egress and its contractual basis, human oversight, guardrails, grounding and explainability; EU AI Act classification with reasoning; agent tool enumeration; coverage reported against the FINOS risk and mitigation catalogues |
| **Governance, policies and controls; board and committee oversight** | Committee structure anchored to the org tree with automatic coverage resolution; enforced quorum; standing agenda including a completeness-audit item and a membership-ratification item; auto-scheduled successor meetings; committee-ratified risk and review policy; committee-ratified role grants |
| **Segregation of duties** | **[PARTIAL]** — reviewer independence enforced at the write and reported by the audit; the remaining negative controls designed at a single enforcement point but not built (§18) |
| **Change management and versioning** | Version register and change history per record; every change an attributed event with a reason; material version change is a review trigger carrying a documentation-currency checklist |
| **Data quality and lineage (BCBS 239)** | Data quality is a seeded validation question; an administered data-source register carrying each feed's sensitivity and egress rules; field-level provider→consumer lineage on every chain edge; field-lineage and data-lineage ingest artefacts with commit-level provenance |
| **Enterprise risk aggregation** | A versioned, read-only ERM feed shaped for operational-risk and strategic consumers, with frozen machine values beside institution labels |
| **Audit trail and record retention** | Append-only, hash-chained store; insert-only database grants; nothing deletable from the application; append-only domain rules on the challenge and sign-off records; out-of-band tampering detectable |
| **Third-party / vendor model governance** | Strict vendor reference list; records registered irrespective of provenance; calculating-agent bindings on products; foundation-model provider and hosting on AI systems |
| **Framework alignment** | Clause-by-clause coverage tables against ISO 31000, COSO ERM, BCBS 239, the FINOS AI Governance Framework and the EU AI Act, counted over the estate as it actually is |
| **Evidence production on demand** | Model Risk Document, Model Review Report, Model Risk Report, Meeting Pack, minutes, completeness audit, handover documents, monitoring reports, product packs, client packs — all generated from live state with as-of stamping |

---

## 24. Claims requiring verification, and known limitations

**Include this content in internal review before submission. Removing it does not
make the issues go away; a regulator will find them, and finding them stated is a
materially better outcome than finding them concealed.**

### 24.1 Verify before citing

- **"SR 26-2, superseding SR 11-7."** The platform's own vocabulary describes its
  validation questions and its completeness audit basis as
  *"SR 26-2 (superseding SR 11-7) and PRA SS1/23"*. **Confirm this citation against
  the current published supervisory guidance before it appears in a regulatory
  submission**, including the exact designation and the effective date. If the
  designation is wrong or not yet in force, the substance is unaffected — the
  questions and the framework do not change — but the citation must be corrected in
  `config/governance/_completeness_scoring.py` (`AUDIT_BASIS`) and in the question
  seed, since it prints on generated reports.
- **PRA SS1/23** is cited in the same string; confirm applicability to the
  institution and jurisdiction the proposal addresses.
- **The framework clause tables** (§13) carry citations to ISO 31000, COSO ERM,
  BCBS 239, the FINOS AI Governance Framework and the EU AI Act. They are
  configuration and were written against those texts, but confirm clause numbering and
  wording against current editions before a coverage table is put in front of an
  assessor.

### 24.2 Not built — do not claim

- **Role-based authorisation.** Roles are ratified data; they gate nothing (§18.2).
- **Segregation of duties beyond reviewer independence.** One control is enforced,
  and only on model records (§18.1); the owner-cannot-approve, validator-cannot-own,
  drafter-cannot-ratify and chair-as-sole-approver controls are not built at all.
- **AI Systems in the completeness findings register.** They are counted in framework
  coverage but do not yet produce ranked, SLA-bearing findings. A claim of a single
  ranked remediation register across the *whole* estate currently overstates it.
- **Risk treatment options.** A remediation step records what will be done, but not
  which option was chosen — accept, reduce, transfer or avoid — nor the residual risk
  left after it, nor who accepted that residual and until when. The ISO coverage table
  reports this against itself.
- **Organisational context.** Internal and external context, and the scope of the risk
  management activity itself, have no record; the coverage tables read Not evidenced.
- **Framework self-review.** Division policies are ratified but not re-reviewed on a
  cycle, and nothing records a change made to the framework in response to a finding.
- **Escalation of a sign-off to a higher-tier committee** — present in the data model
  and API, no user-interface control.
- **Machine-actor scoping to append-only.**
- **Surfacing of pre-enforcement events authored by unrecognised actors.**

### 24.3 Known weaknesses to disclose

- **The identity header is trusted verbatim.** The platform records whatever
  identity the perimeter supplies. Its integrity therefore depends entirely on the
  SSO proxy authenticating and stripping that header. This is an infrastructure
  control, and the proposal should state which component provides it in the
  institution's deployment.
- **Events authored before known-actor enforcement.** The log is append-only, so
  historical events authored by unregistered identities remain. The proposed
  treatment is to surface them on the audit trail as "unrecognised actor" so they can
  be explained rather than silently trusted. That surfacing is **[NOT BUILT]**.
- **Nothing here detects drift.** The platform holds the governance cycle *around*
  drift — the feeds, the monitoring approach, the review schedule, the evaluations
  register — but does not observe model behaviour in production. Do not present it as
  a monitoring system.
- **Monitoring reports exercise, not exceptions**, wherever the institution has no
  production portfolios onboarded. The generated documents state this in terms; a
  proposal should not claim more than the document does.
- **Test evidence in the audit is a declaration plus an artefact.** The completeness
  audit scores whether testing is declared and whether an evidence pack exists. What a
  test *found* lives in the evaluations register (§10.2), which is populated by people
  rather than derived.
- **PDF generation depends on an external LaTeX engine.** Without `tectonic`
  installed, report endpoints return an error rather than a document. This is an
  operational prerequisite, not a defect, but it belongs in a deployment section.
- **Clients and client packs are in early development.** Records and pack generation
  work; the surrounding workflow is maturing.

### 24.4 Framing note

The strongest case this platform makes is not feature breadth — it is that the
**evidence architecture is structurally sound**: append-only, hash-chained,
insert-only at the grant level, single data path, everything attributed, nothing
deletable, all reports generated from live state. That claim survives scrutiny.

Two supporting claims have strengthened since the previous revision and are now safe
to lead with. The **challenge record is complete end to end** — challenge, gate,
signed report, tabled paper — so "was this model effectively challenged?" is answered
by an artefact rather than by an assurance. And the **audit reports the estate as it
is, not as the platform could hold it**: a clause nobody has populated reads Not
evidenced, and the rows that are not green are listed a second time on their own.
An assessor who tests that claim will find it holds, which is worth more than a
coverage table full of ticks.

The entitlement layer remains the immature part. It is scoped and sequenced, it is
held as committee-ratified data rather than administrator settings, one of its
negative controls is enforced, and the rest is enforced at one architectural choke
point rather than scattered. A proposal that leads with the architecture and the
audit's honesty, and is candid about entitlement, is considerably more credible than
one that blurs them.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
