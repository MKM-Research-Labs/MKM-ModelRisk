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
"""Coverage broken down by record type, and the scope statement around it.

A clause met by "90% of the estate" hides which 90%. If every model carries a named
owner and no AI System does, the estate figure reads comfortable and the finding —
that the newest and least understood record type is the one nobody has assigned — is
invisible. So coverage is counted per record type as well as across the estate.

The record type is read from WHICH ID FIELD a row carries, never from a classification
column, because there is no such column and there must not be one.
"""
from __future__ import annotations

from typing import Any

from config.governance._mrm_scope import (GOVERNED_ELSEWHERE, IN_SCOPE_RECORD_TYPES,
                                          NOT_THE_FIRMS, RECORD_TYPE_ID_FIELDS)


def record_type_of(row: dict[str, Any]) -> str | None:
    """Which record type a coverage row is, from the id field it carries."""
    for kind, id_field in RECORD_TYPE_ID_FIELDS.items():
        if row.get(id_field):
            return kind
    return None


def population_by_record_type(records: list[dict[str, Any]]) -> dict[str, int]:
    """How many of each record type the coverage figures were counted over.

    Printed beside every coverage table, because a percentage over an unnamed
    population is not a number an examiner can use.
    """
    counts = {kind: 0 for kind, _, _ in IN_SCOPE_RECORD_TYPES}
    for row in records:
        kind = record_type_of(row)
        if kind in counts:
            counts[kind] += 1
    return counts


def coverage_by_record_type(clause_probe, records: list[dict[str, Any]],
                            estate: dict[str, Any]) -> dict[str, tuple[int, int]]:
    """One clause's (met, total) per record type.

    ``clause_probe`` is called with an estate narrowed to one record type, so the probe
    itself needs no notion of record types — which is what keeps a per-type breakdown
    from becoming a second counting implementation.
    """
    out = {}
    for kind, _, _ in IN_SCOPE_RECORD_TYPES:
        subset = [r for r in records if record_type_of(r) == kind]
        if not subset:
            out[kind] = (0, 0)
            continue
        narrowed = {**estate, "models": subset,
                    "rows": [r for r in estate.get("rows") or []]}
        out[kind] = clause_probe(narrowed)
    return out


def scope_statement() -> dict[str, list[dict[str, str]]]:
    """What is in scope, and what is outside it and why.

    "Out of scope" read without the second half looks like "ungoverned", and the two
    are not the same thing — which is the misreading this exists to prevent.
    """
    def rows(entries):
        return [{"key": key, "label": label, "because": because}
                for key, label, because in entries]

    return {"in_scope": rows(IN_SCOPE_RECORD_TYPES),
            "governed_elsewhere": rows(GOVERNED_ELSEWHERE),
            "not_the_firms": rows(NOT_THE_FIRMS)}


__all__ = ["coverage_by_record_type", "population_by_record_type", "record_type_of",
           "scope_statement"]
