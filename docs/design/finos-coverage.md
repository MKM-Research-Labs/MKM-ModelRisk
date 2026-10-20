# FINOS AI Governance Framework — coverage and gaps

**Status:** Section 5 BUILT on this branch, gate green. Section 6 not started.
**Superseded in part (2026-10-20):** the FINOS shelf (§3, Step 2) was withdrawn from
Documents → Artefacts. With it went the 21 mitigation rows it evidenced; the
mitigation catalogue now lists only the two the register evidences (AIR-PREV-005,
AIR-DET-015). Read the shelf sections below as history.
**Date:** 2026-08-25
**Source:** `docs/finos/FINOS AI Governance Framework_.pdf` — the single-page export
of the AIR governance site, 201pp
**Area:** completeness audit / framework coverage / a new record type
**Driver:** Moody's. They deliver ML-generated solutions *to banks*, and the whole
model-governance push is "do what the banks do".

---

## 1. Why this framework and not another

FINOS AIGF is a member-contributed catalogue, and the members are the banks — Morgan
Stanley among the contributors. That provenance is the point. Short of an ISO there is
no higher bar available for AI governance in financial services, and for a vendor
selling into banks a bank-authored framework is worth more than a standards-body one
anyway: the buyer recognises their own institution's work in it.

So the sentence we want to be able to say is:

> *We have implemented the FINOS approach that the member banks contributed.*

This document is about earning it. The catalogue is **46 entries**: 23 risks
(11 Operational, 9 Security, 3 Regulatory and Compliance) and 23 mitigations
(15 Preventative, 8 Detective). Section 4 walks all 46 against what the platform
actually holds.

### 1.1 How to word the claim

The framework has no conformity scheme, so "certified" is not available and would be
the wrong register in any case. The right register is the one
`config/governance/_frameworks.py` already establishes in `COVERAGE_BASIS`, and it is
*stronger* than a compliance claim because it is checkable:

> This section makes no compliance claim. It states, clause by clause, what the
> platform holds that evidences the clause and how much of the estate actually
> carries it.

Applied to FINOS that becomes: *the platform carries the record that evidences N of
the catalogue's 46 entries, and here is the table, generated from the estate rather
than asserted.* An assessor who is handed a generated table with honest `Not
evidenced` rows trusts the `Evidenced` rows. That is the whole trade, and it is why
section 5 starts by adding the table before adding any capability to it.

### 1.2 The one claim that is already true

**The platform is not itself an AI system.** No `openai`, `anthropic`, `langchain`,
`transformers` or `huggingface` anywhere in the tree — no inference, no prompts, no
embeddings, no vector store. Most of the Security catalogue does not bite on
MKM-ModelRisk as a product, and that is worth stating plainly rather than leaving an
assessor to wonder.

One row does bite on us, and we should say so before it is found: **AIR-PREV-012
(Role-Based Access Control for AI Data)**. Any `X-Auth-Request-User` string becomes an
auditable actor. The authorship gate (permissions P1) narrows it to people in Admin →
People against a protected database, but the header is still trusted verbatim.

---

## 2. The two catalogues stay separate

ISO 31000, COSO and BCBS 239 are clause lists, and the coverage table flattens each
into one sequence of rows. FINOS is not one list. It is a **risk** catalogue and a
**mitigation** catalogue, they are different kinds of statement, and they are
evidenced differently:

| | What it is | How the platform evidences it |
|---|---|---|
| **Risks** (23) | Exposures a deployer carries. AIR-OP-004 is true of every LLM in the estate whether or not anybody has written it down | **From the record.** A probe counts the estate — does the register hold the AI systems, are they rated, owned, reviewed, and are the risk's own attributes captured |
| **Mitigations** (23) | Controls the institution runs. AIR-PREV-005 is a thing a firm *does*, largely outside this platform | **From a filed document.** The firm's own description of how it implements the control, uploaded with a brief description, tagged with the mitigations it covers |

Reported as two tables under one framework heading, never merged. Merging them would
put "we are exposed to prompt injection" and "here is our prompt-injection control" in
the same column, and the reader could no longer tell an exposure from a response to
one.

## 3. Mitigation evidence is a document, not a control register

The platform does not run the AI firewall, the DLP sweep or the tool-chain
sanitiser, and a register that asked an adopter to re-key twenty-three controls as
structured rows would be asking them to describe their control environment in our
schema. What an assessor actually wants against AIR-PREV-017 is *the firm's document
that describes its AI firewall arrangements*, dated and attributable.

So the mitigation half is evidenced the way this platform already evidences
everything else it does not itself perform: **an uploaded file with a brief
description**, exactly as the Testing evidence and the division artefacts work today.

Not a file per risk. A risk is not a thing you file a document against — it is an
exposure the record either captures or does not. Files attach to the mitigation side
only.

### 3.1 The shape

`src/web/api_artefacts.py` already files a document on a shelf with a `kind` and a
`description`, event-sourced and attributed. The addition is a **FINOS shelf**
alongside the divisions and the company-wide shelf, holding documents that each carry
**one or more mitigation references**.

One document may cover many mitigations, and usually will:

```
FINOS shelf
  finos-mitigations-2026.pdf    tags: PREV-002, PREV-005, PREV-010, DET-011, …
  agent-controls-appendix.pdf   tags: PREV-018, PREV-019, PREV-022
```

A firm with a single strategy paper files one document tagged against everything it
covers; a firm whose control documentation is already split files several. The
coverage table reads the same either way — **one row per mitigation, evidenced by
whichever document names it** — so the table's granularity does not depend on how the
adopter happens to organise their paperwork.

The tag has a precedent to copy rather than invent. `add_document` already carries
`model_types`, documented as "a list of labels… orthogonal to `category`", with a
`clean_model_types` normaliser. A mitigation-reference list is that same shape, and
the second use is the point at which the normaliser should be generalised rather than
copied — this repo has been bitten by the third copy before.

### 3.2 What this deliberately does not give

A filed document evidences that the firm has *described* a control. It does not carry
an owner, a last-tested date or an effectiveness judgement, and the coverage table
must not imply otherwise: the row says "evidenced by `agent-controls-appendix.pdf`,
filed 2026-08-25", not "control operating effectively".

That distinction is the correct one for this platform rather than a shortfall in it.
MKM-ModelRisk is the governance record; it does not plug into the systems it governs,
so it cannot observe a control operating and should not print a claim it cannot see.
Documentation is what governance evidences. A firm that files one paper covering
twenty-three mitigations has said something an assessor can read and challenge, and
naming the document and its date in every evidenced row is enough for them to do so.

One consequence to accept openly: ISO 6.5.2 ("selection of risk treatment options")
stays `absent`. It was going to be closed by a control register, and a document shelf
does not close it.

---

## 4. The catalogue, entry by entry

Outcomes use the existing vocabulary: **Evidenced**, **Partial**, **Absent**,
**Outside the platform**. "Partial" is used where we hold part of what the entry asks
for and the note says which part is missing.

### 4.1 Risk catalogue — Operational (11)

| Entry | Outcome | What we hold, or what is missing |
|---|---|---|
| OP-018 Model Overreach / Expanded Use | Counted | Assumptions, limitations and weaknesses recorded — where the bound on a record's use is written down and can be challenged |
| OP-019 Data Quality and Drift | Counted | Review scheduled and not overdue, with the feeds and the monitoring approach recorded. This is the *governance* cycle around drift; nothing detects drift, which the platform does not see |
| OP-017 Lack of Explainability | Partial | One review question on the ML questionnaire. No technique recorded, no per-decision explanation |
| OP-005 Foundation Model Versioning | Absent | `version` and `estimator_version` are free text. Nothing records a pinned foundation-model version, a provider change notification, or a deprecation date |
| OP-006 Non-Deterministic Behaviour | Absent | The audit assumes a deterministic artefact throughout. A seed is recorded for *training*; nothing describes inference-time decoding |
| OP-004 Hallucination and Inaccurate Outputs | Absent | `benchmark_tests` is Yes/No — we record that testing exists, never what it found |
| OP-016 Bias and Discrimination | Absent | "bias" and "fairness" appear **zero times** in `config/` and `src/`. No protected-attribute register, no subgroup performance, no fair-lending attestation |
| OP-020 Reputational Risk | Absent | The three risk dimensions are structural. No conduct or customer-facing exposure dimension |
| OP-007 Availability of Foundational Model | Absent | No availability, SLA or provider-concentration record |
| OP-014 Inadequate System Alignment | Absent | No agentic or generative concept exists |
| OP-028 Multi-Agent Trust Boundary Violations | Absent | As above |

**OP-016 is the row to look at twice.** It is not only a FINOS gap. Bias is an
SR 26-2 and fair-lending question about the *classical* ML estate we already claim to
cover, and the COSO 11 probe (`analysis`) passes on tier/materiality/complexity while
the substance goes unasked. This is the one gap in this document that is a defect in
shipped scope rather than an absence of unshipped scope.

### 4.2 Risk catalogue — Security (9)

| Entry | Outcome |
|---|---|
| SEC-002 Information Leaked to Vector Store | Absent |
| SEC-008 Tampering With the Foundational Model | Absent |
| SEC-009 Data Poisoning | Absent |
| SEC-010 Prompt Injection | Absent |
| SEC-024 Agent Action Authorization Bypass | Absent |
| SEC-025 Tool Chain Manipulation and Injection | Absent |
| SEC-026 MCP Server Supply Chain Compromise | Absent |
| SEC-027 Agent State Persistence Poisoning | Absent |
| SEC-029 Agent-Mediated Credential Discovery and Harvesting | Absent |

Nine of nine, and every one of them for the same reason: these are exposures of
generative and agentic systems, and no such system can be registered. They close as a
block when the AI System record exists (5.3) — its deployment pattern, its egress
class and its tool list are what makes each of these rows answerable — not one field
at a time.

SEC-008 additionally needs supplier substance: `vendor` is currently a name in an
admin list with no due-diligence record, no contract reference and no model card.

### 4.3 Risk catalogue — Regulatory and Compliance (3)

| Entry | Outcome | What we hold, or what is missing |
|---|---|---|
| RC-022 Regulatory Compliance and Oversight | Counted | Our strongest row by some distance: the MRC route, the attributed append-only log, sign-off history, the review programme and the completeness audit itself |
| RC-001 Information Leaked To Hosted Model | Absent | `VALID_DATA_SOURCE_KINDS` is `("Internal", "External")` and that is the entire vocabulary. No sensitivity classification, no egress flag, no residency |
| RC-023 Intellectual Property and Copyright | Absent | Nothing, anywhere |

Adjacent and worth carrying in the same work: **the EU AI Act appears zero times in the
tree.** FINOS cites Articles 12 (record-keeping), 26 (deployer obligations) and 72
(post-market monitoring) directly, and Moody's customers are deployers. No high-risk
classification field exists.

### 4.4 Mitigation catalogue — Preventative (15)

Every row here is evidenced by a tagged document on the FINOS shelf (§3). The outcome
below is what the row reads **today**, with nothing filed; the note says what the
platform contributes *beyond* the filed document, where it contributes anything.

| Entry | Outcome | Note |
|---|---|---|
| PREV-005 System Acceptance Testing | **Evidenced** | The only one the platform evidences from the record itself: three test flags plus the Testing document categories, filed against the record |
| PREV-006 Data Quality & Classification/Sensitivity | Partial | `data_sources` exists; the classification half does not (5.4) |
| PREV-007 Legal and Contractual Frameworks | Partial | `ARTEFACT_KINDS` carries Policy and Terms of Reference; no contract, no due diligence, no attestation |
| PREV-010 AI Model Version Pinning | Absent | The pinned version belongs on the AI System record, not only in a document (5.3) |
| PREV-002 Data Filtering From External Knowledge Bases | Absent | Document only |
| PREV-003 User/App/Model Firewalling/Filtering | Absent | Document only |
| PREV-008 QoS and DDoS Prevention for AI Systems | Absent | Document only |
| PREV-012 Role-Based Access Control for AI Data | Absent | Document only — and see 1.2, this one also bites on us |
| PREV-014 Encryption of AI Data at Rest | Absent | Document only |
| PREV-017 AI Firewall Implementation and Management | Absent | Document only |
| PREV-018 Agent Authority Least Privilege Framework | Absent | Document, plus the AI System's tool list |
| PREV-019 Tool Chain Validation and Sanitization | Absent | Document, plus the AI System's tool list |
| PREV-020 MCP Server Security Governance | Absent | Document, plus the AI System's tool list |
| PREV-022 Multi-Agent Isolation and Segmentation | Absent | Document, plus the AI System's deployment pattern |
| PREV-023 Agentic System Credential Protection Framework | Absent | Document only |

### 4.5 Mitigation catalogue — Detective (8)

| Entry | Outcome | Note |
|---|---|---|
| DET-011 Human Feedback Loop for AI Systems | Partial | The challenge thread is attributed, append-only human feedback — but on the *governance record*, not on the system's outputs. Claiming this one whole would be the flattering reading `framework.py` was written to refuse |
| DET-004 AI System Observability | Partial | `operational_failure_events` records what went wrong after the fact. No runtime telemetry |
| DET-021 Agent Decision Audit and Explainability | Partial | We have exactly the append-only, attributed log this asks for — over *governance* events. The mechanism transfers; the subject does not exist yet |
| DET-001 AI Data Leakage Prevention and Detection | Absent | Document only |
| DET-009 Alerting and Denial of Wallet / Spend Monitoring | Absent | Document only |
| DET-013 Citations and Source Traceability | Absent | Document only |
| DET-015 LLM-as-a-Judge Automated Evaluation | Absent | Document, plus the evaluation record (5.5) |
| DET-016 Preserving Source Data Access Controls | Absent | Document only |

### 4.6 Where that leaves us

Three of the risk rows and one of the mitigation rows are **counted** rather than
declared: their outcome comes from the estate on the day the report runs, and a
better-kept register moves them. The rest are declared, and the table below is the
assessment as at the date of this document.

| | Evidenced | Partial | Absent |
|---|---|---|---|
| **Risks — Operational (11)** | 1 | 2 | 8 |
| **Risks — Security (9)** | 0 | 0 | 9 |
| **Risks — Regulatory (3)** | 1 | 0 | 2 |
| **Risk catalogue (23)** | **2** | **2** | **19** |
| **Mitigations — Preventative (15)** | 1 | 2 | 12 |
| **Mitigations — Detective (8)** | 0 | 3 | 5 |
| **Mitigation catalogue (23)** | **1** | **5** | **17** |

**What it actually reported, run against a restored copy of the estate** on
2026-08-25 with one control document filed and tagged against two mitigations:

| | Evidenced | Partial | Absent |
|---|---|---|---|
| Risk catalogue (23) | 3 | 1 | 19 |
| Mitigation catalogue (23) | 3 | 0 | 20 |

The risk catalogue reads one better than the assessment because the estate is
well kept: all three counted rows clear the 90% bar. That is the table working as
intended — it reports the register, not the capability.

The absences are concentrated rather than scattered: **seventeen mitigation rows
move as an adopter files their control documentation**, which is now a shelf and a
tag rather than a feature. The risk catalogue's nineteen turn on one missing record
type.

---

## 5. The work — built

*What follows is the plan as written, with a note under each step recording what
actually happened. Two steps cost less than expected and two cost more.*

**One piece of work, one merge — not a sequence of shippable steps.** The first time
anybody sees the FINOS table it should already have documents behind it; a report
section that reads 3 of 46 with an empty shelf beneath it is not a milestone, it is a
half-built feature shown to a customer. The steps below are ordered by dependency, and
the dependency is real: nothing can be tagged `AIR-PREV-005` until the catalogue exists
as data.

### Step 1 — the catalogue as config

`config/governance/_finos.py`, a new module: all 46 entries as
`(ref, title, probe, note)`, in the shape `_frameworks.py` already uses, plus the
FINOS-specific wording that qualifies it.

**Its own module, and this is not optional.** `_frameworks.py` is 272 lines against
R2's 300-line gate. Forty-six entries with notes is roughly 150 lines. Adding them in
place breaks the gate and puts a third file on the audit's known-red list.

`FRAMEWORK_COVERAGE` then gains **two** entries, not one:

```python
(FINOS_RISKS, FINOS_RISK_CATALOGUE),          # "FINOS AIGF — Risk catalogue"
(FINOS_MITIGATIONS, FINOS_MITIGATION_CATALOGUE),
```

This is where the earlier draft of this document was wrong. It said the coverage tuple
would have to grow a catalogue dimension to keep the two apart. It does not: the
report already renders one subsection per entry in `FRAMEWORK_COVERAGE`, so two
entries give two tables, two tallies and correct grouping in the Not-evidenced list,
with no structural change at all. Two names, not a nested structure.

### Step 2 — the FINOS shelf

`_shelves()` in `src/web/api_artefacts.py` returns `[COMPANY_WIDE_SHELF, *divisions]`.
It gains a FINOS shelf constant. Storage, upload, download, delete, listing and the
event trail all work unchanged — the shelf is an aggregate id, and that is the whole
mechanism.

Decide here whether the shelf takes `ARTEFACT_KINDS` as-is or its own small vocabulary.
Leaning as-is: Policy and Guide already fit, and a kind list per shelf is a
generalisation nothing else needs yet.

**Built,** kinds as-is. One thing the plan missed: `_platformTiles()` renders a
division risk-policy tile for any shelf that is not the company-wide one, so the
FINOS shelf would have grown a "FINOS Risk Policy" tile pointing at a division that
does not exist. Guarded.

### Step 3 — the mitigation tag

`add_document` already carries `model_types` — "a list of labels… orthogonal to
`category`" — normalised by `clean_model_types`, which is a generic list normaliser
wearing one caller's name.

Generalise it (`clean_tags`, with `clean_model_types` as the one-line caller, or a
rename across both sites) and add `finos_refs` alongside. **This is the second use, so
it is the moment to generalise rather than copy** — a third copy is how this repo has
been bitten before.

Validation is shape-only, as the precedent sets: an unknown reference is not rejected,
because rejecting one would mean a catalogue edit could invalidate a filed document.

**Built.** `clean_model_types` became `clean_tags`, with both call sites moved and the
existing test renamed with it.

### Step 4 — probes and evidence plumbing

Two small changes in `src/governance/completeness/framework.py`, and they are the only
places the design touches existing behaviour:

1. **`coverage()` needs the filed documents.** Its signature is
   `(rows, models, as_of, ratified)` — the estate, and nothing else. Mitigation probes
   read the FINOS shelf. One new parameter, threaded through `framework_section` from
   the single call site at `report.py:263`.
2. **A probe must be able to name its evidence.** Probes return `(met, total)` and
   `_measured` prints `"{met} of {total}. {note}"`. A mitigation row printing "1 of 1"
   is nonsense — it should print the document and its filing date. Let a probe return
   an optional evidence string and have `_measured` prefer it.

Then one mitigation probe: evidenced when some document on the shelf names this
reference, and the evidence string is that document's name and date.

The risk catalogue needs no new probes at all. Its entries are `absent` or
`institution` today, apart from the three that reuse probes the platform already has.

**Built,** both changes as described, plus one the plan did not foresee: the artefacts
aggregate id was a private `_AGG` string in the API, and the audit now reads the same
stream. It has one home in `src/governance/documents.py` beside the documents
aggregate, for the same reason that one does — a second spelling of an aggregate id
reads as an empty shelf rather than as a bug.

### Step 5 — report section and UI

The report section falls out of step 1 with no code change. The UI does not:

- **Documents tab** (`src/static/js/gov_docs.js`): the new shelf appears on its own,
  but the upload form needs a reference selector, and the tiles need to show tags.
  That file is 381 lines and R2 reports web files over 300 — this makes it worse.
  Extract the artefacts panel while adding to it rather than after.
- The tag selector needs the catalogue over HTTP. Cheapest is to serve the 23
  mitigation references from the artefacts endpoint that already returns `kinds`.

Per CLAUDE.md §4: many UI surfaces here are hand-curated rather than spec-driven, so
verify against a restored scratch DB on 5016 rather than assuming the panel picks the
shelf up.

**One thing neither the plan nor the tests would have caught.** The coverage tables
size their reference column to hold the longest citation on one line — its own comment
says a wrapped clause number reads as two clauses. That column was sized for `5.4.3`;
`AIR-PREV-023` wrapped to `AIR-PREV-` over `023` in the compiled PDF, and no test looks
at a PDF. The clause and not-evidenced column weights were rebalanced and the report
recompiled twice to confirm it, since the first widening was still too narrow. The
framework-name column is allowed to wrap: a name over two lines still reads as one
name, where a wrapped reference reads as two references.

**Built.** The artefacts panel moved to `src/static/js/gov_artefacts.js` (235 lines)
with the `load()` / `shell()` / `bind()` interface `gov_vendor_docs.js` already uses;
`gov_docs.js` dropped from 381 to 248. Verified end to end against a restored copy of
the estate on 5016: the shelf lists, the picker offers all 23 references with their
titles as tooltips, ticking two and uploading files the document, the tile reads
"Evidences: AIR-PREV-017, AIR-DET-001", and the coverage table moves those two rows
from Not evidenced to a citation naming the document and its date.

The new `<script>` tag needed a full restart before it was served — the template
caching trap in CLAUDE.md §4, which cost a confused minute exactly as documented.

### Tests

`tests/governance/test_framework_coverage.py` and `test_bcbs239_coverage.py` are the
precedent — a new framework gets its own file. Cover: both catalogues appear and stay
separate; an untagged shelf leaves every mitigation `Not evidenced`; one document
tagged with three references moves exactly three rows; the evidence string names the
document; a reference not in the catalogue is stored but moves nothing.

Test files are gated at 400 lines. Run `python -m audit`, not just `pytest` — the gate
is 2 findings at HEAD and this work must not make it 3.

**Built:** `tests/governance/test_finos_coverage.py` (13 tests) and
`tests/web/test_artefacts_api.py` (5). The existing invariant test in
`test_framework_coverage.py` caught the new probe table on the first run, which is
what it is there for; it was extended rather than worked around. Audit gate back at
2 findings — the two pre-existing over-long files, neither of them touched here.

### Rough size

Steps 1–4 are a day, and most of it is writing 46 honest notes. Step 5 is the
uncertain one, because it is UI in a hand-curated panel that is already over the
reporting threshold.

---

## 6. Not in this piece of work

The four items below came out of the same analysis and are each their own decision.
None of them blocks section 5, and section 5 does not commit you to any of them.

### 6.1 An AI System record type

Sibling to ML Application, and built the same way: **the governance half uses the same
field names a model uses**, so all thirteen clause probes in `framework.py` count it
with no change at all. That is the lesson `_ml_application.py` already documents, and
it is why this is a smaller piece of work than it sounds.

The AI half is new: provider, hosted vs on-premise, foundation model and its *pinned*
version, deployment pattern (direct / RAG / fine-tuned / agentic), data egress
classification, human-oversight mode, and — where agentic — the tools the system may
call. Its own questionnaire, seeded from its own admin list, exactly as the ML
Application has one.

This reverses a scope decision written into two files as deliberate
(`config/governance/_ml.py` lines 65–67, `docs/design/mlmodel.md` line 17). It should
be taken as a decision, not slipped in. **It is the only item here that moves the risk
catalogue**, and it moves nineteen rows of it.

### 6.2 Classification on `data_sources`, and a fairness block

Two small additions that pay off well beyond FINOS: sensitivity and egress on a data
source (RC-001, PREV-006), and protected attributes plus subgroup performance on
models and ML Applications (OP-016, and the SR 26-2 substance noted in 4.1).

### 6.3 An evaluation record

Shaped like `training_runs`: eval set, metric, result, red-team or judge outcome. This
is what turns `benchmark_tests: Yes` into evidence, and it carries OP-004, DET-015 and
part of OP-006.

### 6.4 Close our own PREV-012 exposure

The trusted identity header. Already known, already documented; this framework gives it
a citation and a reason to schedule it.

---

## 7. Sequencing against the Moody's conversation

Section 5 shipped whole is the demonstrable half: *"the audit reports our position
against the FINOS catalogue, risk by risk and mitigation by mitigation, generated from
the estate — and here is the shelf where your control documentation goes."* An adopter
files their papers and watches seventeen mitigation rows turn. That is a live
demonstration rather than a claim, and it is a day or two of work.

6.1 changes what the product **is** — from a model-risk register that FINOS mostly
does not apply to, into one that governs the AI estate a bank's AI governance
committee is actually being asked about. It is the one that earns the sentence in
section 1, and it is the larger decision.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
