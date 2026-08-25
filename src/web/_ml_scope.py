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
"""Decorating an ML Application response with what its division asks of it.

One helper, used by every route that returns a record -- the detail GET, every field
and collection write, the document routes and the sign-off route. A screen that
re-renders from a write's response must see the same scope the detail GET gave it, or
a save silently reverts the tab to the whole catalogue until the next refresh.
"""
from __future__ import annotations

from src.governance.ml_application.review_scope import review_scope, review_status


def scoped(record: dict | None) -> dict | None:
    """Add ``review_scope`` to one record, resolved on read.

    A policy the committee approves this morning applies this afternoon: nothing is
    stored on the record, so there is no view to rebuild and nothing to go stale.
    """
    if record is None:
        return None
    record = dict(record)
    record["review_scope"] = review_scope(record.get("data") or {})
    return record


def scoped_list(records: list) -> list:
    """Add the compact ``review_status`` to every row of an estate listing.

    One cache for the whole listing: resolving the policy walks the catalogue, which
    reads the question register, so doing it per row would turn one listing into one
    register read per record. Each division is paid for once.
    """
    cache: dict = {}
    out = []
    for record in records:
        row = dict(record)
        row["review_status"] = review_status(row.get("data") or {}, cache=cache)
        out.append(row)
    return out
