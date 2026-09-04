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
"""The Model Review Report: the document the MRC receives as evidence.

The committee's decision is the model's risk rating, not the review — so what this
document has to carry is the ARGUMENT, stage by stage, including the exchange
between the owner and the reviewer. An empty section would read as a missing page,
so every absence is stated rather than skipped.
"""
from __future__ import annotations

from src.governance.model_inventory.review_report import (build_review_report_tex,
                                                          render_review_report_pdf)

SETTINGS = {"fields": {"org_name": "MKM"}}
SIGNOFF = {"signed_by": "R. Ellis", "signed_at": "2026-06-22T09:30:00",
           "commentary": "Fit for the retail book only."}
APPROVALS = {"assumptions": {"approved_by": "R. Ellis",
                             "approved_at": "2026-06-20T11:00:00",
                             "note": "Subject to the monitoring below."}}

MODEL = {"model_id": "M1", "data": {
    "name": "Alpha", "owner": "D. Kelly", "peer_reviewer": "R. Ellis",
    "review_trigger": "Annual cycle",
    "assumptions": [{"description": "Rates stay positive", "impact": "High",
                     "monitoring": "Daily curve check", "mitigation": "Floor at zero"}],
    "model_weaknesses": [{"description": "Thin tail data", "impact": "Medium"}],
    "limitations": [{"description": "UK book only", "impact": "Medium",
                     "monitoring_trigger": "Any non-UK exposure",
                     "compensating_control": "Manual review"}],
    "validation_questions": [
        {"short_label": "Ronseal Test", "status": "Addressed",
         "rationale": "It does what it says.", "reviewer_verdict": "Challenged",
         "reviewer_comment": "Not on the 2019 vintage."}],
}}


def _tex(model=MODEL, approvals=APPROVALS):
    return build_review_report_tex(model, SETTINGS, SIGNOFF, "2026-06-22", approvals)


def test_the_report_names_the_model_the_owner_and_the_reviewer():
    tex = _tex()
    assert "M1 --- Alpha" in tex
    assert "D. Kelly" in tex and "R. Ellis" in tex
    assert tex.strip().endswith("\\end{document}")


def test_every_agreed_register_is_carried_in_full():
    """The registers ARE the review: an assumption agreed without its monitoring
    is an assumption nobody is watching."""
    tex = _tex()
    for cell in ("Rates stay positive", "Daily curve check", "Floor at zero",
                 "Thin tail data", "UK book only", "Any non-UK exposure",
                 "Manual review"):
        assert cell in tex, cell


def test_the_owners_answer_and_the_reviewers_verdict_are_shown_together():
    """A question the owner called Addressed and the reviewer Challenged is the
    single most interesting row in the document; two tables would bury it."""
    tex = _tex()
    questions = tex[tex.index("Ronseal Test"):]
    assert "Addressed" in questions[:400]
    assert "Challenged" in questions[:400]
    assert "Not on the 2019 vintage" in questions[:400]


def test_a_stage_nobody_agreed_says_so_rather_than_going_quiet():
    tex = _tex(approvals={})
    assert "Not agreed." in tex
    assert "Agreed by R. Ellis" not in tex


def test_an_agreed_stage_names_who_agreed_it_and_when():
    tex = _tex()
    assert "Agreed by R. Ellis on 2026-06-20" in tex
    assert "Subject to the monitoring below." in tex


def test_an_empty_register_is_stated_as_empty_not_omitted():
    """An empty section reads as a missing page; "None recorded" reads as a
    finding — and the committee can act on a finding."""
    bare = {"model_id": "M2", "data": {"name": "Beta"}}
    tex = _tex(bare, approvals={})
    assert tex.count("None recorded.") >= 3          # the three registers
    assert "No questions recorded." in tex


def test_render_review_report_pdf(monkeypatch):
    monkeypatch.setattr(
        "src.governance.model_inventory.review_report.compile_tex",
        lambda tex, assets=None: b"%PDF-stub")
    assert render_review_report_pdf(
        MODEL, {"fields": {}}, SIGNOFF, "2026-06-22", APPROVALS) == b"%PDF-stub"
