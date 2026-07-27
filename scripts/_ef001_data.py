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
"""Governance data for MKM-EF-001 (Event Frequency Model).

The scalar record and the assumption / limitation / weakness registers, split
from ``register_ef001`` so the script stays within the file-size limit and reads
as pure orchestration. Every entry is a finding from building and validating the
model, not demo filler; see the module docstring in ``register_ef001``.
"""
from __future__ import annotations

MODEL_ID = "MKM-EF-001"

# Scalar governance record. Version 1.0.0: a genuine release — built, wired to
# pricing on the gauge/property/commercial/wind legs, and validated end-to-end
# on real flood and wind data (Stages 1-4).
FIELDS = {
    "name": "Event Frequency Model",
    "short_name": "Event Frequency",
    "category": "Hazard",
    "type": "Analytical Model",
    "tier": 1,
    "tier_rationale": (
        "lambda is a linear multiplier on every PRS spread, so the model is at "
        "least as material as the GEV hazard curve (MKM-GH-001, tier 1) it sits "
        "beside and more material than the storm-intensity model (MKM-SI-001, "
        "tier 2, 'not directly into pricing')."
    ),
    "materiality": "High",
    "complexity": "High",
    "methodology": (
        "Peaks-over-threshold extraction with runs-method declustering; a "
        "per-catchment Poisson arrival rate lambda; a Monte Carlo year "
        "simulation that draws N ~ Poisson(lambda) events per year and scores "
        "each against a population-reweighted event catalogue; annualisation "
        "P = 1 - exp(-lambda * p_event); Poisson/Negative-Binomial family "
        "selection by a small-sample chi-square dispersion test with an AIC "
        "tiebreak."
    ),
    "methodology_rationale": (
        "The platform previously priced PRS off flood_count / num_storms, a "
        "conditional probability with no time dimension (lambda identically 1). "
        "The Monte Carlo is the engine and its closed form is the reconciliation "
        "self-test, not an alternative answer, because the closed form is the "
        "simulation's exact expectation. The construction mirrors the seismic "
        "and fire occurrence models already in the platform."
    ),
    "source_module": "src/models/frequency/",
    "repo_location": "PhysicalRisk",
    "codebase": "PhysicalRisk",
    "owner": "David K Kelly",
    "model_owner_role": "Chief Science Officer",
    "status": "Active",
    "lifecycle_stage": "Development",
    "version": "1.0.0",
    "validation_status": "Initial",
    "rag_rating": "Amber",
    "rating_rationale": (
        "Amber: the mechanism is built, tested and validated end-to-end, but "
        "lambda and the event-population weights are unvalidated engineering "
        "seeds and no route currently constrains them (see limitations)."
    ),
    "review_frequency": "Annual",
    "unit_tests": "Yes",
    "integration_tests": "Yes",
    "benchmark_tests": "No",
}

ASSUMPTIONS = [
    {
        "description": (
            "The event arrival rate lambda is a property of the catchment, not "
            "of a gauge: one storm reaches every gauge, so what differs per "
            "gauge is the conditional response, not the arrival rate."
        ),
        "impact": "High",
        "monitoring": (
            "lambda x P(exceed | event) at each gauge should reproduce that "
            "gauge's directly measured severe-exceedance rate."
        ),
        "mitigation": "Per-catchment override in config.frequency.",
    },
    {
        "description": (
            "Qualifying events arrive as a Poisson process (constant rate, "
            "independent), so an annual count is Poisson(lambda)."
        ),
        "impact": "Medium",
        "monitoring": (
            "Per-gauge chi-square dispersion test; Negative Binomial is "
            "selected where counts are significantly over-dispersed."
        ),
        "mitigation": (
            "Negative-Binomial family for clustering. Under-dispersion is "
            "flagged, not fitted: on synthetic data it is a declustering "
            "artefact, not a physical regularity."
        ),
    },
    {
        "description": (
            "A storm sequence within the 168-hour insurance hours clause is one "
            "event; its level at a gauge is the maximum across the member storms."
        ),
        "impact": "Medium",
        "monitoring": "num_events vs num_storms ratio in the hazard build.",
        "mitigation": "Event granularity is carried through the whole chain.",
    },
    {
        "description": (
            "The generated storm catalogue is an importance sample that "
            "over-represents severe events; per-event population weights "
            "reweight it back onto the population a real year draws from."
        ),
        "impact": "High",
        "monitoring": "Implied severe-flood return period against a plausible band.",
        "mitigation": (
            "EVENT_POPULATION_WEIGHTS in config; catalogue coverage scales the "
            "conditional so mild events absent from the catalogue count at zero, "
            "not renormalised onto the severe end."
        ),
    },
]

LIMITATIONS = [
    {
        "description": (
            "lambda is unvalidated. On synthetic catchments the gauge record is "
            "generated FROM an assumed frequency, and the per-gauge extraction "
            "arm recovers lambda from its own threshold-search target, so both "
            "validation routes are circular. Nothing currently constrains lambda."
        ),
        "impact": "High",
        "monitoring_trigger": "Any use of the model on a real (non-synthetic) catchment.",
        "compensating_control": (
            "Provenance records the class (observed / generator-derived / "
            "regional-fallback); breaking the circularity needs a threshold "
            "anchored outside the rate (bankfull discharge, published flood "
            "frequency) and therefore real gauge data."
        ),
    },
    {
        "description": (
            "The event-population weights (8% severe-or-worse) are owner "
            "engineering judgement; the reprice scales directly with them and "
            "nothing currently contradicts a wrong value."
        ),
        "impact": "High",
        "monitoring_trigger": "Repricing review; parallel-run against the legacy metric.",
        "compensating_control": "Single config source; sensitivity is documented.",
    },
    {
        "description": (
            "Stationarity assumed: no climate-conditioned or non-stationary "
            "lambda(t)."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Drift in the annual-count series over time.",
        "compensating_control": "Annual recalibration; roadmap item for a doubly-stochastic rate.",
    },
    {
        "description": (
            "Calibrated and validated on a single small catchment (halong: 3 "
            "gauges, 1 property, 10 commercial assets). No full-book parallel "
            "run has been performed."
        ),
        "impact": "Medium",
        "monitoring_trigger": "Before production sign-off.",
        "compensating_control": "Stage-3 parallel-run report is the gating artefact.",
    },
]

WEAKNESSES = [
    "The per-gauge validation arm is circular: the peaks-over-threshold search "
    "targets the catchment lambda, so the recovered rate equals the seed by "
    "construction and validates the extraction code rather than the rate.",
    "Under-dispersion in annual counts cannot be represented by any family on "
    "the Poisson-Negative-Binomial axis; it is flagged and Poisson is selected "
    "as the nearest fittable family.",
    "Monte Carlo sampling error on the annual probability is ~1.6% at the "
    "default 10,000 simulated years; higher precision needs more years.",
]

# Chain edges. MKM-EF-001 sits between the GEV hazard curve and PRS pricing:
# GH-001 produces per-event exceedance, EF-001 annualises it, PR-001 prices it.
# Declared as dependency collection items on the producer (direction downstream),
# matching how migrate_phys declares source edges.
CHAIN_EDGES = [
    ("MKM-GH-001", MODEL_ID),
    (MODEL_ID, "MKM-PR-001"),
]


