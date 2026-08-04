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
"""Model Risk Report: the full inventory write-up, for the MRC and for an external
model validation team (LaTeX -> PDF).

The report is a self-contained pack rather than a status sheet. It opens with the
portfolio profile and the inventory table, then carries one dossier per model with
everything the model detail view holds -- classification, methodology, governance,
validation questions and evidence, assumptions, limitations, weaknesses,
remediation, dependencies, change history, MRC decisions and the attached
documents. A reviewer should not have to ask for a second document.

There is deliberately no composite risk verdict here. The governed RAG rating is the
inventory's risk statement; the composite is a derived aid shown beside its
components on the Risk Rating tab, and a bare verdict on paper, detached from the
inputs it came from, reads as an assessment the committee never made.
"""
from __future__ import annotations

from config.governance import CLOSED_REMEDIATION_STATUS
from src.governance.model_inventory._report_model import items, model_section
from src.governance.model_inventory.review import compute_review_status
from src.governance.mrc import pack
from src.governance.latex import (_para_table, _section, _subsection, front_matter,
                                  history_page, logo_asset, preamble)

SCOPE = (
    "This report covers every model on the inventory as at the report date. Each "
    "model's dossier reproduces the full governance record held for it; where a "
    "field or a collection is empty this is stated, so that gaps in the record are "
    "visible rather than silently omitted. Risk is reported as the governed RAG "
    "rating, which is the rating the Model Risk Committee sets and reviews."
)


# The breakdowns making up the portfolio profile. Where a field has a natural
# severity order it is reported in it, worst first, so a reviewer reads the exposure
# before the reassurance; the rest sort by value, which puts the tiers in order.
TALLIES = [
    ("Tier", "tier", ()),
    ("RAG rating", "rag_rating", ("Red", "Amber", "Green")),
    ("Status", "status", ()),
    ("Review status", "review_status",
     ("Overdue", "Due Soon", "Upcoming", "On Track", "Not Scheduled")),
]


def _tally(models: list, key: str, order: tuple, as_of: str) -> list[list]:
    """Count the models by one classification field."""
    counts: dict = {}
    for model in models:
        data = model.get("data", {})
        value = (compute_review_status(data.get("next_review_date"), as_of)
                 if key == "review_status" else data.get(key))
        name = str(value) if value not in (None, "") else "Not recorded"
        counts[name] = counts.get(name, 0) + 1
    rank = {name: index for index, name in enumerate(order)}
    ranked = sorted(counts.items(), key=lambda kv: (rank.get(kv[0], len(rank)), kv[0]))
    return [[name, str(count)] for name, count in ranked]


def _profile(models: list, as_of: str) -> str:
    """The portfolio profile: how the inventory splits by tier, RAG, lifecycle
    status and review status, and how far validation has got."""
    questions = [q for m in models for q in items(m.get("data", {}), "validation_questions")]
    addressed = sum(1 for q in questions if q.get("status") == "Addressed")
    open_steps = sum(1 for m in models for s in items(m.get("data", {}), "remediation_steps")
                     if s.get("status") != CLOSED_REMEDIATION_STATUS)
    body = ["Models on the inventory: \\textbf{" + str(len(models)) + "}. Validation "
            "questions answered: \\textbf{" + str(addressed) + " of " + str(len(questions)) +
            "}. Remediation steps outstanding: \\textbf{" + str(open_steps) + "}.\n\n"]
    for title, key, order in TALLIES:
        body.append(_subsection("By " + title, _para_table(
            [title, "Models"], _tally(models, key, order, as_of), [0.5, 0.5],
            caption="Models by " + title.lower())))
    return _section("Portfolio profile", "".join(body))


def _inventory(models: list, as_of: str) -> str:
    """The one-row-per-model index, pointing into the dossiers that follow."""
    rows = []
    for model in models:
        data = model.get("data", {})
        questions = items(data, "validation_questions")
        addressed = sum(1 for q in questions if q.get("status") == "Addressed")
        rows.append([
            model["model_id"], data.get("name"), data.get("tier"), data.get("rag_rating"),
            f"{addressed}/{len(questions)}",
            compute_review_status(data.get("next_review_date"), as_of),
        ])
    # The model column is wide enough to hold the longest id on one line: a wrapped
    # id reads as two different models when the table is skimmed.
    table = _para_table(["Model", "Name", "Tier", "RAG", "Validation", "Review"],
                        rows, [0.19, 0.28, 0.06, 0.10, 0.15, 0.22],
                        caption="Model inventory index")
    return _section("Model inventory", table)


def build_report_tex(models: list, settings: dict, as_of: str, *, logo: bool = False) -> str:
    """LaTeX source for the model risk report."""
    org = settings.get("fields", {}).get("org_name", "")
    dossiers = "".join(
        model_section(m, compute_review_status(m.get("data", {}).get("next_review_date"), as_of))
        for m in models)
    return (
        preamble("Model Risk Report", org_name=org) + "\\begin{document}\n"
        # Sections only in the contents: with a dossier per model, listing every
        # subsection would run the table of contents to several pages.
        "\\setcounter{tocdepth}{1}\n"
        + front_matter("Model Risk Report", "Model inventory and validation record",
                       org_name=org, date=as_of, logo=logo, toc=True)
        + history_page(as_of, "Model risk report generated from the inventory", org_name=org)
        + _section("Scope and basis of preparation", SCOPE + "\n\n")
        + _profile(models, as_of)
        + _inventory(models, as_of)
        + dossiers
        + "\\end{document}\n"
    )


def render_report_pdf(models: list, settings: dict, as_of: str) -> bytes:
    """Build and compile the model risk report to PDF bytes."""
    assets = logo_asset(settings)
    return pack.compile_tex(build_report_tex(models, settings, as_of, logo=bool(assets)), assets)
