# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Phase 2 of the Test Results backlog: per-model governance completion.

Phase 1 (``scripts.file_test_results_backlog``) filed test evidence and set the
test declarations for 17 models. Phase 2 completes the remaining governance
fields — the validation date and the seven unrecorded validation questions — which
need per-model judgement and so are done in tranches, not one sweep.

Each model's validation_date is anchored to its real final-version date (from the
existing version history); recertification dates and version/change history are
already populated on these records, so they are left untouched. The validation
questions are assessed on each model's actual behaviour: the genuinely satisfied
ones move up, while override controls, data quality, benchmarking and independent
validation stay "Not Addressed" with a rationale — the honest basis for each Red
rating. VQ-006/007 (assumptions, limitations) are already Addressed on the live
records and are listed only so a freshly-registered model is also completed; the
idempotency guard leaves the live rows untouched.

Tranche 1: the flood-hazard chain — DD, FPO, FC, SP, SG.
Tranche 2: BRI, DE, FIRE, GHD, IP, MP. Later tranches extend ``MODELS`` and
re-run (idempotent). A model whose recertification_date is also blank carries one
in its spec; otherwise only the validation_date and questions are filled.

Run as:  python -m scripts.complete_governance_phase2
"""
from __future__ import annotations

from src.governance.model_inventory import (
    get_model,
    rebuild_inventory_view,
    update_collection_item,
    update_model_field,
)

ACTOR = "complete_governance_phase2"

# Model-agnostic honest assessments (identical wording across the tranche).
_A_ASSUMPTIONS = ("Addressed",
    "The model's assumptions are documented and justified in the Assumptions "
    "register on this record.")
_A_LIMITATIONS = ("Addressed",
    "The model's limitations are documented and monitored in the Limitations "
    "register on this record, with monitoring triggers.")
_NA_OVERRIDES = ("Not Addressed",
    "Controls over manual overrides are not documented; parameters live in the "
    "config package but there is no governed, logged override mechanism. "
    "Outstanding.")
_NA_DATA = ("Not Addressed",
    "Input-data quality is not assured: the model runs on synthetic data whose "
    "realism is unvalidated. Data-quality controls are outstanding.")
_NA_BENCHMARK = ("Not Addressed",
    "The model has not been benchmarked against a credible independent "
    "alternative; no benchmark evidence is on record (benchmark_tests = No).")
_NA_INDEP = ("Not Addressed",
    "Not independently validated; this is the basis for the current Red rating. "
    "Independent validation is outstanding.")


def _vq(ronseal, accuracy, resource):
    """Assemble a full 9-question set from the three model-specific answers."""
    return {
        "VQ-001": ("Addressed", ronseal),
        "VQ-002": ("Partially Addressed", accuracy),
        "VQ-003": ("Addressed", resource),
        "VQ-004": _NA_OVERRIDES,
        "VQ-005": _NA_DATA,
        "VQ-006": _A_ASSUMPTIONS,
        "VQ-007": _A_LIMITATIONS,
        "VQ-008": _NA_BENCHMARK,
        "VQ-009": _NA_INDEP,
    }


MODELS = {
    "MKM-DD-001": {
        "name": "Depth-Damage Curve Model",
        "validation_date": "2025-11-15",
        "vq": _vq(
            "Implements piecewise-linear and polynomial depth-damage functions "
            "mapping flood depth to a property damage ratio with property-type "
            "factors — its documented purpose.",
            "The curves are calibrated and numerically stable, the unit suite "
            "passes, and the depth sensitivity analysis confirms a well-behaved "
            "concave response. The curves are not validated against observed loss "
            "data (synthetic calibration), so this is partial.",
            "Damage is a scalar lookup / low-degree polynomial evaluation; "
            "negligible computational resource use."),
    },
    "MKM-FPO-001": {
        "name": "Flood Polynomial Model",
        "validation_date": "2026-03-28",
        "vq": _vq(
            "Provides a closed-form logistic-polynomial surrogate for the GBM "
            "flood classifier in log-feature space (log water margin and log storm "
            "time) — its documented purpose.",
            "The surrogate reproduces the GBM to R^2 ~ 0.94 (MAE ~ 0.046) and is "
            "deterministic with a passing unit suite. The underlying flood "
            "probability is unvalidated on real events and the surrogate "
            "over-predicts in the alert-to-severe transition, so this is partial.",
            "A closed-form evaluation that removes the need to load a trained GBM "
            "at inference; trivial resource use."),
    },
    "MKM-FC-001": {
        "name": "Flood Probability Classifier",
        "validation_date": "2026-03-03",
        "vq": _vq(
            "A gradient-boosting classifier estimating per-gauge flood probability "
            "from water level, storm hour, velocity and acceleration — its "
            "documented purpose.",
            "The classifier reports a high in-sample discrimination (AUC ~ 0.99 on "
            "a large sample) and is trained and tested reproducibly. The labels "
            "are synthetic, so real-world accuracy is unvalidated and this is "
            "partial.",
            "Training is an offline batch step; inference is cheap and is in "
            "practice served by the FloodPoly closed-form surrogate. No excessive "
            "resource use in a normal run."),
    },
    "MKM-SP-001": {
        "name": "Spatial Interpolation Model",
        "validation_date": "2025-11-20",
        "vq": _vq(
            "Inverse-distance-weighting interpolation with a KDTree "
            "nearest-neighbour search, mapping gauge observations to property "
            "locations — its documented purpose.",
            "The interpolation is a standard, deterministic IDW with a passing "
            "unit suite. IDW is known to dilute a sparse-gauge signal — the "
            "documented behaviour that leaves many properties just below threshold "
            "— so its accuracy is limited and unvalidated: partial.",
            "The KDTree keeps nearest-neighbour search efficient and the batch "
            "interpolation is tractable; no excessive resource use."),
    },
    "MKM-SG-001": {
        "name": "Storm-Gauge Response Model",
        "validation_date": "2025-12-01",
        "vq": _vq(
            "A distance-based attenuation model mapping storm intensity to "
            "gauge-level water levels with catchment-specific calibration — its "
            "documented purpose.",
            "The decay model is deterministic with a passing unit suite and "
            "per-catchment calibration. The calibration is not validated against "
            "observed gauge response (synthetic data), so this is partial.",
            "A closed-form distance attenuation; negligible computational "
            "resource use."),
    },
    # --- Tranche 2 ----------------------------------------------------------
    "MKM-BRI-001": {
        "name": "Building Resilience Index (BRI) Model",
        "validation_date": "2026-05-15",
        "vq": _vq(
            "Produces a property's Building Resilience Index — a letter rating "
            "(AA..NR) via weakest-link aggregation across hazard dimensions, plus "
            "the co-located numeric scores that feed the flood, wind and other "
            "resilience credits — its documented purpose.",
            "The aggregation is deterministic and the unit suite passes; the "
            "rating bands and weights are expert-judgement calibrations, not "
            "validated against realised resilience outcomes, so this is partial.",
            "A bounded per-property scoring aggregation; negligible computational "
            "resource use."),
    },
    "MKM-DE-001": {
        "name": "Delta Engine",
        "validation_date": "2026-02-26",
        "vq": _vq(
            "Revalues PRS trades and computes FS01 flood sensitivity, "
            "mark-to-market, risky annuity and the portfolio risk grid by "
            "numerical bump-and-revalue — its documented purpose.",
            "The bump-and-revalue is numerically consistent with the underlying "
            "pricer and the unit suite passes; the step-size choice and the "
            "absence of an analytic cross-check mean numerical accuracy is "
            "demonstrated but not independently validated — partial.",
            "Bump-and-revalue repeats the pricer per risk factor, so cost scales "
            "with the grid; it runs as a bounded batch with no excessive resource "
            "use in a normal run."),
    },
    "MKM-FIRE-001": {
        "name": "Building Fire-Resilience Credit Model",
        "validation_date": "2026-06-16",
        "recertification_date": "2027-06-16",
        "vq": _vq(
            "Prices a commercial asset's fire-resilience into the shared "
            "resilience-credit currency via a Poisson ignition model and a "
            "Bayesian fifteen-minute fire-progression chain, aggregating "
            "pari-passu with the storm and typhoon hazards — its documented "
            "purpose.",
            "The progression mechanism is implemented and the unit suite passes, "
            "but the ignition and transition parameters are defensible seed / "
            "placeholder values, not calibrated to fire-loss data; accuracy is "
            "therefore unvalidated — partial, and the weakest of this tranche.",
            "A bounded per-asset Markov progression; negligible computational "
            "resource use."),
    },
    "MKM-GHD-001": {
        "name": "Gauge Historical Daily",
        "validation_date": "2026-03-18",
        "vq": _vq(
            "Generates synthetic daily gauge water levels with tidal influence, "
            "AR(1) autocorrelation, seasonal cycles and Poisson flood injection — "
            "its documented purpose.",
            "The generator is seeded and reproducible with a passing unit suite; "
            "the statistical parameters are assumed rather than fitted to observed "
            "records, so the realism of the series is unvalidated — partial.",
            "Vectorised daily time-series generation; negligible computational "
            "resource use."),
    },
    "MKM-IP-001": {
        "name": "Insurance Premium Model",
        "validation_date": "2025-12-01",
        "vq": _vq(
            "Computes a factor-based flood insurance premium from property type, "
            "flood zone, claims history and building-resilience measures — its "
            "documented purpose.",
            "The factor model is deterministic with a passing unit suite; the "
            "factors are illustrative loadings, not calibrated to an insurer's "
            "loss experience, so premium accuracy is unvalidated — partial.",
            "A bounded multiplicative factor calculation; negligible computational "
            "resource use."),
    },
    "MKM-MP-001": {
        "name": "Mortgage Pricing Model",
        "validation_date": "2025-12-15",
        "vq": _vq(
            "Builds an amortisation schedule with a credit-spread adjustment, an "
            "LGD calculation and the expected-loss present value for flood-exposed "
            "mortgages — its documented purpose.",
            "The cash-flow and expected-loss mathematics are standard and the unit "
            "suite passes; the credit-spread and LGD inputs are assumed and the "
            "loss link to flood risk is unvalidated on real defaults — partial.",
            "Closed-form amortisation and present-value arithmetic; negligible "
            "computational resource use."),
    },
}


def apply_one(model_id: str, config=None) -> dict:
    """Complete one model's validation date and validation questions idempotently."""
    spec = MODELS[model_id]
    model = get_model(model_id, config=config)
    if model is None:
        raise RuntimeError(f"{model_id} is not registered.")
    data = model["data"]
    summary = {"model": model_id, "fields": [], "questions": 0}

    scalars = {"validation_date": spec["validation_date"]}
    if "recertification_date" in spec:
        scalars["recertification_date"] = spec["recertification_date"]
    for field, value in scalars.items():
        if data.get(field) in (None, "", "None"):
            update_model_field(model_id=model_id, field=field, value=value,
                               actor=ACTOR, config=config,
                               reason="Complete audited governance record (Phase 2)")
            summary["fields"].append(field)

    by_id = {q["item_id"]: q for q in data.get("validation_questions", [])}
    for item_id, (status, rationale) in spec["vq"].items():
        current = by_id.get(item_id)
        if current is not None and (
                current.get("status") != status or not current.get("rationale")):
            update_collection_item(
                model_id=model_id, collection="validation_questions",
                item_id=item_id, fields={"status": status, "rationale": rationale},
                actor=ACTOR, config=config, reason="Validation assessment update")
            summary["questions"] += 1

    rebuild_inventory_view(config=config)
    return summary


def apply(config=None) -> list[dict]:
    """Complete every model in the current tranche; return per-model summaries."""
    return [apply_one(mid, config=config) for mid in MODELS]


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    for s in apply():
        print(f"{s['model']}: +fields {s['fields']}, {s['questions']} validation "
              "questions recorded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
