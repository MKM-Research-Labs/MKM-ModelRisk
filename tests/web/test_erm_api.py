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
"""Tests for the read-only API an ERM platform calls.

This is a CONTRACT test as much as a behaviour test. An ERM integration is written
against these field names and cannot be redeployed because we renamed something, so
a rename must fail here — loudly, in our suite — rather than in somebody else's
dashboard. The payloads are validated against the schemas checked in under
``contracts/erm/v1``, which is what the integrator actually codes to.
"""
from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest

from config.erm import ERM_API_PREFIX, ERM_DEV_TOKEN, ERM_TOKEN_HEADER
from config.governance import ATTENTION_STATES
from tests.web.conftest import HEADERS

CONTRACTS = pathlib.Path(__file__).resolve().parents[2] / "contracts" / "erm" / "v1"
AUTH = {ERM_TOKEN_HEADER: ERM_DEV_TOKEN}


def _schema(name):
    return json.loads((CONTRACTS / f"{name}.schema.json").read_text())


def _register(client, model_id="M1", name="Alpha", **fields):
    return client.post("/api/models",
                       json={"model_id": model_id, "name": name, "fields": fields,
                             "confirmed": True}, headers=HEADERS)


def _get(client, path="/model-risk", **params):
    response = client.get(ERM_API_PREFIX + path, headers=AUTH, query_string=params)
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


# --- the surface is guarded, and read-only ---------------------------------

@pytest.mark.parametrize("path", ["/model-risk", "/model-risk/attention",
                                  "/model-risk/estate"])
def test_every_endpoint_refuses_an_unauthenticated_caller(client, path):
    assert client.get(ERM_API_PREFIX + path).status_code == 401


def test_a_wrong_token_is_refused_and_named(client):
    response = client.get(ERM_API_PREFIX + "/model-risk",
                          headers={ERM_TOKEN_HEADER: "wrong"})
    assert response.status_code == 401
    # A deployment carries two machine tokens; the error must say which one failed.
    assert "ERM" in response.get_json()["error"]


@pytest.mark.parametrize("verb", ["post", "put", "patch", "delete"])
def test_the_erm_can_never_write(client, verb):
    """If the ERM could change the record, the record would no longer be the thing
    the committee signed."""
    call = getattr(client, verb)
    assert call(ERM_API_PREFIX + "/model-risk", headers=AUTH).status_code == 405


# --- the frozen contract ----------------------------------------------------

def test_the_panel_matches_the_checked_in_schema(client):
    _register(client, tier=1, owner="bob", division="Retail")
    jsonschema.validate(_get(client), _schema("model_risk"))


def test_the_queue_matches_the_checked_in_schema(client):
    _register(client, tier=1, owner="bob", division="Retail")
    jsonschema.validate(_get(client, "/model-risk/attention"), _schema("attention"))


def test_the_checked_in_examples_validate(client):
    """An example that does not validate is worse than none: it gets copied."""
    for name in ("model_risk", "attention"):
        example = json.loads((CONTRACTS / "examples" / f"{name}.example.json").read_text())
        jsonschema.validate(example, _schema(name))


def test_every_response_says_what_it_is_and_when_it_was_made(client):
    """An ERM panel showing a stale figure without saying so is worse than none."""
    for path in ("/model-risk", "/model-risk/attention", "/model-risk/estate"):
        payload = _get(client, path)
        assert payload["schema_version"] == "v1"
        assert payload["as_of"] and payload["generated_at"]


def test_the_machine_vocabulary_is_fixed_and_the_label_travels_beside_it(client):
    _register(client, tier=1, owner="bob")
    for item in _get(client, "/model-risk/attention")["items"]:
        assert item["state"] in ATTENTION_STATES
        assert item["reason"] and item["reason_label"]
        assert item["reason"] != item["reason_label"] or item["reason"].islower()


def test_every_state_is_counted_so_a_tile_cannot_render_blank(client):
    assert set(_get(client)["verdict"]["counts"]) == set(ATTENTION_STATES)


def test_items_come_back_individually_and_say_how_they_would_group(client):
    """The console's rollup is a presentation decision; rolling up inside the
    contract would leave a consumer no way back to the records."""
    _register(client, tier=1, owner="bob")
    payload = _get(client, "/model-risk/attention")
    assert payload["total"] == len(payload["items"])
    assert all("group" in i for i in payload["items"])


def test_truncation_is_declared(client):
    payload = _get(client, "/model-risk/attention")
    assert payload["truncated"] is False
    assert payload["returned"] == payload["total"]


def test_a_row_links_back_to_the_record_it_is_about(client):
    _register(client, tier=1, owner="bob")
    items = _get(client, "/model-risk/attention")["items"]
    model = next(i for i in items if i["entity"]["kind"] == "Model")
    assert model["href"].endswith("/#inventory/M1")


def test_direction_reports_a_count_ratio_and_declares_it_has_no_history(client):
    _register(client, tier=1, owner="bob")
    direction = _get(client)["direction"]
    assert direction["records_audited"] == 1
    assert direction["trend"] is None
    assert (direction["records_meeting_standard"]
            + direction["records_below_standard"]) == direction["records_audited"]


def test_the_operational_feed_names_its_window(client):
    operational = _get(client)["operational"]
    assert operational["window_days"] > 0
    assert operational["failures_in_window"] == 0
