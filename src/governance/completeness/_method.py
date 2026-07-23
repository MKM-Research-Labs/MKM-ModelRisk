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
"""The method statement and weight appendix for the completeness audit.

Split from the report body because it is the part a reviewer challenges first.
Every number the audit uses is printed here from the same constants the scoring
reads, so the appendix cannot drift from the arithmetic it documents -- an
appendix maintained by hand would eventually describe a scoring run that no
longer happens.
"""
from __future__ import annotations

from config.governance import (
    AUDIT_BASIS,
    BROKEN_DOC_ESCALATION,
    COLLECTION_CRITICALITY,
    COMPLETENESS_ACCEPTABLE_AT,
    CONDITIONAL_DOC_CATEGORIES,
    DEFAULT_COLLECTION_CRITICALITY,
    DEFAULT_DOC_CRITICALITY,
    DEFAULT_FIELD_CRITICALITY,
    DOC_CRITICALITY,
    EVENT_PRESSURE_CAP,
    EVENT_PRESSURE_PER_EVENT,
    EVENTS_WINDOW_DAYS,
    EXEMPT_COLLECTIONS,
    EXEMPT_FIELDS,
    FIELD_CRITICALITY,
    MODEL_FIELD_SPECS,
    RAG_MULTIPLIERS,
    REMEDIATION_SLA_DAYS,
    SEVERITY_BANDS,
    STALENESS_STEPS,
    TIER_LABELS,
    TIER_WEIGHTS,
    UNRATED_MULTIPLIER,
    UNTIERED_WEIGHT,
)
from src.governance.latex import _para_table, _section, _subsection

SCOPE = (
    "This report covers every model on the inventory and every product on the "
    "product register as at the report date. It reports what the governance "
    "record does not hold: scalar fields left unrecorded, collections left "
    "empty or part-worked, and documentation categories with no retrievable "
    "file. It is a completeness audit and not a validation opinion -- a field "
    "that is populated is reported as populated, and nothing here asserts that "
    "what it holds is correct. Findings are framed against " + AUDIT_BASIS + "."
)

METHOD = (
    "Each gap is scored rather than merely listed, so the register states what "
    "to remediate first. The score is the product of one criticality weight and "
    "four escalation factors:\n\n"
    "\\begin{center}\\ttfamily severity = criticality $\\times$ tier $\\times$ "
    "rag $\\times$ events $\\times$ staleness\\end{center}\n\n"
    "Criticality is how much the absence matters in itself. The four factors are "
    "each centred on 1.0, so a factor that does not apply leaves the score where "
    "the criticality put it, and they multiply rather than add because the "
    "conditions compound: a model that is unvalidated \\emph{and} mission "
    "critical \\emph{and} rated Red \\emph{and} carrying recent operational "
    "failures is not four separate small problems. Every input is tabulated in "
    "the appendix, so any severity in this report can be reproduced by hand.\n\n"
    "Two classes of absence are deliberately \\emph{not} reported as findings. "
    "Collections whose empty state is legitimate are excluded -- an empty "
    "remediation list means nothing is outstanding and an empty events list "
    "means nothing has gone wrong, so scoring them would penalise the "
    "best-kept records. Evidence categories are only expected where there is "
    "something to evidence. Both exclusions are listed in the appendix.\n\n"
    "A documentation category whose records all point at files that are absent "
    "from the document store is reported separately from one never populated, "
    "and scored " + f"{BROKEN_DOC_ESCALATION:g}" + " times higher. Both leave "
    "the same hole in the evidence, but a broken reference also asserts to a "
    "reader of the register that the evidence exists. An inventory that "
    "overstates its own coverage is the more serious finding, and it is not "
    "visible to anyone reading the register alone.\n\n"
    "Weighted completeness, quoted per record, is the share of the criticality "
    "a record was asked to carry that it actually holds. It is weighted because "
    "an unweighted percentage flatters a record that has filled in its cheap "
    "fields and left the expensive ones blank. A record is reported as "
    "materially incomplete below "
    + f"{COMPLETENESS_ACCEPTABLE_AT:.0%}".replace("%", "\\%") + ".\n\n"
)


def _criticality_rows(weights: dict, default: float, universe) -> list[list]:
    """Criticality table rows for one gap kind, defaults folded in."""
    rows = [[key, f"{weights.get(key, default):.2f}"] for key in universe]
    return sorted(rows, key=lambda r: (-float(r[1]), r[0]))


def _band_table() -> str:
    rows = [[label, f"{floor:.2f} and above", f"{REMEDIATION_SLA_DAYS[label]} days"]
            for label, floor in SEVERITY_BANDS]
    return _para_table(["Band", "Severity", "Target to close"], rows, [0.3, 0.4, 0.3])


def _factor_table() -> str:
    """Every escalation factor in one table, since a reviewer checking a score
    reads them together rather than one per page."""
    rows = [["Tier " + str(tier) + " (" + TIER_LABELS[tier] + ")", f"{weight:.2f}"]
            for tier, weight in sorted(TIER_WEIGHTS.items())]
    rows.append(["Tier not recorded", f"{UNTIERED_WEIGHT:.2f}"])
    for rating in ("Red", "Amber", "Green"):
        rows.append(["RAG " + rating, f"{RAG_MULTIPLIERS[rating]:.2f}"])
    rows.append(["RAG not recorded", f"{UNRATED_MULTIPLIER:.2f}"])
    rows.append([
        f"Each operational event in the last {EVENTS_WINDOW_DAYS} days",
        f"+{EVENT_PRESSURE_PER_EVENT:.2f} (capped at {EVENT_PRESSURE_CAP:.2f})"])
    for days, multiplier in STALENESS_STEPS:
        label = ("Review overdue by a year or more" if days >= 365
                 else f"Review overdue by {days} days or more" if days
                 else "Review overdue at all")
        rows.append([label, f"{multiplier:.2f}"])
    rows.append(["Review not yet due, or none scheduled", "1.00"])
    return _para_table(["Condition", "Factor"], rows, [0.7, 0.3])


def method_section() -> str:
    return _section("Basis of preparation and method", SCOPE + "\n\n" + METHOD)


def appendix() -> str:
    """The full weight set, printed from the live constants."""
    body = [
        _subsection("Severity bands and remediation targets", _band_table()),
        _subsection("Escalation factors", _factor_table()),
        _subsection("Field criticality", _para_table(
            ["Field", "Weight"],
            _criticality_rows(FIELD_CRITICALITY, DEFAULT_FIELD_CRITICALITY,
                              [k for k in MODEL_FIELD_SPECS if k not in EXEMPT_FIELDS]),
            [0.7, 0.3])),
        _subsection("Collection criticality", _para_table(
            ["Collection", "Weight"],
            _criticality_rows(COLLECTION_CRITICALITY, DEFAULT_COLLECTION_CRITICALITY,
                              sorted(COLLECTION_CRITICALITY)),
            [0.7, 0.3])),
        _subsection("Documentation criticality", _para_table(
            ["Category", "Weight"],
            _criticality_rows(DOC_CRITICALITY, DEFAULT_DOC_CRITICALITY,
                              sorted(DOC_CRITICALITY)),
            [0.7, 0.3])),
        _subsection("Exclusions", _para_table(
            ["Excluded", "Reason"],
            [[name, "Empty is a legitimate state; scoring it would penalise a "
                    "clean record"] for name in sorted(EXEMPT_COLLECTIONS)]
            + [[name, "Derived from other fields; already raised against those"]
               for name in sorted(EXEMPT_FIELDS)]
            + [[name, "Only expected where there is something to evidence "
                      f"(here: {trigger})"]
               for name, trigger in sorted(CONDITIONAL_DOC_CATEGORIES.items())],
            [0.35, 0.65])),
    ]
    return _section("Appendix: scoring basis", "".join(body))
