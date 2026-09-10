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
"""What the ML Application aggregate refuses, and why.

The register form is deliberately short, so almost everything this record enforces
is enforced on the way IN to a field rather than at registration. The two that
matter most are here: a risk band has to be one the division's own MRC ratified
(decision 8 -- the same risk classification a model gets), and a record nobody has
registered cannot be edited into existence by writing a field to it.
"""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.ml_application import (add_collection_item,
                                           reactivate_ml_application,
                                           register_ml_application,
                                           retire_ml_application,
                                           update_ml_application_field)
from src.governance.ml_application._state import (EVENT_REGISTERED, apply,
                                                  initial_state)
from src.governance.ml_application.commands import _ml_questions

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "David K Kelly",
            "estimator": "GradientBoostingClassifier",
            "use_case": "Ranks retail applicants by probability of default."}


def _register(ml_application_id="MLA-0001", **overrides):
    register_ml_application(ml_application_id=ml_application_id,
                            fields={**_MINIMUM, **overrides}, actor="admin")
    return ml_application_id


# --- Risk bands come from the division's ratified policy ---------------------

@pytest.mark.parametrize("field", ["materiality", "complexity", "rag_rating"])
def test_a_risk_band_the_division_never_ratified_is_refused(field):
    """Not checked against a tuple in config: an ML Application's bands are the ones
    its division's MRC approved, so its categorisation can be challenged on exactly
    the terms a model's can."""
    with pytest.raises(DomainError, match=f"{field} must be one of"):
        register_ml_application(ml_application_id="MLA-0002",
                                fields={**_MINIMUM, field: "Chartreuse"}, actor="admin")


def test_the_refusal_names_the_bands_the_division_actually_has():
    """A refusal that only says "invalid" sends somebody to the source to find out
    what the division calls its bands."""
    with pytest.raises(DomainError, match="Green"):
        register_ml_application(ml_application_id="MLA-0002",
                                fields={**_MINIMUM, "rag_rating": "Chartreuse"},
                                actor="admin")


def test_a_band_from_the_seed_policy_is_accepted():
    _register(rag_rating="Green", materiality="Medium")


def test_editing_a_risk_field_is_validated_against_the_policy_too():
    """The band is checked wherever it is set, or a record could be registered clean
    and then edited into a rating nobody ratified."""
    _register()
    with pytest.raises(DomainError, match="rag_rating must be one of"):
        update_ml_application_field(ml_application_id="MLA-0001", field="rag_rating",
                                    value="Chartreuse", actor="admin")


# --- Vocabularies the platform does own --------------------------------------

def test_a_value_outside_a_fixed_vocabulary_is_refused_and_the_options_listed():
    """``lifecycle_stage`` was the example until 2026-09-09, when the stages became
    the institution's own -- ratified per division from a firm-wide catalogue -- and
    stopped being a vocabulary the platform owns at all."""
    with pytest.raises(DomainError, match="review_frequency must be one of"):
        register_ml_application(ml_application_id="MLA-0002",
                                fields={**_MINIMUM, "review_frequency": "Fortnightly"},
                                actor="admin")


# --- A record has to exist before it can be changed ---------------------------

def test_a_field_cannot_be_written_to_a_record_nobody_registered():
    """Otherwise an edit creates the record silently, and the register form's
    minimum -- the one place division and owner are demanded -- is bypassed."""
    with pytest.raises(DomainError, match="does not exist"):
        update_ml_application_field(ml_application_id="MLA-9999", field="rag_rating",
                                    value="Green", actor="admin")


def test_an_unregistered_record_cannot_be_retired():
    with pytest.raises(DomainError, match="does not exist"):
        retire_ml_application(ml_application_id="MLA-9999", actor="admin")


def test_registration_without_an_id_is_refused():
    with pytest.raises(DomainError, match="ml_application_id is required"):
        register_ml_application(ml_application_id="", fields=_MINIMUM, actor="admin")


# --- The fold ----------------------------------------------------------------

def test_an_event_this_aggregate_does_not_know_leaves_the_state_alone():
    """The log is append-only and shared, so a fold that guessed at an unfamiliar
    event type would corrupt a record the moment a neighbouring aggregate's name
    happened to collide."""
    state = apply(initial_state(), EVENT_REGISTERED, {"name": "Retail PD scorecard"})
    assert apply(state, "SomethingElseEntirely", {"field": "name"}) is state


# --- The questionnaire the record is asked -----------------------------------

def test_the_shipped_questionnaire_stands_in_when_the_register_cannot_be_read(
        monkeypatch):
    """A record registered before the first-run seed still has to be asked
    something. Returning nothing would leave it with an empty review for good --
    the copy is taken once, at registration, and never rewritten."""
    def _unavailable(*args, **kwargs):
        raise RuntimeError("reference view not migrated yet")

    monkeypatch.setattr("src.governance.reference.get_reference_lists", _unavailable)
    questions = _ml_questions(None)
    assert questions and all(q["question"] for q in questions)


# --- Coming back, and what stays writable while hibernated --------------------
#
# The same three guards the AI System carries (tests/governance/test_ai_system_edges.py).
# They were untested here, which is the asymmetry these suites exist to prevent: a rule
# enforced on one record type and unchecked on another is a rule with a hole in it.

def test_reactivating_something_never_registered_is_refused():
    with pytest.raises(DomainError, match="does not exist"):
        reactivate_ml_application(ml_application_id="MLA-NOPE", actor="admin")


def test_reactivating_a_live_ml_application_is_refused():
    """Not a no-op: "reactivate" on a record already in the estate means somebody has
    misread its state, and answering OK would confirm the misreading."""
    _register()
    with pytest.raises(DomainError, match="is not retired"):
        reactivate_ml_application(ml_application_id="MLA-0001", actor="admin")


def test_a_retired_ml_application_comes_back():
    _register()
    retire_ml_application(ml_application_id="MLA-0001", actor="admin")
    reactivate_ml_application(ml_application_id="MLA-0001", actor="admin")
    # And can be retired again — the guard is on state, not on having been retired once.
    retire_ml_application(ml_application_id="MLA-0001", actor="admin")


def test_filing_a_signoff_item_against_nothing_is_refused():
    """Sign-off collections stay writable on a hibernated record — the committee has to
    be able to record the decision that hibernated it, and the request to bring it back.
    So they skip the editable guard and check existence on their own, which is a second
    check needing its own test."""
    with pytest.raises(DomainError, match="does not exist"):
        add_collection_item(ml_application_id="MLA-NOPE", collection="signoff_requests",
                            fields={"kind": "owner"}, actor="admin")

