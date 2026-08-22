# ML Applications — the Training tab

**Status:** Proposed — not started
**Date:** 2026-08-21
**Source:** `docs/sklearn/ml-apps-training-tab-spec.md` (design spec v0.1)
**Reference record:** MKM-FC-001 Flood Probability Classifier

This is the spec translated into this platform's idiom and phased. The spec's
analysis is adopted wholesale; what changes here is the mechanism, because two of
its assumptions do not hold in this codebase.

---

## 1. What the spec gets right, and why it is worth building

Two arguments carry the whole thing:

**Typing the fields is the point, not adding more of them.** Nine free-text rows
cannot answer *"which models were fitted with a random split on spatially correlated
data?"*. That is an estate-level question a committee should be able to run, and no
amount of extra prose makes it answerable.

**The ordering is governance, not pedagogy.** The split is established before the
preprocessing that depends on it, so the leakage question is visible on the page: a
scaler fitted before the split inflates the test metric and everything below it
becomes unreliable. A tab that lists the fields in any other order lets that pass.

*The spec contradicts itself here and we followed the better half.* Its §2 puts the
split before scaling; its §4 schema puts scaling at B.8 and the split at C.1, which
is the opposite. Section C now reads "Split, preprocessing and validation" and
carries encoding, scaling and the scaler fit-point after the split rationale. The
finding fires either way — `scaler_fit_point = "Full dataset"` is flagged wherever
the row sits — but a reader meets it already knowing what the split was.

## 2. Two translations the spec needs

### 2.1 There is no SQL table

The spec sketches `class TrainingEvidence(Base)` with a `ForeignKey`. This platform
is event-sourced and coding rule **R6** is zero-tolerance: no SQL, driver import or
connection outside `src/database/`. The read model is a projection, never a source
of truth.

The translation is exact rather than lossy:

| Spec | Here |
|---|---|
| `ml_training_evidence` table | a `training_evidence` collection on the ML Application |
| one row per `fit_id` | one collection item per fit, `item_id` = the fit |
| `UniqueConstraint(model_id, fit_id)` | items are per-aggregate; the id is unique by construction |
| a field definition module | `config/governance/_ml_training.py` — which is R1, already how every field on this platform is declared |

**The spec's "field definitions live in one config module, not the template" is
already the house rule.** The existing collection specs generate the form, the
validation and the audit field names from one declarative structure. The one thing
they do not yet generate is per-field *requirement* (mandatory / conditional), which
is the new machinery §4 below asks for.

### 2.2 "RAG" already means something else

§5 of the spec proposes Red / Amber / Green for training completeness. On this
platform **RAG is the risk rating** — Materiality × Complexity resolved through the
division's ratified heatmap, and moved only by MRC sign-off. Overloading it would
make a record with a thin Training tab indistinguishable from one the committee
rated Red for risk.

The spec's own better instinct is in the same section: the counter `Training (23/31)`
in the style of `Review (4/9)`. That is the mechanism to use. The Red/Amber/Green
*rules* are worth keeping exactly as written — as a **training completeness state**
shown on the tab, feeding the completeness audit, and never touching `rag_rating`.

## 3. What it collides with today

- **The Training tab currently holds** training_data, training_period, performance,
  benchmark, misinterpretation, the three testing flags and monitoring_approach.
  The spec moves the testing flags to Review and monitoring to Retrains, and maps
  the rest into the new sections. Agreed — they are not training-approach evidence.
- **Retrains is `version_history` today**, with 2 entries on MKM-FC-001. Both go:
  version is removed and every fit is a train (decision 3). The two existing entries
  are not migrated (decision 2) — a fit recorded under the old shape carries none of
  the evidence a train does.
- **39 fields will not fit** in `_ml_application.py` (R2, 300 lines). Its own module.

## 4. Every vocabulary lives in Admin

The spec lists eleven enumerations. None of them may ship as a fixed tuple: the
status vocabularies did exactly that, Admin accepted new words and every record
refused them, and an institution that fits something we never listed must be able to
say so. So each becomes an admin-managed list with a stable stored value and an
editable label — the same shape as the lifecycle stages.

**Two of them already exist and must not be duplicated:**

| Spec field | Use the existing list |
|---|---|
| A.2 Algorithm | **Estimator** (Admin → Estimator). The ML Application already carries `estimator` as a strict reference to it, with source and version. A second "algorithm" list would be the same fact recorded twice, free to disagree. |
| B.1 Source dataset(s) | **Data Source** (Admin → Data Source), now carrying Internal / External. |

**Nine are new**, seeded from the spec:

| List | Seeded values | Used by |
|---|---|---|
| `learning_task` | regression, binary classification, multiclass, clustering, dimensionality reduction, sequence, image | A.1 — and it drives every conditional field |
| `missing_data_treatment` | drop, mean, median, mode, model-based, none | B.6 |
| `categorical_encoding` | one-hot, ordinal, target, embedding, not applicable | B.7 |
| `scaling_method` | standard, min-max, robust, none | B.8 |
| `scaler_fit_point` | train only, full dataset | B.8 — "full dataset" is the amber trigger |
| `split_method` | random, stratified, temporal, spatial-group, entity-group, predefined | C.1 |
| `cross_validation_method` | none, k-fold, stratified k-fold, group k-fold, time-series split | C.4 |
| `search_method` | none, manual, grid, random, Bayesian | D.2 |
| `determinism` | bit-reproducible, reproducible to tolerance, non-deterministic | D.4 |
| `primary_metric` | ROC-AUC, PR-AUC, accuracy, F1, precision, recall, Brier, RMSE, MAE, R², silhouette | E.1, E.2, E.4 |
| `naive_baseline` | majority class, climatological base rate, persistence, mean prediction | E.4 |

**One Admin tab, not eleven.** These go under a single **ML Training** tab, several
vocabularies to a page, exactly as the six status vocabularies share the Vocabulary
tab — whose own comment gives the reason: "shown together rather than as six tabs
nobody would find."

**A.4 Feature inventory is not a list and should not be forced into one.** The spec
asks for a reference to a feature dictionary with a count shown inline. A feature
dictionary is a register in its own right — name, type, source, derivation — closer
to the Estimator list than to a vocabulary, and probably a piece of work of its own.
Until it exists, A.4 can reference the data source and carry a count. Flagged in §5.

## 5. Plan

### T1 — The schema, the six sections, and Trains as a view (decisions 1 + 3)

`config/governance/_ml_training.py`: the section / field / type / requirement table
as one declarative structure. Sections A–F rendered in order, collapsible, using the
existing row and `edit` machinery — a schema change, not a re-skin.

One item per fit in a `training_runs` collection, from the start — the Trains tab is
a view over it rather than a store of its own, so metric drift across trains is a
query and not a manual comparison. `version_history` comes off the ML Application
entirely, and the `change` probe gains `training_runs` beside it (§6).

Existing fields migrate as the spec maps them (training_data → B, training_period →
B.3, performance → E, benchmark → E.4, misinterpretation → A.5's excluded-use half).
The testing flags move to Review; monitoring_approach moves to Trains.

### T2 — Typed fields and the Admin vocabularies

The nine new lists from §4, seeded and reachable under one **ML Training** admin tab,
plus the fields typed against them. Numerics where the thing is a number.

Conditional requirements are driven by A.1: `Target distribution` mandatory for
classification, `Epochs / batch size` and `Convergence evidence` for neural tasks,
`Categorical encoding` where any categorical feature is present.

### T3 — Completeness

The `Training (n/m)` counter, the Red / Amber / Green rules from spec §5 as a
training completeness state, and the amber triggers made explicit: B.8 fitted on the
full dataset, C.3 rationale absent, C.6 test evaluations above the cap, F.5 not
performed. Computed, never set by hand. Feeds the completeness audit alongside the
existing per-collection weights.

### T4 — Artefacts

D.7 convergence evidence, E.3 calibration curve, E.6 segment table. These are
documents with categories, which the record already supports — the work is the
categories and the reference from a field to a filed document.

### T5 — *(folded into T1 by decision 1)*

### T6 — Population at fit time

The spec's strongest practical idea: a decorator or context manager around the
training entry point capturing snapshot hash, hyperparameters, seed, library
versions, commit SHA, duration and artefact hash, and POSTing them — leaving the
owner about seven judgement fields rather than thirty-one.

Two things this platform already provides: an ingest path (`src/ingest`), and an
authorship rule that will apply to it — an automated capture must present an
identity, and `ingest:*` actors pass the P1 known-actor check by design.

Auto-captured fields read-only in the UI and flagged as such in the audit trail: a
field the owner can hand-edit is a field a validator has to verify separately.

## 6. Decisions taken

1. **Retrains becomes a view over fits in T1.** Not deferred — deferring means
   building the tab twice.
2. **The two existing `version_history` entries do not migrate.** MKM-FC-001 starts
   afresh; a fit recorded under the old shape has none of the evidence a train
   carries, and inventing it would be worse than starting clean.
3. **Version is removed. Every fit is a train.** There is no version concept on an
   ML Application: the record of change IS the sequence of trains, each with its own
   snapshot, seed, hyperparameters and metrics.
4. **The feature dictionary is a register of its own** (see T7), not a count squeezed
   into a text field.
5. **BCBS 239 joins the framework coverage table** (see T8).

### What decision 3 costs, and how it is paid

`version_history` is what the completeness audit reads to evidence **COSO principle
15, "Assesses Substantial Change"** — the `change` probe is
`_any_entries(d, "version_history")`. Remove the collection and every ML Application
silently stops evidencing that clause. It would not error; the coverage table would
just quietly report less of the estate.

It is paid without a per-type branch, because `_any_entries` already takes several
collection names — `identification` passes three:

```python
"change": lambda e: _share(e, lambda d: _any_entries(d, "version_history", "training_runs")),
```

A model keeps evidencing the clause through its versions, an ML Application through
its trains, and the probe stays one lambda over one population — which is the whole
point of the field-name parity in `docs/design/mlmodel.md`.

**Naming:** the collection is `training_runs`, the tab is **Trains**. "Retrains" was
only ever right for a record that had versions to re-do. (If "Trains" reads oddly in
a governance document — it is also a railway — "Training runs" is the alternative;
the stored name does not change either way.)

## 6a. Two work packages the decisions add

### T7 — The feature register

A register in its own right, like the Estimator list: each feature with a name, type,
source, derivation and the data source it comes from. A.4 then references it and
shows a count inline, which is what the spec asked for.

This is the piece most likely to grow: a feature used by several ML Applications is
the ML estate's version of "two models share a data source", and the same
correlated-failure question follows from it. Worth building so that question is
answerable later, not worth answering now.

### T8a — ML Applications join the gap audit report

The completeness audit produces the gap report an assessor reads. ML Applications
must appear in it: an estate half of whose models are ML Applications, audited on the
other half, reports a gap picture that is wrong in the direction that flatters.

The training evidence is what makes several of its findings answerable — a missing
snapshot identifier or split rationale is a gap of exactly the kind the report
already scores, and the completeness figure computed per train is the input.

### T8 — BCBS 239 clause coverage

A third framework beside ISO 31000 and COSO in `config/governance/_frameworks.py`.
Self-contained: the clause list, its citations, and which probe evidences each. The
Training tab is what makes several of its lineage clauses answerable at all — a
snapshot identifier and a source-dataset reference are exactly what BCBS 239 asks for
and what free-text training notes cannot provide.

Same caveat as the other two, and it belongs in `COVERAGE_BASIS`: BCBS 239 is
supervisory guidance addressed to institutions, not a standard a product is certified
against. The table states what the platform holds that evidences a clause and how
much of the estate carries it. Nothing more.

## 6b. Nothing is mandatory — settled

The spec marks most of its fields mandatory, which is a fair description of a mature
estate and a poor opening position for an adopter. **A complete set of fifty-one will
not be reached on a real estate**, so a tab that reports most of itself outstanding on
every record is a tab people learn to ignore — and the one thing on it that genuinely
needs reading gets ignored with it.

The requirement levels are gone. What the tab reports instead:

- **A count.** `Training (24/49)` — progress, not a score.
- **Findings, separately.** What has been *recorded* that a reviewer must be told
  about: a scaler fitted on the full dataset, a split rationale too short to be an
  argument, a hold-out looked at more than three times, a fit nobody but the developer
  has reproduced. These are statements about evidence that exists, not complaints
  about evidence that does not.

The distinction is the point. An empty field is work not yet done. A scaler fitted on
the full dataset is a finding, and it does not become one by being mandatory.

## 7. What this does not change

The Training tab is evidence about a fit. It does not touch the risk classification,
the MRC route or the questionnaire — an ML Application is still rated on the same
three dimensions as a model and signed off by the same committee.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
