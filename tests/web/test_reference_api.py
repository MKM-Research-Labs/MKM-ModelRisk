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
"""Tests for the reference-data HTTP API and model-field dropdown enrichment."""
from __future__ import annotations

import io

from tests.web.conftest import HEADERS


def _add_committee(client, value="MRC-1", name="Markets MRC", level="Company"):
    res = client.post(
        "/api/reference/collections/mrc",
        json={"fields": {"value": value, "name": name, "level": level}, "confirmed": True},
        headers=HEADERS,
    )
    return res.get_json()["mrc"][0]["item_id"]


def _model_field(client, key):
    specs = client.get("/api/models/fields").get_json()
    return next(f for g in specs["groups"] for f in g["fields"] if f["key"] == key)


def _meeting_field(client, key):
    specs = client.get("/api/meetings/fields").get_json()
    return next(f for f in specs["fields"] if f["key"] == key)


def _add_person(client, name):
    return client.post(
        "/api/reference/collections/people",
        json={"fields": {"name": name}, "confirmed": True}, headers=HEADERS,
    )


def test_get_reference_empty(client):
    res = client.get("/api/reference").get_json()
    assert res["data"] == {"division": [], "department": [],
                           "calculating_agent": [], "mrc": [], "people": []}
    assert [c["key"] for c in res["collections"]] == [
        "division", "department", "mrc", "calculating_agent", "people"]


def test_mrc_tor_fields_are_hidden_in_specs(client):
    # The ToR file metadata is stored on the committee but must not surface as
    # table columns / add-form inputs.
    res = client.get("/api/reference").get_json()
    mrc = next(c for c in res["collections"] if c["key"] == "mrc")
    hidden = {f["key"] for f in mrc["fields"] if f.get("hidden")}
    assert hidden == {"tor_filename", "tor_original_name", "archived",
                      "chair", "secretary", "voting_members", "non_voting_members",
                      "quorum_require_chair", "quorum_require_secretary", "quorum_min_voting"}


def test_mrc_committee_tor_upload_and_download(client):
    item_id = _add_committee(client)
    up = client.post(
        "/api/reference/collections/mrc/" + item_id + "/tor",
        data={"file": (io.BytesIO(b"%PDF-1.4 ToR"), "terms.pdf")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert up.status_code == 201
    item = next(i for i in up.get_json()["mrc"] if i["item_id"] == item_id)
    assert item["tor_original_name"] == "terms.pdf" and item["tor_filename"]

    dl = client.get("/api/reference/collections/mrc/" + item_id + "/tor")
    assert dl.status_code == 200 and dl.data == b"%PDF-1.4 ToR"


def test_mrc_tor_download_missing_is_404(client):
    item_id = _add_committee(client)
    assert client.get("/api/reference/collections/mrc/" + item_id + "/tor").status_code == 404


def test_mrc_tor_upload_unknown_committee_is_404(client):
    res = client.post(
        "/api/reference/collections/mrc/MRC-999/tor",
        data={"file": (io.BytesIO(b"x"), "t.pdf")},
        content_type="multipart/form-data", headers=HEADERS,
    )
    assert res.status_code == 404


def test_update_division_via_api(client):
    client.post("/api/reference/collections/division",
                json={"fields": {"value": "Markets"}, "confirmed": True}, headers=HEADERS)
    res = client.post("/api/reference/collections/division/DV-001",
                      json={"fields": {"value": "Global Markets"}, "confirmed": True}, headers=HEADERS)
    assert res.status_code == 200
    assert res.get_json()["division"][0]["value"] == "Global Markets"


def test_department_division_field_becomes_dropdown(client):
    """Once a division exists, the Department form's Division field is a dropdown."""
    client.post("/api/reference/collections/division",
                json={"fields": {"value": "Markets"}, "confirmed": True}, headers=HEADERS)
    res = client.get("/api/reference").get_json()
    department = next(c for c in res["collections"] if c["key"] == "department")
    division_field = next(f for f in department["fields"] if f["key"] == "division")
    assert division_field["type"] == "choice"
    assert "Markets" in division_field["options"]


def test_add_and_remove_person(client):
    added = _add_person(client, "Jane Doe")
    assert added.status_code == 201
    person = added.get_json()["people"][0]
    assert person["name"] == "Jane Doe"
    removed = client.post(
        "/api/reference/collections/people/" + person["item_id"] + "/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json()["people"] == []


def test_owner_and_mrc_chair_become_people_dropdowns(client):
    """Chair is now a field on the MRC committee (reference list), not on
    individual meetings — a meeting's chair is derived from its bound MRC."""
    assert _model_field(client, "owner")["type"] == "text"
    _add_person(client, "Jane Doe")
    owner = _model_field(client, "owner")
    assert owner["type"] == "choice" and owner["options"] == ["Jane Doe"]
    # MRC reference spec's chair field lights up too.
    ref = client.get("/api/reference").get_json()
    mrc_spec = next(c for c in ref["collections"] if c["key"] == "mrc")
    chair = next(f for f in mrc_spec["fields"] if f["key"] == "chair")
    assert chair["type"] == "choice" and chair["options"] == ["Jane Doe"]


def test_add_and_remove_option(client):
    add = client.post(
        "/api/reference/collections/division",
        json={"fields": {"value": "Markets"}, "confirmed": True}, headers=HEADERS,
    )
    assert add.status_code == 201
    item = add.get_json()["division"][0]
    assert item["value"] == "Markets"

    removed = client.post(
        "/api/reference/collections/division/" + item["item_id"] + "/delete",
        json={"confirmed": True}, headers=HEADERS,
    )
    assert removed.get_json()["division"] == []


def test_add_missing_value_is_400(client):
    response = client.post(
        "/api/reference/collections/division",
        json={"fields": {}, "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_add_unknown_list_is_400(client):
    response = client.post(
        "/api/reference/collections/nope",
        json={"fields": {"value": "x"}, "confirmed": True}, headers=HEADERS,
    )
    assert response.status_code == 400


def test_add_applies_without_confirmation(client):
    # Adding a non-critical reference value is not gated by confirm-to-amend.
    response = client.post(
        "/api/reference/collections/division",
        json={"fields": {"value": "x"}}, headers=HEADERS,
    )
    assert response.status_code == 201
    assert "x" in [d["value"] for d in response.get_json()["division"]]


def test_model_division_field_becomes_dropdown_after_adding(client):
    assert _model_field(client, "division")["type"] == "text"
    client.post(
        "/api/reference/collections/division",
        json={"fields": {"value": "Markets"}, "confirmed": True}, headers=HEADERS,
    )
    enriched = _model_field(client, "division")
    assert enriched["type"] == "choice"
    assert enriched["options"] == ["Markets"]
