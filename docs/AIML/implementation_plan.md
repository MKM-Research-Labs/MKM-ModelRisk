# AI & Agentic Governance Module — Implementation Plan

Derived from `AI_Agentic_Governance_Module_Spec_v0.5.docx` §13, re-expressed as executable
steps against this codebase. Written 2026-09-04, baselined on `main`.

The spec says *what* and *why*; this says *where*, *in what order*, and *how you know a step
is done*. Where the two disagree about what already exists, this document wins — §2 records
the corrections.

---

## 1. How to read this

Every step below has the same five parts:

| Part | What it is |
|---|---|
| **Goal** | One sentence. If it needs two, it is two steps. |
| **Steps** | Ordered sub-steps, lettered. Config first, then domain, then API, then UI, then tests — that order is not decoration, it is R1 (a threshold that reaches `src/` first rarely comes back out). |
| **Shape** | The record or event, where a step introduces one. Illustrative, not a schema. |
| **Verify** | Named test cases, and the UI surfaces to look at. A step with no named test is not ready to start. |
| **Done when** | The single mechanical check that closes the step. |

**Ordering.** A step may start when everything under its *Depends on* has closed. Steps
listing no dependency inside a phase are parallel.

**Two gates run continuously**, not just at phase ends: `pytest` green, and `python -m audit`
reading `PASS: 0 gated finding(s)`. Read that final line — a background run that exits 0 with
empty output is the shell's exit code, not the gate's.

**The domain anatomy is fixed.** Every aggregate in this codebase is four modules, and new
ones follow it exactly rather than inventing a shape:

| Module | Contains | Example |
|---|---|---|
| `_state.py` | `initial_state()`, `apply(state, event_type, payload)`, `record_data(state)` — pure, no I/O | `src/governance/ai_system/_state.py` |
| `_rules.py` | `decide_*(...)` returning `(event_type, payload)` — pure, raises on invalid | `src/governance/ai_system/_rules.py` |
| `commands.py` | `_load()` via `read_stream`, `_record()` via `append_event` with `expected_version`, then one public function per command | `src/governance/ai_system/commands.py` |
| `projection.py` | `rebuild_<x>_view()` over `read_all`, plus `get_<x>()` / `list_<x>s()` via `read_view` | `src/governance/ai_system/projection.py` |

`__init__.py` re-exports only (R4). No SQL or driver import outside `src/database/` (R6).

**Database changes are enumerated in §13** — which migration each step needs, which need
none, the new event types, and the backfills. Read it before starting any step that stores
something new.

---

## 2. Corrections to the spec's own scope

### 2.1 The review workflow is Models-only

Spec v0.4 §3.9 said the seven-stage review "already holds and needs protecting rather than
building". It does not. Three things *are* shared — the stage list in
`config/governance/_review.py`, the committee sign-off routing via `Subject` in
`src/web/_signoff_subject.py`, and the independence rule in
`src/governance/completeness/_gaps.py:57`. The review workflow is not:

| Record type | Sign-off | Seven-stage review | Review screen |
|---|---|---|---|
| Model | `api_models_signoff.py` | `api_models_review.py`, `_notes.py`, `_signoff.py` | `static/js/inventory/review.js` |
| ML Application | `api_ml_application_signoff.py` | **none** | **none** |
| AI System | `api_ai_system_signoff.py` | **none** | **none** |
| Product, Handoff | `api_product_signoff.py`, `api_handoffs.py` | **none** | **none** |

**Resolved.** Spec v0.5 corrects §3.9, records the decision in its §12, and carries Phase 1R
in its §13 — spec and plan now agree. v0.4 and earlier still carry the overstatement.

### 2.2 `config/governance/_reference.py` has one line of headroom

299 lines against R2's 300, and the audit walks `config` as well as `src`. New config in
Phase 1 goes in new modules. Current headroom on the files this plan touches most:

| File | Lines | Headroom |
|---|---|---|
| `config/governance/_reference.py` | 299 | **1** |
| `src/governance/completeness/framework.py` | 267 | 33 |
| `src/web/_signoff_subject.py` | 198 | 102 |
| `config/governance/_ml.py` | 160 | 140 |
| `config/governance/_review.py` | 159 | 141 |
| `config/governance/_ai.py` | 146 | 154 |

---

## 3. Baseline — what exists at HEAD

| Capability | Status | Where |
|---|---|---|
| AI System record type | **Built** | `src/governance/ai_system/`, `config/governance/_ai_system.py`, `api_ai_system.py`, `static/js/aisystem/detail_core.js` |
| AI System fields (foundation model, pinned version, version policy, hosting, deployment pattern, data egress, EU AI Act class, human oversight, guardrails, grounding, output variability) | **Built** | `AI_SYSTEM_FIELD_SPECS`, `_ai_system.py:87` |
| ML Application record type, training + review policy | **Built** | `src/governance/ml_application/`, `ml_review_policy/`, `static/js/mlapp/detail_core.js` |
| Model chain lineage | **Built** | `src/governance/model_chain/`, `static/js/chain.js` |
| Event log, hash-chained, bi-temporal | **Built** | `src/database/` — `append_event`, `read_stream`, `read_all`, `read_view`, `replace_view` |
| Committee routing, one adapter per record type | **Built** | `src/web/_signoff_subject.py` — `Subject`, `SUBJECTS` (five subjects) |
| FINOS catalogue as config; mitigations evidenced from tagged documents | **Built** | `config/governance/_finos.py`, `_frameworks.py` |
| Completeness audit across record types | **Built** | `src/governance/completeness/` — `PROBES`, `_probes_ai.py`, `_gaps.py` |
| Copy-at-registration questionnaires | **Built** | `src/governance/seeding.py`, `commands._ai_questions()` |
| Three separate question lists (RQ / MLQ / AIQ) | **Built, unshared** | `_reference.py:61`, `_ml.py:64`, `_ai.py:46` |
| Seven-stage review | **Model only** | see §2.1 |
| Four-tier change classification | **Absent** | — |
| Backtesting / PSI / transition matrices / rank correlation | **Absent** | `src/governance/monitoring/` reports position and RAG only |
| Configuration snapshot as versioned artifact | **Absent** | current values only, on the record |
| Variability envelope | **Absent** | — |
| Trajectory scoring | **Absent** | — |
| Common (cross-workflow) question list | **Absent** | — |

---

## 4. Phase 0 — What remains of the shared core

### 0.1 Change-classification engine

**Goal.** Classify any proposed change into one of four tiers and resolve the revalidation
depth that tier implies for the workflow the subject belongs to.

**Steps.**

a. `config/governance/_change.py` (new). `CHANGE_CLASSES = ("Administrative", "Bounded",
   "Measurement", "Material")`; `REVALIDATION_DEPTH` keyed by `(change_class, workflow)`;
   `CHANGE_TRIGGERS` as data — which field or artifact moving implies which tier. Every
   tier name, depth and trigger is a config value; none appears as a literal in `src/`.
b. `src/governance/change/_state.py`. `ChangeState` carrying subject, class, rationale,
   affected artifacts, superseded flag; `apply()` over `ChangeProposed`, `ChangeClassified`,
   `ChangeSuperseded`; `record_data()` for the read model.
c. `src/governance/change/_rules.py`. `decide_propose`, `decide_classify`,
   `decide_supersede`. Classification is a pure function of (subject fields before, after,
   `CHANGE_TRIGGERS`) — the same inputs always give the same tier.
d. `src/governance/change/commands.py`. `AGGREGATE_TYPE = "Change"`; `_load` / `_record` per
   the anatomy above; `propose_change()`, `classify_change()`, `supersede_change()`, each
   taking `actor` and `reason` and passing `expected_version`.
e. `src/governance/change/projection.py`. `rebuild_change_view()`, `get_change()`,
   `list_changes_for(subject_type, subject_id)`.
f. `src/web/api_change.py` (new) — propose, classify, list-for-subject. Register the
   blueprint in `src/web/app.py` beside the others.
g. Surface the open changes on each record's detail screen (`inventory/detail_core.js`,
   `mlapp/detail_core.js`, `aisystem/detail_core.js`).
h. **DB.** `src/database/migrations/0014_change_view.sql` creating `change_view` on the
   standard shape (§13.3), plus an entry in `_REBUILDERS` (`src/web/_startup.py:62`) so the
   view reconciles at startup. The three new event types go on the existing event store —
   no DDL for those.

**Shape.**

```
ChangeRecord
    change_id: str
    subject_type: str            # MODEL | ML_APPLICATION | AI_SYSTEM
    subject_id: str
    change_class: str            # ADMINISTRATIVE | BOUNDED | MEASUREMENT | MATERIAL
    revalidation_depth: str      # resolved from config, per class per workflow
    rationale: str
    affected_artifacts: list[str]
    superseded: bool
```

**Verify.**
- `test_classify_is_deterministic` — same before/after pair, same tier, twice.
- `test_every_class_resolves_a_depth_for_both_workflows` — the 4x2 matrix is total.
- `test_propose_then_classify_round_trips` — through `append_event` and back via
  `read_view`.
- `test_stale_version_conflicts` — a second write on a stale `expected_version` raises.
- `test_change_against_unknown_subject_404s` — and creates no aggregate.
- Look at: a model detail screen showing an open change and its tier.

**Done when.** The 4x2 depth matrix test passes and `python -m audit` finds no hardcoded
tier name or depth string under `src/`.

**Depends on.** Nothing.

---

### 0.2 Mechanically-verifiable-field monitoring library

**Goal.** One implementation of the statistical measures, usable by both workflows. This is
the largest item in the phase — v0.3 called it existing; it does not exist.

**Steps.**

a. `config/governance/_monitoring_measures.py` (new). `PSI_BANDS` (the boundaries and the
   RAG each maps to), `MIN_SAMPLE` per measure, `BACKTEST_METRICS` by field type
   (classification vs regression — the estate has both), `RANK_CORR_METHOD`,
   `TRANSITION_TOLERANCE`. R1: every number here.
b. `src/governance/monitoring/measures/_distribution.py` (new). `psi(expected, actual,
   bins)`, `transition_matrix(previous, current)`, `stability(matrix)`.
c. `src/governance/monitoring/measures/_outcome.py` (new). `backtest(predicted, realised,
   field_type)` dispatching to the metric `BACKTEST_METRICS` names for that type. Do not
   hardcode AUC — half the estate is regression and has RMSE / MAE / R².
d. `src/governance/monitoring/measures/_rank.py` (new). `rank_correlation(a, b)`.
e. `src/governance/monitoring/measures/__init__.py` — re-exports only (R4).
f. A single `rag_for(measure, value)` resolving band to RAG from config, so no caller
   reimplements the mapping.

**Verify.**
- One hand-computed expected value per measure, from a fixture small enough to check by eye.
- `test_psi_of_identical_distributions_is_zero`.
- Degenerate inputs, each with a *stated* return rather than an exception: empty series,
  single-class, zero-variance, fewer rows than `MIN_SAMPLE`.
- `test_crossing_a_band_changes_rag` — one value either side of a configured boundary.
- `test_no_threshold_literals_in_src` — or rely on the audit's R1 check to say the same.

**Done when.** Every measure has a hand-computed test and a degenerate-input test, and the
audit reports no hardcoded threshold.

**Depends on.** Nothing. Parallel with 0.1.

**Note.** Build it against ML App data. Part C reuses it unchanged in 4.2; do not let an
AI-specific need shape the signatures now.

---

### 0.3 Committee routing takes record type and deployment pattern

**Goal.** Record type — and for AI Systems, deployment pattern and tier — join materiality
and mission-criticality as routing inputs, without a parallel committee track appearing.

**Steps.**

a. `config/governance/_mrc.py`. `ROUTING_RULES` as ordered data: a predicate over
   `(record_type, materiality, mission_criticality, deployment_pattern, tier)` to a
   committee. Ordered, first match wins, with a stated default.
b. `Subject` in `src/web/_signoff_subject.py` gains the attributes the resolver reads.
   102 lines of headroom, so this stays in place.
c. A resolver in `src/governance/mrc/` reading the rules from config.
d. MRC agenda screens (`static/js/mrc/`) show which committee a record routed to and why.

**Verify.**
- Table-driven: one case per record type, plus an agentic AI System that routes differently
  from a direct-prompting one.
- `test_routing_changes_from_config_alone` — edit the rules in the fixture, routing moves,
  no `src/` change. This is the R1 proof.
- `test_subjects_still_enumerates_five` — no sixth track appeared.

**Done when.** The table-driven test covers every record type and the config-only test passes.

**Depends on.** Nothing.

---

### 0.4 Lineage node types

**Goal.** Lineage carries all five node kinds, and an AI System can depend on an ML
Application as a tool.

**Steps.**

a. Node-type vocabulary into config: `MODEL`, `ML_APPLICATION`, `AI_SYSTEM`,
   `FOUNDATION_MODEL`, `MCP_SERVER`.
b. `src/governance/model_chain/_rules.py` accepts them; `_state.py` stores them.
c. Cycle detection rejects with a named error rather than recursing.
d. `static/js/chain.js` and `graph_wire.js` render each kind distinguishably — colours from
   `config/theme.py` only (R10).

**Verify.**
- `test_chain_mixing_all_five_node_types_builds`.
- `test_ml_app_as_tool_of_agentic_system` — the spec §2.1 fraud-model case, as a fixture.
- `test_cycle_rejected_by_name`.
- Look at: a rendered chain containing a foundation model and an MCP server.

**Done when.** The five-type chain renders and the fraud-model fixture passes.

**Depends on.** Nothing.

---

### 0.5 SR 11-7 / SR 26-2 criteria as a second data set

**Goal.** The existing mapping engine serves two taxonomies. One engine, two data sets.

**Steps.**

a. `config/governance/_sr117.py` (new) — the validation criteria as clauses, shaped like the
   FINOS entries in `_finos.py`.
b. Register it in `_frameworks.py` alongside FINOS.
c. Coverage queries take a framework filter.
d. The framework picker in the audit-report screens gains the new set.

**Verify.**
- `test_sr117_filter_returns_only_sr_clauses`.
- `test_evidence_resolver_is_shared` — assert both frameworks resolve mitigation status
  through the *same* function. This is what stops a second evidencing mechanism appearing.

**Done when.** Both frameworks report coverage through one code path.

**Depends on.** Nothing.

**Phase 0 exit gate.** `pytest` green · `python -m audit` → `PASS: 0 gated finding(s)` ·
`coverage report` ≥ 99% · nothing in `src/` or `config/` over 300 lines.

---

## 5. Phase 1 — ML Apps wiring and the question library

### 1.1 The common question list

**Goal.** The questions asked of any application of a model, authored once.

**Steps.**

a. `config/governance/_questions_common.py` (**new module — not `_reference.py`, which has
   one line of headroom**). `COMMON_QUESTION_LIST = "common_questions"`; `COMMON_QUESTIONS`
   as a tuple of `{"short_label", "question"}`, the same shape the other two lists use; a
   spec entry with `id_prefix = "CQ"` and `display = "short_label"`.
b. Register it through the aggregator in `config/governance/__init__.py` so `REFERENCE_SPECS`
   picks it up without editing `_reference.py`.
c. Admin: `static/js/reference.js` groups the three lists under an **AI/ML Apps** heading,
   common first, ML and AI beneath.
d. First-run seeding creates it, as the other lists are seeded.

**Content** (from the overlap analysis — these are the questions asked of both today, or
that should be): use case and exclusions; explainability to an affected person; human
oversight; who could be disadvantaged and how you would know; what would show it had
stopped working.

**Verify.**
- `test_common_list_seeds_on_a_fresh_database`.
- `test_common_questions_match_the_shared_shape` — same keys as MLQ and AIQ.
- Look at: the Admin reference screen showing the three lists in the new grouping.

**Done when.** The list seeds and renders in its group.

**Depends on.** Nothing.

---

### 1.2 Composition at registration

**Goal.** A record's questionnaire snapshot is `COMMON` + own-scope, written as one flat
collection, so nothing downstream learns it came from two sources.

**Steps.**

a. `src/governance/seeding.py` gains a composition helper: common questions first, then the
   record type's own.
b. `ml_application/commands.py` and `ai_system/commands.py` call it. Both already have the
   fallback logic to follow — `commands._ai_questions()` reads the recorded list and falls
   back to the shipped set; composition slots in there.
c. Order is fixed and part of the contract: common first.

**Verify.**
- `test_registered_ml_app_carries_common_then_ml_questions` — asserting order, not just
  membership.
- `test_existing_downstream_tests_unchanged` — review, completeness and sign-off pack tests
  must pass **without modification**. That is the proof nothing downstream noticed.
- `test_editing_a_common_question_does_not_rewrite_an_existing_record`.

**Done when.** A newly registered record of each type carries a composed questionnaire and
no existing test needed changing.

**Depends on.** 1.1.

---

### 1.3 Remove the now-duplicated questions

**Goal.** No question text lives in two lists.

**Steps.**

a. Delete Use Case and Explainability from `ML_APPLICATION_QUESTIONS` (`_ml.py:98`) and
   `AI_SYSTEM_QUESTIONS` (`_ai.py:85`).
b. Update the module docstrings in `_ml.py` and `_ai.py`, both of which currently argue for
   full separation — the argument is still right for the type-specific questions and now
   needs to say so precisely.
c. Note in the release note that records registered earlier keep their own wording.

**Verify.**
- `test_the_three_lists_are_disjoint_on_short_label`.
- `test_a_record_registered_before_the_split_keeps_its_wording`.

**Done when.** The disjointness test passes.

**Depends on.** 1.2. **Ordering constraint:** this must land before any estate is seeded.
Records keep the questionnaire they were registered with — correct behaviour, since a review
answers the question it was actually asked — so a late split leaves two populations answering
differently-worded versions of one question, permanently.

---

### 1.4 Wire ML Apps monitoring to the measures library

**Goal.** The Monitor stage reports measured values, not only a prose approach.

**Steps.**

a. `src/governance/monitoring/report.py` calls `measures` for the record's
   mechanically-verifiable fields.
b. An ML Application with no outcome data reads **"not evidenced"**, not zero — a zero PSI
   and an absent PSI are different claims.
c. `static/js/mlapp/detail_core.js` monitoring tab shows the measures and their RAG.

**Verify.**
- `test_ml_app_with_outcomes_reports_psi_and_backtest`.
- `test_ml_app_without_outcomes_reads_not_evidenced`.
- Look at: the monitoring tab, and a generated Ongoing Monitoring Report PDF.

**Done when.** Both tests pass and the report renders the measures.

**Depends on.** 0.2.

---

### 1.5 Migrate ML Apps change triggers onto the four-tier engine

**Goal.** Full adoption, replacing the existing triggers rather than running alongside them
(spec §3.5, §6, §12).

**Steps.**

a. Map every existing trigger onto exactly one tier; the mapping is a test fixture, not a
   comment.
b. Write the backfill for change records already open, classifying each.
c. **Call `rebuild_ml_application_view()` and `rebuild_inventory_view()` afterwards.** A
   domain-command backfill run from a script leaves the read models stale, and the UI then
   shows a correct database through a wrong view.
d. Rehearse the whole migration against a restored scratch DB on 5016 (R9) before it goes
   near anything else.

**Verify.**
- `test_every_legacy_trigger_maps_to_exactly_one_tier`.
- `test_backfill_leaves_no_unclassified_open_change`.
- Look at: the change list on an ML Application detail screen after the backfill.

**Done when.** No open change record is unclassified and the views are rebuilt.

**Depends on.** 0.1.

**Risk.** A vocabulary change for every open change record. Estimate it as a migration.

**Phase 1 exit gate.** As Phase 0, plus: the three lists disjoint, and each record type
registering with a composed questionnaire.

---

## 6. Phase 1R — Generalise the review workflow

*Added to the spec in v0.5 (§13, phase 1R) after this plan surfaced it. The seven-stage
review exists for models only (§2.1), and Phases 3–5 need it for AI Systems — building it
there instead would produce a second implementation to be merged later.*

### 1R.1 Extract the stage machinery

**Goal.** One implementation of stage progression, per-stage notes and per-stage sign-off,
adapted per record type — the shape `Subject` already proves works for committee routing.

**Steps.**

a. `src/web/_review_subject.py` (new). A `ReviewSubject` mirroring `Subject`: the record
   getter, the stage-state reader and writer, the notes collection, the sign-off command,
   the view rebuild, and the id keyword. `REVIEW_SUBJECTS` enumerates them, as `SUBJECTS`
   does.
b. Move the stage logic out of `api_models_review.py`, `api_models_review_notes.py` and
   `api_models_review_signoff.py` into it. `_STAGE_BY_KEY` (`api_models_review.py:48`) moves
   with it.
c. `MODEL_REVIEW_SUBJECT` becomes the first adapter, and the three model APIs become thin
   routing over it.
d. Extract the shared half of `static/js/inventory/review.js` into a review module the
   per-record screens can mount, leaving the model screen mounting it unchanged.

**Verify.**
- **The existing model-review tests pass without modification.** That is the entire proof
  that this was an extraction and not a rewrite. If a test needs editing, the extraction
  changed behaviour — stop and find out why.
- `api_models_review.py` is shorter afterwards.
- Look at: the model review screen, stage by stage, before and after.

**Done when.** Model-review tests pass untouched and the stage logic lives in one module.

**Depends on.** Nothing — but it must precede 1R.2.

---

### 1R.2 ML Application and AI System reviews

**Goal.** A reviewer takes an ML Application or an AI System through the same seven stages,
on the same screen, as a model.

**Steps.**

a. `ML_APPLICATION_REVIEW_SUBJECT` and `AI_SYSTEM_REVIEW_SUBJECT` in `_review_subject.py`.
b. `src/web/api_ml_application_review.py` and `src/web/api_ai_system_review.py` (new), thin
   over the adapters. Register both blueprints in `src/web/app.py`.
c. Mount the shared review module from `static/js/mlapp/detail_core.js` and
   `static/js/aisystem/detail_core.js` — the screen is copied, not redesigned. The reviewer
   should not be able to tell which record type they are on except by its content.
d. Add the script tags to `src/templates/index.html`. **Restart `dev_app.sh` afterwards** —
   with `debug=False` Jinja caches `index.html`, so a new `<script>` tag is not picked up
   until the server restarts, and `kill -HUP` does not do it.
e. **DB: no migration.** Review state is collections on the record, not a view. Add
   `REVIEW_COLLECTION_SPECS` to `ML_APPLICATION_COLLECTION_SPECS` and
   `AI_SYSTEM_COLLECTION_SPECS`; `review_notes` and `review_signoffs` stay in
   `APPEND_ONLY_COLLECTIONS`, because a challenge thread is evidence (§13.5).

**Verify.**
- `test_ai_system_completes_all_seven_stages`, and the same for ML Application.
- `test_no_record_type_has_a_stage_another_lacks` — iterate `REVIEW_STAGE_KEYS` across every
  entry in `REVIEW_SUBJECTS`. This is the "the sequence does not fork" rule, mechanised.
- `test_reviewer_independence_applies_to_every_review_subject`.
- Look at: an AI System review beside a model review, on 5016, restored from a backup.

**Done when.** Both new record types complete all seven stages and the no-divergence test
passes.

**Depends on.** 1R.1.

---

### 1R.3 Derive the questions-stage label

**Goal.** `REVIEW_STAGES` labels its third stage "The nine questions"
(`config/governance/_review.py:41`). Once questionnaires are composed (1.2) the count differs
by record type, and a fixed label becomes wrong on every screen that shows it.

**Steps.**

a. Make the label a function of the record's questionnaire length rather than a constant.
b. Update the consumers: `src/web/api_models_review.py`,
   `src/static/js/inventory/review.js`, `src/governance/completeness/review_programme.py`,
   `src/governance/model_inventory/review_report.py`.

**Verify.**
- `test_label_follows_the_questionnaire` — a record with eleven questions reads
  "The eleven questions".
- `test_no_hardcoded_question_count` — including in the JS, which the audit's embedded-JS
  check will also see.

**Done when.** No count is hardcoded in `src/` or the static JS.

**Depends on.** 1.2, 1R.1.

**Phase 1R exit gate.** As above, plus: model-review tests pass unmodified.

---

## 7. Phase 2 — AI Systems configuration schema and regime map

**Blocked** on the one open decision (§10). It determines how the configuration layer is
built, not merely how it is maintained, so take it first. Everything in Phases 0, 1 and 1R
proceeds without it.

### 2.1 Regime map as data

**Goal.** Regulatory regimes — EU AI Act, PRA SS1/23, NIST AI 600-1 — expressed as
configuration against the shared core's contract.

**Steps.**

a. `config/governance/_ai_regimes.py` (new) — one entry per regime, its clauses, and the
   record attributes that decide whether it applies.
b. Register alongside `_frameworks.py`, reusing the 0.5 mapping engine.
c. The AI System detail screen shows which regimes apply and why.

**Verify.**
- `test_a_fictional_regime_added_purely_in_config_appears_in_coverage` — the contract proof.
- `test_regime_applicability_follows_record_fields` — an EU-deployed high-risk system picks
  up the Act; a non-EU one does not.

**Done when.** The fictional-regime test passes with no `src/` change.

**Depends on.** 0.5, and the §10 decision.

---

## 8. Phase 3 — Design & Instrument · Establish Baseline (Concepts 1–4)

### 3.1 Configuration snapshot as a versioned artifact

**Goal.** Turn current values into a version history. Model pin and version policy already
exist as fields; sampling parameters do not.

**Steps.**

a. Add `sampling_params` and `instruction_hierarchy` to `AI_SYSTEM_FIELD_SPECS`
   (`config/governance/_ai_system.py`). **Adding a field to config is not enough** — wire it
   into the detail lists, the register form and any Admin surface that enumerates fields.
   Many UI surfaces here are hand-curated, not spec-driven.
b. `ConfigurationSnapshotTaken` event in `src/governance/ai_system/`; snapshots are
   immutable once written.
c. A diff between two snapshots of the same system.
d. Show the snapshot history on the AI System detail screen.
e. **DB.** Migration `0015_configuration_snapshot_view.sql`; new event
   `ConfigurationSnapshotTaken`; register the projection in `_REBUILDERS`. Backfill one
   snapshot per existing AI System from its current values, then
   `rebuild_ai_system_view()` (§13.8).

**Shape.**

```
ConfigurationSnapshot
    ai_system_id: str
    config_version: int
    model_pin: FoundationModelRef
    output_schema: dict
    sampling_params: dict
    instruction_hierarchy: list[str]
    taken_at: str
```

**Verify.**
- `test_two_snapshots_are_individually_retrievable_and_diffable`.
- `test_snapshot_is_immutable_once_written`.
- `test_current_values_agree_with_the_latest_snapshot`.
- Look at: the new fields on the register form and the detail screen.

**Done when.** Snapshots are immutable, diffable, and the new fields appear on every
hand-curated surface that lists AI System fields.

**Depends on.** Phase 2.

---

### 3.2 Variability envelope

**Goal.** N runs under a pinned configuration, stored as percentile limits, bound to the
configuration that produced them.

**Steps.**

a. `config/governance/_ai_baseline.py` (new) — N, the percentiles, the minimum run count.
b. Run capture and percentile computation in `src/governance/ai_system/`.
c. The envelope carries `config_version` and is invalidated when the configuration moves.
d. Show the envelope, and its staleness, on the detail screen.
e. **DB.** Migration `0016_variability_envelope_view.sql`; new event
   `VariabilityEnvelopeRecorded`; register in `_REBUILDERS`.

**Verify.**
- `test_envelope_is_bound_to_its_config_version`.
- `test_changing_configuration_invalidates_the_envelope`.
- `test_too_few_runs_is_a_stated_refusal` — not a silently narrow envelope, which is the
  dangerous failure here: a tight envelope from three runs reads like a well-behaved system.

**Done when.** Invalidation and the refusal both hold.

**Depends on.** 3.1.

---

### 3.3 Benchmark, and the judge as a governed model

**Goal.** Dataset, rubric and judge — with the judge itself governed like any other model.

**Steps.**

a. The judge gets its own AI System record and its own `ai_system_id`.
b. A lineage edge (0.4) from the judge to every record whose evaluation it feeds.
c. A change to the judge classifies as **Measurement** under 0.1.
d. `config/governance/_assessments.py` — the existing `LLM-as-a-judge` assessment kind gains
   a reference to the judge's record rather than naming it in prose.

**Verify.**
- `test_judge_change_appears_in_every_dependent_affected_artifacts` — without a separate
  query being needed.
- `test_completeness_still_reads_a_judge_evaluation_as_testing_evidence` — the existing rule
  at `completeness/framework.py:159` must not regress.

**Done when.** A judge version bump surfaces on every dependent record.

**Depends on.** 0.1, 0.4, 3.1.

---

## 9. Phases 4–6

### Phase 4 — Operate & Measure · Escalate (Concepts 5–8)

#### 4.1 Anchored Continuous Evaluation for free-form fields
Rubric and scoring parameters in config. **Depends on** 3.3.

#### 4.2 Mechanically-verifiable fields reuse the Phase 0.2 library
**Verify:** `test_ai_and_ml_paths_call_the_same_measure_functions`. No second
implementation. **Depends on** 0.2.

#### 4.3 Trajectory scoring (graph-edit distance)
Applies only where `deployment_pattern` is in the agentic set — `Agentic (tool-using)`,
`Multi-agent` — derived from the field, never from a second stored label (spec §2).
**Verify:** `test_trajectory_scoring_skipped_for_direct_prompting`. **Depends on** 0.4.

#### 4.4 Trigger register, thresholds per property
A threshold **per property per model** — correctness, consistency, robustness,
predictability set independently (spec §9.4), with materiality and mission-criticality
informing each starting point rather than fixing all four together.
**Verify:** `test_four_thresholds_are_independently_editable` — setting one moves no other.
**Depends on** 3.2.

#### 4.5 Failure-mode register
Entries identified by a FINOS risk/mitigation pair, carrying trigger and fallback state.
Covers Moody's operational failure modes and the FINOS agentic security cluster: tool chain
manipulation, MCP server compromise, agent state persistence poisoning, credential
harvesting.
**Verify:** `test_register_entry_has_no_mitigation_status_field` — asserting the *absence*.
Status resolves at read time from tagged documents, as the FINOS coverage view resolves it
now. This is the easiest thing in the plan to reintroduce by accident, and two registers
that disagree are worse than one. **Depends on** 0.5, 4.4.
**DB:** migration `0017_ai_register_views.sql` creates `failure_mode_register_view` and
`standing_risk_register_view` together (5.2 uses the second); new events
`FailureModeRegistered` and `TriggerThresholdSet`; both projections registered in
`_REBUILDERS`.

---

### Phase 5 — Revalidate (Concept 9) and the standing risk register

#### 5.1 Immutable release manifest
Four-tier classification applied as its primary use.
**Verify:** `test_finos_version_bump_classifies_as_measurement`. **Depends on** 0.1, 3.1.

#### 5.2 Standing risk register
Bias (RI-16), IP and copyright (RI-23), reputational risk (RI-20), and the deeper
supply-chain risks (RI-7, RI-8, RI-26) — outside the five-phase lifecycle, reviewed at every
Material revalidation and at onboarding.
**Verify:** `test_register_absent_from_ml_applications` (spec §7);
`test_row_set_identical_under_both_deployment_configurations` — no entry muted or filtered
per deployment (spec §10). **Depends on** 0.5.

---

### Phase 6 — Coverage reporting across both workflows

One report, filtered primarily on **record type**, answering "what is in MRM scope and what
is governed outside it" in a form an examiner can read.

**Verify:** `test_coverage_counts_all_three_record_types`;
`test_no_model_class_field_exists` — the record type is the filter, and no duplicate
classification field crept in for reporting convenience.

**Depends on.** Phases 1–5.

---

## 10. Working protocol

**Database.** Never write to `mkm_modelrisk` on 5015. `scripts/restore_scratch.sh` then
`scripts/dev_app.sh`, which serves the scratch DB on 5016 and refuses to start on a protected
one. Before the first write in any ad-hoc script, print what you actually resolved to:

```bash
python -c "from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)"
```

**Gates.** `pytest`, then `python -m audit` — and read its last line. `coverage run -m pytest
&& coverage report` for the R3 gate. Run the audit, not just pytest, before calling a test
change done: test files are gated at 400 lines and a few added comments will trip it.

**UI.** Tests do not prove a screen. Restart `dev_app.sh` after any change under `src/` or
`config/` — `kill -HUP` silently keeps serving the old code. New `<script>` tags in
`index.html` need a restart too.

**Backfills.** Any script that drives domain commands must call the relevant
`rebuild_*_view()` afterwards, or the read model stays stale. Applies to 1.3, 1.5 and any
migration in Phase 3.

**Rules that bite here.**

| Rule | What it means |
|---|---|
| **R1** | Thresholds, labels, vocabularies and routing rules in `config/`. The one-way ModelOne fork makes this structural: logic that leaks into the fork is permanent divergence (spec §4). |
| **R2** | 300 lines, `src` and `config` both; 400 for tests. `_reference.py` has 1 line spare — see §2.2. Split along a seam the code already has, not at the line count. |
| **R6** | Zero tolerance: no SQL, driver import or connection outside `src/database/`. |
| **R9** | Restored backup, never the live database. |
| **R10** | Colours and typefaces via `config/theme.py` — relevant to 0.4's node styling. |
| **P1** | Writes against a protected DB need an actor in Admin → People. A 403 saying the actor is not registered is this rule, not a bug. |

---

## 11. Risks

| Risk | Handling |
|---|---|
| 0.2 is scoped as wiring because v0.3 said it existed | §2, §3 and 0.2 all state it as a build. It is the largest item in Phase 0. |
| The question split (1.3) lands after an estate is seeded | Hard ordering constraint in 1.3 — records keep the wording they were registered with. |
| A second review implementation grows for AI Systems | Phase 1R precedes Phases 3–5 deliberately, and 1R.1 closes only if the model tests pass unmodified. |
| `mitigation_status` reappears on the failure-mode register | 4.5 asserts its absence. |
| A `model_class` field returns for reporting convenience | Phase 6 asserts the record type is the filter. |
| A variability envelope from too few runs reads as a well-behaved system | 3.2 refuses rather than narrowing. |
| Logic leaks into ModelOne instead of config | Add each deployment-varying parameter to the audit as it is built, so the boundary is checked per commit. |
| A new field is added to config and not to the hand-curated screens | 3.1 lists the surfaces explicitly; treat every field addition the same way. |

---

## 11a. Completion — what "finished" turned out to mean (2026-09-06)

Phases 0–6 were built by 2026-09-05. Closing the module meant auditing this plan
against the tree rather than against memory: of the 51 tests named in `Verify`
sections, 40 existed under their planned names. The other 11 split three ways.

**Covered under a better name** — no work needed, the plan's name was simply not the
one used: `test_crossing_a_band_changes_rag` is
`test_crossing_a_band_changes_the_rating`; the 1.5 trigger-migration pair became
`tests/governance/test_ml_change_adoption.py`, which also records that 1.5's premise
was false (there were no legacy triggers to migrate — 24 of 25 `change_type` rows
were blank); `test_no_threshold_literals_in_src` is the audit's R1 check, which the
plan explicitly allowed.

**Superseded by a decision made during the build.**
`test_label_follows_the_questionnaire` wanted a record with eleven questions to read
"The eleven questions". It does not, deliberately: "The nine questions" names SR
26-2's nine specifically, so the label is a term of art per record type
(`REVIEW_QUESTION_STAGE_LABELS`) rather than a count. The config said so and now a
test asserts it.

**Genuinely missing, and now built.**

- **The review had never been walked end to end for the two new record types.**
  `tests/web/test_review_across_record_types.py` walks all seven stages to a signed
  review for a model, an ML Application and an AI System, parameterised rather than
  copied — three copies of a stage list is the drift the test exists to catch. It
  also mechanises "the sequence does not fork" by reading the reviewable types off
  `Subject`, so a fourth record type is covered on the day it is added.
- **Reviewer independence applied to models alone.** An ML Application or an AI
  System could be registered with its owner named as its own reviewer and nothing
  refused it — while the completeness audit reported exactly that arrangement as a
  finding on all three. The audit was right and the write path was not. The rule now
  lives in `src/governance/independence.py` and all three use it.
- **Three capabilities were reachable by nothing.** `record_variability_envelope`,
  `set_trigger_threshold` and `seal_release_manifest` were built in Phases 3–5,
  tested at the domain level, and had no route, no ingest endpoint and no button.
  The envelope panel could only ever read "not measured", which is the most
  flattering reading of the least evidence and precisely what the envelope exists to
  prevent. `src/web/api_ai_system_operate.py` exposes them; the AI System screen
  gained a baseline-run control, a Triggers table (listing every property, including
  those with no bar set — that is the gap worth seeing) and a Releases table.

**Verified end to end** against a restored scratch copy on 5017, driving the real
HTTP API: register both record types, refuse the owner as their own reviewer, take a
snapshot, refuse an envelope from too few runs and accept one from 24, refuse a
threshold on `tone`, set one on `correctness`, refuse a nameless release and seal
`2026.09.1`, agree all seven review stages on both records, sign both off, and route
both to the committee. The AI System's routing comes back **blocked** rather than
routed — it is agentic, so it escalates above the Division committee the estate has,
and the screen says so instead of quietly routing it to a committee that cannot take
it. That is 0.3's `blocked` state doing its job.

---

## 12. Open decision

**FINOS taxonomy refresh cadence** — manual quarterly review, live query via the FINOS AIGF
MCP Server, or a hybrid. No default assumed. It decides how the configuration layer is built,
so it blocks Phase 2 rather than merely shaping its maintenance. Phases 0, 1 and 1R proceed
without it.

---

---

## 13. Database changes

Explicit, because two thirds of the steps store something new and only some of them need
DDL.

### 13.1 Two kinds of change, and only one needs a migration

**A new aggregate or event type needs no migration.** The event store
(`0001_event_store.sql`) is generic — aggregate type, aggregate id, event type, JSONB
payload. A new aggregate adds rows, never columns.

**A new read model needs exactly one numbered migration.** Views are tables, created by
DDL and populated by a projection.

### 13.2 Migration mechanics

- Files live in `src/database/migrations/` as `NNNN_name.sql`, applied in **sorted filename
  order** by `run_migrations()` (`src/database/_migrate.py:79`) and recorded in
  `schema_migrations`, so re-running is a no-op.
- `bootstrap()` in `src/web/_startup.py:75` runs the migrations at startup and then
  reconciles the read models. Concurrent bootstraps are unsafe and the module guards against
  them.
- Every migration opens with the licence header comment, uses `CREATE TABLE IF NOT EXISTS`,
  and ends with `GRANT ... TO {{app_user}}` — `{{app_user}}` is a template rendered from
  `DatabaseConfig` by `render()`, not a literal role name.
- **Highest applied today: `0013_ai_system_view.sql`.** New work starts at 0014.

### 13.3 The view table shape

Follow `0007_model_chain_view.sql`:

```sql
CREATE TABLE IF NOT EXISTS <name>_view (
    <key>        TEXT PRIMARY KEY,
    data         JSONB NOT NULL,
    content_hash TEXT NOT NULL,
    version      INTEGER NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT, INSERT, UPDATE, DELETE ON <name>_view TO {{app_user}};
```

A view is a projection, not a source of truth: the app role may freely mutate it because the
authoritative history is the event log, and the whole table can be dropped and rebuilt.

### 13.4 Migrations this plan needs

| # | File | Creates | Step |
|---|---|---|---|
| 0014 | `0014_change_view.sql` | `change_view` | 0.1 |
| 0015 | `0015_configuration_snapshot_view.sql` | `configuration_snapshot_view` | 3.1 |
| 0016 | `0016_variability_envelope_view.sql` | `variability_envelope_view` | 3.2 |
| 0017 | `0017_ai_register_views.sql` | `failure_mode_register_view`, `standing_risk_register_view` | 4.5, 5.2 |

Numbers are allocated in the order the steps land. If two land out of order, renumber before
merging — `_migrate.py` sorts by filename, and a gap is harmless but a duplicate number is
not.

### 13.5 Steps that need no migration at all

- **Phase 1R (the whole review generalisation).** Review state is not a view. `review_notes`
  and `review_signoffs` are collections on the record aggregate, declared in
  `REVIEW_COLLECTION_SPECS` (`config/governance/_review.py:118`) and listed in
  `APPEND_ONLY_COLLECTIONS` (`:111`) — append-only, because a challenge thread is evidence.
  Generalising the review means adding those specs to `ML_APPLICATION_COLLECTION_SPECS` and
  `AI_SYSTEM_COLLECTION_SPECS`. Config, not DDL.
- **The question library (1.1–1.3).** Reference lists and per-record questionnaires are
  collections too.
- **0.3 routing, 0.5 criteria, 2.1 regimes.** Configuration only.

### 13.6 Registering a new projection

A new read model is three things, and the third is the one that gets forgotten:

1. the migration (§13.4),
2. `rebuild_<x>_view()` in the aggregate's `projection.py`,
3. **an entry in `_REBUILDERS` in `src/web/_startup.py:62`** — the table of every
   read-model rebuild, so the view reconciles at startup.

> **Fixed 2026-09-04, before the phases began.** `_REBUILDERS` had ten entries and
> `ml_application` was not among them, although `0011_ml_application_view.sql` and
> `rebuild_ml_application_view()` both existed — so that view alone never reconciled at
> startup and could drift from the log. It is now registered, and
> `test_every_defined_rebuilder_is_registered_for_startup` compares the source tree against
> the list rather than the list against itself, which is what stops the next one being
> forgotten. Step 1.5's backfill depended on that view being current.

### 13.7 New event types

Convention is `<Aggregate><Verb>` in PascalCase — `ModelRegistered`, `AISystemRetired`,
`ModelFieldUpdated`.

| Aggregate | New events | Step |
|---|---|---|
| `Change` (new) | `ChangeProposed`, `ChangeClassified`, `ChangeSuperseded` | 0.1 |
| `AISystem` | `ConfigurationSnapshotTaken` | 3.1 |
| `AISystem` | `VariabilityEnvelopeRecorded` | 3.2 |
| `AISystem` | `TriggerThresholdSet` | 4.4 |
| `AISystem` | `FailureModeRegistered` | 4.5 |
| `AISystem` | `ReleaseManifestSealed` | 5.1 |

**An event type is permanent.** The log is append-only and a junk event can only be retired
through a committee, so name it once and add it to the projection's `apply()` in the same
commit. An event the projection does not handle is silently dropped from the read model
while remaining in the log — which reads as data loss and is not.

### 13.8 Backfills

| Step | Backfill | Then rebuild |
|---|---|---|
| 1.3 | **None by design** — records keep the questionnaire they were registered with | — |
| 1.5 | Classify every open change record onto a tier | `rebuild_ml_application_view()`, `rebuild_inventory_view()` |
| 3.1 | One snapshot per existing AI System, from its current values | `rebuild_ai_system_view()` |

Every backfill goes through domain commands, never SQL (R6), and is rehearsed against a
restored scratch DB on 5016 before anything else (R9). A backfill driven from a bare script
leaves the read models stale, so the rebuild is part of the step, not a follow-up.

### 13.9 Safety

| | |
|---|---|
| **R6** | No SQL, driver import or connection outside `src/database/`. Migrations are SQL and live there by definition; nothing else is exempt. |
| **R9** | 5016 / `mkm_modelrisk_scratch`, never 5015 / `mkm_modelrisk`. `scripts/dev_app.sh` refuses to start against a protected database; `scripts/pg.sh` sources `.env` *after* your environment, so use `scripts/restore_scratch.sh`, which passes the target explicitly. |
| **P1** | A write against a protected database needs an actor registered in Admin → People, or it is refused with 403. |
| **Verify first** | Before the first write in any ad-hoc script: `python -c "from config.database import DatabaseConfig; print(DatabaseConfig.from_env().name)"` |

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
