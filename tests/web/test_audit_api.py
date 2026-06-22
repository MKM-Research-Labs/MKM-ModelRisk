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
    assert [e["event_type"] for e in events] == ["ModelFieldUpdated", "ModelRegistered"]
    assert events[0]["actor"] == "carol@corp"
    assert events[0]["reason"] == "assigned"
    assert events[1]["payload"]["name"] == "Alpha"
    assert "T" in events[0]["recorded_at"]
