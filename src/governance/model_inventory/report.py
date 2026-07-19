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
"""Model Risk Report: an MRC-facing inventory status summary (LaTeX -> PDF)."""
from __future__ import annotations

from src.governance.model_inventory.review import compute_review_status
from src.governance.model_inventory.risk import compute_risk_rating
from src.governance.mrc import pack
from src.governance.latex import _table, preamble, title_block


def build_report_tex(models: list, settings: dict, as_of: str) -> str:
    """LaTeX source for the model risk report."""
    fields = settings.get("fields", {})
    counts = {"Acceptable": 0, "Conditional": 0, "Unacceptable": 0}
    rows = []
    for model in models:
        data = model.get("data", {})
        questions = data.get("validation_questions", [])
        addressed = sum(1 for q in questions if q.get("status") == "Addressed")
        rating = compute_risk_rating(data, as_of=as_of)["rating"]
        counts[rating] = counts.get(rating, 0) + 1
        rows.append([
            model["model_id"], data.get("name"), data.get("tier"), data.get("rag_rating"),
            f"{addressed}/{len(questions)}", rating,
            compute_review_status(data.get("next_review_date"), as_of),
        ])
    summary = (f"Models: {len(models)} \\quad Acceptable: {counts['Acceptable']} "
               f"\\quad Conditional: {counts['Conditional']} "
               f"\\quad Unacceptable: {counts['Unacceptable']}")
    return (
        preamble("Model Risk Report", org_name=fields.get("org_name", ""))
        + "\\begin{document}\n"
        + title_block("Model Risk Report", "Status for the Model Risk Committee", date=as_of)
        + "\\begin{center}" + summary + "\\end{center}\\bigskip\n"
        + _table(["Model", "Name", "Tier", "RAG", "Validation", "Risk", "Review"], rows)
        + "\\end{document}\n"
    )


def render_report_pdf(models: list, settings: dict, as_of: str) -> bytes:
    """Build and compile the model risk report to PDF bytes."""
    return pack.compile_tex(build_report_tex(models, settings, as_of))
