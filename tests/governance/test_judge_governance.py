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
"""The judge is a model, governed like one.

A judge produces numbers somebody relies on, so it goes through the same onboarding,
classification and committee approval as anything else that does — and a change to it
is a Measurement-class change that invalidates the scores it produced.

None of that means anything unless the records depending on a judge can be FOUND. That
is what these tests are about: a judge version bump has to surface on every dependent
record rather than needing to be discovered.
"""
from __future__ import annotations

from config.governance._assessments import (ASSESSMENT_COLLECTION_SPECS,
                                            EVALUATIONS_COLLECTION)
from src.governance.ai_system.judges import (JUDGE_FIELD, affected_by_judge_change,
                                             dependents_of, judges_of)
from src.governance.change._rules import classify
from src.governance.completeness.framework import PROBES


def _scored_by(judge, kind="LLM-as-a-judge"):
    return {EVALUATIONS_COLLECTION: [
        {"kind": kind, JUDGE_FIELD: judge, "result": "0.81"}]}


# --- The judge is named as a record, not in prose -----------------------------

def test_an_evaluation_names_its_judge_as_a_record():
    field = next(f for f in ASSESSMENT_COLLECTION_SPECS[EVALUATIONS_COLLECTION]["fields"]
                 if f["key"] == JUDGE_FIELD)
    assert field["reference"] == "ai_system_inventory", \
        "the judge is picked from the AI System register, not typed"
    assert not field.get("required"), \
        "a held-out score has no judge, and a human review's judge is a person"


# --- A judge change reaches its dependents ------------------------------------

def test_judge_change_appears_in_every_dependent_affected_artifacts():
    """Without a separate query being needed. The evaluations ARE the dependency, so
    the affected list falls out of the estate rather than out of a register somebody
    has to maintain alongside it."""
    estate = {
        "model_id": [{"model_id": "M-1", "data": _scored_by("AIS-JUDGE")},
                     {"model_id": "M-2", "data": _scored_by("AIS-OTHER")}],
        "ml_application_id": [{"ml_application_id": "MLA-1",
                               "data": _scored_by("AIS-JUDGE")}],
        "ai_system_id": [{"ai_system_id": "AIS-9", "data": _scored_by("AIS-JUDGE")}],
    }
    affected = affected_by_judge_change("AIS-JUDGE", estate)
    assert {a["record_id"] for a in affected} == {"M-1", "MLA-1", "AIS-9"}
    assert "M-2" not in {a["record_id"] for a in affected}, \
        "a record scored by a different judge is not affected"


def test_dependents_are_not_all_one_record_type():
    """A judge scores whatever it is pointed at."""
    estate = {"model_id": [{"model_id": "M-1", "data": _scored_by("J")}],
              "ai_system_id": [{"ai_system_id": "A-1", "data": _scored_by("J")}]}
    assert {a["record_type"] for a in affected_by_judge_change("J", estate)} == \
        {"model_id", "ai_system_id"}


def test_a_record_naming_no_judge_depends_on_none():
    assert judges_of({EVALUATIONS_COLLECTION: [{"kind": "Held-out performance"}]}) == []
    assert judges_of({}) == []


def test_a_judge_named_twice_is_one_dependency():
    data = {EVALUATIONS_COLLECTION: [
        {"kind": "LLM-as-a-judge", JUDGE_FIELD: "J"},
        {"kind": "LLM-as-a-judge", JUDGE_FIELD: "J"}]}
    assert judges_of(data) == ["J"]
    assert dependents_of("J", [{"model_id": "M", "data": data}], "model_id") == ["M"]


# --- A change to the judge is Measurement-class --------------------------------

def test_a_judge_version_bump_classifies_as_measurement():
    """§9.6: a version bump, a re-prompted rubric or a swapped provider requires
    revalidating the evaluation stack before its scores are trusted again."""
    assert classify(subject_type="ai_system",
                    before={"pinned_version": "claude-opus-4"},
                    after={"pinned_version": "claude-opus-5"}) == "Measurement"


def test_swapping_the_judges_model_is_material_not_merely_measurement():
    """A different foundation model is a different judge, not the same judge revised."""
    assert classify(subject_type="ai_system",
                    before={"foundation_model": "a"},
                    after={"foundation_model": "b"}) == "Material"


# --- The existing rule must not regress ----------------------------------------

def test_completeness_still_reads_a_judge_evaluation_as_testing_evidence():
    """The rule at framework.py's ``judged`` probe: a recorded judge evaluation IS the
    evidence, and naming the judge must not have changed what counts."""
    estate = {"rows": [{"record_id": "M-1"}],
              "models": [{"model_id": "M-1", "data": _scored_by("AIS-JUDGE")}],
              "as_of": "2026-09-05", "ratified": set(), "evidence": []}
    met, total = PROBES["judged"](estate)
    assert (met, total) == (1, 1)


def test_an_evaluation_of_another_kind_is_still_not_judge_evidence():
    estate = {"rows": [{"record_id": "M-1"}],
              "models": [{"model_id": "M-1",
                          "data": _scored_by("AIS-JUDGE", kind="Human review")}],
              "as_of": "2026-09-05", "ratified": set(), "evidence": []}
    met, _ = PROBES["judged"](estate)
    assert met == 0
