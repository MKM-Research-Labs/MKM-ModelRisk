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
"""One review, three record types — and the guarantee that it does not fork.

A model, an ML Application and an AI System are reviewed identically. That is the whole
premise of the generalised review workflow: the reviewer's job does not change because
the thing under review is an estimator rather than a model, so neither does the sequence,
the statuses, or what sign-off requires.

The plan asked for this as `test_ai_system_completes_all_seven_stages`, and the same for
ML Applications. Written as one parameterised walk instead: three copies of a stage list
is exactly the drift these tests exist to catch. If a stage is ever added for one record
type and not another, every test below fails rather than one.
"""
from __future__ import annotations

import pytest

from config.governance import REVIEW_STAGE_KEYS, REVIEW_STAGES
from config.governance._review import (REVIEW_QUESTION_COLLECTIONS,
                                       REVIEW_QUESTION_STAGE_KEY,
                                       REVIEW_QUESTION_STAGE_LABELS,
                                       review_stages_for)
from config.governance._ai_system_collections import AI_SYSTEM_COLLECTION_SPECS
from config.governance._collections import COLLECTION_SPECS
from config.governance._ml_application import ML_APPLICATION_COLLECTION_SPECS
from src.web._signoff_subject import SUBJECTS

# Where each record type keeps its collections, for the questionnaire check below.
_COLLECTION_SPECS = {"model": COLLECTION_SPECS,
                     "ml_application": ML_APPLICATION_COLLECTION_SPECS,
                     "ai_system": AI_SYSTEM_COLLECTION_SPECS}
from tests.web.conftest import HEADERS

# Each reviewable record type: how to register one, and where it lives.
_SUBJECTS = {
    "model": {
        "api": "/api/models", "id_key": "model_id", "id": "M-REV-1",
        # A model's register form carries ``name`` at the top level rather than inside
        # ``fields``; the two newer record types do not. That asymmetry is the reason
        # this fixture describes each payload instead of assuming one shape.
        "top_level": {"name": "Alpha"},
        "fields": {"division": "Risk", "owner": "David K Kelly"},
    },
    "ml_application": {
        "api": "/api/ml-applications", "id_key": "ml_application_id", "id": "MLA-REV-1",
        "fields": {"name": "Retail PD scorecard", "division": "Risk",
                   "owner": "David K Kelly", "estimator": "GradientBoostingClassifier",
                   "use_case": "Ranks retail applicants by probability of default."},
    },
    "ai_system": {
        "api": "/api/ai-systems", "id_key": "ai_system_id", "id": "AIS-REV-1",
        "fields": {"name": "Client mail summariser", "division": "Risk",
                   "owner": "David K Kelly",
                   "use_case": "Summarises inbound client correspondence for the desk.",
                   "deployment_pattern": "Agentic (tool-using)"},
    },
}
_KINDS = sorted(_SUBJECTS)


def _register(client, kind):
    cfg = _SUBJECTS[kind]
    payload = {cfg["id_key"]: cfg["id"], "fields": cfg["fields"], "confirmed": True,
               **cfg.get("top_level", {})}
    return client.post(cfg["api"], json=payload, headers=HEADERS)


def _approve(client, kind, stage, note=""):
    cfg = _SUBJECTS[kind]
    return client.post(f"{cfg['api']}/{cfg['id']}/review/approve-stage",
                       json={"stage": stage, "note": note, "confirmed": True},
                       headers=HEADERS)


def _read(client, kind):
    cfg = _SUBJECTS[kind]
    return client.get(f"{cfg['api']}/{cfg['id']}", headers=HEADERS).get_json()["data"]


# --- The sequence is the same for everybody ----------------------------------

def test_no_record_type_has_a_stage_another_lacks():
    """The rule that the sequence does not fork, mechanised.

    Read off ``Subject`` rather than off a list written here, so a record type added
    later is covered by this test on the day it is added rather than the day somebody
    remembers to extend the fixture.
    """
    reviewable = [s.kind for s in SUBJECTS if s.reviewable()]
    assert sorted(reviewable) == _KINDS, (
        "a reviewable record type is missing from this test's fixture: "
        f"{sorted(set(reviewable) ^ set(_KINDS))}")
    for kind in reviewable:
        keys = tuple(stage["key"] for stage in review_stages_for(kind))
        assert keys == REVIEW_STAGE_KEYS, f"{kind} has its own stage sequence"


def test_only_the_questions_stage_is_worded_per_record_type():
    """Same stages, same order, same statuses — one substitution, and it is a label.

    A record type may call the questions stage what its questionnaire actually is;
    everything else is shared wording, because a stage that reads differently on two
    screens invites the belief that it is a different stage.
    """
    for kind in _KINDS:
        for shared, mine in zip(REVIEW_STAGES, review_stages_for(kind)):
            assert shared["key"] == mine["key"]
            assert shared["status"] == mine["status"]
            if mine["key"] != REVIEW_QUESTION_STAGE_KEY:
                assert shared["label"] == mine["label"], f"{kind} renamed {mine['key']}"
            else:
                assert mine["label"] == REVIEW_QUESTION_STAGE_LABELS[kind]


def test_every_record_type_has_a_questionnaire_and_a_name_for_it():
    """The claim `_review.py` makes about itself: the per-record collections and labels
    do not drift from the record types that exist. The comment said a test asserted
    this; until now none did."""
    assert sorted(REVIEW_QUESTION_COLLECTIONS) == _KINDS
    assert sorted(REVIEW_QUESTION_STAGE_LABELS) == _KINDS
    # Each names a collection the record actually keeps, not an aspiration.
    for kind, collection in REVIEW_QUESTION_COLLECTIONS.items():
        assert collection in _COLLECTION_SPECS[kind], \
            f"{kind}'s questions stage points at {collection}, which it has no collection for"


# --- The walk ----------------------------------------------------------------

@pytest.mark.parametrize("kind", _KINDS)
def test_every_review_subject_completes_all_seven_stages(client, kind):
    """Register, agree every stage in order, and arrive at a review ready to sign.

    The status after each stage is the status the shared config declares — so a record
    type cannot quietly carry its own vocabulary, and the review's progress is a fact
    about work done rather than about somebody changing a dropdown.
    """
    assert _register(client, kind).status_code in (200, 201)
    for stage in REVIEW_STAGES:
        data = _approve(client, kind, stage["key"], note=f"{stage['key']} agreed").get_json()["data"]
        assert data["review_status"] == stage["status"], \
            f"{kind} reports {data['review_status']!r} after {stage['key']}"
    progress = _read(client, kind)["review_progress"]
    assert [row["stage"] for row in progress] == list(REVIEW_STAGE_KEYS)
    assert all(row["approved_by"] == HEADERS["X-Auth-Request-User"] for row in progress)
    assert all(row["approved_at"] for row in progress)


@pytest.mark.parametrize("kind", _KINDS)
def test_the_questions_stage_is_labelled_for_the_record_it_belongs_to(client, kind):
    """"The nine questions" is SR 26-2's nine specifically. An AI System answering a
    twelve-question AI questionnaire must not be told it answered those nine."""
    _register(client, kind)
    row = _approve(client, kind, REVIEW_QUESTION_STAGE_KEY).get_json()["data"]["review_progress"][0]
    assert row["stage_label"] == REVIEW_QUESTION_STAGE_LABELS[kind]


@pytest.mark.parametrize("kind", _KINDS)
def test_a_review_missing_a_stage_cannot_be_signed_off(client, kind):
    """Sign-off is the reviewer's statement that the work was done. It is refused while
    any of it is outstanding — identically for all three, because a weaker bar for the
    newer record types is exactly the drift this suite exists to prevent."""
    cfg = _SUBJECTS[kind]
    _register(client, kind)
    for stage in REVIEW_STAGES[:-1]:
        _approve(client, kind, stage["key"])
    blockers = client.get(f"{cfg['api']}/{cfg['id']}/review/blockers",
                          headers=HEADERS).get_json()
    outstanding = blockers.get("blockers") or blockers.get("outstanding") or []
    assert outstanding, f"{kind} reports nothing outstanding with a stage unagreed"


# --- Segregation of duties ----------------------------------------------------

@pytest.mark.parametrize("kind", _KINDS)
def test_reviewer_independence_applies_to_every_review_subject(client, kind):
    """A record's reviewer may not be its own owner — on all three, identically.

    This was true of models alone until 2026-09-06. An ML Application or an AI System
    could be registered with the owner named as its own reviewer and nothing refused
    it, while the completeness audit reported exactly that arrangement as a finding on
    all three. The audit was right and the write path was not.
    """
    cfg = _SUBJECTS[kind]
    owner = cfg["fields"]["owner"]
    payload = {cfg["id_key"]: cfg["id"] + "-BREACH",
               "fields": {**cfg["fields"], "peer_reviewer": owner},
               "confirmed": True, **cfg.get("top_level", {})}
    res = client.post(cfg["api"], json=payload, headers=HEADERS)
    assert res.status_code >= 400, f"{kind} accepted its owner as its own reviewer"
    assert "independent" in res.get_json()["error"]


@pytest.mark.parametrize("kind", _KINDS)
def test_the_owner_cannot_be_moved_onto_the_reviewer_either(client, kind):
    """The other side of the pair. A rule enforced on one side is not enforced: a
    record with a distinct reviewer is put in breach just as easily by moving the
    ownership onto them."""
    cfg = _SUBJECTS[kind]
    reviewer = "Tom Cairney"
    payload = {cfg["id_key"]: cfg["id"] + "-PAIR",
               "fields": {**cfg["fields"], "peer_reviewer": reviewer},
               "confirmed": True, **cfg.get("top_level", {})}
    assert client.post(cfg["api"], json=payload, headers=HEADERS).status_code in (200, 201)
    res = client.post(f"{cfg['api']}/{cfg['id']}-PAIR/field",
                      json={"field": "owner", "value": reviewer, "confirmed": True},
                      headers=HEADERS)
    assert res.status_code >= 400, f"{kind} let the owner be moved onto its reviewer"
    assert "independent" in res.get_json()["error"]
