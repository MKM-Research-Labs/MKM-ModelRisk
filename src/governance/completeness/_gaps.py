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
"""Finding which fields, collections and documentation categories are absent.

Detection only: what is missing, and how much its absence is worth before any
model-specific escalation. The escalation and banding live in ``_rules``, so the
question "is this a gap?" can be reviewed separately from "how bad is it here?"
-- the two get challenged by different readers.
"""
from __future__ import annotations

from typing import Any

from config.governance import (
    BROKEN_DOC_ESCALATION,
    COLLECTION_ANSWERED,
    COLLECTION_CRITICALITY,
    CONDITIONAL_DOC_CATEGORIES,
    DOC_CATEGORY_SATISFIED_BY,
    DEFAULT_COLLECTION_CRITICALITY,
    DEFAULT_DOC_CRITICALITY,
    DEFAULT_FIELD_CRITICALITY,
    DOC_CRITICALITY,
    EXEMPT_COLLECTIONS,
    EXEMPT_DOC_CATEGORIES,
    EXEMPT_FIELDS,
    FIELD_CRITICALITY,
    PLACEHOLDER_VALUES,
)


def _recorded(value: Any) -> bool:
    """Whether a scalar field holds an answer.

    A recorded "No" is an answer, so a negative does not count as absent:
    treating it as a gap would push owners to leave a field blank rather than
    record an inconvenient truth.

    A placeholder is not an answer. "TBD" reads to a register as filled and to a
    reader as empty, and scoring it as recorded lets a record certify itself
    complete on words that commit to nothing.
    """
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.casefold() not in PLACEHOLDER_VALUES


def _entries(data: dict, name: str) -> list[dict]:
    """A collection's well-formed entries."""
    return [i for i in data.get(name) or [] if isinstance(i, dict)]


def _collection_shortfall(data: dict, name: str) -> tuple[int, int]:
    """``(answered, expected)`` for a collection.

    Most collections are complete once they hold anything at all. Those named in
    ``COLLECTION_ANSWERED`` are seeded on registration, so presence proves
    nothing and only worked entries count.
    """
    entries = _entries(data, name)
    rule = COLLECTION_ANSWERED.get(name)
    if not rule:
        return (1 if entries else 0), 1
    key, accepted = rule
    answered = sum(1 for e in entries if e.get(key) in accepted)
    return answered, max(len(entries), 1)


def _field_gaps(data: dict, specs: dict) -> list[dict]:
    """One gap per unrecorded scalar field."""
    gaps = []
    for key, spec in specs.items():
        if key in EXEMPT_FIELDS or _recorded(data.get(key)):
            continue
        gaps.append({
            "kind": "field", "key": key, "label": spec.get("label", key),
            "group": spec.get("group", ""), "detail": "",
            "criticality": FIELD_CRITICALITY.get(key, DEFAULT_FIELD_CRITICALITY),
        })
    return gaps


def _collection_gaps(data: dict, specs: dict) -> list[dict]:
    """One gap per empty or part-worked collection."""
    gaps = []
    for name, spec in specs.items():
        if name in EXEMPT_COLLECTIONS:
            continue
        answered, expected = _collection_shortfall(data, name)
        if answered >= expected:
            continue
        partial = answered > 0
        gaps.append({
            "kind": "collection", "key": name, "label": spec.get("label", name),
            "group": "Collections",
            "detail": f"{answered} of {expected} recorded" if partial else "none recorded",
            # A part-worked collection is scaled by how much of it is left, so a
            # model with eight of nine validation questions answered does not
            # rank alongside one that has answered none.
            "criticality": (COLLECTION_CRITICALITY.get(name, DEFAULT_COLLECTION_CRITICALITY)
                            * (1 - answered / expected)),
            "partial": partial,
        })
    return gaps


def _held_categories(data: dict, available) -> tuple[set, set]:
    """``(retrievable, cited_only)`` documentation categories.

    ``available`` is a predicate on a document record saying whether its file can
    actually be produced. It is injected rather than looked up here so this
    module stays free of I/O; passing ``None`` trusts the register, which is what
    a unit test wants and what a reader of the register alone would assume.
    """
    retrievable, cited = set(), set()
    for doc in _entries(data, "documents"):
        category = str(doc.get("category") or "")
        if available is None or available(doc):
            retrievable.add(category)
        else:
            cited.add(category)
    return retrievable, cited - retrievable


def _document_gaps(data: dict, categories: tuple, available=None) -> list[dict]:
    """One gap per documentation category that cannot produce a file.

    A category whose only records point at absent files is reported separately
    from one never populated: the register claims that evidence exists, so the
    finding is not merely a hole but a misstatement of coverage.
    """
    retrievable, cited_only = _held_categories(data, available)
    gaps = []
    for category in categories:
        if category in retrievable or category in EXEMPT_DOC_CATEGORIES:
            continue
        # A category covered by a broader pack is closed by that pack: the Test
        # Results document already reports every unit and integration test it
        # would restate.
        covering = DOC_CATEGORY_SATISFIED_BY.get(category)
        if covering and covering in retrievable:
            continue
        trigger = CONDITIONAL_DOC_CATEGORIES.get(category)
        # Evidence categories are only expected once there is something to
        # evidence; a clean model should not collect guaranteed findings.
        if trigger and not _entries(data, trigger):
            continue
        broken = category in cited_only
        criticality = DOC_CRITICALITY.get(category, DEFAULT_DOC_CRITICALITY)
        gaps.append({
            "kind": "document_broken" if broken else "document",
            "key": category, "label": category, "group": "Documentation",
            "detail": "recorded, file absent" if broken else "nothing uploaded",
            "criticality": criticality * (BROKEN_DOC_ESCALATION if broken else 1.0),
        })
    return gaps
