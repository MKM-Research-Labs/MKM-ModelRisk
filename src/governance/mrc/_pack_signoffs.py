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
"""How a routed sign-off reads in the meeting pack.

Two small readers, split from ``pack.py`` because they answer a different question
from the rest of it: ``pack.py`` is how the document is BUILT, and these are how one
agenda item is INTERPRETED — which requests the committee is answering (as against
its running order), and what each one asks. They mirror the console's Approvals row,
so the pack and the screen describe the same decision.
"""
from __future__ import annotations


# Every field an agenda item can carry a routed subject on — the pack's half of the
# console's SUBJECT_KINDS table. A record type missing here is not merely unnamed: its
# item is counted into the running order and its decision never reaches the sign-offs
# table, which is how ML Application requests went unlisted in both.
SUBJECT_FIELDS = ("subject_model_id", "subject_product_id", "subject_handoff_id",
                  "subject_ml_application_id", "subject_ai_system_id")


def subject_of(item: dict) -> str:
    """The record a routed sign-off is about — empty for an ordinary agenda item,
    which is what separates the running order from the requests the committee is
    answering."""
    return next((item[f] for f in SUBJECT_FIELDS if item.get(f)), "")


def signoff_ask(item: dict) -> str:
    """What the committee was asked to ratify, in one cell.

    A rating names the RAG proposed, a change of owner names who it moves between,
    and a lifecycle decision names itself. Plain ASCII for the arrow — the preamble
    loads ``inputenc`` with utf8, and a literal arrow is a compile risk this document
    should not take on.
    """
    kind = item.get("signoff_kind") or "rag"
    if kind == "owner":
        return (f"{item.get('from_owner') or 'unassigned'} -> "
                f"{item.get('to_owner') or 'unassigned'}")
    if kind in ("retire", "reactivate"):
        return kind.capitalize()
    return item.get("proposed_rag") or ""
