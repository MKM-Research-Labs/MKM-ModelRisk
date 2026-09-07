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
"""A record may only be filed under a group its own division's MRC has ratified.

The rule is written once (``functional_groups/_validate``) and all four registers
call it, so these run the same cases against each of them: the failure that matters
is one register quietly enforcing something the others do not, which is what four
copies of a rule always end in.
"""
from __future__ import annotations

import pytest

from src.governance.ai_system import register_ai_system, update_ai_system_field
from src.governance.errors import DomainError
from src.governance.functional_groups import (approve_functional_groups,
                                              propose_functional_groups)
from src.governance.ml_application import (register_ml_application,
                                           update_ml_application_field)
from src.governance.model_inventory import register_model, update_model_field
from src.governance.product import register_product, update_product_field

DIV = "PhysicalRisk"
OTHER = "Analytics"
FIELD = "functional_group"


def _ratify(groups, division):
    propose_functional_groups(division=division, groups=groups, actor="admin")
    approve_functional_groups(division=division, actor="chair")


def _model(division=DIV):
    register_model(model_id="M1", name="Alpha", actor="admin",
                   fields={"division": division})
    return lambda value: update_model_field(model_id="M1", field=FIELD, value=value,
                                            actor="admin")


def _product(division=DIV):
    register_product(product_id="P1", product="Pricer", actor="admin",
                     fields={"division": division, "calculating_agent": "In-house"})
    return lambda value: update_product_field(product_id="P1", field=FIELD,
                                              value=value, actor="admin")


def _ml_application(division=DIV):
    register_ml_application(ml_application_id="MLA1", actor="admin",
                            fields={"name": "Scorer", "division": division,
                                    "owner": "alice", "estimator": "XGBoost",
                                    "use_case": "Scoring"})
    return lambda value: update_ml_application_field(
        ml_application_id="MLA1", field=FIELD, value=value, actor="admin")


def _ai_system(division=DIV):
    register_ai_system(ai_system_id="AIS1", actor="admin",
                       fields={"name": "Assistant", "division": division,
                               "owner": "alice", "use_case": "Drafting",
                               "deployment_pattern": "Direct prompting"})
    return lambda value: update_ai_system_field(ai_system_id="AIS1", field=FIELD,
                                                value=value, actor="admin")


REGISTERS = pytest.mark.parametrize(
    "make", [_model, _product, _ml_application, _ai_system],
    ids=["model", "product", "ml_application", "ai_system"])


@REGISTERS
def test_a_record_can_be_filed_under_its_own_divisions_group(make):
    _ratify([{"name": "Storm Generation"}], DIV)
    event = make()("FG-001")
    assert event.payload["value"] == "FG-001"


@REGISTERS
def test_a_record_cannot_be_filed_under_a_group_its_division_does_not_define(make):
    """Ids are minted per division, so both lists start at FG-001 and the boundary
    that matters is an id the record's OWN division has not ratified."""
    _ratify([{"name": "Storm Generation"}], DIV)
    _ratify([{"name": "Instrument Pricer"}, {"name": "Curves"}], OTHER)
    with pytest.raises(DomainError, match="Storm Generation"):
        make(division=DIV)("FG-002")


@REGISTERS
def test_the_refusal_names_the_groups_because_a_person_reads_it(make):
    _ratify([{"name": "Storm Generation"}], DIV)
    with pytest.raises(DomainError, match=r"Storm Generation \(FG-001\)"):
        make()("FG-999")


@REGISTERS
def test_a_division_whose_mrc_has_ratified_nothing_refuses_every_group(make):
    with pytest.raises(DomainError, match="no ratified functional groups"):
        make()("FG-001")


@REGISTERS
def test_blank_takes_a_record_out_of_a_group_rather_than_being_refused(make):
    """A functional group is a filing decision, and "not filed" is a real answer —
    unlike a risk rating, which a record must always carry."""
    _ratify([{"name": "Storm Generation"}], DIV)
    update = make()
    update("FG-001")
    assert update("").payload["value"] == ""


def test_a_group_can_be_set_at_registration_not_only_by_a_later_edit():
    _ratify([{"name": "Storm Generation"}], DIV)
    event = register_model(model_id="M2", name="Beta", actor="admin",
                           fields={"division": DIV, FIELD: "FG-001"})
    assert event.payload[FIELD] == "FG-001"


def test_registration_is_refused_against_the_divisions_list_too():
    _ratify([{"name": "Storm Generation"}], DIV)
    with pytest.raises(DomainError, match="must be one of"):
        register_model(model_id="M3", name="Gamma", actor="admin",
                       fields={"division": DIV, FIELD: "FG-404"})


# --- A group does not travel with a record to another division -------------------
#
# Run against every register for the same reason the cases above are: the guard is one
# call in four `decide_*` functions, and three of them being right is exactly the shape
# of failure that leaves one register enforcing something the others do not.

def _move(kind):
    return {
        "model": lambda: update_model_field(model_id="M1", field="division",
                                            value=OTHER, actor="admin"),
        "product": lambda: update_product_field(product_id="P1", field="division",
                                                value=OTHER, actor="admin"),
        "ml_application": lambda: update_ml_application_field(
            ml_application_id="MLA1", field="division", value=OTHER, actor="admin"),
        "ai_system": lambda: update_ai_system_field(ai_system_id="AIS1",
                                                    field="division", value=OTHER,
                                                    actor="admin"),
    }[kind]


MOVES = pytest.mark.parametrize("make, kind", [
    (_model, "model"), (_product, "product"),
    (_ml_application, "ml_application"), (_ai_system, "ai_system"),
], ids=["model", "product", "ml_application", "ai_system"])


@MOVES
def test_moving_a_filed_record_to_another_division_is_refused(make, kind):
    """Ids are per division, so FG-001 in PhysicalRisk and FG-001 in Analytics are
    different groups. Carrying one across would not dangle -- it would silently
    re-file the record under a group nobody chose, which is worse."""
    _ratify([{"name": "Storm Generation"}], DIV)
    _ratify([{"name": "Instrument Pricer"}], OTHER)
    make(DIV)("FG-001")
    with pytest.raises(DomainError, match="clear the functional group"):
        _move(kind)()


@MOVES
def test_clearing_the_group_first_lets_the_record_move(make, kind):
    _ratify([{"name": "Storm Generation"}], DIV)
    _ratify([{"name": "Instrument Pricer"}], OTHER)
    update = make(DIV)
    update("FG-001")
    update("")
    assert _move(kind)().payload["value"] == OTHER


@MOVES
def test_an_ungrouped_record_moves_division_exactly_as_before(make, kind):
    """The guard must not make a division change harder for the whole estate, none
    of which carries a group yet."""
    make(DIV)
    assert _move(kind)().payload["value"] == OTHER
