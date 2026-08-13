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
"""A review is a programme, and is reported as one rather than scored as a gap.

Scoring the review workflow would have marked every model in the estate incomplete
on the day it shipped and held it there until each had been reviewed — a new bar
applied backwards, which reads as decay rather than as the backlog it is. These
tests hold the separation: the audit does not charge a model for a review it has
not had, and the programme section says where the work has got to.
"""
from __future__ import annotations

from config.governance import (EXEMPT_COLLECTIONS, EXEMPT_DOC_CATEGORIES,
                               EXEMPT_FIELDS, REVIEW_STAGES)
from src.governance.completeness.review_programme import model_state, programme


def _model(model_id="M1", **data):
    return {"model_id": model_id, "data": {"name": "Alpha", **data}}


def test_the_review_is_out_of_the_scoring_entirely():
    """Collections, documents and the brief — none of them a gap in the record."""
    for collection in ("review_notes", "review_progress", "review_signoffs"):
        assert collection in EXEMPT_COLLECTIONS, collection
    for category in ("Review", "Model Review Report"):
        assert category in EXEMPT_DOC_CATEGORIES, category
    for field in ("review_trigger", "review_scope", "review_due_date",
                  "review_docs_updated"):
        assert field in EXEMPT_FIELDS, field


def test_a_model_with_no_review_is_counted_not_listed():
    """A list of everything not yet begun is the inventory, which the reader has."""
    state = programme([_model("M1"), _model("M2")])
    assert (state["records"], state["not_started"]) == (2, 0 + 2)
    assert state["under_way"] == 0 and state["signed_off"] == 0
    assert state["rows"] == []
    assert state["stages_possible"] == 2 * len(REVIEW_STAGES)


def test_a_review_under_way_reports_how_far_it_has_got():
    model = _model("M1", peer_reviewer="Priya Anand", review_trigger="New version",
                   review_progress=[{"stage": "documents"}, {"stage": "questions"}])
    state = programme([model])
    assert state["under_way"] == 1 and state["not_started"] == 0
    assert state["stages_agreed"] == 2
    assert state["rows"][0]["stages_agreed"] == 2
    assert state["rows"][0]["reviewer"] == "Priya Anand"


def test_progress_reads_forward_from_the_current_cycle():
    """Last year's approvals must not flatter this year's review."""
    model = _model("M1", review_progress=[
        {"stage": "documents"}, {"stage": "questions"}, {"stage": "weaknesses"},
        {"stage": "cycle-start"},
        {"stage": "documents"},
    ])
    assert model_state(model)["stages_agreed"] == 1


def test_a_signed_off_review_is_reported_as_done():
    model = _model("M1", review_signoffs=[{"signed_at": "2026-08-09T10:00:00",
                                           "commentary": "Fit for use."}])
    state = programme([model])
    assert state["signed_off"] == 1 and state["under_way"] == 0
    assert state["rows"][0]["signed_off_at"] == "2026-08-09"


def test_open_challenges_are_surfaced_across_the_estate():
    """What is standing in the way of a sign-off, not just that one is outstanding."""
    model = _model("M1", review_notes=[
        {"item_id": "RN-001", "kind": "Challenge"},
        {"item_id": "RN-002", "kind": "Challenge"},
        {"item_id": "RN-003", "kind": "Note", "resolves": "RN-001"},
    ])
    assert model_state(model)["open_challenges"] == 1
    assert programme([model])["open_challenges"] == 1
