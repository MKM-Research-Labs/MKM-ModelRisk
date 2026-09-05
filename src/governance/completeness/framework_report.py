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
"""The framework-coverage section of the completeness audit.

One table per framework: every clause, what evidences it, and how much of the
estate carries that evidence. It is the section an external assessor is handed,
and the only place in the report where a clause nothing evidences is named --
the findings register can only report gaps in records that exist, so a capability
the platform has never held is invisible to it by construction.

The clauses reading Not evidenced are listed again, on their own, after the
tables. A reader who works only from a forty-row table reads the rows that are
green; the point of this section is the rows that are not.
"""
from __future__ import annotations

from config.governance import (
    COVERAGE_ABSENT,
    COVERAGE_ABSENT_WEIGHTS,
    COVERAGE_BASIS,
    COVERAGE_CLAUSE_WEIGHTS,
    COVERAGE_EVIDENCED,
    COVERAGE_EVIDENCED_AT,
    COVERAGE_STATES,
    FRAMEWORK_COVERAGE,
    FRAMEWORK_NOTES,
)
from src.governance.completeness.framework import coverage, tally
from src.governance.completeness.scope import (population_by_record_type,
                                               scope_statement)
from src.governance.latex import _para_table, _section, _subsection

TITLE = "Framework coverage"


def _headline(clauses: list[dict]) -> str:
    counts = tally(clauses)
    parts = [f"\\textbf{{{counts.get(state, 0)}}} {state.lower()}"
             for state in COVERAGE_STATES]
    return (f"Clauses assessed: \\textbf{{{counts['clauses']}}} --- "
            + "; ".join(parts) + ".\n\n" + COVERAGE_BASIS + "\n\n"
            + "A clause reads evidenced where at least "
            + f"{COVERAGE_EVIDENCED_AT:.0%}".replace("%", "\\%")
            + " of the applicable records carry the evidence, partially evidenced "
              "where some do, and not evidenced where none do or where the "
              "platform holds no record that could.\n\n")


def _framework_table(framework: str, clauses: list[dict]) -> str:
    scoped = [c for c in clauses if c["framework"] == framework]
    counts = tally(clauses, framework)
    intro = (f"{counts.get(COVERAGE_EVIDENCED, 0)} of {counts['clauses']} clauses "
             f"evidenced by the estate as recorded.\n\n")
    # A framework whose rows are not read the way the shared basis paragraph
    # describes says so here, before its table rather than after it.
    note = FRAMEWORK_NOTES.get(framework)
    if note:
        intro += note + "\n\n"
    table = _para_table(
        ["Ref.", "Clause", "Coverage", "Evidence"],
        [[c["ref"], c["title"], c["state"], c["evidence"]] for c in scoped],
        list(COVERAGE_CLAUSE_WEIGHTS), caption=f"{framework} coverage")
    return _subsection(framework, intro + table)


def _not_evidenced(clauses: list[dict]) -> str:
    """The clauses nothing on the platform can evidence, pulled out of the tables.

    Repetition on purpose. These are the findings of this section, and a reader
    who skims two long tables will not assemble them.
    """
    absent = [c for c in clauses if c["state"] == COVERAGE_ABSENT]
    if not absent:
        return ""
    intro = ("Every clause above that no record on the platform evidences, "
             "gathered so that the gap in the framework is legible without "
             "reading the tables across.\n\n")
    table = _para_table(
        ["Framework", "Ref.", "Clause", "What is missing"],
        [[c["framework"], c["ref"], c["title"], c["evidence"]] for c in absent],
        list(COVERAGE_ABSENT_WEIGHTS), caption="Clauses not evidenced")
    return _subsection("Not evidenced", intro + table)


def _scope(models: list[dict]) -> str:
    """What the coverage figures were counted over, and what sits outside them.

    Printed FIRST, before any clause table. A clause met by 90% of the estate says
    nothing until somebody says what the estate is — and "out of scope" read without
    what is governed elsewhere looks like "ungoverned", which is the misreading this
    paragraph exists to prevent.
    """
    statement = scope_statement()
    counted = population_by_record_type(models)
    in_scope = _para_table(
        ["Record type", "Counted", "Why it is in scope"],
        [[row["label"], str(counted.get(row["key"], 0)), row["because"]]
         for row in statement["in_scope"]],
        [0.18, 0.10, 0.72], caption="In model risk management scope")
    outside = _para_table(
        ["", "Governed how", "Why it is not counted here"],
        [[row["label"], "By the firm, elsewhere", row["because"]]
         for row in statement["governed_elsewhere"]]
        + [[row["label"], "Not the firm's to validate", row["because"]]
           for row in statement["not_the_firms"]],
        [0.18, 0.20, 0.62], caption="Governed outside this report")
    lead = ("The clause figures below are counted over every record in scope, of all "
            "three types. The record type is the filter: there is no separate "
            "classification field, because two answers to what a record is would "
            "differ the first time somebody edited one.\n\n")
    return _subsection("Scope", lead + in_scope + "\n" + outside)


def framework_section(rows: list[dict], models: list[dict], as_of: str,
                      ratified=(), evidence=()) -> str:
    """The coverage section, or nothing at all when no framework is configured.

    ``evidence`` are the documents filed on the FINOS shelf; see ``coverage``.
    """
    if not FRAMEWORK_COVERAGE:
        return ""
    clauses = coverage(rows, models, as_of, ratified, evidence)
    body = [_scope(models), _headline(clauses)]
    body.extend(_framework_table(framework, clauses)
                for framework, _rows in FRAMEWORK_COVERAGE)
    body.append(_not_evidenced(clauses))
    return _section(TITLE, "".join(body))


__all__ = ["framework_section", "TITLE"]
