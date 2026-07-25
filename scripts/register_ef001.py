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

"""Register MKM-EF-001 (Event Frequency Model) into the ModelRisk inventory.

The other 24 PhysicalRisk models were bulk-migrated from the source
``model_inventory.json`` by ``migrate_phys``. MKM-EF-001 post-dates that
inventory and was never added to it, so it is registered directly here through
the same governance command API rather than by editing the source file.

Idempotent: an already-registered model is left untouched, and each chain edge
is added only if absent, so the script is safe to re-run.

Run as:  python -m scripts.register_ef001

The governance content is not invented for the demo. Every assumption,
limitation and weakness below is a finding from building and validating the
model — see ``PhysicalRisk/docs/storm_freq/frequency_layer_definition_and_plan_v2.md``.
The two that matter most for effective challenge:

- lambda is a per-catchment engineering-judgement seed, and NOTHING in the
  platform currently validates it (both the synthetic-record and the
  per-gauge-extraction validation routes are circular — plan §5).
- the reprice it produces is real and material (0.35-0.56x downward on flood),
  but rests on that unvalidated lambda and on population weights that are also
  owner judgement.
"""
from __future__ import annotations

from src.governance.errors import DomainError
from src.governance.model_inventory import (
    add_collection_item,
    derive_chain,
    get_model,
    rebuild_inventory_view,
    register_model,
)

ACTOR = "register_ef001"
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


def _register(config=None) -> bool:
    """Register the model with its scalar fields and collections.

    Returns True if it was registered, False if it already existed.
    """
    if get_model(MODEL_ID, config=config) is not None:
        return False
    register_model(
        model_id=MODEL_ID, name=FIELDS["name"], actor=ACTOR, config=config,
        fields=FIELDS,
        reason="Register MKM-EF-001 Event Frequency Model (Stage 5 governance)",
    )
    for assumption in ASSUMPTIONS:
        add_collection_item(model_id=MODEL_ID, collection="assumptions",
                            fields=assumption, actor=ACTOR, config=config)
    for limitation in LIMITATIONS:
        add_collection_item(model_id=MODEL_ID, collection="limitations",
                            fields=limitation, actor=ACTOR, config=config)
    for weakness in WEAKNESSES:
        add_collection_item(model_id=MODEL_ID, collection="model_weaknesses",
                            fields={"description": weakness}, actor=ACTOR, config=config)
    return True


def _declare_chain(config=None) -> int:
    """Declare the two chain edges around MKM-EF-001, skipping any that exist.

    Returns the number of edges newly declared.
    """
    existing = {(link["from"], link["to"]) for link in derive_chain(config=config)["links"]}
    declared = 0
    for producer, consumer in CHAIN_EDGES:
        if (producer, consumer) in existing:
            continue
        if get_model(producer, config=config) is None or get_model(consumer, config=config) is None:
            continue
        try:
            add_collection_item(
                model_id=producer, collection="dependencies", actor=ACTOR, config=config,
                fields={"direction": "downstream", "model_id": consumer})
            declared += 1
        except DomainError:
            continue  # a cycle the guard rejects — leave the chain intact
    return declared


def register(config=None) -> dict:
    """Register MKM-EF-001 and place it in the model chain.

    Returns a summary of what was done.
    """
    registered = _register(config=config)
    # Rebuild before declaring the chain: derive_chain and the get_model guards
    # in _declare_chain read the inventory view, which must reflect the just-
    # registered model or both new edges are silently skipped.
    rebuild_inventory_view(config=config)
    declared = _declare_chain(config=config)
    rebuild_inventory_view(config=config)
    return {"registered": registered, "edges_declared": declared}


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    result = register()
    if result["registered"]:
        print(f"MKM-EF-001 registered with "
              f"{len(ASSUMPTIONS)} assumptions, {len(LIMITATIONS)} limitations, "
              f"{len(WEAKNESSES)} weaknesses.")
    else:
        print("MKM-EF-001 already registered; left untouched.")
    print(f"chain edges declared: {result['edges_declared']} "
          f"(MKM-GH-001 -> MKM-EF-001 -> MKM-PR-001)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
