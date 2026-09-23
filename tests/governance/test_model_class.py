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
"""``model_class`` on the two record types inside SR 26-2 scope (spec v0.5 §2.1).

A model in the inventory and an ML Application are both ``ML_APP``: stamped at
registration, refused if a caller names the other class, never editable, and read as
``ML_APP`` when registered before the field existed — so live needs no backfill.
"""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.ml_application import (get_ml_application, register_ml_application,
                                           update_ml_application_field)
from src.governance.ml_application._state import (EVENT_REGISTERED as ML_REGISTERED,
                                                  apply as ml_apply,
                                                  initial_state as ml_initial,
                                                  record_data as ml_record_data)
from src.governance.ml_application.projection import rebuild_ml_application_view
from src.governance.model_class import (reject_immutable_edit, stamp_model_class,
                                        with_model_class)
from src.governance.model_inventory import (get_model, rebuild_inventory_view,
                                            register_model, update_model_field)
from src.governance.reference import ensure_default_estimators

_ML = {"name": "Retail PD scorecard", "division": "Risk", "owner": "A",
       "use_case": "Ranks applications.", "estimator": "LogisticRegression"}


# --- The helper, once for all three ------------------------------------------

def test_the_class_is_stamped_from_the_record_type():
    assert stamp_model_class("ModelInventoryEntry", {})["model_class"] == "ML_APP"
    assert stamp_model_class("AISystem", {"model_class": "AI_SYSTEM"})["model_class"] \
        == "AI_SYSTEM"
    with pytest.raises(DomainError, match="for this record type is ML_APP"):
        stamp_model_class("MLApplication", {"model_class": "AI_SYSTEM"})


def test_an_immutable_field_refuses_edits_and_others_do_not():
    specs = {"model_class": {"immutable": True}, "name": {}}
    with pytest.raises(DomainError, match="cannot be edited"):
        reject_immutable_edit(specs, "model_class")
    reject_immutable_edit(specs, "name")
    reject_immutable_edit(specs, "not_a_field")


def test_a_stored_class_is_never_overwritten_on_read():
    assert with_model_class("MLApplication", {})["model_class"] == "ML_APP"
    assert with_model_class("MLApplication", {"model_class": "ML_APP"}) == \
        {"model_class": "ML_APP"}


# --- A model -----------------------------------------------------------------

def test_a_model_is_registered_as_an_ml_app_and_stays_one():
    register_model(model_id="M-MC-1", name="Alpha", actor="admin")
    rebuild_inventory_view()
    assert get_model("M-MC-1")["data"]["model_class"] == "ML_APP"
    with pytest.raises(DomainError, match="cannot be edited"):
        update_model_field(model_id="M-MC-1", field="model_class", value="AI_SYSTEM",
                           actor="admin")


def test_a_model_cannot_be_registered_across_the_line():
    with pytest.raises(DomainError, match="for this record type is ML_APP"):
        register_model(model_id="M-MC-2", name="Beta", actor="admin",
                       fields={"model_class": "AI_SYSTEM"})


# --- An ML Application -------------------------------------------------------

def test_an_ml_application_is_registered_as_an_ml_app_and_stays_one():
    ensure_default_estimators()
    register_ml_application(ml_application_id="MLA-MC-1", fields=_ML, actor="admin")
    rebuild_ml_application_view()
    assert get_ml_application("MLA-MC-1")["data"]["model_class"] == "ML_APP"
    with pytest.raises(DomainError, match="cannot be edited"):
        update_ml_application_field(ml_application_id="MLA-MC-1", field="model_class",
                                    value="AI_SYSTEM", actor="admin")


def test_an_ml_application_registered_before_the_field_reads_as_an_ml_app():
    state = ml_apply(ml_initial(), ML_REGISTERED, {"ml_application_id": "MLA-OLD", **_ML})
    assert "model_class" not in state.fields
    assert ml_record_data(state)["model_class"] == "ML_APP"
