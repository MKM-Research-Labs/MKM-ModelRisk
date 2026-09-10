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
"""A division chooses its stages from the institution's catalogue, and its MRC agrees.

The second layer. Three things are held here: a division that has ratified nothing
offers the WHOLE catalogue, which is what lets this ship without a per-division backfill
and without a committee having met; a division chooses from the catalogue and cannot add
to it; and the choice is intersected with the catalogue on every read, so a stage the
institution drops leaves every division at once.
"""
from __future__ import annotations

import pytest

from config.governance import VALID_LIFECYCLE_STAGES
from src.governance.errors import DomainError
from src.governance.lifecycle_stage_catalogue import (approve_lifecycle_catalogue,
                                                      propose_lifecycle_catalogue)
from src.governance.lifecycle_stages import (approve_division_stages, chosen_stages,
                                             chosen_stages_draft, load,
                                             propose_division_stages,
                                             reject_division_stages, stage_labels,
                                             stages_for, stages_in_use)
from src.governance.model_inventory import (rebuild_inventory_view, register_model,
                                            update_model_field)

DIV = "PhysicalRisk"
OTHER = "Analytics"


def _ratify(stages, division=DIV):
    propose_division_stages(division=division, stages=stages, actor="admin")
    approve_division_stages(division=division, actor="chair", meeting_id="MRC-1")
    return stages_for(division)


def _ratify_catalogue(stages):
    propose_lifecycle_catalogue(stages=stages, actor="admin")
    approve_lifecycle_catalogue(actor="chair", meeting_id="MRC-1")


def _model(model_id, stage=None, division=DIV):
    register_model(model_id=model_id, name=model_id, actor="admin",
                   fields={"division": division})
    if stage:
        update_model_field(model_id=model_id, field="lifecycle_stage", value=stage,
                           actor="admin")
    rebuild_inventory_view()


# --- the default: why this needs no per-division backfill --------------------------

def test_a_division_that_has_ratified_nothing_offers_the_whole_catalogue():
    assert stages_for(DIV) == VALID_LIFECYCLE_STAGES
    assert chosen_stages(DIV) == [], "and it has chosen nothing"
    assert load(DIV)["state"] == "seed"


def test_the_labels_are_the_institution_s_not_the_division_s():
    """A division chooses its stages, not what they are called: one firm-wide word per
    stage is most of the point of having a catalogue."""
    _ratify_catalogue([{"value": v, "label": "Live" if v == "Production" else v}
                       for v in VALID_LIFECYCLE_STAGES])
    _ratify(["Production", "Retired"])
    assert stage_labels(DIV) == {"Production": "Live", "Retired": "Retired"}


# --- choosing from the catalogue ---------------------------------------------------

def test_a_division_narrows_the_catalogue_to_what_it_uses():
    assert _ratify(["Development", "Production"]) == ("Development", "Production")
    assert stages_for(OTHER) == VALID_LIFECYCLE_STAGES, "and only for itself"


def test_the_division_s_own_order_is_what_it_offers():
    """A committee that arranged its list arranged it for a reason."""
    assert _ratify(["Production", "Development"]) == ("Production", "Development")


def test_a_division_cannot_coin_a_stage_of_its_own():
    """The reason the catalogue exists: two divisions inventing 'Decommissioning' and
    'Decommissioned' for the same thing is what this refuses."""
    with pytest.raises(DomainError, match="not in the institution's lifecycle stage "
                                          "catalogue"):
        propose_division_stages(division=DIV, stages=["Decommissioning"], actor="admin")


def test_choosing_no_stages_is_refused():
    """It would be indistinguishable from having ratified nothing, which already means
    the whole catalogue — and it would leave the division unable to file anything."""
    with pytest.raises(DomainError, match="at least one lifecycle stage"):
        propose_division_stages(division=DIV, stages=[], actor="admin")


def test_a_stage_chosen_twice_is_refused():
    with pytest.raises(DomainError, match="Production is chosen twice"):
        propose_division_stages(division=DIV, stages=["Production", "Production"],
                                actor="admin")


# --- the lifecycle ------------------------------------------------------------------

def test_a_draft_changes_nothing_until_it_is_ratified():
    propose_division_stages(division=DIV, stages=["Production"], actor="admin")
    assert stages_for(DIV) == VALID_LIFECYCLE_STAGES, "the committee has not met"
    assert chosen_stages_draft(DIV) == ["Production"]


def test_rejecting_leaves_the_list_standing():
    _ratify(["Development", "Production"])
    propose_division_stages(division=DIV, stages=["Production"], actor="admin")
    reject_division_stages(division=DIV, actor="chair", meeting_id="MRC-2")
    assert stages_for(DIV) == ("Development", "Production")


# --- the invariant the intersection buys --------------------------------------------

def test_a_stage_the_catalogue_drops_leaves_every_division_at_once():
    """Including a division that had ratified a subset naming it — which is what stops
    a division being left offering a word the institution no longer defines."""
    _ratify(["Development", "Production"])
    _ratify_catalogue([{"value": v, "label": v} for v in VALID_LIFECYCLE_STAGES
                       if v != "Production"])
    assert stages_for(DIV) == ("Development",)
    assert chosen_stages(DIV) == ["Development", "Production"], "the choice is untouched"


# --- what the estate holds ----------------------------------------------------------

def test_a_stage_cannot_be_dropped_while_this_division_s_records_are_in_it():
    _ratify(["Development", "Production"])
    _model("M1", "Production")
    with pytest.raises(DomainError, match="Production cannot be dropped .* M1"):
        propose_division_stages(division=DIV, stages=["Development"], actor="admin")
    assert stages_in_use(DIV) == {"Production": ["M1"]}


def test_another_division_s_records_do_not_block_it():
    _model("M2", "Production", division=OTHER)
    assert _ratify(["Development"]) == ("Development",)


# --- moving a record between divisions ----------------------------------------------

def test_a_record_cannot_move_into_a_division_that_does_not_use_its_stage():
    """It would be counted, filtered and reported under a stage that division does not
    recognise, with nothing on the screen to say so."""
    _model("M3", "Production")
    _ratify(["Development"], division=OTHER)
    with pytest.raises(DomainError, match="does not use the lifecycle stage"):
        update_model_field(model_id="M3", field="division", value=OTHER, actor="admin")


def test_a_record_moves_freely_where_the_target_uses_its_stage():
    """A stage does not become a different stage on the way across — the catalogue is
    firm-wide — so this is a check, not a refusal to travel at all."""
    _model("M4", "Production")
    _ratify(["Development", "Production"], division=OTHER)
    update_model_field(model_id="M4", field="division", value=OTHER, actor="admin")
    rebuild_inventory_view()
    assert stages_in_use(OTHER) == {"Production": ["M4"]}


def test_a_record_with_no_stage_moves_freely():
    _model("M5")
    _ratify(["Development"], division=OTHER)
    update_model_field(model_id="M5", field="division", value=OTHER, actor="admin")
