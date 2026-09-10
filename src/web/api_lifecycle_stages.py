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
"""The lifecycle stage API: the institution's catalogue, and each division's choice.

Two layers, two committees, one blueprint. The catalogue is firm-wide and the
Company-level MRC ratifies it; a division ratifies which of those stages it uses. See
docs/design/lifecycle-stages.md.

The registry is what the console loads once at startup and re-reads whenever a
committee ratifies something, the way it already loads the risk policies and the
functional groups. It hands back the stages **already resolved per division** -- the
whole catalogue where a division has ratified nothing, its own ordered choice where it
has -- so the "empty means everything" rule lives in one place rather than being
re-implemented in JavaScript. Making the per-register ``/fields`` endpoints
division-aware instead would mean a spec that varies by record, which those endpoints
are not built to be.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from src.command import dispatch
from src.governance.lifecycle_stage_catalogue import (approve_lifecycle_catalogue,
                                                      get_catalogue,
                                                      get_catalogue_draft,
                                                      propose_lifecycle_catalogue,
                                                      reject_lifecycle_catalogue,
                                                      stages_in_use)
from src.governance.lifecycle_stage_catalogue import load as load_catalogue
from src.governance.lifecycle_stages import (approve_division_stages, chosen_stages,
                                             chosen_stages_draft, load,
                                             propose_division_stages,
                                             reject_division_stages, stage_labels,
                                             stages_for)
from src.governance.lifecycle_stages import stages_in_use as division_stages_in_use
from src.governance.mrc import committee_at_levels
from src.governance.reference import get_reference_lists
from src.web._helpers import context_from_request, json_body, reference_options
from src.web._ratified_policy_api import register_ratification_routes

lifecycle_stages_bp = Blueprint("lifecycle_stages", __name__)

# The catalogue sits at ``/api/lifecycle-catalogue`` rather than under the stages
# prefix. It would have read well as ``/api/lifecycle-stages/catalogue``, and Werkzeug
# does prefer a static rule to ``/<division>`` -- but a division named "catalogue" would
# then be unreachable, and a routing table that depends on nobody naming a division
# badly is not one to leave lying around. The two layers are addressed separately
# because they are ratified by different committees.


def _catalogue_detail() -> dict:
    """The catalogue for the Admin editor and the Company MRC's sign-off item.

    ``in_use`` counts the live records in each stage, so the editor can say what
    removing one would cost before an administrator tries it -- the domain refuses the
    removal either way, but a count beside the row is an explanation and a refusal
    afterwards is a surprise.
    """
    state = load_catalogue()
    # Which committee can actually ratify this, if any. The catalogue is firm-wide, so
    # only a Company-level committee is entitled to -- and an estate that has never
    # defined one (a single Division-level MRC is a real configuration, and is what the
    # MKM estate has) would otherwise let an administrator save a draft that no meeting
    # can ever carry. The editor says so instead.
    committee, _level = committee_at_levels(("Company",), None, None,
                                            get_reference_lists())
    return {
        "live": state["live"],
        "draft": state["draft"],
        "state": state["state"],
        "approved_at": state["approved_at"],
        "ratifier": (committee or {}).get("value"),
        "in_use": {value: len(records) for value, records in stages_in_use().items()},
    }


def _division_detail(division: str) -> dict:
    """One division's choice, and what it currently resolves to.

    ``stages`` is the resolved list -- what records may actually be in -- while
    ``chosen`` is what the committee ratified. They differ where a division has ratified
    nothing (chosen empty, stages the whole catalogue) and where the catalogue has since
    dropped something the division named.
    """
    state = load(division)
    return {
        "division": division,
        "chosen": chosen_stages(division),
        "draft": chosen_stages_draft(division),
        "stages": list(stages_for(division)),
        "labels": stage_labels(division),
        "state": state["state"],
        "approved_at": state["approved_at"],
        "in_use": {value: len(records)
                   for value, records in division_stages_in_use(division).items()},
    }


@lifecycle_stages_bp.get("/api/lifecycle-stages")
def lifecycle_registry():
    """Every division's offered stages and labels, plus the catalogue behind them."""
    divisions = reference_options().get("division") or []
    states = {division: load(division) for division in divisions}
    catalogue = load_catalogue()
    return jsonify({
        "catalogue": catalogue["live"],
        "catalogue_state": catalogue["state"],
        "divisions": {d: list(stages_for(d)) for d in divisions},
        "labels": {d: stage_labels(d) for d in divisions},
        "states": {d: {"state": s["state"], "approved_at": s["approved_at"]}
                   for d, s in states.items()},
    })


@lifecycle_stages_bp.get("/api/lifecycle-catalogue")
def catalogue_detail():
    """The live catalogue, any pending draft, and how many records are in each stage."""
    return jsonify(_catalogue_detail())


@lifecycle_stages_bp.post("/api/lifecycle-catalogue/propose")
def propose_catalogue():
    """Save the edited catalogue as a draft for the Company MRC to sign off.

    No record moves until it is approved. A proposal that would drop a stage records are
    in, or rename a stored value, is refused here rather than at the meeting.
    """
    body = json_body()
    dispatch("propose_lifecycle_catalogue", propose_lifecycle_catalogue,
             context=context_from_request(body), stages=body.get("stages"))
    return jsonify(_catalogue_detail()), 201


@lifecycle_stages_bp.post("/api/lifecycle-catalogue/approve")
def approve_catalogue():
    """Ratify the catalogue draft: it becomes what every division chooses from."""
    body = json_body()
    dispatch("approve_lifecycle_catalogue", approve_lifecycle_catalogue,
             context=context_from_request(body), meeting_id=body.get("meeting_id"))
    return jsonify(_catalogue_detail())


@lifecycle_stages_bp.post("/api/lifecycle-catalogue/reject")
def reject_catalogue():
    """Decline the catalogue draft. The live catalogue is unchanged."""
    body = json_body()
    dispatch("reject_lifecycle_catalogue", reject_lifecycle_catalogue,
             context=context_from_request(body), meeting_id=body.get("meeting_id"))
    return jsonify(_catalogue_detail())


@lifecycle_stages_bp.get("/api/lifecycle-stages/<division>")
def division_detail(division: str):
    """A division's ratified choice, any draft, and what it resolves to today."""
    return jsonify(_division_detail(division))


@lifecycle_stages_bp.post("/api/lifecycle-stages/<division>/propose")
def propose_division(division: str):
    """Save the division's edited choice as a draft for its MRC to sign off."""
    body = json_body()
    dispatch("propose_division_stages", propose_division_stages,
             context=context_from_request(body), division=division,
             stages=body.get("stages"))
    return jsonify(_division_detail(division)), 201


# Approve / reject are the same two handlers every ratified policy has, so they come
# from the shared helper rather than being written a fourth time.
register_ratification_routes(
    lifecycle_stages_bp, "/api/lifecycle-stages",
    approve_command="approve_division_stages", approve=approve_division_stages,
    reject_command="reject_division_stages", reject=reject_division_stages,
    detail=_division_detail,
)
