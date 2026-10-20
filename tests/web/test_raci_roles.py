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
"""The RACI roles are the institution's: an Admin list, read by every RACI picker.

A Product's RACI entry stores the role's stable value and a screen shows its label,
so renaming a role in Admin changes every screen and moves nothing on record. What a
new Product is scaffolded with is read off the same list, not out of code.
"""
from __future__ import annotations

from config.governance._raci import DEFAULT_RACI, RACI_ROLE_LIST, VALID_RACI_CODES
from src.governance.reference import (add_option, ensure_default_raci_roles,
                                      get_reference_lists, remove_option,
                                      update_option)
from tests.web.conftest import HEADERS


def _register(client, product_id="Product-0001"):
    return client.post("/api/products", json={
        "product_id": product_id, "product": "Government Bond",
        "fields": {"calculating_agent": "Murex"}, "confirmed": True}, headers=HEADERS)


def _roles():
    return {item["value"]: item for item in get_reference_lists()[RACI_ROLE_LIST]}


def _role_field(client):
    specs = client.get("/api/products/fields").get_json()["collections"]
    raci = next(c for c in specs if c["key"] == "raci_roles")
    return next(f for f in raci["fields"] if f["key"] == "role")


def _raci(client, product_id="Product-0001"):
    return client.get(f"/api/products/{product_id}").get_json()["data"]["raci_roles"]


def test_the_seed_is_the_roles_products_were_scaffolded_with():
    assert ensure_default_raci_roles() == len(DEFAULT_RACI)
    seeded = get_reference_lists()[RACI_ROLE_LIST]
    assert [(i["raci"], i["value"]) for i in seeded] == list(DEFAULT_RACI)
    assert all(i["label"] == i["value"] for i in seeded)
    # Seeds a vacuum only: a curated list is never topped back up.
    assert ensure_default_raci_roles() == 0


def test_the_role_picker_reads_the_admin_list_and_its_labels(client):
    ensure_default_raci_roles()
    add_option(list_name=RACI_ROLE_LIST, actor="admin",
               fields={"label": "Front Office", "value": "Front Office"})
    user = _roles()["Model user"]
    update_option(list_name=RACI_ROLE_LIST, item_id=user["item_id"], actor="admin",
                  fields={"label": "Desk user"})
    field = _role_field(client)
    assert field["type"] == "choice"
    assert "Front Office" in field["options"] and "Model user" in field["options"]
    assert field["option_labels"]["Model user"] == "Desk user"


def test_registration_scaffolds_the_roles_the_list_marks(client):
    ensure_default_raci_roles()
    add_option(list_name=RACI_ROLE_LIST, actor="admin",
               fields={"label": "Front Office", "value": "Front Office",
                       "raci": "Responsible"})
    remove_option(list_name=RACI_ROLE_LIST, item_id=_roles()["Model user"]["item_id"],
                  actor="admin")
    # Offered, but not scaffolded: no accountability marked.
    add_option(list_name=RACI_ROLE_LIST, actor="admin",
               fields={"label": "Quant", "value": "Quant"})
    assert _register(client).status_code == 201
    assert [(r["raci"], r["role"]) for r in _raci(client)] == [
        ("Responsible", "Front Office"), ("Accountable", "Model owner"),
        ("Consulted", "Model Risk Committee"), ("Informed", "Senior management")]


def test_an_unseeded_list_still_scaffolds_all_four(client):
    assert _register(client).status_code == 201
    assert [r["raci"] for r in _raci(client)] == list(VALID_RACI_CODES)


def test_a_role_off_the_list_is_refused_but_a_held_one_keeps_displaying(client):
    assert _register(client).status_code == 201
    ensure_default_raci_roles()
    url = "/api/products/Product-0001/collections/raci_roles"
    refused = client.post(url, json={"fields": {"role": "Nobody defined this",
                                                "raci": "Informed"},
                                     "confirmed": True}, headers=HEADERS)
    assert refused.status_code == 400
    # Removing a role from the list leaves the entries that hold it alone, and they
    # can still be edited.
    remove_option(list_name=RACI_ROLE_LIST, item_id=_roles()["Model owner"]["item_id"],
                  actor="admin")
    held = next(r for r in _raci(client) if r["role"] == "Model owner")
    edited = client.post(f"{url}/{held['item_id']}",
                         json={"fields": {"description": "Signs off the use"},
                               "confirmed": True}, headers=HEADERS)
    assert edited.status_code == 200, edited.get_json()
    held = next(r for r in _raci(client) if r["role"] == "Model owner")
    assert held["description"] == "Signs off the use"
    assert "Model owner" not in _role_field(client)["options"]


def test_the_seed_takes_in_the_roles_the_estate_already_carries(client):
    """Free text before the list existed: each word on record becomes an entry."""
    client.post("/api/models", json={"model_id": "M1", "name": "Alpha", "confirmed": True},
                headers=HEADERS)
    for role in ("Trading Desk", "Model owner", "Trading Desk"):
        added = client.post("/api/models/M1/collections/raci_roles",
                            json={"fields": {"role": role, "raci": "Informed"},
                                  "confirmed": True}, headers=HEADERS)
        assert added.status_code == 201, added.get_json()
    assert ensure_default_raci_roles() == len(DEFAULT_RACI) + 1
    desk = _roles()["Trading Desk"]
    assert desk["label"] == "Trading Desk" and not desk.get("raci")
