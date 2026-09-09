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
"""The stages an institution had already curated survive the move to the catalogue.

A new ratified policy seeds a vacuum and never reaches an existing estate. This is the
test of the thing that carries the estate across: build the first catalogue from the
admin list AS IT STANDS, not from the words the platform ships, or an adopter's renames
and additions are silently lost the day the catalogue goes live.
"""
from __future__ import annotations

from config.governance import LIFECYCLE_STAGE_LIST, VALID_LIFECYCLE_STAGES
from scripts.backfill_lifecycle_catalogue import backfill, plan
from src.governance.lifecycle_stage_catalogue import (approve_lifecycle_catalogue,
                                                      catalogue_labels,
                                                      catalogue_values, load,
                                                      propose_lifecycle_catalogue)
from src.governance.model_inventory import (rebuild_inventory_view, register_model,
                                            update_model_field)
from src.governance.reference import (add_option, ensure_default_status_vocabularies,
                                      get_reference_lists, remove_option, update_option)


def _item(value):
    return next(i for i in get_reference_lists()[LIFECYCLE_STAGE_LIST]
                if i["value"] == value)


def _rename(value, label):
    update_option(list_name=LIFECYCLE_STAGE_LIST, item_id=_item(value)["item_id"],
                  fields={"label": label}, actor="admin")


def test_an_untouched_list_is_left_alone():
    """Ratifying the words the catalogue already defaults to would add an event and
    change nothing, so the backfill declines to."""
    ensure_default_status_vocabularies()
    result = backfill(apply=True)
    assert result["verdict"] == "skip"
    assert load()["state"] == "seed"


def test_an_unseeded_list_is_left_alone():
    assert plan()["verdict"] == "skip"
    assert "never been seeded" in plan()["why"]


def test_a_rename_the_institution_made_is_carried_across():
    """The whole reason this script exists."""
    ensure_default_status_vocabularies()
    _rename("Production", "Live")
    assert backfill(apply=True)["verdict"] == "ratify"
    assert catalogue_labels()["Production"] == "Live", "the rename survived"
    assert catalogue_values() == VALID_LIFECYCLE_STAGES, "and nothing else moved"
    assert load()["state"] == "approved"


def test_a_stage_the_institution_added_is_carried_across():
    ensure_default_status_vocabularies()
    add_option(list_name=LIFECYCLE_STAGE_LIST,
               fields={"value": "Decommissioning", "label": "Winding down"},
               actor="admin")
    backfill(apply=True)
    assert catalogue_values()[-1] == "Decommissioning", "and in the list's own order"
    assert catalogue_labels()["Decommissioning"] == "Winding down"


def test_a_stage_records_are_in_is_carried_in_even_if_the_list_dropped_it():
    """An administrator who deleted a stage from the list did not delete it from the
    records still in it, and a catalogue without it could not be proposed at all."""
    ensure_default_status_vocabularies()
    register_model(model_id="M1", name="Alpha", actor="admin",
                   fields={"division": "PhysicalRisk"})
    update_model_field(model_id="M1", field="lifecycle_stage", value="Production",
                       actor="admin")
    rebuild_inventory_view()
    remove_option(list_name=LIFECYCLE_STAGE_LIST, item_id=_item("Production")["item_id"],
                  actor="admin")

    result = backfill(apply=True)
    assert result["carried"] == ["Production"]
    assert "Production" in catalogue_values(), "the records in it still resolve"


def test_it_does_not_write_without_apply():
    ensure_default_status_vocabularies()
    _rename("Production", "Live")
    assert plan()["verdict"] == "ratify"
    backfill()
    assert load()["state"] == "seed", "the plan is a plan until --apply"


def test_it_is_idempotent():
    ensure_default_status_vocabularies()
    _rename("Production", "Live")
    backfill(apply=True)
    version = load()["version"]
    assert backfill(apply=True)["verdict"] == "skip"
    assert load()["version"] == version, "a second run writes nothing"


def test_it_refuses_to_walk_over_a_draft_somebody_is_deciding():
    """A draft outstanding is a committee mid-decision. Ratifying underneath it would
    settle a question nobody asked this script to settle."""
    ensure_default_status_vocabularies()
    _rename("Production", "Live")
    propose_lifecycle_catalogue(
        stages=[{"value": v, "label": v} for v in VALID_LIFECYCLE_STAGES],
        actor="admin")
    result = backfill(apply=True)
    assert result["verdict"] == "skip"
    assert "draft is outstanding" in result["why"]
    assert load()["draft"] is not None, "the committee's draft is untouched"


def test_it_leaves_a_ratified_catalogue_alone():
    ensure_default_status_vocabularies()
    propose_lifecycle_catalogue(stages=[{"value": "Production", "label": "Live"}],
                                actor="admin")
    approve_lifecycle_catalogue(actor="chair", meeting_id="MRC-1")
    _rename("Production", "Something else")
    assert backfill(apply=True)["verdict"] == "skip"
    assert catalogue_labels() == {"Production": "Live"}, "the committee's word stands"
