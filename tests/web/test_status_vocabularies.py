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
"""Renaming a status must not move anything a record already holds.

Six vocabularies — the lifecycle stages, validation statuses, impact levels,
priorities, remediation statuses and review-answer statuses — all the same shape: a
record stores a stable value, a screen shows a label, and only the label is
editable. Seeding the value to the word records already carry is what makes this
free of migration — nothing in the estate has to be rewritten for it to work, and a
model set to "Production" years ago still reads correctly under whatever the
institution calls that stage now.
"""
from __future__ import annotations

from config.governance import (LIFECYCLE_STAGE_LIST, STATUS_VOCABULARIES,
                               VALID_LIFECYCLE_STAGES, VALIDATION_STATUS_LIST,
                               VQ_STATUS_LIST)
from src.governance.reference import (ensure_default_estimators,
                                      ensure_default_status_vocabularies,
                                      get_reference_lists)
from tests.web.conftest import HEADERS


def _stages(client):
    return client.get("/api/reference").get_json()["data"][LIFECYCLE_STAGE_LIST]


def _spec(client):
    groups = client.get("/api/models/fields").get_json()["groups"]
    for group in groups:
        for field in group["fields"]:
            if field["key"] == "lifecycle_stage":
                return field
    raise AssertionError("the lifecycle field should be in the model specs")


def test_the_seed_stores_the_words_records_already_carry():
    """The migration-free part: every value equals the word in the estate today."""
    added = ensure_default_status_vocabularies()
    assert added == sum(len(words) for _l, _p, words, _h in STATUS_VOCABULARIES.values())
    lists = get_reference_lists()
    for name, (_label, _prefix, words, _hint) in STATUS_VOCABULARIES.items():
        assert [i["value"] for i in lists[name]] == list(words), name
        assert [i["label"] for i in lists[name]] == list(words), name
    seeded = lists[LIFECYCLE_STAGE_LIST]
    assert [s["value"] for s in seeded] == list(VALID_LIFECYCLE_STAGES)
    assert [s["label"] for s in seeded] == list(VALID_LIFECYCLE_STAGES)
    assert ensure_default_status_vocabularies() == 0


def test_renaming_a_stage_changes_what_is_shown_not_what_is_stored(client):
    ensure_default_status_vocabularies()
    client.post("/api/models",
                json={"model_id": "M1", "name": "Alpha", "confirmed": True,
                      "fields": {"lifecycle_stage": "Production"}}, headers=HEADERS)
    production = next(s for s in _stages(client) if s["value"] == "Production")
    client.post(f"/api/reference/collections/{LIFECYCLE_STAGE_LIST}/{production['item_id']}",
                json={"fields": {"label": "Live"}, "confirmed": True}, headers=HEADERS)

    stored = client.get("/api/models/M1").get_json()["data"]["lifecycle_stage"]
    assert stored == "Production", "the record must not move when a label changes"
    spec = _spec(client)
    assert spec["option_labels"]["Production"] == "Live"
    assert "Production" in spec["options"], "the dropdown still submits the stored value"


def test_the_stored_value_cannot_be_edited(client):
    """Records already carry it; editing it would orphan every one of them."""
    ensure_default_status_vocabularies()
    stage = _stages(client)[0]
    response = client.post(
        f"/api/reference/collections/{LIFECYCLE_STAGE_LIST}/{stage['item_id']}",
        json={"fields": {"value": "something-else"}, "confirmed": True}, headers=HEADERS)
    assert response.status_code == 400
    assert "cannot be changed once set" in response.get_json()["error"]


def test_a_stage_the_institution_adds_is_offered(client):
    ensure_default_status_vocabularies()
    client.post(f"/api/reference/collections/{LIFECYCLE_STAGE_LIST}",
                json={"fields": {"value": "Decommissioning", "label": "Winding down"},
                      "confirmed": True}, headers=HEADERS)
    spec = _spec(client)
    assert "Decommissioning" in spec["options"]
    assert spec["option_labels"]["Decommissioning"] == "Winding down"


def test_before_the_list_is_seeded_the_shipped_words_still_stand(client):
    """A database that has never been seeded still offers a usable dropdown."""
    assert not get_reference_lists()[LIFECYCLE_STAGE_LIST]
    assert list(_spec(client)["options"]) == list(VALID_LIFECYCLE_STAGES)


def test_a_renamed_review_answer_still_counts_as_addressed(client):
    """The completeness audit matches on the stored value, so renaming what a
    reviewer sees cannot quietly change whether a question counts as answered."""
    ensure_default_status_vocabularies()
    addressed = next(i for i in get_reference_lists()[VQ_STATUS_LIST]
                     if i["value"] == "Addressed")
    client.post(f"/api/reference/collections/{VQ_STATUS_LIST}/{addressed['item_id']}",
                json={"fields": {"label": "Satisfied"}, "confirmed": True}, headers=HEADERS)
    client.post("/api/models",
                json={"model_id": "M9", "name": "Alpha", "confirmed": True}, headers=HEADERS)
    # Every question answered, so any remaining shortfall would be the audit failing
    # to recognise the stored value rather than a half-finished questionnaire.
    for question in client.get("/api/models/M9").get_json()["data"]["validation_questions"]:
        client.post(f"/api/models/M9/collections/validation_questions/{question['item_id']}",
                    json={"fields": {"status": "Addressed"}, "confirmed": True},
                    headers=HEADERS)

    from src.governance.completeness.scan import scan
    row = next(r for r in scan("2026-08-10") if r["entity_id"] == "M9")
    unanswered = [g for g in row["gaps"] if g["key"] == "validation_questions"]
    assert not unanswered, "the audit reads the stored value, not the label"


# --- The console's promise and the domain's answer ---------------------------------
#
# Until 2026-09-09 these were decided by two different rules that disagreed: the
# dropdown came from the admin list (``resolve_field``) and validation came from the
# tuple the platform shipped (``FIELD_CHOICES``). A stage an institution added was
# therefore offered on every screen and refused on save. ``live_choice_values`` is the
# one rule both sides now use; these are the tests that would have caught the drift.

_ADDED = {"value": "Decommissioning", "label": "Winding down"}


def _add_stage(client, fields=None):
    return client.post(f"/api/reference/collections/{LIFECYCLE_STAGE_LIST}",
                       json={"fields": fields or _ADDED, "confirmed": True},
                       headers=HEADERS)


def test_a_stage_the_institution_adds_can_be_saved(client):
    """The other half of ``test_a_stage_the_institution_adds_is_offered``, which
    asserted only that the dropdown offered it."""
    ensure_default_status_vocabularies()
    _add_stage(client)
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha", "confirmed": True},
                headers=HEADERS)
    saved = client.post("/api/models/M1/field",
                        json={"field": "lifecycle_stage", "value": "Decommissioning",
                              "confirmed": True}, headers=HEADERS)
    assert saved.status_code == 200, saved.get_json()
    assert client.get("/api/models/M1").get_json()["data"]["lifecycle_stage"] \
        == "Decommissioning"


def test_a_stage_the_institution_removed_is_refused(client):
    """The drift ran both ways: a stage taken off the list stayed acceptable to the
    domain, so the curated list was advisory in both directions."""
    ensure_default_status_vocabularies()
    retired_stage = next(s for s in _stages(client) if s["value"] == "Retired")
    client.post(f"/api/reference/collections/{LIFECYCLE_STAGE_LIST}/"
                f"{retired_stage['item_id']}/delete",
                json={"confirmed": True}, headers=HEADERS)
    client.post("/api/models", json={"model_id": "M2", "name": "Beta", "confirmed": True},
                headers=HEADERS)
    refused = client.post("/api/models/M2/field",
                          json={"field": "lifecycle_stage", "value": "Retired",
                                "confirmed": True}, headers=HEADERS)
    assert refused.status_code == 400
    assert "Retired" not in refused.get_json()["error"]


def test_registration_accepts_an_added_stage_too(client):
    """Registration validates the same fields by the same rule, so it drifted too."""
    ensure_default_status_vocabularies()
    _add_stage(client)
    created = client.post(
        "/api/models",
        json={"model_id": "M3", "name": "Gamma", "confirmed": True,
              "fields": {"lifecycle_stage": "Decommissioning"}}, headers=HEADERS)
    assert created.status_code == 201, created.get_json()


def test_the_other_status_vocabulary_moved_with_it(client):
    """``validation_status`` is the same shape as the lifecycle field and carried the
    same defect. It is fixed by the same rule rather than by a second copy of it."""
    ensure_default_status_vocabularies()
    client.post(f"/api/reference/collections/{VALIDATION_STATUS_LIST}",
                json={"fields": {"value": "Under Appeal", "label": "Under appeal"},
                      "confirmed": True}, headers=HEADERS)
    client.post("/api/models", json={"model_id": "M4", "name": "Delta", "confirmed": True},
                headers=HEADERS)
    saved = client.post("/api/models/M4/field",
                        json={"field": "validation_status", "value": "Under Appeal",
                              "confirmed": True}, headers=HEADERS)
    assert saved.status_code == 200, saved.get_json()


def test_an_unseeded_database_still_enforces_the_shipped_words(client):
    """The fallback matters: an empty list means the words the platform shipped, not
    'anything goes'. That is what keeps the vocabulary closed on a fresh install."""
    assert not get_reference_lists()[LIFECYCLE_STAGE_LIST]
    client.post("/api/models", json={"model_id": "M5", "name": "Epsilon",
                                     "confirmed": True}, headers=HEADERS)
    refused = client.post("/api/models/M5/field",
                          json={"field": "lifecycle_stage", "value": "Decommissioning",
                                "confirmed": True}, headers=HEADERS)
    assert refused.status_code == 400
    assert "Production" in refused.get_json()["error"]


def test_an_ml_application_takes_the_added_stage(client):
    """All three registers carried their own copy of the defect, so all three are
    covered: the fix is one rule they share, not three that agree today."""
    ensure_default_status_vocabularies()
    ensure_default_estimators()
    _add_stage(client)
    client.post("/api/ml-applications",
                json={"ml_application_id": "MLA-0001", "confirmed": True,
                      "fields": {"name": "Retail PD scorecard", "division": "Risk",
                                 "owner": "David K Kelly",
                                 "estimator": "GradientBoostingClassifier",
                                 "use_case": "Ranks retail applicants."}},
                headers=HEADERS)
    saved = client.post("/api/ml-applications/MLA-0001/field",
                        json={"field": "lifecycle_stage", "value": "Decommissioning",
                              "confirmed": True}, headers=HEADERS)
    assert saved.status_code == 200, saved.get_json()


def test_an_ai_system_takes_the_added_stage(client):
    ensure_default_status_vocabularies()
    _add_stage(client)
    client.post("/api/ai-systems",
                json={"ai_system_id": "AIS-0001", "confirmed": True,
                      "fields": {"name": "Client mail summariser", "division": "Risk",
                                 "owner": "David K Kelly",
                                 "use_case": "Summarises client correspondence.",
                                 "deployment_pattern": "Agentic (tool-using)"}},
                headers=HEADERS)
    saved = client.post("/api/ai-systems/AIS-0001/field",
                        json={"field": "lifecycle_stage", "value": "Decommissioning",
                              "confirmed": True}, headers=HEADERS)
    assert saved.status_code == 200, saved.get_json()
