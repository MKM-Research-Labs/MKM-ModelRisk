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
"""What the AI System aggregate refuses.

An AI System is governed alongside a model rather than instead of one, so its risk
bands come from the same place a model's do -- the division's ratified policy --
and its refusals read the same way. Where the two records differ is in what they
ARE, never in how they are categorised.
"""
from __future__ import annotations

import pytest

from src.governance.ai_system import (register_ai_system, retire_ai_system,
                                      update_ai_system_field)
from src.governance.ai_system._state import EVENT_REGISTERED, apply, initial_state
from src.governance.ai_system.commands import _ai_questions
from src.governance.errors import DomainError

_MINIMUM = {"name": "Client mail summariser", "division": "Risk",
            "owner": "David K Kelly",
            "use_case": "Summarises inbound client correspondence for the desk.",
            "deployment_pattern": "Agentic (tool-using)"}


def _register(ai_system_id="AIS-0001", **overrides):
    register_ai_system(ai_system_id=ai_system_id, fields={**_MINIMUM, **overrides},
                       actor="admin")
    return ai_system_id


@pytest.mark.parametrize("field", ["materiality", "complexity", "rag_rating"])
def test_a_risk_band_the_division_never_ratified_is_refused(field):
    with pytest.raises(DomainError, match=f"{field} must be one of"):
        register_ai_system(ai_system_id="AIS-0002",
                           fields={**_MINIMUM, field: "Chartreuse"}, actor="admin")


def test_editing_a_risk_field_is_validated_against_the_policy_too():
    _register()
    with pytest.raises(DomainError, match="rag_rating must be one of"):
        update_ai_system_field(ai_system_id="AIS-0001", field="rag_rating",
                               value="Chartreuse", actor="admin")


def test_a_field_that_is_not_the_owners_to_change_is_refused():
    _register()
    with pytest.raises(DomainError, match="field not editable"):
        update_ai_system_field(ai_system_id="AIS-0001", field="ai_system_id",
                               value="AIS-9999", actor="admin")


def test_a_field_cannot_be_written_to_a_record_nobody_registered():
    with pytest.raises(DomainError, match="does not exist"):
        update_ai_system_field(ai_system_id="AIS-9999", field="rag_rating",
                               value="Green", actor="admin")


def test_an_unregistered_record_cannot_be_retired():
    with pytest.raises(DomainError, match="does not exist"):
        retire_ai_system(ai_system_id="AIS-9999", actor="admin")


def test_retiring_twice_is_refused():
    """Retirement is hibernation, and a second retirement of the same record would
    record a decision the committee never took."""
    _register()
    retire_ai_system(ai_system_id="AIS-0001", actor="admin")
    with pytest.raises(DomainError, match="already retired"):
        retire_ai_system(ai_system_id="AIS-0001", actor="admin")


def test_registration_without_an_id_is_refused():
    with pytest.raises(DomainError, match="ai_system_id is required"):
        register_ai_system(ai_system_id="", fields=_MINIMUM, actor="admin")


def test_an_event_this_aggregate_does_not_know_leaves_the_state_alone():
    state = apply(initial_state(), EVENT_REGISTERED, {"name": "Client mail summariser"})
    assert apply(state, "SomethingElseEntirely", {"field": "name"}) is state


def test_the_shipped_questionnaire_stands_in_when_the_register_cannot_be_read(
        monkeypatch):
    def _unavailable(*args, **kwargs):
        raise RuntimeError("reference view not migrated yet")

    monkeypatch.setattr("src.governance.reference.get_reference_lists", _unavailable)
    questions = _ai_questions(None)
    assert questions and all(q["question"] for q in questions)
