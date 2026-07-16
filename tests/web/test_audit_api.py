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
"""Tests for the audit-trail (event log) HTTP API."""
from __future__ import annotations

from tests.web.conftest import HEADERS


def test_audit_is_empty_initially(client):
    assert client.get("/api/audit").get_json() == []


def test_audit_records_actor_reason_and_newest_first(client):
    client.post(
        "/api/models",
        json={"model_id": "M1", "name": "Alpha", "confirmed": True, "reason": "onboarding"},
        headers=HEADERS,
    )
    client.post(
        "/api/models/M1/field",
        json={"field": "owner", "value": "bob", "confirmed": True, "reason": "assigned"},
        headers={"X-Auth-Request-User": "carol@corp"},
    )
    events = client.get("/api/audit").get_json()
    # Newest first: the field update, then nine seeded questions, then registration.
    assert events[0]["event_type"] == "ModelFieldUpdated"
    assert events[0]["actor"] == "carol@corp"
    assert events[0]["reason"] == "assigned"
    assert events[-1]["event_type"] == "ModelRegistered"
    assert events[-1]["payload"]["name"] == "Alpha"
    assert "T" in events[0]["recorded_at"]
