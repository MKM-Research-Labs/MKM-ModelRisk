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
"""Tests for the ML Application aggregate (domain core).

An ML Application is a use case for an off-the-shelf estimator. It is kept apart
from the model inventory because it evolves at a different rate, but it is built
from the same machinery -- so the tests that matter most here are the ones that
prove it has not quietly drifted away from a model where it must not.
"""
from __future__ import annotations

import pytest

from config.governance import (ML_APPLICATION_FIELD_SPECS, ML_APPLICATION_QUESTION_LIST,
                               ML_REVIEW_QUESTIONS_COLLECTION, MODEL_FIELD_SPECS)
from src.governance.errors import DomainError
from src.governance.ml_application import (add_collection_item, get_ml_application,
                                           list_ml_applications,
                                           rebuild_ml_application_view,
                                           register_ml_application, remove_collection_item,
                                           retire_ml_application, update_collection_item,
                                           update_ml_application_field)

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "David K Kelly",
            "estimator": "GradientBoostingClassifier",
            "use_case": "Ranks retail applicants by probability of default."}


def _register(ml_application_id="MLA-0001", **overrides):
    register_ml_application(ml_application_id=ml_application_id,
                            fields={**_MINIMUM, **overrides}, actor="admin")
    rebuild_ml_application_view()
    return ml_application_id


def _data(ml_application_id="MLA-0001"):
    return get_ml_application(ml_application_id)["data"]


# --- Registration -----------------------------------------------------------

def test_register_records_the_minimum():
    _register()
    data = _data()
    assert data["name"] == "Retail PD scorecard"
    assert data["estimator"] == "GradientBoostingClassifier"
    assert len(list_ml_applications()) == 1


def test_registration_invents_no_lifecycle_stage():
    """The stages are the institution's own vocabulary (Admin > Vocabulary), so there
    is no word this code could choose that is certainly in their list. A model sets
    none at registration; nor does this. The owner picks from their own menu."""
    _register()
    assert not _data().get("lifecycle_stage")


@pytest.mark.parametrize("missing", sorted(_MINIMUM))
def test_every_field_on_the_register_form_is_required(missing):
    fields = {k: v for k, v in _MINIMUM.items() if k != missing}
    with pytest.raises(DomainError, match=missing):
        register_ml_application(ml_application_id="MLA-0002", fields=fields, actor="admin")


def test_an_unknown_field_is_refused():
    with pytest.raises(DomainError, match="unknown field"):
        register_ml_application(ml_application_id="MLA-0003",
                                fields={**_MINIMUM, "hyperparameters": "n=500"},
                                actor="admin")


def test_registering_the_same_id_twice_is_refused():
    _register()
    with pytest.raises(DomainError, match="already registered"):
        register_ml_application(ml_application_id="MLA-0001", fields=_MINIMUM, actor="admin")


# --- The questionnaire snapshot ---------------------------------------------

def test_registration_copies_the_ml_questionnaire_onto_the_record():
    """Its own set, under its own name -- never a model's validation_questions."""
    _register()
    asked = _data()[ML_REVIEW_QUESTIONS_COLLECTION]
    assert [q["item_id"] for q in asked][:2] == ["MLQ-001", "MLQ-002"]
    assert asked[0]["short_label"] == "Use Case"
    assert all(q["status"] == "Not Addressed" for q in asked)
    assert "validation_questions" not in _data()


def test_the_record_keeps_the_questions_it_was_actually_asked():
    """Editing the admin list afterwards must not restate what a reviewer answered."""
    from src.governance.reference import add_option

    add_option(list_name=ML_APPLICATION_QUESTION_LIST,
               fields={"short_label": "Fairness", "question": "Which groups were tested?"},
               actor="admin")
    _register()
    before = len(_data()[ML_REVIEW_QUESTIONS_COLLECTION])

    add_option(list_name=ML_APPLICATION_QUESTION_LIST,
               fields={"short_label": "Latency", "question": "Does it answer in time?"},
               actor="admin")
    rebuild_ml_application_view()
    assert len(_data()[ML_REVIEW_QUESTIONS_COLLECTION]) == before


# --- Editing and retirement -------------------------------------------------

def test_a_field_can_be_edited_and_an_unknown_one_cannot():
    _register()
    update_ml_application_field(ml_application_id="MLA-0001", field="training_data",
                               value="Retail book, 2019-2025, 1.2m applications.",
                               actor="admin")
    rebuild_ml_application_view()
    assert _data()["training_data"].startswith("Retail book")
    with pytest.raises(DomainError, match="not editable"):
        update_ml_application_field(ml_application_id="MLA-0001", field="learning_rate",
                                   value="0.05", actor="admin")


def test_retiring_marks_the_record_and_freezes_it():
    _register()
    retire_ml_application(ml_application_id="MLA-0001", actor="admin")
    rebuild_ml_application_view()
    assert get_ml_application("MLA-0001")["retired"] is True
    # ``retired`` is the fact. The lifecycle stage is not overwritten with a word we
    # chose -- an estate whose stages are New / Being Enhanced / No New Development /
    # Marked for Removal has no "Retired" for us to write.
    assert not _data().get("lifecycle_stage")
    with pytest.raises(DomainError, match="retired"):
        update_ml_application_field(ml_application_id="MLA-0001", field="training_data",
                                   value="anything", actor="admin")


def test_retiring_twice_is_refused():
    _register()
    retire_ml_application(ml_application_id="MLA-0001", actor="admin")
    with pytest.raises(DomainError, match="already retired"):
        retire_ml_application(ml_application_id="MLA-0001", actor="admin")


# --- Collections ------------------------------------------------------------

def test_collections_add_update_and_remove():
    _register()
    add_collection_item(ml_application_id="MLA-0001", collection="assumptions",
                        fields={"description": "Applicant income is self-reported."},
                        actor="admin")
    rebuild_ml_application_view()
    item = _data()["assumptions"][0]

    update_collection_item(ml_application_id="MLA-0001", collection="assumptions",
                           item_id=item["item_id"],
                           fields={"description": "Income is verified at origination."},
                           actor="admin")
    rebuild_ml_application_view()
    assert _data()["assumptions"][0]["description"].startswith("Income is verified")

    remove_collection_item(ml_application_id="MLA-0001", collection="assumptions",
                           item_id=item["item_id"], actor="admin")
    rebuild_ml_application_view()
    assert _data()["assumptions"] == []


# --- The contract with the completeness audit -------------------------------

# The scalar fields and collections the ISO/COSO clause probes read (see
# src/governance/completeness/framework.py). They are named here rather than
# imported because the point of the test is that the ML Application spells them
# THE SAME WAY a model does: match, and every probe counts ML Applications with
# no change; drift, and thirteen probes each grow a branch somebody will forget.
_PROBE_FIELDS = ("tier", "materiality", "complexity", "rag_rating", "division", "owner",
                 "peer_reviewer", "next_review_date", "mrc_signoff_date")
_PROBE_COLLECTIONS = ("assumptions", "limitations", "model_weaknesses",
                      "remediation_steps", "version_history", "signoff_history",
                      "review_notes")


@pytest.mark.parametrize("field", _PROBE_FIELDS)
def test_the_audit_probe_fields_are_spelled_as_a_model_spells_them(field):
    assert field in ML_APPLICATION_FIELD_SPECS
    assert field in MODEL_FIELD_SPECS


@pytest.mark.parametrize("collection", _PROBE_COLLECTIONS)
def test_the_audit_probe_collections_exist_on_the_record(collection):
    from config.governance import ML_APPLICATION_COLLECTION_SPECS
    assert collection in ML_APPLICATION_COLLECTION_SPECS


def test_what_the_record_deliberately_does_not_carry():
    """An ML Application has no dependency chain, and no model TYPE: the admin
    model_type list describes a model's part in a Product, and an ML Application's
    provenance is its Estimator instead.

    Repository, codebase, source module and vendor ARE carried: an ML Application has
    code in exactly the sense a model does, and a record migrated from the inventory
    would otherwise lose them.
    """
    assert "type" not in ML_APPLICATION_FIELD_SPECS
    from config.governance import ML_APPLICATION_COLLECTION_SPECS
    assert "dependencies" not in ML_APPLICATION_COLLECTION_SPECS
    for carried in ("repo_location", "codebase", "source_module", "vendor"):
        assert carried in ML_APPLICATION_FIELD_SPECS


def test_no_raci_on_the_record():
    """Accountability for an ML Application's use in production sits on the Product
    that consumes it, where the RACI operating model already lives. A second one here
    would ask the same question twice and let the two answers disagree."""
    from config.governance import ML_APPLICATION_COLLECTION_SPECS

    assert "raci_roles" not in ML_APPLICATION_COLLECTION_SPECS
    _register()
    assert not _data().get("raci_roles")
