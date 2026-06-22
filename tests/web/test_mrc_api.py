# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Tests for the MRC-meeting HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def _schedule(client, meeting_id="MTG1"):
    return client.post(
        "/api/meetings",
        json={"meeting_id": meeting_id, "title": "Q2 MRC", "date": "2026-06-30", "confirmed": True},
        headers=HEADERS,
    )


def _post(client, path, body):
    body = dict(body)
    body["confirmed"] = True
    return client.post(path, json=body, headers=HEADERS)


def test_schedule_then_get_and_list(client):
    assert _schedule(client).status_code == 201
    assert [m["meeting_id"] for m in client.get("/api/meetings").get_json()] == ["MTG1"]
    assert client.get("/api/meetings/MTG1").get_json()["status"] == "Scheduled"


def test_get_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none").status_code == 404


def test_full_agenda_decision_action_flow(client):
    _schedule(client)
    _post(client, "/api/meetings/MTG1/field", {"field": "status", "value": "Held"})
    _post(client, "/api/meetings/MTG1/agenda", {"title": "Review", "presenter": "bob"})
    _post(client, "/api/meetings/MTG1/decisions", {"text": "Approved"})
    _post(client, "/api/meetings/MTG1/actions", {"description": "Follow up", "owner": "bob"})
    _post(client, "/api/meetings/MTG1/actions/A-001/status", {"status": "Closed"})

    meeting = client.get("/api/meetings/MTG1").get_json()
    assert meeting["status"] == "Held"
    assert meeting["data"]["agenda"][0]["item_id"] == "AG-001"
    assert meeting["data"]["decisions"][0]["text"] == "Approved"
    assert meeting["data"]["actions"][0]["status"] == "Closed"


def test_schedule_without_confirmation_is_409(client):
    response = client.post(
        "/api/meetings",
        json={"meeting_id": "MTG1", "title": "t", "date": "2026-06-30"},
        headers=HEADERS,
    )
    assert response.status_code == 409


def test_invalid_meeting_status_is_400(client):
    _schedule(client)
    response = _post(client, "/api/meetings/MTG1/field", {"field": "status", "value": "Bogus"})
    assert response.status_code == 400
