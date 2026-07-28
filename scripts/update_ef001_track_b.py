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

"""Bring the MKM-EF-001 record up to date with Track B (PhysicalRisk Stage 6).

The model was registered at v1.0.0 (``register_ef001``) describing the model as
it stood before Track B. Track B then extended it materially but *additively*:
a loss view (event/year loss tables, AEP/OEP, monetary loss), a non-stationary
multi-year term structure, and an opt-in decoupled-wind process — each
behaviour-preserving by default, so nothing reprices until a registry is
deliberately filled. Those additions carry assumptions and limitations the
v1.0.0 record does not, and the version should reflect the extension.

This applies that delta. It is a minor bump (1.0.0 -> 1.1.0): the model gained
backward-compatible capability, it did not change its released outputs.

Idempotent: the version bump is skipped once applied, and each collection item
is added only if an item with the same description is not already present, so
the script is safe to re-run.

Run as:  python -m scripts.update_ef001_track_b
"""
from __future__ import annotations

from scripts.register_ef001 import FIELDS
from src.governance.model_inventory import (
    add_collection_item,
    get_model,
    rebuild_inventory_view,
    update_model_field,
)

ACTOR = "update_ef001_track_b"
MODEL_ID = "MKM-EF-001"
NEW_VERSION = "1.1.0"

# The v1.0.0 methodology, extended with the Track B capability. Reused from the
# registration record so the base description cannot drift.
UPDATED_METHODOLOGY = FIELDS["methodology"] + (
    " Track B (Stage 6) extends this additively: a loss view — per-event and "
    "per-year loss tables, aggregate and occurrence exceedance curves, and a "
    "monetary loss of damage-ratio times exposure value, reconciled against the "
    "compound-Poisson closed form; a non-stationary multi-year term structure "
    "that compounds a per-year arrival rate over the tenor; and an opt-in "
    "decoupled-wind process that prices wind as an independent arrival counting "
    "the unpaired typhoons the coupled model drops. Each is behaviour-preserving "
    "by default, gated behind an empty per-catchment registry."
)

TRACK_B_ASSUMPTIONS = [
    {
        "description": (
            "A subject's loss for an event is its damage ratio times its exposure "
            "value (a currency amount), or the damage ratio at unit exposure where "
            "no value is available. The annual aggregate loss is a compound-Poisson "
            "sum whose closed-form mean the year simulation reconciles against."
        ),
        "impact": "Medium",
        "monitoring": (
            "Per-subject loss-block reconciliation deviation, in sampling standard "
            "errors of the average annual loss."
        ),
        "mitigation": (
            "The event loss table's average annual loss is the sampler's exact "
            "expectation; a gap beyond sampling error fails the reconciliation gate."
        ),
    },
]

TRACK_B_LIMITATIONS = [
    {
        "description": (
            "Two reprices are built but switched off behind empty registries: a "
            "non-stationary climate trend (CATCHMENT_ANNUAL_GROWTH) and decoupled "
            "wind (DECOUPLED_WIND_CATCHMENTS). Every default reproduces the prior "
            "stationary and coupled numbers; activating either moves a priced "
            "quantity."
        ),
        "impact": "High",
        "monitoring_trigger": "Any non-empty growth or decoupled-wind registry.",
        "compensating_control": (
            "Off by default. The Stage 6j sensitivity harness quantifies each "
            "reprice before it is switched on, and activation is a model-risk "
            "decision resting on a real climate or typhoon signal."
        ),
    },
    {
        "description": (
            "When decoupled wind is enabled it treats flood and wind as independent "
            "Poisson processes and weights the typhoon catalogue uniformly — trading "
            "the coupled model's pairing correlation for coverage of the unpaired "
            "typhoons the coupled model drops — and the wind rate stays unvalidated "
            "on synthetic catchments."
        ),
        "impact": "Medium",
        "monitoring_trigger": "A catchment opted into DECOUPLED_WIND_CATCHMENTS.",
        "compensating_control": (
            "Off by default; the assumptions are documented and the sensitivity "
            "harness reports the coupled-versus-decoupled spread delta and the "
            "count of dropped typhoons."
        ),
    },
]

TRACK_B_WEAKNESSES = [
    "The additive loss view, the non-stationary trend and the decoupled-wind "
    "option all rest on the same per-catchment arrival rate, so each inherits its "
    "lack of independent validation on synthetic catchments (plan section 5).",
]


def _descriptions(model: dict, collection: str) -> set:
    """Return the descriptions already present in a collection."""
    return {item.get("description")
            for item in model["data"].get(collection, [])}


def apply(config=None) -> dict:
    """Apply the Track B governance delta idempotently.

    Returns a summary of what was changed.
    """
    model = get_model(MODEL_ID, config=config)
    if model is None:
        raise RuntimeError(
            f"{MODEL_ID} is not registered; run scripts.register_ef001 first.")

    data = model["data"]
    summary = {"version_bumped": False, "assumptions": 0,
               "limitations": 0, "weaknesses": 0}

    if data.get("version") != NEW_VERSION:
        update_model_field(
            model_id=MODEL_ID, field="version", value=NEW_VERSION, actor=ACTOR,
            config=config, reason="Track B (Stage 6) material extension")
        update_model_field(
            model_id=MODEL_ID, field="methodology", value=UPDATED_METHODOLOGY,
            actor=ACTOR, config=config, reason="Track B methodology")
        summary["version_bumped"] = True

    for collection, items, key in (
        ("assumptions", TRACK_B_ASSUMPTIONS, None),
        ("limitations", TRACK_B_LIMITATIONS, None),
        ("model_weaknesses", TRACK_B_WEAKNESSES, "description"),
    ):
        present = _descriptions(model, collection)
        for item in items:
            fields = item if key is None else {key: item}
            if fields["description"] in present:
                continue
            add_collection_item(model_id=MODEL_ID, collection=collection,
                                fields=fields, actor=ACTOR, config=config)
            bucket = "weaknesses" if collection == "model_weaknesses" else collection
            summary[bucket] += 1

    rebuild_inventory_view(config=config)
    return summary


def main() -> int:
    from src.database import run_migrations

    run_migrations()
    summary = apply()
    print(
        f"MKM-EF-001 -> v{NEW_VERSION}: "
        f"version_bumped={summary['version_bumped']}, "
        f"+{summary['assumptions']} assumptions, "
        f"+{summary['limitations']} limitations, "
        f"+{summary['weaknesses']} weaknesses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
