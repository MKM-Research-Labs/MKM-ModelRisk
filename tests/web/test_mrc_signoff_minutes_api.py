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
"""Sign-off approvals auto-create a meeting minute; rejections do not."""
from __future__ import annotations

from tests.web.conftest import HEADERS
from tests.web.test_mrc_signoff_api import (
    _register_subject_model,
    _request_signoff,
    _schedule_meeting,
    _seed_mrc,
    _signoff_item,
)


def _agenda_id(client, meeting_id="MTG1"):
    # The sign-off item, not agenda[0] — every meeting also seeds standing items.
    return _signoff_item(client, meeting_id)["item_id"]


def test_approve_signoff_auto_creates_a_minute(client):
    # Approving a sign-off records the decision as a meeting minute so it lands
    # in the log without re-typing — referencing the model and the review date.
    _seed_mrc(client)
    _register_subject_model(client, owner="Dana Owner")
    _schedule_meeting(client)
    _request_signoff(client)
    resp = client.post(
        f"/api/meetings/MTG1/agenda/{_agenda_id(client)}/approve-signoff",
        json={"confirmed": True, "next_review_date": "2027-01-31"}, headers=HEADERS,
    )
    minutes = resp.get_json()["meeting"]["data"].get("minutes") or []
    assert len(minutes) == 1
    minute = minutes[0]
    assert minute["model_id"] == "M1" and not minute.get("product_id")
    assert "granted approval" in minute["text"]
    assert "2027-01-31" in minute["text"]
    assert "Dana Owner" in minute["text"]


def test_reject_signoff_creates_no_minute(client):
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    _request_signoff(client)
    resp = client.post(
        f"/api/meetings/MTG1/agenda/{_agenda_id(client)}/reject-signoff",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert (resp.get_json()["meeting"]["data"].get("minutes") or []) == []
