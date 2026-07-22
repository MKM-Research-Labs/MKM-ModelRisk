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
"""Tests for the Model Risk Report generation."""
from __future__ import annotations

from src.governance.latex import _wrappable
from src.governance.model_inventory._report_model import model_section
from src.governance.model_inventory.report import build_report_tex, render_report_pdf

# M1 is fully populated, so every collection layout is exercised; M2 is bare, so the
# report has to state the gaps rather than skip them.
MODELS = [
    {"model_id": "M1", "data": {
        "name": "Alpha", "tier": 2, "rag_rating": "Green", "status": "Active",
        "description": "An alpha model.", "next_review_date": "2030-01-01",
        "source_module": "src/models/alpha_engine.py",
        "validation_questions": [
            {"short_label": "Data Quality", "question": "Is the input data sound?",
             "status": "Addressed", "evidence": "VAL-1", "rationale": ""},
        ],
        "assumptions": [{"description": "Losses are lognormal", "impact": "High"}],
        "limitations": [{"description": "Thames only", "impact": "Medium"}],
        "model_weaknesses": [{"description": "No extrapolation", "impact": "Low"}],
        "remediation_steps": [{"description": "Recalibrate", "status": "Open"},
                              {"description": "Already done", "status": "Closed"}],
        "dependencies": [{"direction": "downstream", "model_id": "M2"}],
        "version_history": [{"version": "1.0.0", "date": "2026-01-01"}],
        # One entry duplicating the version above, one recorded only here.
        "change_history": [{"version": "1.0.0", "date": "2026-01-01"},
                           {"version": "1.1.0", "date": "2026-02-01",
                            "description": "First cut"}],
        "signoff_history": [{"date": "2026-02-01", "outcome": "Approved"}],
        "documents": [{"category": "Analysis", "filename": "a.pdf",
                       "original_name": "a.pdf", "description": "A"},
                      {"category": "Analysis", "filename": "a.tex",
                       "original_name": "a.tex", "description": "A"},
                      "not-a-dict"],
    }},
    {"model_id": "M2", "data": {"name": "Beta", "tier": 1, "rag_rating": "Amber",
                                "validation_questions": []}},
]

SETTINGS = {"fields": {"org_name": "MKM"}}


def test_report_opens_with_scope_profile_and_inventory():
    tex = build_report_tex(MODELS, SETTINGS, "2026-06-22")
    assert "Model Risk Report" in tex and "MKM" in tex
    assert "Scope and basis of preparation" in tex
    assert "\\section{Portfolio profile}" in tex
    assert "\\section{Model inventory}" in tex
    assert "Models on the inventory: \\textbf{2}" in tex
    # One of M1's two questions across the portfolio is answered.
    assert "\\textbf{1 of 1}" in tex
    assert tex.strip().endswith("\\end{document}")


def test_profile_counts_only_outstanding_remediation():
    """"Outstanding" means still to do. A closed step is history, so it is listed in
    the model's dossier but does not inflate the portfolio's open count."""
    tex = build_report_tex(MODELS, SETTINGS, "2026-06-22")
    assert "Remediation steps outstanding: \\textbf{1}" in tex
    assert "Already done" in tex


def test_profile_orders_ordinal_categories_worst_first():
    tex = build_report_tex(MODELS, SETTINGS, "2026-06-22")
    profile = tex.split("Portfolio profile")[1].split("Model inventory")[0]
    assert profile.index("Amber") < profile.index("Green")
    # A model with no status at all is counted, not dropped.
    assert "Not recorded" in profile


def test_report_carries_no_composite_risk_verdict():
    """The composite rating is a Risk Rating tab aid; on paper, detached from the
    components it is derived from, it reads as a committee assessment it is not."""
    tex = build_report_tex(MODELS, SETTINGS, "2026-06-22")
    for verdict in ("Acceptable", "Conditional", "Unacceptable"):
        assert verdict not in tex


def test_dossier_covers_every_tab():
    section = model_section(MODELS[0], "On Track")
    assert "\\section{M1 --- Alpha}" in section
    for heading in ("Overview", "Classification", "Methodology", "Governance",
                    "Review dates", "Testing", "Assumptions",
                    "Validation questions and evidence", "Limitations",
                    "Model weaknesses", "Remediation plan", "Model dependencies",
                    "Version history", "Model Risk Committee sign-off history",
                    "Attached documents"):
        assert "\\subsection{" + heading + "}" in section
    assert "Losses are lognormal" in section and "Thames only" in section
    assert "Recalibrate" in section and "First cut" in section
    assert "a.pdf" in section


def test_dossier_lists_a_document_once_not_once_per_format():
    """The LaTeX source filed beside its PDF is the same document, not a second one."""
    section = model_section(MODELS[0], "On Track")
    assert "a.pdf" in section and "a.tex" not in section


def test_dossier_states_gaps_rather_than_omitting_them():
    section = model_section(MODELS[1], "Not Scheduled")
    assert "\\subsection{Limitations}" in section
    assert section.count("Not recorded") > 1
    # Empty collections and an empty document list are declared, not skipped.
    assert "\\subsection{Attached documents}\n\\textit{Not recorded.}" in section


def test_dossier_reports_derived_review_status_not_the_stored_field():
    section = model_section(MODELS[1], "Overdue")
    assert "Overdue" in section


def test_dossier_states_the_description_once_under_its_own_heading():
    """Unheaded prose between the contents page and section 1 reads as a stray
    paragraph, and never appeared in the table of contents."""
    section = model_section(MODELS[0], "On Track")
    assert section.count("An alpha model.") == 1
    assert "Overview" in section.split("An alpha model.")[0]


def test_history_merges_change_entries_and_drops_the_duplicate_section():
    """The two registers record the same thing and models populate one, the other or
    both. Reported separately one was usually empty; merged, no model loses the
    record that happens to live in change history."""
    section = model_section(MODELS[0], "On Track")
    assert "Change history" not in section
    assert "First cut" in section              # recorded only in change history
    history_table = section.split("Version history")[1]
    assert history_table.count("1.0.0") == 1   # the duplicated entry appears once


def test_blocks_render_questions_with_their_evidence():
    section = model_section(MODELS[0], "On Track")
    assert "\\textbf{Topic:} Data Quality" in section
    assert "\\textbf{Evidence:} VAL-1" in section
    # An empty field is left out of the block rather than printed blank.
    assert "\\textbf{Rationale:}" not in section


def test_wrappable_breaks_identifiers_and_paths():
    """Long identifiers have no hyphenation points and would run over the margin."""
    assert _wrappable("a_b") == "a\\_\\allowbreak{}b"
    assert _wrappable("src/x") == "src/\\allowbreak{}x"


def test_render_report_pdf(monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex",
                        lambda tex, assets=None: b"%PDF-stub")
    assert render_report_pdf(MODELS, {"fields": {}}, "2026-06-22") == b"%PDF-stub"
