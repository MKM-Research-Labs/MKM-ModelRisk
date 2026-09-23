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
"""An AI System's classification and its place on the grid (spec v0.5 §2, AIGov edition).

``model_class`` is stamped at registration and never edited; the three complexity fields
are the owner's to set; the grid position is resolved on every read, so a record that
has not been classified yet reads as unplaced rather than as a quiet default.
"""
from __future__ import annotations

import pytest

from src.governance.ai_system import (get_ai_system, list_ai_systems,
                                      rebuild_ai_system_view, register_ai_system,
                                      update_ai_system_field)
from src.governance.ai_system._state import (EVENT_REGISTERED, apply, initial_state,
                                             record_data)
from src.governance.errors import DomainError

_MINIMUM = {"name": "Credit memo drafter", "division": "Risk", "owner": "David K Kelly",
            "use_case": "Drafts the first pass of a credit memo from the file.",
            "deployment_pattern": "Agentic (tool-using)"}


def _register(ai_system_id="AIS-0001", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    rebuild_ai_system_view()
    return get_ai_system(ai_system_id)


def test_registration_stamps_the_ai_system_class():
    assert _register()["data"]["model_class"] == "AI_SYSTEM"


def test_registering_across_the_sr26_2_line_is_refused():
    with pytest.raises(DomainError, match="model_class is AI_SYSTEM"):
        register_ai_system(ai_system_id="AIS-0002",
                           fields={**_MINIMUM, "model_class": "ML_APP"}, actor="admin")


def test_the_class_cannot_be_edited_afterwards():
    _register()
    with pytest.raises(DomainError, match="cannot be edited"):
        update_ai_system_field(ai_system_id="AIS-0001", field="model_class",
                               value="ML_APP", actor="admin")


def test_a_record_registered_before_the_field_existed_reads_as_an_ai_system():
    """No backfill against live: the record's type answers the question the same way."""
    state = apply(initial_state(), EVENT_REGISTERED, {"ai_system_id": "AIS-OLD", **_MINIMUM})
    assert "model_class" not in state.fields
    assert record_data(state)["model_class"] == "AI_SYSTEM"


def test_the_complexity_fields_are_validated_against_their_vocabulary():
    with pytest.raises(DomainError, match="ai_autonomy must be one of"):
        _register(ai_system_id="AIS-0003", ai_autonomy="SWARM")
    _register()
    with pytest.raises(DomainError, match="ai_usage_frequency must be one of"):
        update_ai_system_field(ai_system_id="AIS-0001", field="ai_usage_frequency",
                               value="HOURLY", actor="admin")


def test_an_unclassified_system_is_not_placed_and_says_what_is_missing():
    grid = _register()["grid"]
    assert grid["placed"] is False
    assert grid["missing"] == ["Materiality", "Autonomy", "Usage frequency"]


def test_a_classified_system_is_placed_and_moves_when_an_input_moves():
    _register(materiality="High", ai_system_type="AGENTIC", ai_autonomy="AGENT",
              ai_usage_frequency="AD_HOC")
    assert get_ai_system("AIS-0001")["grid"]["position"] == "High × Medium"
    update_ai_system_field(ai_system_id="AIS-0001", field="ai_usage_frequency",
                           value="CONTINUOUS", actor="admin")
    rebuild_ai_system_view()
    grid = get_ai_system("AIS-0001")["grid"]
    assert grid["position"] == "High × High"
    assert grid["intensity"] == "Intensive"
    assert [r["grid"]["position"] for r in list_ai_systems()] == ["High × High"]
