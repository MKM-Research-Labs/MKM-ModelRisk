# AI & Agentic Governance Module — Implementation Plan

Derived from `AI_Agentic_Governance_Module_Spec_v0.4.docx` §13, re-expressed as executable
steps against this codebase. Written 2026-09-04, baselined on `main` at the state of this
branch.

The spec says *what* and *why*; this says *where*, *in what order*, and *how you know a step
is done*. Where the two disagree about what already exists, this document wins — §2 records
the corrections and why they matter to the estimate.

---

## 1. How to read this

- **Steps are ordered.** A step may start when every step it lists under *Depends on* has
  passed its acceptance check. Steps within a phase that list no dependency are parallel.
- **Every step names its files.** A step that cannot name where its code goes is not yet a
  step; it is a question, and belongs in §7.
- **Acceptance is mechanical wherever it can be.** "A test asserts X" beats "X works".
- **Two gates run on every step, not just at phase ends:** `pytest` green and
  `python -m audit` reading `PASS: 0 gated finding(s)`. A background run that exits 0 with
  empty output is not a pass — read the final line.
- **Config before code.** Anything an adopter could reasonably want different — a threshold,
  a label, a vocabulary, a routing rule — is a `config/` value under R1, not a literal in
  `src/`. This is the constraint the one-way ModelOne fork rests on (spec §4): logic that
  leaks into the fork instead of into config is permanent divergence.

---

## 2. Corrections to the spec's own scope

Two things were checked against the code after v0.4 was written. Both change the estimate.

### 2.1 The review workflow is Models-only — the spec overstates what is shared

Spec §3.9 says the seven-stage review sequence "is shared". That is true of the *configuration*
— `REVIEW_STAGES` in `config/governance/_review.py` is one list, consumed by one implementation
— but not of the *workflow*. Only models have a review:

| Record type | Committee sign-off | Six-stage review |
|---|---|---|
| Model | `api_models_signoff.py` | `api_models_review.py`, `_notes.py`, `_signoff.py` |
| ML Application | `api_ml_application_signoff.py` | **none** |
| AI System | `api_ai_system_signoff.py` | **none** |
| Product, Handoff | `api_product_signoff.py`, `api_handoffs.py` | **none** |

What *is* genuinely shared is the committee routing: `Subject` in `src/web/_signoff_subject.py`
adapts model, product, handoff, ML Application and AI System onto one sign-off path, and
`SUBJECTS` enumerates all five.

So "the reviewer's role is portable" is currently an aspiration for every record type except
Model. Generalising the review is a phase of real work, not the protection of something that
already holds. It is inserted below as **Phase 1R**, and it is a prerequisite for the AI
System review surfaces in Phases 3–5 — building those first would mean building a second
review implementation and then merging two.

**Action:** correct §3.9 in a v0.5 of the spec. Until then this document is the accurate
statement.

### 2.2 `config/governance/_reference.py` is one line from the R2 gate

It is 299 lines; R2 gates non-test source at 300 and the audit walks `src` **and** `config`.
Adding the common question list there trips the gate on the first commit. New config in
Phase 1 goes in new modules, not into `_reference.py`.

Current headroom on the files this plan touches most:

| File | Lines | Headroom to 300 |
|---|---|---|
| `config/governance/_reference.py` | 299 | **1** |
| `src/governance/completeness/framework.py` | 267 | 33 |
| `src/web/_signoff_subject.py` | 198 | 102 |
| `config/governance/_ml.py` | 160 | 140 |
| `config/governance/_review.py` | 159 | 141 |
| `config/governance/_ai.py` | 146 | 154 |

---

## 3. Baseline — what exists at HEAD

Verified by reading the code, not by reading v0.3. Nothing in this table is in a phase below.

| Capability | Status | Where |
|---|---|---|
| AI System record type | **Built** | `src/governance/ai_system/` (commands, projection, `_rules`, `_state`), `config/governance/_ai_system.py`, `api_ai_system.py` |
| AI System fields (foundation model, pinned version, version policy, hosting, deployment pattern, data egress, EU AI Act class, human oversight, guardrails, grounding, output variability) | **Built** | `AI_SYSTEM_FIELD_SPECS`, `config/governance/_ai_system.py:87` |
| ML Application record type, training + review policy | **Built** | `src/governance/ml_application/`, `src/governance/ml_review_policy/`, `api_ml_application.py` |
| Model chain lineage | **Built** | `src/governance/model_chain/` |
| Immutable, hash-chained event log; bi-temporal stamping | **Built** | `src/database/` (`append_event`, `read_stream`, `read_view`) |
| Committee routing, one adapter per record type | **Built** | `src/web/_signoff_subject.py` (`Subject`, `SUBJECTS`) |
| FINOS catalogue as configuration; mitigations evidenced from tagged documents | **Built** | `config/governance/_finos.py`, `_frameworks.py` |
| Completeness audit reading across record types | **Built** | `src/governance/completeness/` (`PROBES`, `_probes_ai.py`, `_gaps.py`) |
| Reviewer independence (reviewer ≠ owner) | **Built** | `src/governance/completeness/_gaps.py:57` |
| Three separate question lists (RQ / MLQ / AIQ) | **Built, unshared** | `_reference.py:61`, `_ml.py:64`, `_ai.py:46` |
| Six-stage review | **Model only** | `src/web/api_models_review.py` |
| Four-tier change classification | **Absent** | — |
| Backtesting / PSI / transition-matrix monitoring | **Absent** | `src/governance/monitoring/` reports position and RAG only |
| Configuration snapshot as a versioned artifact | **Absent** | current values live on the record |
| Variability envelope | **Absent** | — |
| Trajectory scoring | **Absent** | — |
| Common (cross-workflow) question list | **Absent** | — |

---

## 4. Phase plan

### Phase 0 — What remains of the shared core

The bulk of this phase is two builds the spec's v0.3 described as already existing.

#### 0.1 Change-classification engine

- **Build.** The four tiers (Administrative, Bounded, Measurement, Material), the rules that
  classify a proposed change, and the revalidation depth each tier implies per workflow.
- **Where.**
  - `config/governance/_change.py` (new) — tier vocabulary, per-workflow revalidation depth
    map, the trigger conditions. All of it data; no thresholds in `src/`.
  - `src/governance/change/` (new package) — `commands.py`, `projection.py`, `_rules.py`,
    `_state.py`, following the `ai_system/` anatomy exactly.
  - `src/web/api_change.py` (new) — read + propose endpoints.
- **Acceptance.** A `ChangeRecord` event round-trips through `append_event` / `read_view`;
  classifying the same change twice is idempotent; every tier resolves a revalidation depth
  for both workflows; a change against an unknown record 404s rather than creating one.
- **Depends on.** Nothing.

#### 0.2 Mechanically-verifiable-field monitoring library

The largest single item in the phase. Read it as a build.

- **Build.** Backtesting against realised outcomes; distribution and transition-matrix
  monitoring; rank correlation; population stability index.
- **Where.**
  - `config/governance/_monitoring_measures.py` (new) — PSI bands, drift thresholds,
    minimum sample sizes, the RAG mapping for each measure. R1: every number lives here.
  - `src/governance/monitoring/measures/` (new sub-package) — `_distribution.py` (PSI,
    transition matrices), `_outcome.py` (backtesting), `_rank.py` (rank correlation),
    `__init__.py` re-exporting only, per R4.
- **Acceptance.** Each measure has a test with a hand-computed expected value, a
  degenerate-input case (empty, single-class, zero-variance) that returns a stated result
  rather than raising, and a case that crosses a configured band and changes RAG. No
  numeric literal for a threshold anywhere under `src/` — `python -m audit` proves it.
- **Depends on.** Nothing. Parallel with 0.1.
- **Note.** Build it against ML App data first; Part C reuses it unchanged in Phase 4. Do
  not let an AI-specific requirement shape its API.

#### 0.3 Committee routing takes record type and deployment pattern

- **Build.** Extend the routing inputs so record type, and for AI Systems the deployment
  pattern and risk tier, join materiality and mission-criticality in deciding which committee
  sees a record.
- **Where.** `src/web/_signoff_subject.py` (`Subject` gains the routing attributes),
  `config/governance/_mrc.py` (the routing rules as data).
- **Acceptance.** A test per record type asserting the committee chosen for a given
  (materiality, mission-criticality, record type, deployment pattern). No parallel committee
  track appears — `SUBJECTS` is still the single enumeration.
- **Depends on.** Nothing.

#### 0.4 Lineage node types

- **Build.** `node_type` accepts `MODEL`, `ML_APPLICATION`, `AI_SYSTEM`, `FOUNDATION_MODEL`,
  `MCP_SERVER`. An AI System's harness can reference an ML Application as a tool dependency.
- **Where.** `src/governance/model_chain/`, node vocabulary in `config/governance/`.
- **Acceptance.** A chain mixing all five node types builds and renders; the fraud-model
  case from spec §2.1 (ML App called as a tool by an agentic system) is a test fixture;
  a cycle is rejected with a named error.
- **Depends on.** Nothing.

#### 0.5 SR 11-7 / SR 26-2 criteria as a second data set

- **Build.** Populate the existing risk/mitigation mapping engine with the ML Apps validation
  criteria, alongside the FINOS catalogue it already carries.
- **Where.** `config/governance/_frameworks.py` and a new `config/governance/_sr117.py` for
  the criteria themselves.
- **Acceptance.** One engine serves both data sets; a coverage query filtered to SR 11-7
  returns only those clauses; **no second evidencing mechanism appears** — mitigation status
  still resolves from tagged documents (spec §9.4).
- **Depends on.** Nothing.

**Phase 0 exit gate.** `pytest` green · `python -m audit` reads `PASS: 0 gated finding(s)` ·
`coverage report` ≥ 99% · no file in `src/` or `config/` over 300 lines.

---

### Phase 1 — ML Apps wiring and the question library

#### 1.1 The common question list

- **Build.** A `COMMON` question list, authored once, holding what is asked of any
  application of a model: use case and exclusions, explainability to an affected person,
  human oversight, who could be disadvantaged and how you would know, and what would show it
  had stopped working.
- **Where.** `config/governance/_questions_common.py` (**new module — not `_reference.py`,
  which is at 299 of 300 lines**), registered in `REFERENCE_SPECS` with an `id_prefix` of
  `CQ` and displayed under an *AI/ML Apps* grouping above the two specific lists.
- **Acceptance.** The list appears in Admin above the ML and AI lists; its rows carry the
  same `short_label` / `question` shape the other two use; a fresh install seeds it.
- **Depends on.** Nothing.

#### 1.2 Composition at registration

- **Build.** When a record is registered, its questionnaire snapshot is `COMMON` +
  own-scope, in that order, written as one flat collection on the record.
- **Where.** `src/governance/seeding.py` (`seed_items`), called from
  `ml_application/commands.py` and `ai_system/commands.py`.
- **Acceptance.** A newly registered ML Application carries common questions followed by ML
  questions, in order, as its own snapshot. **Nothing downstream changes** — review,
  completeness probes and the sign-off pack read the same collection they read today, and
  their existing tests pass untouched. Editing a common question afterwards does not alter
  any existing record's snapshot.
- **Depends on.** 1.1.

#### 1.3 Remove the now-duplicated questions

- **Build.** Delete Use Case and Explainability from `ML_APPLICATION_QUESTIONS` and
  `AI_SYSTEM_QUESTIONS`; they now come from `COMMON`.
- **Where.** `config/governance/_ml.py:98`, `config/governance/_ai.py:85`.
- **Acceptance.** No question text appears in two lists. A test asserts the three lists are
  disjoint on `short_label`.
- **Depends on.** 1.2. **Must land before any estate is seeded** — records keep the wording
  they were registered with, so a split settled late leaves two populations answering
  differently-worded versions of one question. This is the ordering constraint of the phase.

#### 1.4 Wire ML Apps monitoring to the measures library

- **Build.** The Monitor stage of the ML Apps lifecycle calls the Phase 0.2 library instead
  of recording a prose monitoring approach alone.
- **Where.** `src/governance/monitoring/`, `src/governance/ml_application/`.
- **Acceptance.** An ML Application with outcome data produces a PSI and a backtest result
  on its monitoring report; one without data reads "not evidenced" rather than zero.
- **Depends on.** 0.2.

#### 1.5 Migrate ML Apps change triggers onto the four-tier engine

- **Build.** Replace the existing SR 11-7 / SR 26-2-aligned triggers with the shared engine.
  Full adoption, not alongside (spec §3.5, §6, §12).
- **Where.** `src/governance/ml_application/`, `src/governance/model_inventory/`.
- **Acceptance.** Every existing trigger maps onto exactly one tier, and the mapping is a
  test fixture. Open change records at migration time are classified, not orphaned — write
  the backfill, then rebuild the read models, or the UI shows a stale view.
- **Depends on.** 0.1.
- **Risk.** This is a vocabulary change for every open change record. It is a migration, not
  wiring; treat its estimate accordingly.

**Phase 1 exit gate.** As Phase 0, plus: the three question lists are disjoint, and a
registered record of each type carries a composed questionnaire.

---

### Phase 1R — Generalise the review workflow

*Not in the spec's §13. Inserted here per §2.1: the six-stage review exists for models only,
and Phases 3–5 need it for AI Systems. Building it there instead would produce a second
implementation to be merged later.*

#### 1R.1 Extract the stage machinery

- **Build.** A `ReviewSubject` adapter mirroring the `Subject` pattern that already works —
  stage progression, notes, and stage sign-off written once and adapted per record type.
- **Where.** `src/web/_review_subject.py` (new), factored out of
  `src/web/api_models_review.py`; `api_models_review.py` becomes a thin adapter over it.
- **Acceptance.** The model review behaves identically — its existing tests pass **unchanged**,
  which is the whole proof of the extraction. `api_models_review.py` shrinks.
- **Depends on.** Nothing, but do it before 1R.2.

#### 1R.2 ML Application and AI System reviews

- **Build.** `ML_APPLICATION_REVIEW_SUBJECT` and `AI_SYSTEM_REVIEW_SUBJECT`; thin
  `api_ml_application_review.py` and `api_ai_system_review.py`.
- **Where.** `src/web/`, with the review screen reusing the model review's markup so the
  reviewer meets one screen, not three (see the standing "mirror the existing screen" rule).
- **Acceptance.** A reviewer can take an AI System through all seven stages. The stage
  sequence does not fork — no record type has a stage another lacks, asserted by a test over
  `REVIEW_STAGE_KEYS` for every subject. Independence (reviewer ≠ owner) applies identically.
- **Depends on.** 1R.1.

#### 1R.3 Derive the questions-stage label

- **Build.** `REVIEW_STAGES`'s `questions` stage is labelled "The nine questions", which stops
  being true once questionnaires are composed and differ in length by record type. Derive the
  label from the questionnaire the record actually carries.
- **Where.** `config/governance/_review.py:41` and its consumers
  (`api_models_review.py`, `src/static/js/inventory/review.js`,
  `src/governance/completeness/review_programme.py`,
  `src/governance/model_inventory/review_report.py`).
- **Acceptance.** A record with eleven questions reads "The eleven questions". No count is
  hardcoded in `src/` or in the JS.
- **Depends on.** 1.2, 1R.1.

**Phase 1R exit gate.** As above, plus: model review tests pass without modification.

---

### Phase 2 — AI Systems configuration schema and regime map

**Blocked.** The one decision v0.4 leaves open — the FINOS taxonomy refresh cadence (manual
quarterly review, live query via the FINOS AIGF MCP Server, or a hybrid) — determines how the
configuration layer is built, not merely how it is maintained. Take it before starting, not
during. See §7.

- **Build.** The AI Systems configuration schema and the regulatory regime map (EU AI Act,
  PRA SS1/23, NIST profiles), defined as data against the shared core's config contract.
- **Where.** `config/governance/_ai_regimes.py` (new); schema contract alongside
  `_frameworks.py`.
- **Acceptance.** A regime is added by adding data and nothing else — proven by a test that
  registers a fictional regime purely through config and sees it in the coverage output.
- **Depends on.** 0.5, and the §7 decision.

---

### Phase 3 — Design & Instrument · Establish Baseline (Concepts 1–4)

#### 3.1 Configuration snapshot as a versioned artifact

- **Build.** Model pin, output schema, sampling parameters and instruction hierarchy captured
  as one versioned, immutable artifact. Partly present today as *current-value* fields on the
  AI System record (`pinned_version`, `version_policy` exist; sampling parameters do not), so
  this turns current values into a version history rather than creating the fields.
- **Where.** `src/governance/ai_system/` (new snapshot commands + projection),
  `config/governance/_ai_system.py` for the added sampling fields.
- **Acceptance.** Two snapshots of the same system are individually retrievable and diffable;
  a snapshot is immutable once written; the record's current values and its latest snapshot
  agree.
- **Depends on.** Phase 2.

#### 3.2 Variability envelope

- **Build.** N repeated runs under the pinned configuration, stored as percentile-based limits.
- **Where.** `src/governance/ai_system/`, with N, the percentiles and the minimum run count in
  `config/governance/_ai_baseline.py` (new).
- **Acceptance.** An envelope is bound to a `config_version` and invalidated when the
  configuration changes; too few runs is a stated refusal, not a silent narrow envelope.
- **Depends on.** 3.1.

#### 3.3 Expert-grounded benchmark, and the judge as a governed model

- **Build.** Dataset, rubric and judge. The judge gets **its own AI System record** and a
  lineage edge (Phase 0.4) to every model whose evaluation it feeds; a change to it is a
  Measurement-class change under the Phase 0.1 engine.
- **Where.** `src/governance/ai_system/`, `src/governance/model_chain/`,
  `config/governance/_assessments.py` (the existing `LLM-as-a-judge` assessment kind gains a
  reference to the judge's record rather than naming it in prose).
- **Acceptance.** Changing the judge surfaces in the affected-artifacts list of every
  dependent model without a separate query. The existing completeness evidence rule
  (`framework.py:159`) still reads a recorded judge evaluation as testing evidence — that
  behaviour must not regress.
- **Depends on.** 0.1, 0.4, 3.1.

---

### Phase 4 — Operate & Measure · Escalate (Concepts 5–8)

#### 4.1 Anchored Continuous Evaluation for free-form fields
- **Where.** `src/governance/ai_system/`; rubric and scoring parameters in config.
- **Depends on.** 3.3.

#### 4.2 Mechanically-verifiable fields reuse the Phase 0.2 library
- **Acceptance.** No second implementation appears. A test asserts the AI path and the ML
  path call the same functions.
- **Depends on.** 0.2.

#### 4.3 Trajectory scoring (graph-edit distance) for agentic systems
- **Acceptance.** Applies only where `deployment_pattern` is in the agentic set
  (`Agentic (tool-using)`, `Multi-agent`) — derived from the field, never from a second
  stored label (spec §2).
- **Depends on.** 0.4.

#### 4.4 Trigger register, thresholds per property
- **Build.** A threshold **per property per model** — correctness, consistency, robustness,
  predictability set independently (spec §9.4), with materiality and mission-criticality
  informing the starting point for each rather than fixing all four.
- **Acceptance.** Four independent thresholds are storable and independently editable; a
  test asserts that setting one does not move the others.
- **Depends on.** 3.2.

#### 4.5 Failure-mode register
- **Build.** Entries identified by a FINOS risk/mitigation pair, carrying trigger and
  fallback state. Covers Moody's operational failure modes and the FINOS agentic security
  cluster (tool chain manipulation, MCP server compromise, agent state persistence poisoning,
  credential harvesting).
- **Acceptance.** **The register has no `mitigation_status` column.** Whether a mitigation is
  evidenced resolves at read time from tagged documents, exactly as the FINOS coverage view
  resolves it now. A test asserts the field does not exist — this is the single easiest thing
  in the plan to reintroduce by accident, and two registers that disagree are worse than one.
- **Depends on.** 0.5, 4.4.

---

### Phase 5 — Revalidate (Concept 9) and the standing risk register

#### 5.1 Immutable release manifest, four-tier classification applied
- **Acceptance.** A FINOS taxonomy version bump classifies as Measurement against the mapping
  engine. **Depends on.** 0.1, 3.1.

#### 5.2 Standing risk register
- **Build.** Bias (RI-16), IP and copyright (RI-23), reputational risk (RI-20), and the deeper
  supply-chain risks (RI-7, RI-8, RI-26), outside the five-phase lifecycle, reviewed at every
  Material revalidation and at onboarding.
- **Acceptance.** AI Systems only — it does not appear on an ML Application (spec §7).
  Visibility is identical across ModelRisk and ModelOne: no entry is muted or filtered per
  deployment, asserted by a test that runs the register under both configurations and
  compares the row sets.
- **Depends on.** 0.5.

---

### Phase 6 — Coverage reporting across both workflows

- **Build.** One coverage report filtered primarily on **record type**.
- **Where.** `src/governance/completeness/`, `src/web/api_audit_reports/`.
- **Acceptance.** A single report counts models, ML Applications and AI Systems, filters by
  record type, and produces an exam-ready answer to "what is in MRM scope and what is
  governed outside it". No `model_class` field is introduced to make this work — the record
  type is the filter.
- **Depends on.** Phases 1–5.

---

## 5. Cross-cutting constraints

| Rule | What it means here |
|---|---|
| **R1** | Every threshold, band, label and routing rule in `config/`. The one-way fork makes this structural, not stylistic (spec §4). |
| **R2** | 300 lines, `src` and `config` both. `_reference.py` has 1 line of headroom — see §2.2. Split along the seam the code already has, not at the line count. |
| **R6** | Zero tolerance: no SQL, driver import or connection outside `src/database/`. Use `append_event`, `read_stream`, `read_view`. |
| **R9** | Test against a restored backup. `scripts/restore_scratch.sh` then `scripts/dev_app.sh` on 5016. Never 5015. |
| **R10** | Any colour or typeface goes through `config/theme.py`. |
| **P1** | Authorship is gated against a protected DB: a write must be authored by somebody in Admin → People. A 403 saying the actor is not registered is this rule, not a bug. |

**Backfills.** Any step that backfills through domain commands from a script must call the
relevant `rebuild_*_view()` afterwards, or the read models stay stale and the UI shows a
correct database through a wrong view. This applies to 1.3 and 1.5 in particular.

**UI verification.** Tests do not prove a screen. For anything visible — the Admin question
grouping (1.1), the review screens (1R.2), the registers (4.5, 5.2) — restore the scratch DB,
serve on 5016, and look at it. Restart `dev_app.sh` after any change under `src/` or
`config/`; `kill -HUP` does not pick up changed Python.

---

## 6. Risks

| Risk | Handling |
|---|---|
| The monitoring library (0.2) is scoped as wiring because v0.3 said it existed | §2 and §3 state it as a build. Estimate it as the largest item in Phase 0. |
| Question split (1.3) lands after an estate is seeded | Hard ordering constraint stated in 1.3: records keep the wording they were registered with. |
| A second review implementation grows for AI Systems | Phase 1R precedes Phases 3–5 deliberately. |
| `mitigation_status` reappears on the failure-mode register | 4.5 asserts its absence in a test. |
| A `model_class` field gets reintroduced for convenience in reporting | 6 asserts the record type is the filter. |
| Logic leaks into ModelOne instead of config | Add each deployment-varying parameter to the audit as it is built, so the boundary is checked per commit (spec §4). |

---

## 7. Open decision

**FINOS taxonomy refresh cadence** — manual quarterly review, live query via the FINOS AIGF
MCP Server, or a hybrid. No default assumed. It determines how the configuration layer is
built, so it blocks Phase 2 rather than merely shaping its maintenance. Everything in Phase 0,
Phase 1 and Phase 1R proceeds without it.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
