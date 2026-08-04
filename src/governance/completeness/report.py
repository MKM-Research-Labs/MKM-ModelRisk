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
"""
from __future__ import annotations

from collections import Counter

from config.governance import (
    COMPLETENESS_ACCEPTABLE_AT,
    COMPLETENESS_CONDITIONAL_AT,
    SEVERITY_BANDS,
)
from src.governance.completeness._method import appendix, method_section
from src.governance.completeness.scan import findings, scan
from src.governance.latex import (_para_table, _section, _subsection, front_matter,
                                  history_page, logo_asset, preamble)
from src.governance.mrc import pack

TITLE = "Governance Completeness Audit"
SUBTITLE = "Unrecorded fields, undocumented evidence and remediation priority"

BAND_ORDER = [label for label, _floor in SEVERITY_BANDS]

# Gap kinds, in the order the summary reports them, with the wording an audit
# reader expects rather than the internal key.
KIND_LABELS = {
    "field": "Field not recorded",
    "collection": "Collection empty or part-worked",
    "document": "Documentation never uploaded",
    "document_broken": "Documentation recorded but file absent",
}


def _pct(value: float) -> str:
    """A percentage for a table cell. Table cells are escaped on the way in, so
    this must hand over a bare ``%``; pre-escaping it here would reach the page
    as a literal backslash."""
    return f"{value:.1%}"


def _pct_tex(value: float) -> str:
    """A percentage for narrative text, which is emitted as raw LaTeX and so
    carries its own escape."""
    return f"{value:.1%}".replace("%", "\\%")


def _headline(rows: list[dict], gaps: list[dict]) -> str:
    """The three numbers a committee reads before anything else."""
    models = [r for r in rows if r["entity_kind"] == "Model"]
    products = [r for r in rows if r["entity_kind"] == "Product"]
    incomplete = [r for r in rows if r["completeness"] < COMPLETENESS_ACCEPTABLE_AT]
    critical = [g for g in gaps if g["band"] == "Critical"]
    broken = [g for g in gaps if g["kind"] == "document_broken"]
    return (
        f"Records audited: \\textbf{{{len(models)}}} models and "
        f"\\textbf{{{len(products)}}} products. Findings raised: "
        f"\\textbf{{{len(gaps)}}}, of which \\textbf{{{len(critical)}}} are "
        f"Critical. Records below the "
        f"{_pct_tex(COMPLETENESS_ACCEPTABLE_AT)} completeness threshold: "
        f"\\textbf{{{len(incomplete)}}} of \\textbf{{{len(rows)}}}. "
        f"Documentation categories citing a file that is not in the document "
        f"store: \\textbf{{{len(broken)}}}.\n\n")


def _tally(gaps: list[dict], key: str, order: list, labels=None) -> list[list]:
    counts = Counter(g[key] for g in gaps)
    ranked = [k for k in order if k in counts] + sorted(
        k for k in counts if k not in order)
    return [[(labels or {}).get(k, k), str(counts[k])] for k in ranked]


def _summary(rows: list[dict], gaps: list[dict]) -> str:
    body = [_headline(rows, gaps)]
    body.append(_subsection("Findings by severity", _para_table(
        ["Severity", "Findings"], _tally(gaps, "band", BAND_ORDER), [0.6, 0.4],
        caption="Findings by severity")))
    body.append(_subsection("Findings by type", _para_table(
        ["Type", "Findings"],
        _tally(gaps, "kind", list(KIND_LABELS), KIND_LABELS), [0.7, 0.3],
        caption="Findings by type")))
    by_tier = Counter(str(r["tier"] or "Not recorded") for r in rows)
    body.append(_subsection("Records by tier", _para_table(
        ["Tier", "Records"],
        [[t, str(by_tier[t])] for t in sorted(by_tier)], [0.6, 0.4],
        caption="Records by tier")))
    return _section("Summary of findings", "".join(body))


def _register(rows: list[dict]) -> str:
    """One line per record: the escalation applied to it and how complete it is."""
    table_rows = []
    for row in rows:
        counts = Counter(g["band"] for g in row["gaps"])
        state = ("Acceptable" if row["completeness"] >= COMPLETENESS_ACCEPTABLE_AT
                 else "Conditional" if row["completeness"] >= COMPLETENESS_CONDITIONAL_AT
                 else "Materially incomplete")
        table_rows.append([
            row["entity_id"], row["entity_kind"], str(row["tier"] or "--"),
            str(row["rag"] or "--"), str(row["events_in_window"]),
            f"{row['escalation']:.2f}", _pct(row["completeness"]),
            str(len(row["gaps"])), str(counts["Critical"]), state,
        ])
    # The record column is wide enough for the longest id on one line: a wrapped
    # id reads as two different records when the table is skimmed. Headers are
    # abbreviated for the same reason -- a full word in a narrow column wraps
    # into its neighbour and the row stops being readable.
    return _section("Register", _para_table(
        ["Record", "Kind", "Tier", "RAG", "Evts", "Esc.", "Compl.",
         "Gaps", "Crit.", "Assessment"],
        table_rows, [0.17, 0.08, 0.05, 0.08, 0.05, 0.06, 0.08, 0.05, 0.05, 0.13],
        caption="Completeness register"))


def _priority(gaps: list[dict]) -> str:
    """The cross-estate remediation plan: every Critical and High finding.

    Medium and Low findings are not dropped -- they appear in full under the
    record they belong to. What is deferred is said in the text rather than left
    for a reader to notice a count that does not reconcile.
    """
    ranked = [g for g in gaps if g["band"] in ("Critical", "High")]
    deferred = len(gaps) - len(ranked)
    intro = (
        f"Every Critical and High finding across the estate, worst first "
        f"({len(ranked)} of {len(gaps)}). The remaining {deferred} Medium and "
        f"Low findings are reported in full under their own record in the next "
        f"section.\n\n")
    table = _para_table(
        ["Sev.", "Record", "Finding", "Action", "Days"],
        [[g["band"], g["entity_id"], g["label"], g["action"], str(g["sla_days"])]
         for g in ranked],
        [0.09, 0.18, 0.19, 0.46, 0.08], caption="Remediation priority (Critical and High)")
    return _section("Remediation priority", intro + table)


def _dossier(row: dict) -> str:
    """Every finding on one record, with the factors that produced its score."""
    heading = f"{row['entity_id']} --- {row['entity_name'] or row['entity_kind']}"
    if not row["gaps"]:
        return _subsection(heading, "No completeness findings. Every audited "
                                    "field, collection and documentation "
                                    "category is populated.\n\n")
    context = (
        f"Weighted completeness \\textbf{{{_pct_tex(row['completeness'])}}}. "
        f"Tier {row['tier'] or 'not recorded'}, RAG {row['rag'] or 'not recorded'}, "
        f"{row['events_in_window']} operational event(s) in the window. "
        f"Escalation applied to every finding below: "
        f"\\textbf{{{row['escalation']:.2f}}} "
        f"(tier {row['tier_weight']:.2f} $\\times$ rag {row['rag_multiplier']:.2f} "
        f"$\\times$ events {row['event_pressure']:.2f} $\\times$ staleness "
        f"{row['staleness']:.2f}).\n\n")
    table = _para_table(
        ["Sev.", "Finding", "Type", "Crit.", "Severity", "Action", "Days"],
        [[g["band"], g["label"], KIND_LABELS.get(g["kind"], g["kind"]),
          f"{g['criticality']:.2f}", f"{g['severity']:.2f}", g["action"],
          str(g["sla_days"])] for g in row["gaps"]],
        [0.08, 0.15, 0.15, 0.07, 0.10, 0.36, 0.09],
        caption="Findings for " + str(row["entity_id"]))
    return _subsection(heading, context + table)


def build_completeness_tex(rows: list[dict], settings: dict, as_of: str, *,
                           logo: bool = False) -> str:
    """LaTeX source for the completeness audit."""
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
        + appendix()
        + "\\end{document}\n"
    )


def render_completeness_pdf(settings: dict, as_of: str, rows=None) -> bytes:
    """Scan the registers and compile the completeness audit to PDF bytes."""
    assets = logo_asset(settings)
    rows = scan(as_of) if rows is None else rows
    return pack.compile_tex(
        build_completeness_tex(rows, settings, as_of, logo=bool(assets)), assets)
