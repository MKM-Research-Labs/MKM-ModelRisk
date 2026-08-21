# ML Applications — design and project plan

**Status:** Phase 1 built on branch (admin lists), phases 2–5 outstanding
**Date:** 2026-08-21
**Area:** ML Applications / Products / MRC
**Driver:** A named Moody's use case — a Product that draws on several models *and*
several ML Applications. Functionality is expected to evolve once that feedback lands.

---

## 1. Scope

**In scope:** classical / statistical machine learning — regression, GLMs, gradient
boosting, random forests. The trained-on-data estate.

**Out of scope:** LLMs and agentic AI. Nothing in this plan should be designed to
accommodate them; if they arrive they arrive as their own question.

## 2. The decision

Three layers, each a different kind of thing:

| Layer | What it is | Where it lives |
|---|---|---|
| **Estimator** | The off-the-shelf ML engine — its source, name and available versions | Admin reference list |
| **ML Application** | *This institution's use case for that estimator* — the governed record | Its own section, apart from Models |
| **Product** | Binds several models **and** several ML Applications | Existing `components` collection |

The middle layer is the whole point. An ML Application record is a **use case for an
off-the-shelf estimator**: nobody validates scikit-learn's implementation of gradient
boosting, they validate the firm's use of it. That is the standard vendor-model /
implementation split, and it is what the record is for.

### Terminology, and why it is not "ML Model"

`Model` is the platform's central noun and stays reserved for the inventory — a second
record type carrying the word would collide in the sign-off tabs, in the audit output,
in `model_id` / `get_model` / `list_models`, and in every conversation about either.
The irony is worth recording: a data scientist would call a fitted estimator applied to
a use case "a model", so the natural word is precisely the unavailable one.

`Component` was likewise already taken — a Product has a `components` collection, so
"ML component" would have become ambiguous the moment an ML record reached a Product.

**Estimator** and **ML Application** are free in both namespaces and idiomatic to both
audiences. "Application" is the standard term in vendor-model governance — a vendor
supplies the model, the institution is accountable for its *application* of it — which
is exactly the split this design turns on.

*"ML Instance" was considered and rejected.* In ML usage an instance is a single
training example — Weka's data class is literally `Instances`, scikit-learn says
"samples" — so the data scientists filling these records in would have read it as a
data row.

### Why ML Applications sit apart from the model inventory

Not because they are a different subject — because they change at a different rate.
The governance framework around models is settled (SR 26-2 has not moved in years);
ML functionality will evolve through the Moody's rollout. The boundary exists to keep
that churn away from the record type that MRC sign-off, the completeness audit and
every issued document already depend on.

The corollary is that **the join has to be the boring part**. An ML Application does *not*
link to a model. It links to a Product, alongside models. That is the only connection.

### Self-contained record, borrowed machinery

An ML Application carries its own validation, review and challenge — a Product delegates
validation downwards to its components, and the model inventory will not know these
records exist, so nothing above them will do it for them.

"Self-contained" means **its own records, not its own code.** Products already reuse
`limitations`, `assumptions`, `remediation_steps`, `actions`, `signoff_requests` and
`signoff_history` from the shared `COLLECTION_SPECS` rather than reimplementing them.
ML Applications follow that precedent. Three review workflows and three MRC sign-off paths
in one system would drift, and sharing the plumbing is what confines the churn to the
ML-specific fields — which is the reason for the separation in the first place.

## 3. What already exists (and is not to be rebuilt)

- **Products are already an open component list.** `product-as-components.md`, accepted
  2026-07-29: `PRODUCT_BINDINGS` is down to `calculating_agent` alone, and the
  `components` collection carries `component_type` / `model_id` / `role` with a
  Components tab shipped. "A product links to several models" is **done**.
- **The MRC route already generalises past two aggregates.** `src/web/_signoff_subject.py`
  defines a `Subject` adapter — "the routing is written once for both kinds" — and it
  already carries three: model, product, handoff. ML Applications are a fourth registration,
  not a new route.
- **Questionnaires are already adopter-managed and snapshotted.** `REVIEW_QUESTION_LIST`
  is an admin list, seeded from SR 26-2, *copied onto each record at registration*, so a
  record keeps the questions it was actually asked. The ML set reuses this mechanism.
- **The VQ status vocabulary** (`VQ_STATUS_LIST`) is shared unchanged.

## 4. Decisions taken

1. **One Estimator row per source + estimator name**, carrying available versions and notes.
   The row list *is* the menu of industry norms. Not one row per version — that explodes
   combinatorially and makes the row meaningless.
2. **The ML Application picks the Estimator and the version.** Menu in admin, choice on the
   record.
3. **`source` is a field, not an assumption.** Not hardcoded to sklearn: production
   gradient boosting is often XGBoost or LightGBM, and regression is often statsmodels
   or R. Seeded, extensible. It is *not* the `vendor` list — an open-source library is
   not a supplier with due diligence behind it.
4. **Named Estimator and ML Application, not "ML Model"** — `model` and `component` are
   both already taken. See §2.
5. **A separate `ml_application_questions` list**, same shape and snapshot behaviour as the
   existing one. Content differs; mechanism does not.
6. **Same MRC route, non-negotiable.** ML Applications appear in the sign-off surfaces
   alongside models and products.
7. **ML Applications are counted in the completeness audit and framework coverage.**
   An uncounted ML estate would leave the ISO/COSO tables describing a shrinking non-ML
   slice while reporting it as the whole.

   This is the decision that sizes the work. The probes in
   `src/governance/completeness/framework.py` are field-name lambdas over a single
   `estate["models"]` population — `analysis` reads `tier` / `materiality` /
   `complexity`, `accountability` reads `owner`, `criteria` reads `division` against the
   ratified policies, `treatment` reads `remediation_steps` when the rating is Red or
   Amber, and so on. So an ML Application must carry **the same governance field names a
   model carries**, not merely equivalent ones:

   `owner`, `division`, `tier`, `materiality`, `complexity`, `rag_rating`,
   `next_review_date`, and the `assumptions` / `limitations` / `model_weaknesses` /
   `remediation_steps` / `version_history` / `signoff_history` / `review_notes`
   collections.

   Do that and the probes run over a merged population unchanged. Diverge on names and
   every probe grows a per-type branch — thirteen of them, each a place to forget one.
8. **The same risk classification as a model** — the same three dimensions, the same tier
   bands, the same Materiality x Complexity heatmap, so an ML Application's categorisation
   can be challenged on the same terms as a model's. This follows from decision 7 in any
   case: the `analysis` probe reads `tier` / `materiality` / `complexity` and nothing else
   would satisfy it.

## 5. Open questions

- **One component list on a Product, or two?** Extending `components` so an entry points
  at either an inventory model or an ML Application keeps "what is this built from" a single
  list. Two parallel collections means every consumer has to read both, and the ones that
  forget under-report silently — the worst failure mode on a completeness audit.
  *Leaning: one list with a kind discriminator.*
- **Does the heatmap still discriminate?** (Sharpened by decision 8, not answered by it.)
  If an ML Application rates High complexity essentially by construction, the map stops
  separating the risky ones from the rest across the whole ML population — precisely
  where the reader needs it most.

  The obvious lever is the per-division risk policy, which already lets a division say
  what its bands mean and have its MRC ratify it. But the policy is keyed by **division**
  (`aggregate_id=division` in `src/governance/risk_policy/_store.py`), not by record type,
  so recalibrating "High complexity" to suit an ML population would move it for the
  traditional models in that division too. Unless ML Applications get their own divisions
  — which nobody wants — the lever does not reach. Worth watching once Moody's has enough
  ML Applications registered to see whether the population actually clusters.
- **The day-one coverage dip.** `COVERAGE_EVIDENCED_AT` is 0.90. The moment Moody's
  registers ML Applications with governance fields not yet filled, they enter the
  denominator of every probe and clauses slide from Evidenced to Partially evidenced
  across the board. That is the audit working correctly, but it will look like a
  regression during a pilot, so decide whether to onboard with the fields populated or
  to explain the dip in advance.
- **Products still are not counted.** `coverage()` takes `rows` and `models` only. After
  this decision the estate has three record types and the audit counts two, which is an
  asymmetry somebody will ask about even though it predates this work.
- **Orphans.** An ML Application no Product binds is governed by nothing and invisible to the
  audit. On the inventory everything is swept up whether or not anyone remembers it.
- **Chains.** ML Applications have no dependency chain. But `product-as-components.md` justifies
  the open component list by saying how components connect is captured by model
  dependencies and the Model Chain. A product with ML Application components therefore has
  an incomplete chain view by construction. Acceptable, but it is a deliberate gap.
- **Version dropdown.** Constraining the version choice to the selected Estimator's
  versions is a dependent dropdown. Nothing in the current reference specs cascades
  (`line_of_business` carries a parent field on the *entry*, which is not the same thing),
  and UI here is hand-curated. Costed in phase 2, not phase 1.

## 6. Plan

### Phase 1 — Admin (start here)

Both lists are pure vocabulary, and nothing downstream can be shaped until they are.

- New `config/governance/_ml.py`. **Required, not stylistic:** `_reference.py` is at 293
  lines against R2's 300-line source gate, and `config/governance/__init__.py` at 298.
  Both re-export points need care.
- `estimator` reference list — estimator (display), source, versions, notes.
- `ml_application_questions` reference list — same shape as `REVIEW_QUESTION_LIST`.
- Seeds following the established rule in `src/governance/reference/commands.py`: **seed a
  vacuum, never reconcile a curated list**, wired into `src/web/_startup.py`.
- ~~**Backfill.**~~ **Not needed — verified 2026-08-21.** The concern was borrowed from the
  standing-agenda work, but that was a new *kind* inside an list that already had rows, so
  the vacuum rule skipped it. These are brand-new lists: on a scratch DB restored from the
  live estate both were empty and seeded on boot (18 estimators, 10 questions). No backfill
  ships with this.
- Admin tab wiring — hand-curated, not spec-driven.

**Line budgets after phase 1.** `config/governance/__init__.py` now sits at **exactly 300**,
which is the R2 gate: the next name added to it trips the audit, so it wants splitting before
anything else re-exports through it. `_reference.py` is at 298. `reference.js` went to 315 —
reported, not gated, and mid-pack among the existing web files.

### Phase 2 — The ML Application record

No chains and no dependencies — but decision 7 makes this the biggest *design* phase
rather than a light one. The record has two halves:

- **The governance half** — field-for-field the same names a model uses, so the audit
  probes and the `Subject` adapter both work over it without special cases.
- **The ML half** — use case, algorithm choice against alternatives, training data,
  performance, weaknesses and scope for misinterpretation, plus the chosen Estimator
  and version.

What it deliberately does *not* carry: chains, dependencies, `type` / `vendor` /
`codebase` / `repo_location`, and the SR 26-2 questionnaire — it has its own.

**Choose the id scheme and event names here, with the MRC route in mind, and keep them
neutral with respect to the display label.** The log is append-only: the screen wording
is cheap to change later, ids and event names are not.

### Phase 3 — Link to Products

Resolve the one-list-or-two question, then extend the Components tab.
Housekeeping to decide at the same time: `product-as-components.md` follow-up 2 —
remove the now-vestigial `binding_role` from `model_type`, deferred on 2026-08-11 until
"Product functionality is reviewed". This is that review.

### Phase 4 — MRC and sign-off

Register a fourth `Subject`; surface ML Applications in the sign-off tabs.

**This is the largest phase, not a footnote.** Thirteen JS files reference sign-off,
including the MRC detail panels, and CLAUDE.md is explicit that these surfaces are
hand-curated — a config field is not enough. `api_models_signoff.py` and
`api_product_signoff.py` are parallel per-type modules; a third continues that pattern
and is worth looking at before it triplicates.

### Phase 5 — Expand on Moody's feedback

Deliberately unplanned.

## 7. Draft ML Application review questions

For editing, not adoption. Ten rather than nine — SR 26-2 has nine because SR 26-2 has
nine, and padding or truncating a questionnaire an assessor reads closely is worse than
an uneven count. Cut what does not apply.

| Topic | Question |
|---|---|
| Use Case | What decision does this model inform, and what is it explicitly not to be used for? |
| Algorithm Choice | Why this estimator rather than a simpler or alternative one? |
| Training Data | What was it trained on, over what period, and is that population still representative? |
| Data Leakage | Could any feature encode information that would not be available at prediction time? |
| Out-of-Sample Performance | How does it perform on data it was not trained on, and against which metric? |
| Benchmarking | How does it compare with a simple baseline a reviewer would recognise? |
| Overfitting and Stability | How were hyperparameters selected, and how stable is performance across resamples and over time? |
| Explainability | Can an individual prediction be explained to someone affected by it? |
| Drift and Monitoring | What would show that it has stopped working, and who is watching for it? |
| Weaknesses and Misinterpretation | Where does it fail, and how might its output be misread by a consumer? |

Note on metrics: **area under the curve is a classification metric.** A regression model
has RMSE, MAE and R². Whatever captures performance must hold both, or half the stated
estate cannot answer honestly.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
