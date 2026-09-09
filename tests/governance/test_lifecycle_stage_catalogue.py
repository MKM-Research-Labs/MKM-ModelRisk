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
"""The institution's stage vocabulary, and the committee that owns it.

Three things are held here. A draft drives nothing until the Company MRC ratifies it,
because a vocabulary an administrator can re-cut the week before an inspection is not
one anybody stands behind. A stage nobody could be in any more cannot be removed while
somebody is in it. And a stored VALUE never changes, because records carry it — renaming
is what the label is for, and it moves nothing.
"""
from __future__ import annotations

import pytest

from config.governance import VALID_LIFECYCLE_STAGES
from src.governance.errors import DomainError
from src.governance.lifecycle_stage_catalogue import (approve_lifecycle_catalogue,
                                                      catalogue_labels,
                                                      catalogue_values, get_catalogue,
                                                      get_catalogue_draft, load,
                                                      propose_lifecycle_catalogue,
                                                      reject_lifecycle_catalogue,
                                                      stages_in_use)
from src.governance.model_inventory import (rebuild_inventory_view, register_model,
                                            update_model_field)

LIVE = {"value": "Production", "label": "Production"}
DECOM = {"value": "Decommissioning", "label": "Winding down",
         "description": "Being switched off, with its consumers moving away."}


def _shipped() -> list[dict]:
    """The catalogue as it stands before anybody has ratified anything."""
    return [dict(stage) for stage in get_catalogue()]


def _propose(stages):
    return propose_lifecycle_catalogue(stages=stages, actor="admin")


def _ratify(stages):
    """The whole loop, since almost nothing here is observable without it."""
    _propose(stages)
    approve_lifecycle_catalogue(actor="chair", meeting_id="MRC-1")
    return get_catalogue()


def _put_model_in(model_id, stage):
    register_model(model_id=model_id, name=model_id, actor="admin",
                   fields={"division": "PhysicalRisk"})
    update_model_field(model_id=model_id, field="lifecycle_stage", value=stage,
                       actor="admin")
    rebuild_inventory_view()


# --- the default: why adopting this needs no migration ----------------------------

def test_an_institution_that_has_ratified_nothing_runs_on_the_shipped_five():
    """Not empty, unlike the functional groups: every record in the estate already
    carries one of these words, so an empty default would orphan the lot."""
    assert catalogue_values() == VALID_LIFECYCLE_STAGES
    assert load()["state"] == "seed"


def test_the_label_starts_as_the_stored_word():
    """The whole of the migration-free guarantee: nothing has to move for the
    catalogue to become live, and a rename afterwards touches only the label."""
    assert catalogue_labels() == {word: word for word in VALID_LIFECYCLE_STAGES}


# --- the lifecycle ----------------------------------------------------------------

def test_a_draft_changes_nothing_until_it_is_ratified():
    _propose(_shipped() + [DECOM])
    assert "Decommissioning" not in catalogue_values(), "the committee has not met"
    assert load()["state"] == "draft"
    assert get_catalogue_draft()[-1]["value"] == "Decommissioning"


def test_ratifying_makes_the_draft_the_catalogue():
    assert "Decommissioning" in [s["value"] for s in _ratify(_shipped() + [DECOM])]
    assert load()["state"] == "approved"
    assert get_catalogue_draft() is None
    assert catalogue_labels()["Decommissioning"] == "Winding down"


def test_rejecting_leaves_the_catalogue_standing():
    _propose(_shipped() + [DECOM])
    reject_lifecycle_catalogue(actor="chair", meeting_id="MRC-1")
    assert catalogue_values() == VALID_LIFECYCLE_STAGES
    assert get_catalogue_draft() is None


def test_the_refusal_does_not_name_the_id_it_is_stored_under():
    """A singleton has no scope a reader can see, so the wording says so. Naming
    ``global`` — which is what the per-division wording would have done — tells
    somebody reading the error nothing at all."""
    with pytest.raises(DomainError, match="there is no proposed lifecycle stage "
                                          "catalogue awaiting sign-off"):
        approve_lifecycle_catalogue(actor="chair")


# --- what makes a catalogue valid --------------------------------------------------

def test_an_empty_catalogue_is_refused():
    with pytest.raises(DomainError, match="cannot be empty"):
        _propose([])


def test_two_stages_a_reader_cannot_tell_apart_are_refused():
    # The refusal names the offending entry as it was written -- the second one, the
    # one to delete -- rather than the entry it collides with.
    with pytest.raises(DomainError, match="value production is used twice"):
        _propose([LIVE, {"value": "production", "label": "Live"}])
    with pytest.raises(DomainError, match="both shown as 'production'"):
        _propose([LIVE, {"value": "Live", "label": "production"}])


def test_a_stage_needs_both_a_value_and_a_label():
    with pytest.raises(DomainError, match="needs a stored value"):
        _propose([{"label": "Live"}])
    with pytest.raises(DomainError, match="Production needs a label"):
        _propose([{"value": "Production"}])


def test_a_key_nobody_expected_is_refused_rather_than_dropped():
    """The catalogue is a document a committee ratifies: a mistyped key that silently
    lost its value would be approved without anybody having seen what was lost."""
    with pytest.raises(DomainError, match="unknown lifecycle stage key\\(s\\): colour"):
        _propose([{**LIVE, "colour": "green"}])


def test_padding_is_stripped_as_it_is_taken_in():
    """A stage stored padded would pass every check and match nothing on a record."""
    assert "Production" in [s["value"] for s in _ratify([{"value": "  Production  ",
                                                          "label": " Live "}])]
    assert catalogue_labels()["Production"] == "Live"


# --- the two checks that look outside the catalogue --------------------------------

def test_nothing_is_in_use_on_an_empty_estate():
    assert stages_in_use() == {}


def test_a_stage_cannot_be_removed_while_a_record_is_in_it():
    _put_model_in("M1", "Production")
    with pytest.raises(DomainError, match="Production cannot be removed .* M1"):
        _propose([s for s in _shipped() if s["value"] != "Production"])
    assert load()["state"] == "seed", "the committee was never troubled"


def test_a_hibernated_record_does_not_block_a_tidy_up():
    """A hibernated record is out of every estate-wide figure, and blocking a committee
    from tidying its vocabulary for one nobody will ever complete is a poor trade."""
    from src.governance.model_inventory import retire_model
    _put_model_in("M2", "Production")
    retire_model(model_id="M2", actor="chair")
    rebuild_inventory_view()
    assert "Production" not in [s["value"] for s in
                                _ratify([s for s in _shipped()
                                         if s["value"] != "Production"])]


def test_a_stored_value_cannot_be_renamed():
    """Records carry the value, so editing one orphans every record in that stage
    silently. This is the case nothing holds yet — the removal check above covers the
    rest — and it is where a rename would otherwise pass unnoticed."""
    with pytest.raises(DomainError, match="a stored value cannot be changed once set"):
        _propose([{**s, "value": "PRODUCTION"} if s["value"] == "Production" else s
                  for s in _shipped()])


def test_renaming_the_label_moves_nothing():
    """The rename that IS allowed, and the reason the value/label split exists."""
    _put_model_in("M3", "Production")
    _ratify([{**s, "label": "Live"} if s["value"] == "Production" else s
             for s in _shipped()])
    assert catalogue_labels()["Production"] == "Live"
    assert stages_in_use() == {"Production": ["M3"]}, "the record never moved"
