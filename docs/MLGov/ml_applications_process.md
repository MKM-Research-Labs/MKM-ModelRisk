# ML Applications — how the process works, and why it asks what it asks

**Date:** 2026-09-02  ·  **Audience:** model owners, validators, MRC secretaries and
anyone implementing the console at an adopting institution.

This document describes the ML Application process as it is actually built: what the
record is, every stage it passes through, what each screen asks for, and — the part
most often missing from a governance tool — *why* each question is on the form and
what a blank one costs.

It is the operating description. The design decisions behind it, with the
alternatives that were rejected, are in [`docs/design/mlmodel.md`](design/mlmodel.md),
[`docs/design/ml-training-tab.md`](design/ml-training-tab.md) and
[`docs/design/ml-review-policy.md`](design/ml-review-policy.md). The general console
walkthrough is [`docs/user_guide.md`](user_guide.md); this document assumes it.

**Scope.** Classical and statistical machine learning — regression, GLMs, gradient
boosting, random forests, clustering. The trained-on-data estate. LLMs and agentic AI
are deliberately out of scope here; they are governed as **AI Systems**, a separate
record type with its own framework coverage.

---

## Contents

1. [What an ML Application is](#1-what-an-ml-application-is)
2. [The process end to end](#2-the-process-end-to-end)
3. [Admin — the vocabularies the process runs
on](#3-admin--the-vocabularies-the-process-runs-on)
4. [Registering an ML Application](#4-registering-an-ml-application)
5. [The record, and its two halves](#5-the-record-and-its-two-halves)
6. [Trains — the evidence that a fit
happened](#6-trains--the-evidence-that-a-fit-happened)
7. [The ten review questions, and why each is
asked](#7-the-review-questions-and-why-each-is-asked)
8. [The ML review policy — the institution decides what it asks
for](#8-the-ml-review-policy--the-institution-decides-what-it-asks-for)
9. [Risk rating and MRC sign-off](#9-risk-rating-and-mrc-sign-off)
10. [The other registers on the record](#10-the-other-registers-on-the-record)
11. [Where an ML Application shows up
elsewhere](#11-where-an-ml-application-shows-up-elsewhere)
12. [The screens](#12-the-screens)
13. [API and configuration reference](#13-api-and-configuration-reference)
14. [Deliberate gaps](#14-deliberate-gaps)

---

## 1. What an ML Application is

Three layers, each a different kind of thing:

| Layer | What it is | Where it lives |
|---|---|---|
| **Estimator** | The off-the-shelf ML engine — its source, name and available versions | Admin reference list |
| **ML Application** | *This institution's use case for that estimator* — the governed record | Its own register, apart from Models |
| **Product** | Binds several models **and** several ML Applications | The Product's `components` list |

The middle layer is the point. **Nobody validates scikit-learn's implementation of
gradient boosting.** What is validated is the firm's use of it — on this data, for
this decision, with these features and this owner. That is the standard vendor-model
/ implementation split, and it is what the record is for. The estimator is a
component the institution names; the application is what the institution is
accountable for.

### Why it is not called an "ML Model"

`Model` is the platform's central noun and is reserved for the inventory. A second
record type carrying the word would collide in the sign-off tabs, in the audit
output, in `model_id` / `get_model` / `list_models`, and in every conversation about
either. `Component` was already taken too — a Product has components. **Estimator**
and **ML Application** are free in both namespaces, and "application" is the standard
term in vendor-model governance: a vendor supplies the model, the institution is
accountable for its *application* of it.

The irony is worth stating plainly for the data scientists filling these in: a
fitted estimator applied to a use case is exactly what you would call "a model", and
that is precisely the word that was unavailable.

### Why it sits apart from the model inventory

Not because it is a different subject — because it **changes at a different rate**.
The governance framework around models is settled; ML functionality is still
evolving. The boundary keeps that churn away from the record type that MRC sign-off,
the completeness audit and every issued document already depend on.

The corollary is that the join has to be the boring part: **an ML Application does
not link to a model.** It links to a Product, alongside models. That is the only
structural connection.

### Self-contained record, borrowed machinery

An ML Application carries its own validation, review and challenge, because nothing
above it will do that for it — a Product delegates validation *downwards* to its
components, and the model inventory does not know these records exist.

"Self-contained" means its own *records*, not its own *code*. The challenge thread,
the sign-off queue, the actions register, the document store and the risk policy are
the same machinery a model and a product use. Three review workflows and three MRC
sign-off paths in one system would drift apart within a year.

---

## 2. The process end to end

| # | Stage | Who | Where | What enforces it |
|---|---|---|---|---|
| 0 | Curate the vocabulary; ratify the review policy | Admin / MRC | Admin → reference lists; Admin → ML Review Policy | MRC approval of the policy draft |
| 1 | Register the ML Application | Owner | ML Apps → Register | 10 questions copied onto the record; five required fields |
| 2 | Fill the governance half | Owner | Overview, Risk Rating | Reference lists; the division's risk policy |
| 3 | Record trains | The training code, or the owner | Training / Trains tabs, or `POST /api/ingest/ml-training-run` | Capturable fields refused from a human, judgement fields refused from a machine |
| 4 | Record fairness, evaluations, assumptions, limitations, weaknesses | Owner | The register tabs | — |
| 5 | Answer the review questions | Owner, then reviewer | Review tab | Status vocabulary |
| 6 | Mark the review complete | Owner | Review status field | **Gated**: every mandatory item the division's policy names must be filled |
| 7 | Propose a risk rating to the committee | Owner | Risk Rating → Request sign-off | **Gated** by the same rule; routed to the MRC covering the division |
| 8 | Committee approves | MRC | Meeting → Signoff | The stored `rag_rating` does not move until approval |
| 9 | Issue the document | Anyone | Docs → ML Application Document | Generated from the record on request, never stored |
| 10 | Retrain, re-review, retire | Owner / MRC | Trains tab; Danger tab | A retrain is a new train, never an edit of the last one |

Two properties hold throughout, and they explain most of the design:

**Nothing blocks recording.** A train can be created and edited with every mandatory
field blank; a question can be left unanswered indefinitely. What is refused is
*finishing* — completing the review, and raising it to the committee. A barrier to
writing evidence down is a barrier to evidence.

**Everything is append-only.** The record is event-sourced. A correction is a new
event, a retrain is a new train, a review cycle is a new set of notes. Nothing that
was true on the day the committee saw it can be made untrue afterwards.

---

## 3. Admin — the vocabularies the process runs on

Everything the ML process chooses from is an admin-managed reference list. None of it
is a fixed tuple in the code, because an institution that fits something we never
listed must be able to say so.

Two rules apply to all of these:

- **Seed a vacuum, never reconcile a curated list.** A list that is empty on first
  boot is seeded with our starting set; a list somebody has edited is never
  reconciled against ours afterwards. Your deletions stay deleted.
- **A record stores the value, a screen shows the label.** Renaming a vocabulary
  entry in Admin changes every screen and never rewrites a stored record — and, for
  the training conditionals, never changes which fields are demanded.

### 3.1 Estimators

One row per **source + estimator name** — scikit-learn's `GradientBoostingRegressor`
is one row, XGBoost's `XGBRegressor` another — each carrying the versions available
for it. Deliberately *not* one row per version: that is a cartesian product which
grows without bound and leaves each row meaning nothing on its own. The ML
Application picks the row, and then the version.

`source` is a field rather than an assumption. Production gradient boosting is more
often XGBoost or LightGBM than scikit-learn's own implementation, and regression is
frequently statsmodels or R, so an estate hardcoded to one library would be wrong on
its first day. It is **not** the `vendor` list: a vendor is a firm with a contract
and due diligence behind it, and an open-source library is not that.

`versions` and `notes` seed **empty** on purpose. The estimator names are universal
and we can state them; which versions an institution actually runs is a fact about
its own environment, and seeding our guesses would put releases in the register that
nothing in the estate uses.

The 18 seeded rows:

| Estimator | Source | Note |
|---|---|---|
| `LinearRegression` | scikit-learn | Ordinary least squares. |
| `LogisticRegression` | scikit-learn | Binary / multinomial classification. |
| `Ridge` | scikit-learn | L2-penalised linear regression. |
| `Lasso` | scikit-learn | L1-penalised; performs feature selection. |
| `ElasticNet` | scikit-learn | Combined L1/L2 penalty. |
| `DecisionTreeRegressor` | scikit-learn | Single tree; interpretable, high variance. |
| `RandomForestRegressor` | scikit-learn | Bagged trees, regression. |
| `RandomForestClassifier` | scikit-learn | Bagged trees, classification. |
| `GradientBoostingRegressor` | scikit-learn | Boosted trees, regression. |
| `GradientBoostingClassifier` | scikit-learn | Boosted trees, classification. |
| `HistGradientBoostingRegressor` | scikit-learn | Histogram-based boosting for larger data. |
| `XGBRegressor` | XGBoost | Gradient boosting, regression. |
| `XGBClassifier` | XGBoost | Gradient boosting, classification. |
| `LGBMRegressor` | LightGBM | Leaf-wise boosting, regression. |
| `LGBMClassifier` | LightGBM | Leaf-wise boosting, classification. |
| `OLS` | statsmodels | Least squares with inference diagnostics. |
| `GLM` | statsmodels | Generalised linear models. |
| `Logit` | statsmodels | Logistic regression with inference diagnostics. |

### 3.2 Features

A **register**, not a vocabulary: each entry is a thing with properties — what type
it is, where it comes from, how it is derived — rather than a word with a label. It
is not seeded, because an institution's features are its own and a starter list of
ours would be somebody else's model described in your register.

It earns its keep beyond providing a dropdown. A feature used by several ML
Applications is the ML estate's version of "two models share a data source", and the
same correlated-failure question follows from it: **a feature that turns out to be
wrong, or to have leaked, is wrong everywhere it is used at once.** That question is
only askable if the uses are recorded against one entry rather than typed into fifty
free-text boxes.

### 3.3 The ML review questions

The 10-question set, held as its own list (`ml_application_questions`)
and deliberately not shared with a model's SR 26-2 questionnaire. Same mechanism —
adopter-managed, copied onto each record at registration — different content, moving
independently. See [§7](#7-the-review-questions-and-why-each-is-asked).

### 3.4 The training vocabularies

Eleven lists behind the Training tab's choice fields. Two enumerations the training
spec names are deliberately *absent* because they already exist elsewhere: the
algorithm **is** the Estimator list, and the source dataset **is** the Data Source
list. A second copy of either would record the same fact twice and be free to
disagree with itself.

| Admin list | Seeded values | What it decides |
|---|---|---|
| Learning tasks<br>`learning_task` | Regression, Binary classification, Multiclass classification, Clustering, Dimensionality reduction, Sequence, Image | What kind of problem the fit solves. Drives which other fields apply. |
| Missing data treatments<br>`missing_data_treatment` | Drop, Mean, Median, Mode, Model-based, None | How absent values were handled before fitting. |
| Categorical encodings<br>`categorical_encoding` | One-hot, Ordinal, Target, Embedding, Not applicable | How categorical features were represented. |
| Scaling methods<br>`scaling_method` | Standard, Min-max, Robust, None | How features were scaled or normalised. |
| Fit points<br>`scaler_fit_point` | Train only, Full dataset | Where a transform was fitted -- the scaler, the imputer, the encoder. Fitting on the full dataset leaks the test set into the fit. |
| Split methods<br>`split_method` | Random, Stratified, Temporal, Spatial-group, Entity-group, Predefined | How the data was divided into train, validation and test. |
| Cross-validation methods<br>`cross_validation_method` | None, K-fold, Stratified k-fold, Group k-fold, Time-series split | How the fit was cross-validated. |
| Hyperparameter searches<br>`search_method` | None, Manual, Grid, Random, Bayesian | How the hyperparameters were arrived at. |
| Determinism statements<br>`determinism` | Bit-reproducible, Reproducible to tolerance, Non-deterministic | How exactly the fit reproduces. |
| Performance metrics<br>`primary_metric` | ROC-AUC, PR-AUC, Accuracy, F1, Precision, Recall, Brier score, RMSE, MAE, R-squared, Silhouette | The metrics a fit is scored on. |
| Naive baselines<br>`naive_baseline` | Majority class, Climatological base rate, Persistence, Mean prediction | The unskilled comparison a fit must beat before any other. |

### 3.5 The ML review policy

**Admin → ML Review Policy.** Which of the catalogue this institution actually asks
for, per division, ratified by that division's MRC. See
[§8](#8-the-ml-review-policy--the-institution-decides-what-it-asks-for).

---

## 4. Registering an ML Application

**ML Apps → Register.** The id carries the `MLA` prefix (`MLA-0001`). Besides the id,
the form's minimum is five fields:

`name`, `division`, `owner`, `estimator`, `use_case`

That list is short on purpose. An ML Application is registered before most of it is
known, and a form that demands the narrative up front is answered with placeholders —
which are worse than blanks, because a blank is visible to the completeness audit and
"TBC" is not. What is missing after registration is a completeness finding, which is
where that gap belongs and where somebody actually acts on it.

Two of the five are worth noting:

- **`estimator` is strict.** A record may not name an estimator nobody has defined in
  Admin, for the same reason a model may not name an undefined type. The register is
  a controlled vocabulary or it is a spelling exercise.
- **`use_case` is required at registration** although it is narrative. It is the one
  piece of narrative every other answer is judged against, and a record that cannot
  say what it is for should not exist yet.

### The questionnaire snapshot

Immediately after registration the institution's ML questions are **copied onto the
record** as its own collection, each starting at the default status. This is the same
mechanism a model's validation questions use, and the reason is the audit trail: a
record keeps the questions it was actually asked. Editing the admin list afterwards
changes what *new* records are asked and never rewrites an answer already given.

The one case that skips the copy is a record migrating in from the model inventory
with a questionnaire it has already answered — seeding on top of that would leave the
record carrying two sets, and a reader could not tell which the committee saw.

### Migrating a model that is really an ML Application

`scripts/migrate_model_to_ml_application.py` moves a record across. An estate
contains models that are really ML applications and the inventory is where they are
today, so this is expected to be used repeatedly during a rollout. The **estimator is
an argument to the script**, because the inventory does not record one — that is
precisely the information the ML register adds, and inferring it from a methodology
sentence would be a guess presented as a fact. Dependencies and RACI do not travel; a
value the target refuses is reported rather than mangled.

---

## 5. The record, and its two halves

42 fields, in two halves, and the split is the whole design.

### 5.1 The governance half uses a model's field names — exactly

Not similar names. **The same ones.** The completeness audit's clause probes are
field-name lambdas over a single population: `analysis` reads `tier` / `materiality`
/ `complexity`, `accountability` reads `owner`, `independence` compares
`peer_reviewer` against `owner`, `criteria` reads `division`, `monitoring` reads
`next_review_date`, `treatment` reads `remediation_steps`.

Match the names and every probe counts ML Applications with no change at all. Diverge
and each probe grows a per-type branch — thirteen places to forget one, and the
failure mode is silent: the ISO/COSO tables would go on describing a shrinking
non-ML slice of the estate while reporting it as the whole.

The same reasoning governs the shared collections. `assumptions`, `limitations`,
`model_weaknesses`, `remediation_steps`, `data_sources`, `fairness_assessments`,
`evaluations`, `change_history`, `actions` and the sign-off collections are the
*same* specs a model uses, under the same names, so an estate-wide question has one
answer rather than three.

### 5.2 The ML half is what a model record has no place for

Which estimator and version, why that one rather than a simpler alternative, what it
was trained on, how it performs, and how it could be misread.

### 5.3 The fields


**Identity**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `name` | Name | text |  |
| `short_name` | Short name | text |  |
| `description` | Description | textarea |  |

**Organisation**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `division` | Division | text | `division` list |
| `line_of_business` | Line of Business | text | `line_of_business` list |
| `repo_location` | Repository location | text |  |
| `codebase` | Codebase | text | `codebase` list |

**Estimator and method**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `use_case` | Use case | textarea |  |
| `estimator` | Estimator | text | `estimator` list — **strict** |
| `estimator_version` | Estimator version | text |  |
| `estimator_rationale` | Why this estimator | textarea |  |
| `methodology` | Methodology | text |  |
| `source_module` | Source module | text |  |
| `vendor` | Vendor | text | `vendor` list — **strict** |
| `category` | Category | text |  |

**Classification**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `tier` | Tier | tier | the division's ratified tier bands |
| `tier_rationale` | Tier rationale | text |  |
| `materiality` | Materiality | choice | Low, Medium, High |
| `materiality_rationale` | Materiality rationale | text |  |
| `complexity` | Complexity | choice | Low, Medium, High |
| `complexity_rationale` | Complexity rationale | text |  |
| `rating_rationale` | Rating rationale | text |  |
| `rag_rating` | RAG rating | choice | Green, Amber, Red |

**Governance**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `owner` | Owner | text | `people` list |
| `peer_reviewer` | Peer reviewer | text | `people` list |
| `status` | Status | text |  |
| `review_status` | Review status | choice | Not started, Documents reviewed, Assumptions agreed, Questions answered, Weaknesses agreed, Limitations agreed, Monitoring agreed, Remediation agreed, Signed off |
| `lifecycle_stage` | Lifecycle stage | choice | `lifecycle_stage` list |
| `validation_status` | Validation status | choice | `validation_status` list |
| `version` | Version | text |  |
| `review_frequency` | Review frequency | choice | Monthly, Quarterly, Semi-annual, Annual |

**Review dates**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `last_review_date` | Last review | date |  |
| `validation_date` | Validation date | date |  |
| `recertification_date` | Recertification | date |  |
| `next_review_date` | Next review | date |  |
| `mrc_signoff_date` | MRC sign-off | date |  |
| `mrc_signoff_meeting` | MRC sign-off meeting | text |  |

**Monitoring**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `monitoring_approach` | Monitoring approach | textarea |  |

**Testing**

| Field | Label | Type | Values drawn from |
|---|---|---|---|
| `unit_tests` | Unit tests | choice | Yes, No |
| `integration_tests` | Integration tests | choice | Yes, No |
| `benchmark_tests` | Benchmark tests | choice | Yes, No |

### 5.4 What the record deliberately does not carry

| Not on the record | Why |
|---|---|
| `dependencies` / model chain | An ML Application has no upstream/downstream graph. |
| `type`, `codebase` provenance of a model | Its provenance is its **Estimator**. |
| `validation_questions` | It has its own questionnaire, from its own admin list. |
| `version_history` | There is no version. Every fit is a **train**, and the sequence of trains *is* the record of change. |
| `training_data`, metrics as record fields | These belong to the **train** that produced them. A copy on the record would be a second answer to the same question, free to disagree with the fit it describes. |
| `raci_roles` | Accountability for use in production sits on the **Product** that consumes it, where the RACI operating model already lives. Two RACIs would be asked the same question twice and allowed to differ. |

---

## 6. Trains — the evidence that a fit happened

**A train is one fit.** Not a version, not a release: an ML Application has no
versions, and the record of change is the sequence of trains, each with its own
snapshot, seed, hyperparameters and metrics. The **Training** tab shows the most
recent train in full; the **Trains** tab is the sequence.

53 typed fields, across six sections.

### 6.1 The order of the sections is governance, not pedagogy

Split (section C) comes *before* the preprocessing questions it constrains, which is
not the order a data scientist performs them in. It is the order that makes the leak
visible on the page: a scaler, an imputer or an encoder fitted before the split has
seen the test set, the reported test metric is inflated, and **everything below it
becomes unreliable**. A reader meets "fitted on: full dataset" already knowing what
the split was, and can tell in one line whether the numbers underneath are worth
reading.

### 6.2 No field is mandatory by default, and completeness is not a score

A complete set of 53 will not be reached on a real estate, and a form
that opens by declaring most of itself outstanding is a form somebody stops filling
in. What the tab reports is `filled / in-use` — progress against what the institution
asked for, not against our catalogue — and, separately and far more usefully, **what
has been recorded that a reviewer must be told about**.

A field either *applies* to a fit or it does not. A regression is not asked for a
loss curve it never produced; a classifier is not asked for nothing. Four conditional
rules narrow the form:

| Rule | Fires for | Fields it gates |
|---|---|---|
| `classification` | Binary or Multiclass classification (matched on the **stored** task value) | Target distribution |
| `neural task` | Sequence, Image | Epochs / batch size / early stopping; convergence evidence |
| `categorical features present` | Always offered — the platform cannot know | Categorical encoding |
| `probability consumed downstream` | Always offered — the platform cannot know | Calibration |

The last two are always shown rather than inferred, on the principle that a field
nobody is asked is a field nobody answers.

### 6.3 Captured by the run, or written by the owner

Everything a fit can report about *itself* is a fact rather than a judgement, so a
human retyping it adds nothing but the chance of a typo — and a metric transcribed by
hand is a metric nobody can tie back to the fit that produced it.

So the boundary is enforced in both directions:

- A field the platform does not mark capturable is **refused by name** when a run
  tries to report it: *"these are the owner's to write, not the run's to report"*. A
  producer that believes it recorded the split rationale, and did not, has been told
  something false about its own evidence.
- Fields that arrived by capture are stored as such (`captured_fields`) and shown
  read-only, so a reviewer can tell them from typed ones. A field the owner can
  hand-edit is a field a validator has to verify separately.

What is left to the owner is roughly seven text boxes: the target definition, the
intended and excluded uses, why the missing data was handled that way, why the split
does not leak, what the segment table means. **Those are the argument, and an
argument is not captured — it is made.**

### 6.4 The producer API

`modelrisk/capture.py` ships a small client with no dependencies beyond the standard
library. It collects what the fit knows and posts once, on exit:

```python
from modelrisk.capture import TrainingRun

with TrainingRun("MLA-0007", fit_id="2026-09-02-nightly") as run:
    run.data(snapshot_id=snapshot, row_count=len(X), feature_count=X.shape[1])
    run.split("Temporal", "70/15/15", scaler_fit_point="Train only")
    model.fit(X_train, y_train)
    run.fit(model, seed=42)                      # hyperparameters AS FITTED
    run.score("ROC-AUC", train=0.91, cv=0.84, test=0.83)
```

Four things it does without being asked, each answering a question the form would
otherwise have to ask a human:

- **The commit**, as a SHA — and stamped `(uncommitted changes)` when the tree is
  dirty, because a commit that does not describe what ran is worse than no commit.
- **The environment**, as installed library versions. A scikit-learn or TensorFlow
  minor release can change estimator behaviour without your code changing at all.
- **Hyperparameters off the estimator itself**, via `get_params()` — the defaults you
  did not pass are still the values it ran with.
- **It posts even when the fit raised.** A fit that fell over is a fact about the fit,
  and a train recorded as incomplete beats one nobody knows happened. The post never
  masks the original exception.

Re-reporting the same `fit_id` **updates** that train rather than creating a second
one, so a long fit can report as it progresses and a run that crashes after reporting
can report again. Every stored event carries the producer's provenance — source repo,
commit, producer and version, generated-at — which is the audit trail for a value
nobody typed and the answer to "where did this number come from?".

### 6.5 The fields, and why each is asked

Each note answers *"why is this required?"*, not *"what is this?"* — the label
already says what it is. A form that explains itself is a form somebody completes
honestly rather than plausibly, and several of these are the difference between a
number that means something and a number that does not.


#### A — Task and target (6 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Learning task**<br>`learning_task` | choice — `learning_task` | the run | always | Fixes what the rest of this tab asks for. A regression is not asked for a base rate; a classifier is. |
| **Target definition**<br>`target_definition` | textarea | the owner | always | The label AS CONSTRUCTED, in physical units and with its thresholds. Two teams can build the same-sounding target and predict different things. |
| **Features**<br>`features` | multichoice — `feature` | the owner | always | Which inputs, from the feature register. Linked rather than pasted, so a feature that turns out to be wrong or to have leaked can be traced to every fit that used it at once. |
| **Feature count**<br>`feature_count` | number | the run | always | How many inputs the fit had, as the run counted them. A jump between trains is a change of model, not a refresh of one -- and a count that exceeds the features linked above says the register is behind what was actually fitted. |
| **Intended use**<br>`intended_use` | textarea | the owner | always | What the output may be used for. Every other judgement on this tab is made against it. |
| **Excluded use**<br>`excluded_use` | textarea | the owner | always | What it may NOT be used for. An explicit exclusion can be policed; a general warning about misinterpretation cannot. |

#### B — Training data (5 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Snapshot identifier**<br>`snapshot_id` | text | the run | always | An immutable reference to the data as fitted. Without it nothing else on this tab can be verified — the numbers cannot be reproduced because the data they came from cannot be recovered. |
| **Training period**<br>`training_period` | text | the owner | always | What the fit has seen. A model cannot be assumed to hold in conditions outside it. |
| **Coverage**<br>`coverage` | textarea | the owner | always | Rows, columns, extent and exclusions. What was left out shapes the result as much as what was kept. |
| **Rows**<br>`row_count` | number | the run | always | The size of the fit. Read alongside the feature count: many features on few rows is how a model memorises rather than learns. |
| **Target distribution**<br>`target_distribution` | text | the owner | classification | The base rate. On a rare positive class a headline accuracy is dominated by the majority and says almost nothing. |

#### C — Split, preprocessing and validation (13 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Split method**<br>`split_method` | choice — `split_method` | the run | always | How the data was divided. This is the single most common way a reported metric turns out to be wrong. |
| **Split proportions (train/val/test)**<br>`split_proportions` | text | the run | always | How much was held back. A very small test set produces a metric with a confidence interval nobody quotes. |
| **Split rationale**<br>`split_rationale` | textarea | the owner | always | Why this split does not leak. On spatially or temporally correlated data a random split puts the same event on both sides, and the model is scored on data it has effectively seen. |
| **Missing data treatment**<br>`missing_data` | choice — `missing_data_treatment` | the run | always | Absent values are never absent from the result. Filling with a mean invents typical cases; dropping rows can drop a whole segment. |
| **Columns affected**<br>`missing_data_columns` | text | the owner | always | Which columns were affected, so the treatment can be judged against the features that mattered. |
| **Imputation fitted on**<br>`missing_data_fit_point` | choice — `scaler_fit_point` | the run | always | WHERE the imputation was fitted. A median computed over the full dataset leaks the test set into the fit exactly as a scaler does, and the leak is quieter: nobody thinks of filling in a blank as training on the answer. |
| **Categorical encoding**<br>`encoding` | choice — `categorical_encoding` | the run | categorical features present | How categories became numbers. Ordinal encoding of an unordered category asserts an ordering the data does not have. |
| **Scaling / normalisation**<br>`scaling` | choice — `scaling_method` | the run | always | Which transform was applied. It changes what the coefficients and the importances mean. |
| **Scaler fitted on**<br>`scaler_fit_point` | choice — `scaler_fit_point` | the run | always | WHERE the scaler was fitted. Fitted on the full dataset it has seen the test set, and the reported test metric is inflated. |
| **Cross-validation**<br>`cv_method` | choice — `cross_validation_method` | the run | always | How the fit was validated beyond one split. Stratification and grouping matter for the same reason the split does. |
| **Folds (k)**<br>`cv_folds` | number | the run | always | How many folds. Too few and the estimate is noisy; too many and it is expensive without being better. |
| **CV result (mean +/- std)**<br>`cv_result` | text | the run | always | The mean AND the spread. A single fold score hides instability, and the spread is what says whether the headline number is dependable. |
| **Times the hold-out was evaluated**<br>`test_evaluations` | number | the owner | always | How many times the hold-out was looked at. Every look leaks a little of it into the choices that follow; past a few, the test set has quietly become a validation set. |

#### D — Fit record (9 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Hyperparameters (as fitted)**<br>`hyperparameters` | textarea | the run | always | The values AS FITTED, not the defaults. A fit cannot be reproduced from a description of the algorithm alone. |
| **Search method**<br>`search_method` | choice — `search_method` | the run | always | How they were arrived at. An extensive search on a small validation set overfits the validation set. |
| **Random seed(s)**<br>`random_seed` | text | the run | always | What made this run this run. Without it 'we reran it and got something else' has no explanation. |
| **Determinism**<br>`determinism` | choice — `determinism` | the run | always | Whether it reproduces exactly, approximately, or not at all. An honest 'non-deterministic' is worth more than a false claim. |
| **Run date**<br>`run_date` | date | the run | always | When it was fitted. Everything about the world it was fitted in is dated from here. |
| **Duration**<br>`run_duration` | text | the run | always | How long it took. A retrain that cannot be afforded is a retrain that will not happen when it is needed. |
| **Hardware**<br>`run_hardware` | text | the run | always | What it ran on. GPU non-determinism and library builds are real sources of difference between two runs of the same code. |
| **Epochs / batch size / early stopping**<br>`epochs` | text | the run | neural task | How long it trained, and what stopped it. Early stopping on the test set is a leak; early stopping on a validation set is not. |
| **Convergence evidence**<br>`convergence_evidence` | text | the owner | neural task | The loss curve. It shows whether the fit converged or was merely stopped, which the final loss alone does not. |

#### E — Performance (12 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Primary metric**<br>`primary_metric` | choice — `primary_metric` | the run | always | The one number this fit is judged on, named before the results are read rather than chosen after them. |
| **Metric on train**<br>`metric_train` | text | the run | always | Performance on data it was fitted to. On its own it means nothing; against the test figure it is the overfitting evidence. |
| **Metric on CV**<br>`metric_cv` | text | the run | always | Performance across folds. The honest middle estimate between train and a single test split. |
| **Metric on test**<br>`metric_test` | text | the run | always | Performance on data it has never seen. The only figure that estimates behaviour in use — and only if C is sound. |
| **Secondary metrics**<br>`secondary_metrics` | textarea | the owner | always | What the headline metric hides. Accuracy conceals which class is being got wrong, and that is usually the one that matters. |
| **Calibration (curve + Brier)**<br>`calibration` | text | the owner | probability consumed downstream | Whether a stated probability means what it says. A model that ranks correctly but is mis-calibrated produces wrong prices and wrong capital, and ranking metrics will not show it. |
| **Naive baseline**<br>`baseline_kind` | choice — `naive_baseline` | the owner | always | The unskilled comparison. Beating a challenger means little if neither beats the base rate. |
| **Baseline score**<br>`baseline_value` | text | the owner | always | What the baseline actually scores, on the same metric, so the comparison is a comparison. |
| **Challenger comparison**<br>`challenger` | textarea | the owner | always | The credible alternative it was tested against, and by how much it won. 'Best available' is a claim; this is the evidence. |
| **Segment performance**<br>`segment_performance` | textarea | the owner | always | How it does by region, peril or period. A headline on a pooled dataset is dominated by the easy majority. |
| **Worst segment**<br>`worst_segment` | text | the owner | always | Named, not implied. The worst segment is where the model will first do harm, and it is the one nobody volunteers. |
| **Stability (bootstrap / repeated CV spread)**<br>`stability` | text | the owner | always | How much the headline moves under resampling. A metric quoted to four decimals with a wide spread is three decimals of theatre. |

#### F — Reproducibility (8 fields)

| Field | Type | Filled by | Asked when | Why it is asked |
|---|---|---|---|---|
| **Code reference (commit + repo)**<br>`code_commit` | text | the run | always | The exact code. A branch name is not a version. |
| **Environment (lockfile)**<br>`environment` | text | the run | always | The library versions. A scikit-learn or TensorFlow minor release can change estimator behaviour without changing your code. |
| **Serialised artefact (path + hash)**<br>`artefact` | text | the run | always | The fitted object and its hash, so what is scoring in production can be shown to be what was validated. |
| **Rebuild command**<br>`rebuild_command` | text | the owner | always | One line that rebuilds it. If it takes a paragraph, it is not reproducible. |
| **Independently reproduced by**<br>`reproduced_by` | text | the owner | always | Somebody other than the developer reran it and got the same numbers. This is the field that turns the whole tab from assertion into evidence. |
| **Reproduction matched**<br>`reproduced_matched` | choice | the owner | always | Whether it matched. A reproduction that did not is a finding, not an omission. |
| **Owner attestation**<br>`attested_by` | text | the owner | always | Who stands behind these numbers. A record with no name against it is nobody's to defend. |
| **Attested on**<br>`attested_date` | date | the owner | always | When they did. Attestation is required again on every train, because the numbers change. |

### 6.6 Qualifications — what a train says about itself

A train's evidence state is **computed, never set by hand**: the point of typing the
fields was to make this answerable, and a completeness figure somebody types is an
assertion like any other.

The state is not a pass mark. Either something has been recorded that a reviewer must
be told about — **Qualified** — or nothing has — **No findings**. Five rules raise a
qualification:

| Qualification | Raised when | Why it matters |
|---|---|---|
| The scaler was fitted on the full dataset | `scaler_fit_point` = Full dataset | It has seen the test set; the reported test metric is inflated. |
| The imputation was fitted on the full dataset | `missing_data_fit_point` = Full dataset | The same leak, and quieter — nobody thinks of filling in a blank as training on the answer. |
| The split rationale is too short to be an argument | A rationale under 80 characters | A random split on spatially or temporally correlated data leaks, and "random" is not an answer to that. |
| The hold-out has become a validation set | `test_evaluations` above 3 | Every look leaks a little of the hold-out into the choices that follow. |
| Nobody other than the developer has reproduced the fit | A test metric recorded with no `reproduced_by` — or a reproduction that did not match | This is the field that turns the tab from assertion into evidence. |

The reproduction rule fires **only once a metric has been reported**. Raising it
against a train that has not finished is telling somebody off for work they have not
done, which is how a tab teaches people to ignore it.

Both thresholds — 3 evaluations, 80 characters — are judgements, which is why they
live in `config/` where an institution can move them, and not in the code.

**Qualified is not a RAG rating.** The RAG rating is the record's risk — Materiality
× Complexity through the division's ratified heatmap, moved only by MRC sign-off. A
thin Training tab is a different fact from a risky model, and a reader must be able
to see both.

---

## 7. The review questions, and why each is asked

Ten questions, seeded on a fresh install, editable in Admin, and copied onto
each record at registration.

**Why ten and not nine.** A model's SR 26-2 questionnaire has nine
because SR 26-2 has nine. Padding or truncating a questionnaire an assessor reads
closely is worse than an uneven count, so the ML set is the length the ML subject
matter needs. An adopter rewords these, drops what does not apply and adds its own,
exactly as with the SR 26-2 set.

**Why they are a separate list.** An ML Application is asked different questions from
a model, and the two sets have to move independently — an institution that tightens
its ML questionnaire should not thereby change what it asks of a Monte Carlo pricing
model.

**1. Use Case**

> What decision does this model inform, and what is it explicitly not to be used for?

Every other answer on the record is judged against this one. A performance
figure means nothing until somebody has said what the output is for: an AUC of
0.78 is excellent for a triage queue and unusable for a capital calculation. The
second half — what it is **explicitly not** to be used for — is the half that
can be policed. "Use with care" cannot be enforced; "not to be used for
individual pricing decisions" can.

**2. Algorithm Choice**

> Why this estimator rather than a simpler or alternative one?

SR 26-2 asks for the reasoning behind a choice, not just the choice. For an ML
Application the choice most in need of defending is the estimator, because a
gradient boosting machine where a logistic regression would have done is the
single most common finding against an ML estate: it costs explainability,
stability and reviewability, and buys performance that is often within noise of
the simpler alternative. A good answer names the simpler alternative and says
what it scored.

**3. Training Data**

> What was it trained on, over what period, and is that population still representative?

Two questions in one, and the second is the live one. What it was trained on
bounds where its behaviour can be assumed to hold; whether that population is
**still** representative is the question that turns from Yes to No without
anybody touching the model. This is where a model quietly stops working — the
fit is unchanged and the world is not.

**4. Data Leakage**

> Could any feature encode information that would not be available at prediction time?

The failure that produces a brilliant validation result and a worthless deployed
model. A feature that encodes information unavailable at prediction time — a
field back-filled after the outcome is known, a post-event timestamp, an
identifier that correlates with the label because of how cases were assigned —
inflates every reported metric at once, so none of the numbers below it can be
trusted until this is answered. It is asked of the reviewer's judgement here
because no automated check finds it.

**5. Out-of-Sample Performance**

> How does it perform on data it was not trained on, and against which metric?

The only figure that estimates behaviour in use. The question says "against
which metric" rather than naming one on purpose: area under the curve is a
**classification** metric, and a regression has RMSE, MAE and R-squared. A
questionnaire that names a metric forces half an estate to answer dishonestly or
leave the field blank.

**6. Benchmarking**

> How does it compare with a simple baseline a reviewer would recognise?

A number with nothing beside it is not evidence. The comparison is to a baseline
a reviewer would recognise — the majority class, the base rate, last year's
value, the mean — because that is what says whether the machinery earned its
complexity. Beating a challenger means little if neither beats the base rate.

**7. Overfitting and Stability**

> How were hyperparameters selected, and how stable is performance across resamples and over time?

How the hyperparameters were arrived at is a question about the process, not the
values: an extensive search scored on a small validation set overfits that
validation set, and the resulting model looks better than it is. Stability
across resamples and over time is what separates a headline metric that will
hold from one that happened.

**8. Explainability**

> Can an individual prediction be explained to someone affected by it?

Asked as "can an individual prediction be explained to someone affected by it",
not "is the model interpretable". Global feature importances do not answer a
customer, a regulator or a complaints process asking why **this** case came out
this way, and it is the individual case that generates the obligation.

**9. Drift and Monitoring**

> What would show that it has stopped working, and who is watching for it?

Two halves, and both are required. What would show that it has stopped working
is a testable statement — a metric, a population, a threshold — and who is
watching for it turns that statement into somebody's job. A monitoring plan with
no name against it is a monitoring plan that runs until the person who wrote it
changes team.

**10. Weaknesses and Misinterpretation**

> Where does it fail, and how might its output be misread by a consumer?

The record already carries a weaknesses register; this question asks for the
part that a register of defects does not hold — how a **sound** output can be
misread by whoever consumes it. A calibrated probability presented as a
certainty, a ranking read as a score, a segment average applied to an
individual: the model is not wrong in any of these, and the decision is.


### How a question is answered

Each copy on the record carries a status from the shared question-status vocabulary
(admin-managed) plus the answer itself. A question counts as **answered** once a
status has been recorded that is not the not-yet word — the check is "a status was
set", not equality with a word we happen to ship, so an institution that renames its
vocabulary does not silently un-answer its estate.

Questions the division's policy has switched off are hidden from the tab but never
removed from the record. A record migrated from the inventory carries the *model's*
questions; those are still shown and still resolved, because a question the current
register does not list is a question that was nonetheless put to this record.

---

## 8. The ML review policy — the institution decides what it asks for

The ML review asks for a lot: 53 training fields and 10
questions. Every one of them is a reasonable thing to want. Asking for all of them at
once, of somebody who has just been handed the console, is how a governance tool gets
abandoned.

The list is not wrong. What would be wrong is **we** deciding it. So the catalogue
stays, and the institution says which of it applies.

### Two ticks per item

| Tick | Meaning |
|---|---|
| **In use** | The item appears on the ML Application's screens at all |
| **Mandatory** | The item must be filled before the review can be completed |

Two ticks rather than one three-state control, because they are two different
questions that an adopter answers at different times: switch things on to begin with,
tighten later once people are filling them in. `mandatory` implies `in_use` — an item
nobody is shown cannot be one they are required to answer — and that implication is
enforced in the domain rules, not left to a checkbox to remember.

One mechanism covers both catalogues: the training fields (defined in code; an
institution chooses among them) and the review questions (rows of an admin list;
already institution-owned). A single policy keyed by item id — `training:learning_task`,
`question:Data Leakage` — covers both.

### The rules that make it safe

1. **Default: everything in use, nothing mandatory.** An estate running today sees no
   change on the day a policy ships. Tightening is a deliberate act.
2. **Per division, and MRC-ratified**, on the same footing as the risk policy. What a
   review must contain is a governance standard, not a form preference: an
   institution that can quietly drop a mandatory item the week before an inspection
   has not got a standard at all. The Admin tab edits a **draft**; the draft becomes
   the live policy only when the committee approves it (Proposed → Approved /
   Rejected).
3. **A field that is switched off keeps its data.** Un-ticking hides a field; it does
   not erase what a train already recorded, and re-ticking shows it again. Governance
   records are append-only and a policy change is not a deletion.
4. **An item the policy has never heard of resolves to the default** — asked, not
   required. A question added to the register after ratification, or a training field
   shipped in a later release, appears on the screen rather than vanishing from it or
   silently becoming mandatory.
5. **Completeness counts the policy, not the catalogue.** `filled / in-use`. Mandatory
   gaps are counted and reported *separately*: progress and permission are different
   questions, and a bar at 40% that is nonetheless completable is not a contradiction.
6. **The gate is on completion, never on recording.** See below.

### Where the policy is resolved

Per record, **when the record is read** — never stored on it. A policy the committee
ratifies this morning applies to every record this afternoon without a view rebuild,
and a figure baked into a read model is a figure that goes quietly stale the moment
the standard behind it moves.

The same resolution serves three callers, which is why it is one function: the
screens (what to show, what to mark with a red rule), the completion gate (what may
not be blank), and the estate dashboard (how many records are short).

### The two gates

Both refusals are domain rules, so a script hits the same wall the UI does:

- **Marking the review complete** — setting review status to *Signed off*.
- **Raising the record for MRC sign-off.** The committee is asked to sign off a
  review, so the review has to be one.

A refusal **names what is outstanding**, item by item. A gate that says "3 items
missing" makes somebody open six sub-tabs to find them, and a gate people resent is a
gate that gets switched off.

A mandatory field that does not *apply* to a train is not missing — a classifier is
not withheld for want of a regression's diagnostic.

---

## 9. Risk rating and MRC sign-off

An ML Application is classified on **the same three dimensions as a model**: Tier,
Materiality and Complexity, with the same bands and the same Materiality × Complexity
heatmap, so its categorisation can be challenged on precisely the terms a model's
can. Each dimension carries its own rationale field, because a rating with no
argument behind it cannot be reviewed, only overruled.

The allowed values come from the **division's ratified risk policy**, not from a
static list in the code: an ML Application's bands are the ones its division's MRC
approved.

### The sign-off route

The owner **proposes** a rating; the record is routed to the committee responsible for
its division and line of business; and the **stored rating does not move until that
committee approves it**. Before this route existed, an ML rating applied directly —
which meant the one class of record most likely to be argued about was the one class
exempt from the committee that signs off everything else.

Mechanically, ML Applications are a fourth registration on the existing sign-off
adapter, alongside models, products and handoffs, so they appear in the meeting
agenda, the signoff tab and the MRC linkage history exactly as the others do. If no
committee covers the record's division, the request is refused with an instruction to
configure one — not silently queued.

### The four triggers, and they are the same four

A rating is one of them. The complete set that reaches the committee is the same for
an ML Application as for a model:

| Trigger | What the committee decides |
|---|---|
| **Risk rating** | The proposed RAG; the stored rating does not move until it approves. |
| **The review** | The reviewer signs off the seven-stage review and files the report the committee receives. |
| **A change of owner** | Who owns the record is who answers for it, so the appointment is ratified. The new owner takes the record straight away — it cannot sit ownerless — and the request carries both names, so the committee ratifies a *change* rather than a fact it cannot check. |
| **Presentation for analysis** | The record is put in scope at a meeting, and the committee records an outcome, a discussion note and the basis on which it is content for work to proceed. |

The last two only became true of ML Applications on **2026-09-06**. Until then a
change of ML Application owner went to nobody while a change of model owner was
ratified, and a meeting could put models and products in scope for analysis but not
ML Applications — so the record could be governed but never actually discussed. Both
were differences nobody had chosen; neither survived the question "is this governed
the same way a model is?".

---

## 10. The other registers on the record

| Register | What one row is | Why it is a register and not a paragraph |
|---|---|---|
| **Fairness assessments** | One protected attribute or group, how it was assessed, the metric, and what it showed | The question is asked per attribute and the answers differ: a model may be tested against age and never against postcode-as-a-proxy, and a single "we assessed fairness" field cannot say which. `attribute` is free text because which characteristics are protected is a matter of law and differs by jurisdiction. `finding` is prose, not pass/fail — "no disparity above the threshold" and "not measured" are different answers. |
| **Evaluations** | One evaluation run: kind, dataset, date, result, verdict | A held-out accuracy figure, a benchmark against a baseline and an adversarial attempt answer different questions and fail in different ways; averaged together they mean nothing. `result` is prose because half of what matters is not a scalar. The verdict may be blank — an exploratory run has a finding and no pass mark. |
| **Assumptions / Limitations / Weaknesses** | One item, with impact and status | Shared, unchanged, with the model inventory: the ISO/COSO `identification` and `treatment` probes read these, and an estate-wide question needs one shape. |
| **Remediation steps / Actions** | One thing somebody has to do, with an owner and a status | What the committee sees before it signs anything off. |
| **Data sources** | One feed, internal or external | For an ML Application this is where training and scoring data comes from. `kind` matters: an external feed is a third-party dependency — provenance, licensing, and whether the fit could be reproduced if it changed — and an internal one is not. Shared shape, so "which records share a source" is one query. |
| **Change history / Operational failure events** | What changed, and what went wrong in production | The evidence behind the change-management and incident clauses. |
| **Documents** | Uploaded evidence, filed by category | Testing evidence, monitoring output, review papers. The plot or the table is the evidence; the field beside it carries the *reading* of it. |
| **Review notes / Review sign-offs** | The owner–reviewer exchange, and the reviewer's conclusion | Append-only: this is the evidence that the record was challenged, and evidence that can be edited afterwards is not evidence. A correction is a new note, as it would be in minutes. |
| **Sign-off requests / history** | The trip through the committee | Shared with models and products. |

---

## 11. Where an ML Application shows up elsewhere

**Products.** A Product's `components` list carries both kinds. The row's `kind` says
whether `model_id` names an inventory model or an ML Application, and each kind
resolves against its own register — so a bound ML Application is named from the ML
register rather than reported as a missing model. A blank `kind` means Model, because
the log is append-only and every component bound before ML Applications existed
carries none: the default has to be the old meaning, or those rows change meaning
retrospectively.

**The completeness audit.** ML Applications are audited on the same terms as
everything else, in the same report, sorted into the same worst-first list. An estate
half of which is ML, audited on the other half, reports a gap picture that is wrong in
the direction that flatters — and nothing on the page would say so. Retired records
are out of the estate and out of every figure.

**Framework coverage (ISO 31000 / COSO / FINOS).** The clause probes count over one
population — models, ML Applications and AI Systems together. This is what §5.1's
field-name discipline buys.

**The dashboard and the attention queue.** ML Applications are collected into the
attention queue beside models and products — overdue reviews, outstanding sign-offs —
and an item on the dashboard opens the ML Application detail directly. The register
itself carries one extra tile, **Mandatory complete**, counting how many records meet
the division's standard. The tile stays off a register whose divisions have never
ratified a policy, rather than reporting a confident "0 short" about a standard
nobody has set.

**The ML Application Document.** A PDF for a single record, built from the same
shared blocks as the Model Risk Document and the Product Document so the three read
as one family. **Generated on request, never stored**, so it can never be a stale copy
of what the register says. The order is a reader's, not the record's: use case and
estimator lead, the classification and governance record follows, the registers and
the questionnaire close it. An unanswered question is printed **as unanswered** rather
than omitted — a dossier that silently drops what nobody filled in reads as a complete
record of a complete model.

---

## 12. The screens

**ML Apps** (the register) mirrors the Models register field for field — the same
tiles, filters and sortable table, driven by the same shared list component — because
the two are read side by side and a reader should not have to relearn the page.
Columns: ID, Name, Estimator, Criticality, Risk Rating, Owner, Next Review, MRC
Status, Lifecycle.

The detail view carries the same tabs a model does, less Connections (there is no
dependency graph to draw):

| Tab | What it holds |
|---|---|
| **Overview** | Identity, organisation, the estimator and method, the governance record. Mirrors the model Overview column for column; `use_case` leads, and `estimator` sits where a model's `type` does. |
| **Training** | The most recent train, in six sub-tabs (A–F). Fifty-odd fields in a single scroll is not a page anybody finishes. Mandatory items carry a left red rule; the badge counts `filled / in-use`. |
| **Trains** | The sequence of fits. This is the record of change. |
| **Review** | The testing-evidence flags and the questionnaire. The badge counts answered / asked. |
| **Risk Rating** | Tier, materiality, complexity, the rationales, and the request-sign-off action. |
| **Fairness** | One row per attribute assessed. |
| **Evaluations** | One row per evaluation run. |
| **MRC linkage** | The record's trips through the committee. |
| **Docs** | Uploaded evidence by category, and the generated ML Application Document. |
| **Danger** | Retire. Retiring stops all further edits; the record and its history are kept. |
| **Audit** | Every event on the record, in order, with actor and reason. |

---

## 13. API and configuration reference

### Endpoints

| Method | Path | What it does |
|---|---|---|
| `GET` | `/api/ml-applications` | The register |
| `GET` | `/api/ml-applications/<id>` | One record, with its resolved review scope |
| `GET` | `/api/ml-applications/fields` | Field specs, choices and estimator versions — what the screens are built from |
| `POST` | `/api/ml-applications` | Register |
| `POST` | `/api/ml-applications/<id>/field` | Edit one field. Setting review status to *Signed off* is the one edit the policy gates |
| `POST` | `/api/ml-applications/<id>/collections/<collection>[/<item_id>][/delete]` | Register items |
| `POST` | `/api/ml-applications/<id>/request-signoff` | Propose a rating to the MRC (gated) |
| `GET` | `/api/ml-applications/<id>/risk-rating` | The resolved rating and the division's heatmap |
| `POST` / `GET` | `/api/ml-applications/<id>/documents…` | Upload, download, delete evidence |
| `GET` | `/api/ml-applications/<id>/document.pdf` | The generated ML Application Document |
| `POST` | `/api/ml-applications/<id>/retire` | Retire |
| `POST` | `/api/ingest/ml-training-run` | A run reports a train (201 new, 200 updated) |
| `GET` | `/api/ml-review-policy[/<division>]` | The live policy, and the pending draft |
| `POST` | `/api/ml-review-policy/<division>/propose\|approve\|reject` | The ratification lifecycle |

### Where the rules live

| Concern | File |
|---|---|
| Record fields, collections, register minimum | `config/governance/_ml_application.py` |
| Estimators, features, the question set | `config/governance/_ml.py` |
| Training schema, sections, vocabularies, thresholds | `config/governance/_ml_training.py` |
| Why each training field is asked | `config/governance/_ml_training_notes.py` |
| Policy shape, item ids, resolution | `config/governance/_ml_review_policy.py` |
| Validation (pure) | `src/governance/ml_application/_rules.py` |
| Commands, questionnaire seeding | `src/governance/ml_application/commands.py` |
| Train completeness and qualifications | `src/governance/ml_application/training.py` |
| Policy resolution and the completion gate | `src/governance/ml_application/review_scope.py` |
| Capture boundary | `src/governance/ml_application/capture.py` |
| The producer client | `modelrisk/capture.py` |

---

## 14. Deliberate gaps

Stated here so they are not mistaken for oversights.

- **No dependency chain.** ML Applications have no upstream/downstream graph, so a
  Product with ML components has an incomplete chain view by construction.
- **Orphans.** An ML Application no Product binds is governed by nothing structural
  above it — it is still audited, but nothing points at it.
- **Does the heatmap still discriminate?** If ML Applications rate High complexity
  essentially by construction, the map stops separating the risky ones from the rest
  across the ML population, which is where a reader most needs it. The obvious lever
  — the per-division risk policy — is keyed by division rather than by record type,
  so recalibrating "High complexity" for an ML population would move it for that
  division's traditional models too. Worth revisiting once an estate is large enough
  to show whether the population actually clusters.
- **The day-one coverage dip.** The moment ML Applications are registered with
  governance fields not yet filled, they enter the denominator of every clause probe
  and clauses slide from Evidenced to Partially evidenced across the board. That is
  the audit working correctly, but during a pilot it will look like a regression —
  onboard with the fields populated, or explain the dip in advance.
- **The estimator version is free text.** Constraining it to the chosen estimator's
  own version list is a dependent dropdown, which nothing in the reference specs does
  yet.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
