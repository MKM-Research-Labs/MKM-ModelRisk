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
"""Ongoing Monitoring Report: one model's monitoring position (LaTeX -> PDF).

What ongoing monitoring means here is narrow and stated as such. The platform
carries no client business, so a monitoring document cannot report exceptions
from production use. What it can report — and what this document does — is which
portfolios the model has been exercised against, and the standing position on
every weakness and limitation of use recorded for it.

The weaknesses and limitations come from the inventory, so the document cannot
monitor against a list that has drifted from the one the committee approved. The
portfolio activity comes from the producing repo's port output, so the exercise
record is observed rather than asserted.
"""
from __future__ import annotations

from config.governance import (
    NO_PORTFOLIO_STATEMENT,
    NO_PRODUCTION_STATEMENT,
    NO_SOURCE_STATEMENT,
)
from src.governance.latex import (_para_table, _section, _subsection, front_matter,
                                  history_page, logo_asset, preamble)
from src.governance.model_inventory._report_model import items
from src.governance.monitoring.portfolio import catchments, source_present, summary
from src.governance.mrc import pack

TITLE = "Ongoing Monitoring Report"
SUBTITLE = "Model exercise, recorded weaknesses and limitations of use"

NOT_RECORDED = "\\textit{None recorded.}\n\n"

# The standing position reported against every weakness and limitation while the
# platform runs on generated portfolios. Phrased once, here, so all 24 documents
# say the same thing and a reader comparing two of them is not left wondering
# whether a wording difference means a difference in position.
NO_EXCEPTION = "No exception observed; model exercised on generated portfolios only"


def _basis(model: dict) -> str:
    data = model.get("data", {})
    name = str(data.get("name") or model["model_id"])
    body = (
        f"This report covers ongoing monitoring of \\textbf{{{model['model_id']}}} "
        f"--- {name}. It records the portfolios the model has been exercised "
        f"against and the standing position on each weakness and limitation of "
        f"use held for it on the inventory.\n\n" + NO_PRODUCTION_STATEMENT + "\n\n")
    return _section("Basis of monitoring", body)


def _activity(found: list[dict], configured: bool = True) -> str:
    """The portfolio estate: what has been built, and what has not.

    An unconfigured source is reported as such rather than as an empty estate —
    "we looked and found nothing" and "we never looked" are different statements
    to make in a governance document.
    """
    if not configured:
        return _section("Portfolio activity", NO_SOURCE_STATEMENT + "\n\n")
    totals = summary(found)
    lead = (
        f"Portfolios generated to date: \\textbf{{{totals['populated']}}} of "
        f"\\textbf{{{totals['catchments']}}} catchments, carrying "
        f"\\textbf{{{totals['records']:,}}} records in total. Most recently "
        f"built: \\textbf{{{totals['last_built'] or 'never'}}}.\n\n")
    rows = []
    for entry in found:
        if entry["populations"]:
            detail = "; ".join(f"{p['label']}: {p['records']:,}"
                               for p in entry["populations"])
            rows.append([entry["catchment"], entry["last_built"], detail])
        else:
            rows.append([entry["catchment"], "--", NO_PORTFOLIO_STATEMENT])
    table = _para_table(["Catchment", "Last built", "Population"], rows,
                        [0.22, 0.16, 0.62])
    return _section("Portfolio activity", lead + table)


def _weaknesses(data: dict) -> str:
    entries = items(data, "model_weaknesses")
    if not entries:
        return _subsection("Recorded weaknesses", NOT_RECORDED)
    rows = [[str(w.get("item_id") or ""), str(w.get("description") or ""),
             str(w.get("impact") or ""), NO_EXCEPTION] for w in entries]
    return _subsection("Recorded weaknesses", _para_table(
        ["Ref", "Weakness", "Impact", "Monitoring position"], rows,
        [0.09, 0.42, 0.11, 0.38]))


def _limitations(data: dict) -> str:
    entries = items(data, "limitations")
    if not entries:
        return _subsection("Limitations of use", NOT_RECORDED)
    rows = []
    for limit in entries:
        # The trigger is what this document will report against once there is
        # production activity, so it is printed even though nothing can breach
        # it yet: it is the monitoring rule, not an observation.
        rows.append([
            str(limit.get("item_id") or ""), str(limit.get("description") or ""),
            str(limit.get("impact") or ""),
            str(limit.get("monitoring_trigger") or "--"), NO_EXCEPTION])
    return _subsection("Limitations of use", _para_table(
        ["Ref", "Limitation", "Impact", "Monitoring trigger", "Position"], rows,
        [0.08, 0.30, 0.10, 0.29, 0.23]))


def build_monitoring_tex(model: dict, settings: dict, as_of: str, *,
                         logo: bool = False, found=None,
                         configured: bool | None = None) -> str:
    """LaTeX source for one model's Ongoing Monitoring Report."""
    data = model.get("data", {})
    org = settings.get("fields", {}).get("org_name", "")
    found = catchments() if found is None else found
    configured = source_present() if configured is None else configured
    title = f"{model['model_id']} --- {data.get('name') or ''}"
    return (
        preamble(TITLE, org_name=org) + "\\begin{document}\n"
        + front_matter(title, TITLE, org_name=org, date=as_of, logo=logo, toc=True)
        + _basis(model)
        + _activity(found, configured)
        + _section("Monitoring position",
                   _weaknesses(data) + _limitations(data))
        + "\\clearpage\n"
        + history_page(as_of, TITLE + " generated from the inventory and the "
                              "portfolio generator's output", org_name=org)
        + "\\end{document}\n"
    )


def render_monitoring_pdf(model: dict, settings: dict, as_of: str, found=None,
                          configured: bool | None = None) -> bytes:
    """Build and compile one model's Ongoing Monitoring Report to PDF bytes."""
    assets = logo_asset(settings)
    return pack.compile_tex(
        build_monitoring_tex(model, settings, as_of, logo=bool(assets), found=found,
                             configured=configured),
        assets)
