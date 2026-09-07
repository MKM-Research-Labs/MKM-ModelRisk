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
"""An ML Application and an AI System can name a line of business when registered.

Without one, ``committee_at_levels`` skips the Line of Business level entirely and the
record can only ever route to its DIVISION's committee — a model has carried the field
since the beginning and these two did not, so they were unreachable by a Line of
Business-level MRC however the committees were arranged.

It is offered, not demanded. A division may have no lines of business defined, and a
record genuinely governed at division level has no honest answer to give, so these pin
both halves: naming one routes by it, and omitting it still registers.
"""
from __future__ import annotations

import pytest

from src.web._helpers import resolve_mrc_for_record
from tests.web.conftest import HEADERS

DIV = "PhysicalRisk"
LOB = "PRS Platform"

REGISTERS = pytest.mark.parametrize("url, id_key, new_id, extra", [
    ("/api/ml-applications", "ml_application_id", "MLA-LOB",
     {"name": "Scorer", "owner": "alice", "estimator": "XGBoost", "use_case": "Scoring"}),
    ("/api/ai-systems", "ai_system_id", "AIS-LOB",
     {"name": "Assistant", "owner": "alice", "use_case": "Drafting",
      "deployment_pattern": "Direct prompting"}),
], ids=["ml_application", "ai_system"])


def _org(client):
    """A division with a line of business under it, and a committee at each level."""
    for coll, fields in (
        ("division", {"value": DIV}),
        ("line_of_business", {"value": LOB, "division": DIV}),
        ("mrc", {"value": "MRC-DIV", "name": "Division committee", "level": "Division",
                 "scope_value": DIV}),
        ("mrc", {"value": "MRC-LOB", "name": "LoB committee", "level": "Line of Business",
                 "scope_value": LOB}),
    ):
        client.post(f"/api/reference/collections/{coll}",
                    json={"fields": fields, "confirmed": True}, headers=HEADERS)


@REGISTERS
def test_the_field_is_offered_at_registration_but_not_demanded(client, url, id_key,
                                                               new_id, extra):
    specs = client.get(f"{url}/fields").get_json()
    assert "line_of_business" not in specs["register"], "it must not become mandatory"
    assert specs["register_optional"] == ["line_of_business"]


@REGISTERS
def test_registering_without_one_still_works(client, url, id_key, new_id, extra):
    """A division may have no lines of business, and division-level is a real answer."""
    res = client.post(url, json={id_key: new_id, "fields": {**extra, "division": DIV},
                                 "confirmed": True}, headers=HEADERS)
    assert res.status_code in (200, 201), res.get_json()


@REGISTERS
def test_naming_one_at_registration_routes_to_that_committee(client, url, id_key,
                                                             new_id, extra):
    """The point of the whole change: the closest committee, not the division's."""
    _org(client)
    client.post(url, json={id_key: new_id,
                           "fields": {**extra, "division": DIV, "line_of_business": LOB},
                           "confirmed": True}, headers=HEADERS)
    record = client.get(f"{url}/{new_id}").get_json()
    assert record["data"]["line_of_business"] == LOB
    routed = resolve_mrc_for_record("record", record["data"])
    assert routed["level"] == "Line of Business"
    assert routed["mrc"]["value"] == "MRC-LOB"


@REGISTERS
def test_without_one_it_falls_back_to_the_divisions_committee(client, url, id_key,
                                                              new_id, extra):
    _org(client)
    client.post(url, json={id_key: new_id, "fields": {**extra, "division": DIV},
                           "confirmed": True}, headers=HEADERS)
    record = client.get(f"{url}/{new_id}").get_json()
    routed = resolve_mrc_for_record("record", record["data"])
    assert routed["level"] == "Division"
    assert routed["mrc"]["value"] == "MRC-DIV"
