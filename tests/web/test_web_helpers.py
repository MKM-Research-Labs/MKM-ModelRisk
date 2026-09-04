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
"""The web layer's small shared helpers, at the edges the routes never reach.

Each of these guards a case a route already checks for before it calls: a record
that is not there, a meeting that is gone, an id that does not end in a number.
They are here because the helpers are called from several routes and one of them
will eventually not check — the guard is the point, so it is worth a test.
"""
from __future__ import annotations

from src.command import CommandContext
from src.identity import Principal
from src.web._ml_scope import scoped
from src.web._owner_ratification import pending_owner_request, raise_owner_ratification
from src.web._signoff_routing import _meeting_is_open, _newest


def _ctx():
    return CommandContext(
        principal=Principal(actor="admin", display_name="admin", source="fallback"),
        confirmed=True)


def test_a_record_that_is_not_there_is_not_decorated_with_a_review_scope():
    assert scoped(None) is None


def test_no_ratification_is_raised_for_a_model_nobody_registered():
    """This runs off the back of an ordinary field edit, so a change that cannot be
    routed must not fail the edit that was actually asked for."""
    assert raise_owner_ratification(_ctx(), "NOPE", from_owner="ana",
                                    to_owner="bo") is None


def test_a_sign_off_of_another_kind_is_not_read_as_an_owner_ratification():
    """The queue carries every kind of decision the committee ratifies. Reading a
    RAG sign-off as an owner one would mark a ratified owner as outstanding."""
    data = {"signoff_requests": [{"kind": "rag", "status": "Pending"}]}
    assert pending_owner_request(data) is None


def test_the_newest_request_is_the_one_with_the_highest_generated_suffix():
    items = [{"item_id": "SR-001"}, {"item_id": "SR-003"}, {"item_id": "SR-002"}]
    assert _newest(items)["item_id"] == "SR-003"


def test_an_id_that_does_not_end_in_a_number_sorts_last_rather_than_raising():
    """Ids are generated, so this should not happen — but the log is append-only
    and a hand-written one cannot be taken back out."""
    items = [{"item_id": "SR-hand-written"}, {"item_id": "SR-001"}]
    assert _newest(items)["item_id"] == "SR-001"


def test_there_is_no_newest_request_when_there_are_none():
    assert _newest([]) is None


def test_a_meeting_that_is_not_there_cannot_be_amended():
    assert _meeting_is_open("MRC-9999") is False
