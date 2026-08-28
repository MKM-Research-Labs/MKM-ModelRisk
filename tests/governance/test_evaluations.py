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
"""The evaluation record: what testing returned, as opposed to that it happened.

``benchmark_tests: Yes`` is the thing this replaces as evidence. It records that
testing took place and nothing else — not what was tested, against what, what it
found, or when — and a committee cannot challenge a Yes.

The tests worth holding are about that distinction: a description is not a
measurement, and the rows that turn on measurement must not accept prose.
"""
from __future__ import annotations

import pytest

from config.governance import COLLECTION_SPECS, COVERAGE_ABSENT, COVERAGE_EVIDENCED
from config.governance._assessments import (EVALUATIONS_COLLECTION,
                                            VALID_EVALUATION_KINDS,
                                            VALID_EVALUATION_VERDICTS)
from config.governance._finos import FINOS_MITIGATIONS, FINOS_RISKS
from src.governance.completeness.framework import coverage
from src.governance.errors import DomainError
from src.governance.model_inventory import (add_collection_item, get_model,
                                            rebuild_inventory_view, register_model)

AS_OF = "2026-08-28"


def _row(estate, framework, ref):
    rows = coverage([], estate, AS_OF, (), [])
    return next(r for r in rows if r["framework"] == framework and r["ref"] == ref)


def _ai(**data):
    """An AI System record as the clause probes see it."""
    base = {"name": "Summariser", "deployment_pattern": "Retrieval-augmented (RAG)"}
    return [{"ai_system_id": "AIS-1", "data": {**base, **data}}]


def _eval(kind="Held-out performance", **extra):
    return {"kind": kind, "dataset": "Q2 holdout", "metric": "Accuracy",
            "result": "0.91 overall.", **extra}


# --- The shape ---------------------------------------------------------------

def test_an_evaluation_records_what_came_back_not_just_that_it_ran():
    fields = {f["key"] for f in COLLECTION_SPECS[EVALUATIONS_COLLECTION]["fields"]}
    assert {"kind", "dataset", "metric", "result", "passed", "performed_on"} == fields


def test_the_result_is_prose_not_a_number():
    """Half of what matters is not a scalar. "Held at 0.81 AUC but degraded sharply
    below 200 observations per segment" is the finding; a numeric column keeps the
    0.81 and loses the sentence that makes it actionable."""
    result = next(f for f in COLLECTION_SPECS[EVALUATIONS_COLLECTION]["fields"]
                  if f["key"] == "result")
    assert result["type"] == "textarea"


def test_a_verdict_is_optional_because_not_every_run_reaches_one():
    """An exploratory red-team run produces findings without a pass mark, and
    forcing one would make somebody invent it."""
    passed = next(f for f in COLLECTION_SPECS[EVALUATIONS_COLLECTION]["fields"]
                  if f["key"] == "passed")
    assert not passed.get("required")
    assert "Inconclusive" in VALID_EVALUATION_VERDICTS


def test_the_kinds_are_kept_apart_because_they_fail_differently():
    """A held-out score says whether it generalises; a red team says whether it can
    be made to misbehave. One "testing" bucket would average them into nothing."""
    assert "Adversarial / red team" in VALID_EVALUATION_KINDS
    assert "LLM-as-a-judge" in VALID_EVALUATION_KINDS
    assert "Reproducibility check" in VALID_EVALUATION_KINDS


def test_the_kind_is_required():
    register_model(model_id="M-EV", name="Scorecard", actor="admin")
    with pytest.raises(DomainError):
        add_collection_item(model_id="M-EV", collection=EVALUATIONS_COLLECTION,
                            fields={"result": "Looked fine."}, actor="admin")


def test_a_model_records_one():
    register_model(model_id="M-EV2", name="Scorecard", actor="admin")
    add_collection_item(model_id="M-EV2", collection=EVALUATIONS_COLLECTION,
                        fields=_eval(passed="Passed with caveats",
                                     performed_on="2026-07-01"), actor="admin")
    rebuild_inventory_view()
    rows = get_model("M-EV2")["data"][EVALUATIONS_COLLECTION]
    assert len(rows) == 1 and rows[0]["passed"] == "Passed with caveats"


# --- A description is not a measurement --------------------------------------

def test_hallucination_needs_a_measurement_not_a_description():
    """AIR-OP-004. "Answers are drawn only from the retrieved documents" is what the
    team meant to build. The row asks whether anybody checked."""
    described = _ai(grounding="Drawn only from retrieved documents.",
                    human_oversight="Human reviews before action")
    assert _row(described, FINOS_RISKS, "AIR-OP-004")["state"] == COVERAGE_ABSENT

    measured = _ai(grounding="Drawn only from retrieved documents.",
                   human_oversight="Human reviews before action",
                   evaluations=[_eval()])
    assert _row(measured, FINOS_RISKS, "AIR-OP-004")["state"] == COVERAGE_EVIDENCED


def test_non_determinism_wants_the_reproducibility_check_specifically():
    """AIR-OP-006. A held-out score does not answer whether the same input gives the
    same output, so counting any evaluation would report a check nobody ran."""
    wrong_kind = _ai(output_variability="Temperature 0.", evaluations=[_eval()])
    assert _row(wrong_kind, FINOS_RISKS, "AIR-OP-006")["state"] == COVERAGE_ABSENT

    right_kind = _ai(output_variability="Temperature 0.",
                     evaluations=[_eval(kind="Reproducibility check")])
    assert _row(right_kind, FINOS_RISKS, "AIR-OP-006")["state"] == COVERAGE_EVIDENCED


def test_the_judge_mitigation_is_evidenced_from_the_register():
    """AIR-DET-015, the second mitigation the platform evidences from the record
    rather than a filed paper — on the same reasoning as acceptance testing."""
    none_yet = _ai(evaluations=[_eval()])
    assert _row(none_yet, FINOS_MITIGATIONS, "AIR-DET-015")["state"] == COVERAGE_ABSENT

    judged = _ai(evaluations=[_eval(kind="LLM-as-a-judge",
                                    result="Scored 4.2/5 for faithfulness.")])
    row = _row(judged, FINOS_MITIGATIONS, "AIR-DET-015")
    assert row["state"] == COVERAGE_EVIDENCED
    assert row["probe"] != "finos_evidence"
