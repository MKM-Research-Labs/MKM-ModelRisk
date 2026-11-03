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
"""Tests for the record findings API — what a Remediation stage lists, with dates."""
from __future__ import annotations

from src.governance.attention import observe
from tests.web.conftest import HEADERS


def _register(client, model_id="M1"):
    return client.post(
        "/api/models",
        json={"model_id": model_id, "name": "Alpha", "fields": {"tier": 1, "owner": "bob"},
              "confirmed": True},
        headers=HEADERS,
    )


def _findings(client, record="M1", **params):
    response = client.get("/api/findings/" + record, query_string=params)
    assert response.status_code == 200
    return response.get_json()


def test_before_the_first_observation_no_finding_has_a_date(client):
    _register(client)
    payload = _findings(client, as_of="2026-08-25")
    assert payload["observed"] is False
    assert payload["findings"]
    assert {f["status"] for f in payload["findings"]} == {"unobserved"}


def test_findings_are_dated_from_the_day_they_were_first_observed(client):
    _register(client)
    observe(as_of="2026-08-25")
    payload = _findings(client, as_of="2026-11-03")
    assert payload["observed"] is True and payload["entity_id"] == "M1"
    assert {f["first_seen"] for f in payload["findings"]} == {"2026-08-25"}
    for f in payload["findings"]:
        assert f["due"] and f["status"] in ("overdue", "due_soon", "open")


def test_a_record_that_does_not_exist_has_nothing_open(client):
    assert _findings(client, "NOPE")["findings"] == []


def test_the_findings_are_read_only(client):
    for verb in (client.post, client.put, client.delete, client.patch):
        assert verb("/api/findings/M1", headers=HEADERS).status_code == 405
