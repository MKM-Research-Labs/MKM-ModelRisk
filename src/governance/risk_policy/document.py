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
"""The Risk Categorisation document: one PDF of a division's proposed categorisation.

Generated for the division's MRC to ratify — the three dimensions, the overall risk
ratings (each with its colour, explanation and score) and the generated
risk grids — in the shared LaTeX house style, under the division's own names for
its dimensions.

This is DISTINCT from the division's Risk Policy document, which is the formal written
policy uploaded separately (see the ``document`` on the risk-policy store); the two are
referenced against each other but are not the same artefact.
"""
from __future__ import annotations

from src.governance.latex import (
    _esc,
    _section,
    _subsection,
    _wrappable,
    front_matter,
    history_page,
    logo_asset,
    preamble,
)
from src.governance.mrc.pack import compile_tex
from src.governance.risk_policy._store import load

DOC_TITLE = "Risk Categorisation"

_STATUS_SUBTITLE = {
    "draft": "Proposed for MRC sign-off",
    "approved": "Approved policy",
    "seed": "Firm-wide seed policy",
}
# The three dimensions are structural — one grid per band of the first, across the
# other two. What a division CALLS them is its own, and is read from the policy
# being published: a document that spelled them out here would keep printing the
# old name the day a division renamed one, which is exactly the moment the
# document matters most.
_DIMENSION_KEYS = ("mission_criticality", "materiality", "complexity")


def _dim_label(policy: dict, key: str) -> str:
    """What this policy calls one of its dimensions."""
    dim = (policy.get("dimensions") or {}).get(key) or {}
    return dim.get("label") or key.replace("_", " ").capitalize()


def _hex(colour) -> str:
    """A 6-digit uppercase RRGGBB for xcolor's HTML model, defaulting to grey."""
    h = str(colour or "").lstrip("#").upper()
    if len(h) == 6 and all(c in "0123456789ABCDEF" for c in h):
        return h
    return "9E9E9E"


def _swatch(colour) -> str:
    return "\\textcolor[HTML]{" + _hex(colour) + "}{\\rule{9pt}{9pt}}"


def _band_table(bands: list[dict], score_label: str, caption: str) -> str:
    """A booktabs table of bands: name, a colour swatch, the explanation, and the score."""
    cols = (">{\\raggedright\\arraybackslash}p{0.20\\textwidth} c "
            ">{\\raggedright\\arraybackslash}p{0.50\\textwidth} r")
    head = ("\\textbf{Name} & \\textbf{Colour} & \\textbf{Explanation} & \\textbf{"
            + _esc(score_label) + "} \\\\")
    body = "".join(
        _wrappable(b.get("name", "")) + " & " + _swatch(b.get("colour")) + " & "
        + _wrappable(b.get("explanation", "")) + " & " + _esc(b.get("score", "")) + " \\\\\n\\addlinespace\n"
        for b in bands)
    header_rows = "\\toprule\n" + head + "\n\\midrule\n"
    return ("\\begin{longtable}{" + cols + "}\n\\caption{" + _esc(caption) + "}\\\\\n"
            + header_rows + "\\endfirsthead\n" + header_rows + "\\endhead\n"
            + body + "\\bottomrule\n\\end{longtable}\n")


def _grid_cell(rating: str, colour) -> str:
    return "\\textcolor[HTML]{" + _hex(colour) + "}{\\textbf{" + _esc(rating) + "}}" if rating else "---"


def _grids(policy: dict) -> str:
    """One table per band of the first dimension, the second down the rows (high at
    top) and the third across the columns; each cell is its assigned risk rating in
    the rating's colour. Every heading is the division's own name for the dimension."""
    mat = [b["name"] for b in policy["dimensions"]["materiality"]["bands"]]
    comp = [b["name"] for b in policy["dimensions"]["complexity"]["bands"]]
    mat_label, comp_label = _dim_label(policy, "materiality"), _dim_label(policy, "complexity")
    colour = {r["name"]: r.get("colour") for r in policy["risk_ratings"]}
    out = ""
    for band in policy["dimensions"]["mission_criticality"]["bands"]:
        mc = band["name"]
        cells = policy["grid"].get(mc, {})
        head = " & " + " & ".join("\\textbf{" + _esc(c) + "}" for c in comp) + " \\\\"
        rows = "".join(
            "\\textbf{" + _esc(a) + "} & "
            + " & ".join(_grid_cell(cells.get(a + "|" + c, ""), colour.get(cells.get(a + "|" + c)))
                         for c in comp) + " \\\\\n"
            for a in reversed(mat))
        table = ("\\begin{center}\\begin{tabular}{l" + "c" * len(comp) + "}\n\\toprule\n"
                 + head + "\n\\midrule\n" + rows + "\\bottomrule\n\\end{tabular}\\end{center}\n")
        out += _subsection(mc, _esc(mat_label) + " (rows) $\\times$ " + _esc(comp_label)
                           + " (columns).\\par\\medskip\n" + table)
    return out


def build_policy_document_tex(division: str, detail: dict, settings: dict, *,
                              logo: bool = False, as_of: str = "") -> str:
    """LaTeX for a division's proposed (or live) risk policy sign-off document."""
    policy = detail.get("draft") or detail.get("live")
    org = (settings.get("fields") or {}).get("org_name", "")
    subtitle = _STATUS_SUBTITLE.get(detail.get("state"), DOC_TITLE)
    # Division-qualified title so the running header on EVERY page names the division —
    # the policy is owned and signed off at the division level.
    doc_title = division + " " + DOC_TITLE

    intro = _section(
        "Purpose",
        "This document sets out the risk categorisation for the \\textbf{" + _esc(division)
        + "} division, submitted to its Model Risk Committee for ratification. Once approved "
        "it governs how the division's models are placed on the risk grid, the ratings they "
        "can carry, and the escalation weights applied in the completeness audit. It is "
        "distinct from the division's formal written Risk Policy document, which is filed "
        "separately.\n")

    dims = "".join(
        _band_table(policy["dimensions"][key]["bands"], "Score",
                    _esc(policy["dimensions"][key]["label"]) + " bands")
        for key in _DIMENSION_KEYS)
    dims_section = _section(
        "Risk dimensions",
        "A model is placed by three dimensions. Each is an ordered set of bands.\n" + dims)

    ratings_section = _section(
        "Overall risk ratings",
        "The ratings a model can carry. The score is the completeness-audit escalation "
        "multiplier.\n" + _band_table(policy["risk_ratings"], "Score / multiplier",
                                      "Overall risk ratings"))

    grids_section = _section(
        "Risk tables",
        "One " + _esc(_dim_label(policy, "materiality")) + " $\\times$ "
        + _esc(_dim_label(policy, "complexity")) + " table per "
        + _esc(_dim_label(policy, "mission_criticality")) + " band, mapping each cell "
        "to an overall risk rating.\n" + _grids(policy))

    doc_note = ""
    if detail.get("document"):
        doc_note = _section("Risk Policy document",
                            "The division's formal written Risk Policy, \\textbf{"
                            + _wrappable(detail["document"]["original_name"])
                            + "}, is filed alongside this categorisation.\n")

    return (
        preamble(doc_title, org_name=org) + "\\begin{document}\n"
        + front_matter(division + " --- Risk Categorisation", subtitle, org_name=org,
                       date=as_of, logo=logo, toc=True)
        + history_page(as_of, "Risk categorisation for the " + division + " division "
                       "submitted for MRC sign-off", org_name=org)
        + intro + dims_section + ratings_section + grids_section + doc_note
        + "\\end{document}\n"
    )


def render_policy_document_pdf(division: str, settings: dict, as_of: str) -> bytes:
    """Build and compile a division's risk-policy sign-off document to PDF bytes."""
    detail = load(division)
    assets = logo_asset(settings)
    tex = build_policy_document_tex(division, detail, settings, logo=bool(assets), as_of=as_of)
    return compile_tex(tex, assets)
