# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
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
from src.governance.mrc.pack import _esc, _table


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
    header = ""
    if fields.get("org_name"):
        header = "{\\large\\textbf{" + _esc(fields["org_name"]) + "}}\\\\\n"
    summary = (f"Models: {len(models)} \\quad Acceptable: {counts['Acceptable']} "
               f"\\quad Conditional: {counts['Conditional']} "
               f"\\quad Unacceptable: {counts['Unacceptable']}")
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[a4paper,margin=20mm]{geometry}\n"
        "\\usepackage{longtable}\\usepackage{array}\\usepackage{xcolor}\\usepackage{parskip}\n"
        "\\begin{document}\n\\begin{center}\n" + header +
        "{\\Large\\textbf{Model Risk Report}}\\\\[2pt]\n"
        "{\\small Status for the Model Risk Committee --- as of " + _esc(as_of) + "}\\\\[6pt]\n"
        + summary + "\\end{center}\\bigskip\n" +
        _table(["Model", "Name", "Tier", "RAG", "Validation", "Risk", "Review"], rows) +
        "\\vfill\\begin{center}\\small\\textcolor{gray}{" +
        _esc(fields.get("framework", "")) + "}\\end{center}\n\\end{document}\n"
    )


def render_report_pdf(models: list, settings: dict, as_of: str) -> bytes:
    """Build and compile the model risk report to PDF bytes."""
    return pack.compile_tex(build_report_tex(models, settings, as_of))
