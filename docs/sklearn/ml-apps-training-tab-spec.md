# ModelRisk — ML Apps → Training subtab

**Design specification v0.1**
Reference model: MKM-FC-001 Flood Probability Classifier
Evidence spine derived from the standard supervised-learning pipeline (Malik, *Python Machine Learning for Beginners*, ch. 5–10)

---

## 1. Problem with the current subtab

The Training subtab today holds nine rows, seven of them free-text and six of them empty. Two structural weaknesses, not one:

1. **Wrong granularity.** "Training data — *(string)*" is a single field standing in for provenance, snapshot identity, coverage, class balance and preprocessing. A validator cannot challenge it because there is nothing specific to challenge.
2. **Wrong field types.** Every row is an unconstrained string. That makes the tab unqueryable. You cannot ask the estate-level question — *which models were fitted with a random train/test split on spatially correlated data?* — which is precisely the aggregation BCBS 239 expects the MRC to be able to run.

The fix is to type the fields, not just add more of them. Enumerations where an enumeration exists; numerics where the thing is a number; artefact references where the evidence is a plot or a file; free text reserved for **rationale only**.

## 2. Design principle

Every step a developer actually performs when fitting a model is a step a validator must be able to reconstruct. The book's pipeline gives the ordering for free:

| Book step | Ch. | Evidence obligation |
|---|---|---|
| Load and inspect data | 4–5 | Provenance, snapshot, coverage, target distribution |
| Features and labels | 6.1.1 / 7.1.1 | Target definition, feature inventory |
| Encode categoricals | 6.1.2 / 7.1.2 | Encoding method, cardinality handling |
| Train/test split | 6.1.3 / 7.1.3 | Split method **and rationale** |
| Scale / normalise | 6.1.4 / 7.1.4 | Scaler, and **where it was fitted** (leakage) |
| Dimensionality reduction | 10 | Method, components, variance retained |
| Fit algorithm | 6.2–6.5 / 7.2–7.5 / 9 | Algorithm, hyperparameters, seed, run record |
| K-fold cross-validation | 6.6 / 7.6 | k, stratification, mean ± std |
| Evaluate | 6.6 / 7.6 / 9.1.3 | Metrics on train / CV / test, baseline, segments |
| Predict single record | 6.7 / 7.7 | Serving path matches training path |

Note the order matters as governance, not just pedagogy. Sections 4.3 (split) and 4.4 (preprocessing) are ordered so that the tab makes the leakage question visible: if the scaler or the encoder was fitted before the split, the reported test metric is inflated and everything downstream in the tab is unreliable.

## 3. Structure

Six ordered sections inside the Training subtab, each collapsible, each with its own completeness pip. Keep the existing two-column row layout and `edit` affordance — this is a schema change, not a re-skin.

```
Training
├── A. Task and target          (5 fields)
├── B. Training data            (8 fields)
├── C. Split and validation     (6 fields)   ← the section that currently doesn't exist
├── D. Fit record               (7 fields)
├── E. Performance              (7 fields)
└── F. Reproducibility          (6 fields)
```

Existing rows migrate: *Training data* → B, *Training period* → B.3, *Performance* → E, *Benchmark comparison* → E.4, *Scope for misinterpretation* → A.5. *Unit / integration / benchmark tests* and *Monitoring approach* move out to the Review and Retrains subtabs respectively — they are not training-approach evidence and they dilute the section.

---

## 4. Field schema

`M` = mandatory for Green. `C` = conditional (rule stated). `O` = optional.

### A. Task and target

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| A.1 | Learning task | enum | M | regression / binary classification / multiclass / clustering / dim. reduction / sequence / image. **Drives all conditional fields below.** |
| A.2 | Algorithm | enum + free text | M | logistic regression, KNN, random forest, SVC, dense NN, LSTM, CNN, k-means, hierarchical, PCA, LDA, other |
| A.3 | Target definition | text | M | The label as constructed, in physical units and with thresholds. For MKM-FC-001: what depth, at what point on the parcel, over what window, from which hazard source. |
| A.4 | Feature inventory | ref → feature dictionary + count | M | Link, not a paste. Count shown inline. |
| A.5 | Intended use / excluded use | text ×2 | M | Two-sided. Replaces "Scope for misinterpretation" — an explicit excluded-use list is far easier to police than an abstract misinterpretation note. |

### B. Training data

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| B.1 | Source dataset(s) | ref → data inventory | M | System of record per source. BCBS 239 lineage anchor. |
| B.2 | Snapshot identifier | hash / version string | M | Immutable. If the fit cannot be tied to a frozen snapshot, nothing else in this tab is verifiable. |
| B.3 | Training period | date range | M | Existing field. |
| B.4 | Coverage | text + counts | M | Rows, columns, geographic/portfolio extent, exclusions applied. |
| B.5 | Target distribution | numeric / artefact | C | Mandatory for classification. Base rate and class counts. For a flood classifier the positive class is rare and this number governs how E.1 should be read. |
| B.6 | Missing data treatment | enum + text | M | drop / mean / median / mode / model-based / none; plus the affected columns. |
| B.7 | Categorical encoding | enum | C | one-hot / ordinal / target / embedding / n-a. Mandatory if any categorical feature present. |
| B.8 | Scaling / normalisation | enum + fit-point | M | standard / min-max / robust / none, **and** fitted on: train only / full dataset. "Full dataset" is an automatic amber. |

### C. Split and validation protocol

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| C.1 | Split method | enum | M | random / stratified / temporal / spatial-group / entity-group / predefined |
| C.2 | Split proportions | numeric ×3 | M | train / validation / test |
| C.3 | Split rationale | text | M | **The single highest-value field on the tab.** A random split on flood data leaks: neighbouring parcels share the same event and the same catchment. The owner must state why the chosen split does not leak. |
| C.4 | Cross-validation | enum + k + stratified flag | M | Book 6.6 / 7.6. |
| C.5 | CV result | mean ± std | M | The spread is the point. A single fold score hides instability. |
| C.6 | Test-set discipline | integer + declaration | M | Number of times the hold-out was evaluated against during development. Anything above a small number means the test set has become a validation set. |

### D. Fit record

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| D.1 | Hyperparameters | JSON | M | Full dict as fitted, not the defaults. |
| D.2 | Search method | enum + space | O | none / manual / grid / random / Bayesian |
| D.3 | Random seed(s) | integer(s) | M | |
| D.4 | Determinism statement | enum | M | bit-reproducible / reproducible to tolerance / non-deterministic + reason |
| D.5 | Run record | date, duration, hardware | M | |
| D.6 | Epochs / batch size / early stopping | numeric | C | Mandatory for NN tasks (A.1 ∈ {sequence, image, dense NN}). |
| D.7 | Convergence evidence | artefact | C | Loss curve. Mandatory for NN tasks. |

### E. Performance

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| E.1 | Primary metric | enum + 3 numerics | M | Value on **train / CV / test**. Three numbers, not one. The train–test gap *is* the overfitting evidence, and the current single "Performance" field destroys it. |
| E.2 | Secondary metrics | numeric set | C | By task: classification → precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix; regression → MAE, RMSE, R²; clustering → silhouette, inertia. |
| E.3 | Calibration | artefact + Brier score | C | Mandatory where the output is a probability consumed downstream. For MKM-FC-001 this is not optional — a classifier that ranks correctly but is mis-calibrated produces wrong prices and wrong capital. Reliability curve plus Brier. |
| E.4 | Naive baseline | enum + value | M | Majority class / climatological base rate / persistence, scored on the same metric. Distinguish from E.5 — beating a challenger model means little if neither beats the base rate. |
| E.5 | Challenger comparison | text + value | M | Existing "Benchmark comparison". |
| E.6 | Segment performance | table | M | By region / peril / return period. **Worst segment must be named.** Headline metrics on a nationally-pooled flood dataset are dominated by the dry majority. |
| E.7 | Stability | numeric | O | Bootstrap or repeated-CV spread on the primary metric. |

### F. Reproducibility and attestation

| # | Field | Type | Req | Notes |
|---|---|---|---|---|
| F.1 | Code reference | commit SHA + repo | M | |
| F.2 | Environment | lockfile ref | M | Library versions. `sklearn` and `TF` minor versions change estimator behaviour. |
| F.3 | Serialised artefact | path + hash | M | |
| F.4 | Rebuild command | text | M | One line. If it takes a paragraph, it is not reproducible. |
| F.5 | Independent reproduction | name, date, matched? | M | Someone other than the developer reran it and got the same numbers. This is the field that converts the whole tab from assertion to evidence. |
| F.6 | Owner attestation | name + date | M | Re-attestation required on every retrain (link to Retrains subtab). |

---

## 5. Completeness and RAG

The status chip currently reads *Green / Development*, which is doing no work while six of nine rows are empty. Proposed rule:

- **Red** — any mandatory field in A, B or C empty.
- **Amber** — all mandatory fields populated but any of: B.8 fit-point = full dataset; C.3 rationale absent or under a substantive threshold; C.6 test evaluations above the agreed cap; F.5 not performed.
- **Green** — all mandatory and applicable conditional fields populated, no amber triggers, F.5 matched, F.6 attested within the current retrain cycle.

Completeness is computed, never set by hand. The subtab header shows `Training (23/31)` in the same style as the existing `Retrains (2)` and `Review (4/9)` counters.

## 6. Data model sketch

```python
class TrainingEvidence(Base):
    __tablename__ = "ml_training_evidence"
    id            = Column(Integer, primary_key=True)
    model_id      = Column(String, ForeignKey("models.id"), nullable=False)
    fit_id        = Column(String, nullable=False)   # one row per fit, not per model
    learning_task = Column(Enum(LearningTask), nullable=False)
    ...
    __table_args__ = (UniqueConstraint("model_id", "fit_id"),)
```

Two points worth locking in early:

- **One row per fit, not per model.** A retrain is a new `fit_id` with a new snapshot, new seed and new metrics. The Retrains subtab then becomes a view over this table rather than a separate store, and metric drift across retrains is a query rather than a manual comparison.
- **Field definitions live in one config module**, not in the template. The section/field/type/requirement table above should be a single declarative structure that generates the form, the validation, the completeness calculation and the audit-log field names. Adding a field is then a one-line change in one place.

## 7. Population route

Most of B, D and F is machine-readable at fit time. A thin `modelrisk.ml` decorator or context manager around the training entry point can capture snapshot hash, hyperparameters, seed, library versions, commit SHA, run duration and artefact hash automatically, and POST them. That leaves the owner to type only the fields that require judgement — A.3, A.5, B.6 rationale, C.3, E.6 commentary — which is roughly seven text boxes rather than thirty-one.

Auto-captured fields should be flagged as such in the audit trail and made read-only in the UI. A field the owner can hand-edit is a field a validator has to verify separately.

---

© 2022–2026 MKM Research Labs. Licensed under the MIT License.
