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
"""Governance Completeness Audit: what the register does not hold (LaTeX -> PDF).

The inverse of the Model Risk Report. That document reproduces the governance
record; this one reports its holes, ranked, with an instruction and a target date
against each. A reader should be able to work top-down through the priority
register and close the estate's worst exposure first without reading anything
else.

Findings are never summarised away. Every gap on every record appears in the
per-record findings, and the counts in the summary reconcile to it, because a
completeness audit that quietly truncates its own register is the one document
where an omission is indefensible.

The sections themselves are in ``report_sections``; see the note there. This file puts
them in order, wraps them in the house style, and compiles the PDF.
"""
from __future__ import annotations

from collections import Counter

from config.governance import (
    COMPLETENESS_ACCEPTABLE_AT,
    COMPLETENESS_CONDITIONAL_AT,
    SEVERITY_BANDS,
)
from src.governance.completeness._method import appendix, method_section
from src.governance.completeness.framework_report import framework_section
from src.governance.completeness.review_programme import programme
from src.governance.completeness.scan import (findings, finos_evidence,
                                              ratified_divisions, scan,
                                              coverage_population, scoped_models)
from src.governance.latex import (_para_table, _section, _subsection, front_matter,
                                  history_page, logo_asset, preamble)
from src.governance.mrc import pack
from src.governance.completeness.report_sections import (
    SUBTITLE, TITLE, _dossier, _priority, _register, _review_programme,
    _summary,
)


def build_completeness_tex(rows: list[dict], settings: dict, as_of: str, *,
                           logo: bool = False, models: list | None = None,
                           coverage: list | None = None,
                           ratified=(), evidence=()) -> str:
    """LaTeX source for the completeness audit.

    ``ratified`` are the divisions whose risk policy their committee has approved;
    the framework-coverage section reads it, and an empty one reports the criteria
    clause as unevidenced rather than guessing.

    ``evidence`` are the documents filed on the FINOS shelf, which the same section
    counts its mitigation catalogue against. Defaulted empty rather than read here,
    so a caller building the report from records it has already scoped cannot have
    a shelf fetched behind its back.
    """
    org = settings.get("fields", {}).get("org_name", "")
    gaps = findings(rows)
    return (
        preamble(TITLE, org_name=org) + "\\begin{document}\n"
        # Sections only in the contents: a subsection per record would run the
        # table of contents past the report it introduces.
        "\\setcounter{tocdepth}{1}\n"
        + front_matter(TITLE, SUBTITLE, org_name=org, date=as_of, logo=logo, toc=True)
        + history_page(as_of, "Completeness audit generated from the model "
                              "inventory, the product register and the document "
                              "store", org_name=org)
        + method_section()
        + _summary(rows, gaps)
        + _register(rows)
        + _priority(gaps)
        + _section("Findings by record",
                   "".join(_dossier(row) for row in rows))
        + _review_programme(models or [])
        # The clause coverage counts ML Applications beside models; the review
        # programme above it does not, because that reports on the inventory's own
        # review cycle. Two populations, two questions, said so here.
        + framework_section(rows, coverage or models or [], as_of, ratified,
                            evidence)
        + appendix()
        + "\\end{document}\n"
    )


def render_completeness_pdf(settings: dict, as_of: str, rows=None, models=None,
                            model_ids=None, ml_application_ids=None,
                            ai_system_ids=None) -> bytes:
    """Scan the registers and compile the completeness audit to PDF bytes.

    ``models`` backs the review-programme and framework-coverage sections, which
    report on the inventory rather than on the findings — the same records, read
    for a different question.

    The ``*_ids`` arguments scope that inventory the way ``scan`` scopes the
    findings, and a caller that scopes one must scope the other -- two populations in
    one report have nothing to tell them apart. Only ``model_ids`` was wired until
    2026-09-07, so a meeting holding an ML Application or an AI System audited its
    models and counted the whole firm.
    """
    assets = logo_asset(settings)
    rows = scan(as_of) if rows is None else rows
    models = scoped_models(model_ids) if models is None else models
    return pack.compile_tex(
        build_completeness_tex(rows, settings, as_of, logo=bool(assets), models=models,
                               coverage=coverage_population(
                                   model_ids, ml_application_ids, ai_system_ids),
                               ratified=ratified_divisions(models),
                               evidence=finos_evidence()),
        assets)
