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
"""Per-model Phase 2 validation assessments (validation date + nine VQs each),
applied by ``scripts.complete_governance_phase2``; split out to keep the applier
small (rule R2). See that module for the tranche history and Red-rating basis.
"""

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
    "MKM-PR-001": {
        "name": "PRS Analytical Pricing Model",
        "validation_date": "2026-01-10",
        "vq": _vq(
            "Computes fair Physical Risk Swap spreads for flood protection at "
            "gauge and property level from hazard-curve exceedance probabilities — "
            "its documented purpose.",
            "The analytical spread is a closed-form transform of the exceedance "
            "probabilities and the unit suite passes; its accuracy inherits the "
            "unvalidated hazard curves it consumes (and, via MKM-EF-001, the "
            "unvalidated arrival rate), so this is partial.",
            "A closed-form spread calculation per instrument; negligible "
            "computational resource use."),
    },
    "MKM-PV-001": {
        "name": "Property Valuation Model",
        "validation_date": "2025-11-30",
        "vq": _vq(
            "A factor-based property valuation from area, price per square metre, "
            "age, condition, flood risk, EPC rating and proximity adjustments — "
            "its documented purpose.",
            "The factor model is deterministic with a passing unit suite; the "
            "adjustment factors are illustrative rather than calibrated to a "
            "transaction dataset, so valuation accuracy is unvalidated — partial.",
            "A bounded multiplicative factor calculation; negligible computational "
            "resource use."),
    },
    "MKM-RA-001": {
        "name": "Risk Analytics Model",
        "validation_date": "2025-12-20",
        "vq": _vq(
            "A Monte Carlo engine computing portfolio-level flood-risk analytics — "
            "Value-at-Risk, Expected Shortfall, HHI concentration and risk "
            "clustering — its documented purpose.",
            "The estimators are standard, seeded and reproducible with a passing "
            "unit suite; convergence depends on the simulation count and the tail "
            "metrics inherit the unvalidated loss inputs, so this is partial.",
            "Monte Carlo cost scales with path count but runs as a bounded batch; "
            "no excessive resource use in a normal run."),
    },
    "MKM-SEIS-001": {
        "name": "Building Seismic-Resilience Credit Model",
        "validation_date": "2026-06-08",
        "recertification_date": "2027-06-08",
        "vq": _vq(
            "Prices a commercial asset's seismic resilience into the shared "
            "resilience-credit currency so seismic loss aggregates pari-passu with "
            "the storm and fire hazards — its documented purpose.",
            "The mechanism is implemented and the unit suite passes, but the "
            "seismic hazard and fragility parameters are defensible seed / "
            "placeholder values, not calibrated to seismic-loss data; accuracy is "
            "unvalidated — partial.",
            "A bounded per-asset resilience-credit calculation; negligible "
            "computational resource use."),
    },
    "MKM-SI-001": {
        "name": "Storm Intensity Distribution",
        "validation_date": "2025-12-01",
        "vq": _vq(
            "A hybrid Normal-Pareto distribution for storm rainfall intensity — a "
            "Gaussian core with a Generalised Pareto tail above a fitted "
            "threshold — its documented purpose.",
            "The GPD tail and Gaussian core are standard, fitted, and the unit "
            "suite passes; the fit is to synthetic intensities rather than "
            "observed rainfall, so the tail's realism is unvalidated — partial.",
            "Closed-form sampling and density evaluation; negligible computational "
            "resource use."),
    },
    "MKM-SS-001": {
        "name": "Storm Sequence Generator",
        "validation_date": "2026-03-11",
        "vq": _vq(
            "Generates multi-storm sequences under the insurance hours clause "
            "(168-hour event window), producing catalogues of one-to-five related "
            "precipitation events — its documented purpose.",
            "The sequence logic is deterministic and seeded with a passing unit "
            "suite; the clustering parameters are assumed rather than fitted to an "
            "observed storm record, and the catalogue over-samples severe events "
            "(a documented coverage caveat consumed by MKM-EF-001), so this is "
            "partial.",
            "Catalogue generation is a bounded batch; negligible computational "
            "resource use in a normal run."),
    },
}
