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
"""A division carves its estate up by function, and its MRC agrees the carve-up.

The two halves held here: the list is worthless if it can be re-cut silently, so a
draft drives nothing until it is ratified; and a carve-up is worthless if it can
strand records, so a group nobody can be filed under any more cannot be removed
while somebody is filed under it.
"""
from __future__ import annotations

import pytest

from config.governance import FUNCTIONAL_GROUP_ID_PREFIX
from src.governance.errors import DomainError
from src.governance.functional_groups.commands import _validate_groups
from src.governance.functional_groups import (approve_functional_groups,
                                              get_functional_groups,
                                              get_functional_groups_draft, group_ids,
                                              group_names, groups_in_use, load,
                                              propose_functional_groups,
                                              reject_functional_groups)
from src.governance.model_inventory import (register_model, rebuild_inventory_view,
                                            retire_model, update_model_field)
from src.governance.product import (rebuild_product_view, register_product,
                                    retire_product, update_product_field)

DIV = "PhysicalRisk"
OTHER = "Analytics"
STORM = {"name": "Storm Generation", "description": "Hazard generation."}
FLOOD = {"name": "Flood Simulation"}


def _propose(groups, division=DIV):
    return propose_functional_groups(division=division, groups=groups, actor="admin")


def _ratify(groups, division=DIV):
    """The whole loop, since almost nothing here is observable without it."""
    _propose(groups, division)
    approve_functional_groups(division=division, actor="chair", meeting_id="MRC-1")
    return get_functional_groups(division)


# --- Nothing until a committee says so ---------------------------------------

def test_a_division_that_has_ratified_nothing_has_no_groups():
    assert get_functional_groups(DIV) == []
    assert group_ids(DIV) == ()
    assert load(DIV)["state"] == "seed"


def test_the_default_is_not_shared_between_divisions():
    """A mutable default handed out twice is one edit away from reaching everybody."""
    first = get_functional_groups(DIV)
    first.append({"id": "FG-999", "name": "Injected"})
    assert get_functional_groups(OTHER) == []


def test_a_draft_drives_nothing_until_it_is_approved():
    _propose([STORM])
    assert get_functional_groups(DIV) == [], "a proposal is not a decision"
    assert load(DIV)["state"] == "draft"
    assert get_functional_groups_draft(DIV)[0]["name"] == "Storm Generation"


def test_approving_makes_the_draft_live_and_records_the_meeting():
    _propose([STORM])
    event = approve_functional_groups(division=DIV, actor="chair", meeting_id="MRC-7")
    assert event.payload["meeting_id"] == "MRC-7"
    assert [g["name"] for g in get_functional_groups(DIV)] == ["Storm Generation"]
    assert load(DIV)["state"] == "approved"
    assert load(DIV)["approved_at"], "the ratification date is the evidence"


def test_rejecting_withdraws_the_draft_and_leaves_the_live_list_standing():
    _ratify([STORM])
    _propose([STORM, FLOOD])
    reject_functional_groups(division=DIV, actor="chair", meeting_id="MRC-8")
    assert [g["name"] for g in get_functional_groups(DIV)] == ["Storm Generation"]
    assert get_functional_groups_draft(DIV) is None


def test_approving_with_no_draft_is_refused_and_names_the_division():
    with pytest.raises(DomainError, match=DIV):
        approve_functional_groups(division=DIV, actor="chair")


def test_one_divisions_list_is_not_anothers():
    _ratify([STORM])
    _ratify([FLOOD], division=OTHER)
    assert [g["name"] for g in get_functional_groups(DIV)] == ["Storm Generation"]
    assert [g["name"] for g in get_functional_groups(OTHER)] == ["Flood Simulation"]


# --- Ids are minted, and order is the committee's ------------------------------

def test_ids_are_minted_so_the_editor_never_invents_one():
    groups = _ratify([STORM, FLOOD])
    assert [g["id"] for g in groups] == ["FG-001", "FG-002"]
    assert all(g["id"].startswith(FUNCTIONAL_GROUP_ID_PREFIX) for g in groups)


def test_an_existing_id_survives_a_rename_so_records_are_not_orphaned():
    """The whole reason a record stores the id: a ratified rename moves nothing."""
    _ratify([STORM])
    renamed = _ratify([{"id": "FG-001", "name": "Inundation Modelling"}])
    assert renamed == [{"id": "FG-001", "name": "Inundation Modelling"}]
    assert group_names(DIV) == {"FG-001": "Inundation Modelling"}


def test_a_removed_groups_number_is_not_reissued_to_a_different_group():
    _ratify([STORM, FLOOD])
    grown = _ratify([{"id": "FG-001", "name": "Storm Generation"}, {"name": "Pricer"}])
    assert [g["id"] for g in grown] == ["FG-001", "FG-002"]


def test_order_is_preserved_because_the_committee_chose_it():
    ordered = _ratify([FLOOD, STORM])
    assert [g["name"] for g in ordered] == ["Flood Simulation", "Storm Generation"]
    assert group_ids(DIV) == ("FG-001", "FG-002")


def test_group_names_falls_back_to_the_id_rather_than_showing_a_blank():
    _propose([STORM])
    approve_functional_groups(division=DIV, actor="chair")
    assert group_names(DIV) == {"FG-001": "Storm Generation"}


# --- What a committee may not be asked to ratify -------------------------------

@pytest.mark.parametrize("groups, message", [
    ("Storm Generation", "must be an array"),
    ([["Storm Generation"]], "must be an object"),
    ([{"name": ""}], "needs a name"),
    ([{"name": "Storm", "colour": "red"}], "unknown functional group key"),
    ([{"id": "FG-001", "name": "Storm"}, {"id": "FG-001", "name": "Flood"}],
     "used twice"),
    ([{"name": "Storm"}, {"name": " storm "}], "both named"),
])
def test_a_malformed_list_never_reaches_an_agenda(groups, message):
    with pytest.raises(DomainError, match=message):
        _propose(groups)
    assert load(DIV)["state"] == "seed", "nothing was recorded"


def test_a_group_with_no_id_and_no_name_is_refused_before_it_is_numbered():
    with pytest.raises(DomainError, match="needs a name"):
        _propose([{"description": "nameless"}])


# --- A carve-up may not strand the records filed under it -----------------------
#
# The commands deliberately do not project (the web layer does), so a test that
# reads the estate has to rebuild the view itself -- the same rule any backfill
# script is held to.

def _file_model(model_id, group_id, division=DIV):
    register_model(model_id=model_id, name=model_id, actor="admin",
                   fields={"division": division})
    if group_id:
        update_model_field(model_id=model_id, field="functional_group",
                           value=group_id, actor="admin")
    rebuild_inventory_view()


def test_nothing_is_in_use_on_an_empty_estate():
    _ratify([STORM])
    assert groups_in_use(DIV) == {}


def test_a_group_cannot_be_removed_while_a_record_is_filed_under_it():
    _ratify([STORM, FLOOD])
    _file_model("M1", "FG-001")
    with pytest.raises(DomainError, match="FG-001 cannot be removed"):
        _propose([{"id": "FG-002", "name": "Flood Simulation"}])
    assert load(DIV)["state"] == "approved", "the committee was never troubled"


def test_the_refusal_names_the_records_so_somebody_can_go_and_refile_them():
    _ratify([STORM])
    _file_model("M1", "FG-001")
    _file_model("M2", "FG-001")
    with pytest.raises(DomainError, match="M1, M2"):
        _propose([])


def test_a_group_still_in_use_may_be_renamed_it_is_only_removal_that_strands():
    _ratify([STORM])
    _file_model("M1", "FG-001")
    renamed = _ratify([{"id": "FG-001", "name": "Inundation Modelling"}])
    assert renamed[0]["name"] == "Inundation Modelling"


def test_another_divisions_records_do_not_block_this_divisions_tidying():
    _ratify([STORM])
    _ratify([STORM], division=OTHER)
    _file_model("M1", "FG-001", division=OTHER)
    _propose([], division=DIV)
    assert get_functional_groups_draft(DIV) == []


def test_a_hibernated_record_does_not_block_a_removal():
    """It carries no obligations and is out of every estate figure; blocking a
    committee on one would be a poor trade."""
    _ratify([STORM])
    _file_model("M1", "FG-001")
    retire_model(model_id="M1", actor="chair", reason="superseded")
    rebuild_inventory_view()
    _propose([])
    assert get_functional_groups_draft(DIV) == []


def test_in_use_counts_across_registers_not_just_the_model_inventory():
    _ratify([STORM])
    _file_model("M1", "FG-001")
    register_product(product_id="P1", product="Pricer", actor="admin",
                     fields={"division": DIV, "calculating_agent": "In-house"})
    update_product_field(product_id="P1", field="functional_group", value="FG-001",
                         actor="admin")
    rebuild_product_view()
    assert sorted(groups_in_use(DIV)["FG-001"]) == ["M1", "P1"]


def test_padding_is_stripped_on_the_way_in_not_only_when_it_is_checked():
    """Validation compares a stripped id, so storing the padded one would leave a
    group that passed every check and matches nothing on a record."""
    groups = _ratify([{"id": "  FG-001  ", "name": "  Storm Generation  "}])
    assert groups == [{"id": "FG-001", "name": "Storm Generation"}]
    assert group_ids(DIV) == ("FG-001",)


def _file_product(product_id, group_id, division=DIV):
    register_product(product_id=product_id, product=product_id, actor="admin",
                     fields={"division": division, "calculating_agent": "In-house"})
    if group_id:
        update_product_field(product_id=product_id, field="functional_group",
                             value=group_id, actor="admin")
    rebuild_product_view()


def test_a_hibernated_product_does_not_block_a_removal_either():
    """Not a repeat of the model case: ``list_models`` drops hibernated records for
    you and ``list_products`` does not, so Products is the only register where the
    retired guard actually fires. Without it a retired Product would veto a tidy-up
    no live record objects to."""
    _ratify([STORM])
    _file_product("P1", "FG-001")
    retire_product(product_id="P1", actor="chair", reason="withdrawn")
    rebuild_product_view()
    _propose([])
    assert get_functional_groups_draft(DIV) == []


def test_an_ungrouped_record_is_not_counted_against_any_group():
    _ratify([STORM])
    _file_model("M1", "FG-001")
    _file_model("M2", None)
    assert groups_in_use(DIV) == {"FG-001": ["M1"]}


def test_the_id_check_holds_even_though_minting_makes_it_unreachable_today():
    """``propose`` mints an id before validating, so nothing reaches this through the
    public path. It is the contract ``RatifiedPolicy.validate`` exists to keep: a
    stored list is well formed whoever wrote it, not only when the mint ran first."""
    with pytest.raises(DomainError, match="needs an id"):
        _validate_groups([{"id": "", "name": "Storm Generation"}])
