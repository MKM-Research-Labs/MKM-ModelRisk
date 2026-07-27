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
"""Tests for the Client aggregate (domain core)."""
from __future__ import annotations

import pytest

from config.governance import (
    CLIENT_CONTACTS,
    CLIENT_DEPARTMENTS,
    CLIENT_DIVISIONS,
    CLIENT_LINKS,
    CLIENT_PACKS,
)
from src.governance.client import (
    add_collection_item,
    get_client,
    list_clients,
    rebuild_client_view,
    record_client_pack,
    register_client,
    remove_collection_item,
    retire_client,
    update_client_field,
    update_collection_item,
)
from src.governance.errors import DomainError


def _register(name="Acme Bank", **fields):
    event = register_client(name=name, actor="admin", fields=fields)
    rebuild_client_view()
    return event.aggregate_id


def test_register_generates_sequential_ids():
    first = _register("Acme Bank")
    second = _register("Globex")
    assert first == "CL-001" and second == "CL-002"
    acme = get_client("CL-001")
    assert acme["data"]["name"] == "Acme Bank"
    assert acme["data"]["status"] == "Active"


def test_register_id_is_log_based_not_view_based():
    # Two registrations without a view rebuild in between still get distinct ids,
    # because the next id is counted from the event log, not the stale view.
    register_client(name="Acme Bank", actor="admin")
    register_client(name="Globex", actor="admin")
    rebuild_client_view()
    assert [c["client_id"] for c in list_clients()] == ["CL-001", "CL-002"]


def test_register_requires_name():
    with pytest.raises(DomainError):
        register_client(name="", actor="admin")


def test_register_rejects_unknown_field():
    with pytest.raises(DomainError):
        register_client(name="Acme", actor="admin", fields={"bogus": "x"})


def test_register_rejects_bad_status_choice():
    with pytest.raises(DomainError):
        register_client(name="Acme", actor="admin", fields={"status": "Nope"})


def test_edit_field():
    _register()
    update_client_field(client_id="CL-001", field="sector", value="Banking", actor="admin")
    update_client_field(client_id="CL-001", field="status", value="Prospect", actor="admin")
    rebuild_client_view()
    data = get_client("CL-001")["data"]
    assert data["sector"] == "Banking" and data["status"] == "Prospect"


def test_edit_rejects_non_editable_and_bad_choice():
    _register()
    with pytest.raises(DomainError):
        update_client_field(client_id="CL-001", field="client_id", value="X", actor="admin")
    with pytest.raises(DomainError):
        update_client_field(client_id="CL-001", field="status", value="Bogus", actor="admin")


def test_edit_unknown_client_rejected():
    with pytest.raises(DomainError):
        update_client_field(client_id="CL-404", field="sector", value="X", actor="admin")


def test_org_tree_and_contacts():
    _register()
    add_collection_item(client_id="CL-001", collection=CLIENT_DIVISIONS,
                        fields={"value": "Risk"}, actor="admin")
    add_collection_item(client_id="CL-001", collection=CLIENT_DEPARTMENTS,
                        fields={"value": "Model Validation", "division": "Risk"}, actor="admin")
    add_collection_item(client_id="CL-001", collection=CLIENT_CONTACTS,
                        fields={"name": "Dana Lee", "email": "dana@acme.test",
                                "role": "Head of MV", "department": "Model Validation"},
                        actor="admin")
    rebuild_client_view()
    data = get_client("CL-001")["data"]
    assert data[CLIENT_DIVISIONS][0]["value"] == "Risk"
    assert data[CLIENT_DEPARTMENTS][0]["item_id"] == "CLDP-001"
    assert data[CLIENT_CONTACTS][0]["name"] == "Dana Lee"


def test_department_requires_a_name():
    _register()
    with pytest.raises(DomainError):
        add_collection_item(client_id="CL-001", collection=CLIENT_DEPARTMENTS,
                            fields={"division": "Risk"}, actor="admin")


def test_links_update_and_remove():
    _register()
    add_collection_item(client_id="CL-001", collection=CLIENT_LINKS,
                        fields={"link_type": "Model", "subject_id": "MKM-EF-001"}, actor="admin")
    update_collection_item(client_id="CL-001", collection=CLIENT_LINKS, item_id="CLL-001",
                           fields={"note": "primary model"}, actor="admin")
    rebuild_client_view()
    link = get_client("CL-001")["data"][CLIENT_LINKS][0]
    assert link["subject_id"] == "MKM-EF-001" and link["note"] == "primary model"
    remove_collection_item(client_id="CL-001", collection=CLIENT_LINKS, item_id="CLL-001",
                           actor="admin")
    rebuild_client_view()
    assert get_client("CL-001")["data"].get(CLIENT_LINKS, []) == []


def test_link_rejects_bad_type():
    _register()
    with pytest.raises(DomainError):
        add_collection_item(client_id="CL-001", collection=CLIENT_LINKS,
                            fields={"link_type": "Widget", "subject_id": "X"}, actor="admin")


def test_record_pack_history_is_bitemporal():
    _register()
    record_client_pack(client_id="CL-001", as_of="2026-07-27",
                       generated_at="2026-07-27T09:30:00", filename="CL-001_pack.zip",
                       original_name="Acme Bank pack.zip", size=2048, actor="admin")
    rebuild_client_view()
    packs = get_client("CL-001")["data"][CLIENT_PACKS]
    assert len(packs) == 1
    assert packs[0]["as_of"] == "2026-07-27"
    assert packs[0]["generated_at"] == "2026-07-27T09:30:00"
    assert packs[0]["size"] == 2048
    assert packs[0]["item_id"] == "CLP-001"


def test_retire_makes_read_only():
    _register()
    retire_client(client_id="CL-001", actor="admin")
    rebuild_client_view()
    client = get_client("CL-001")
    assert client["retired"] and client["data"]["status"] == "Retired"
    with pytest.raises(DomainError):
        update_client_field(client_id="CL-001", field="notes", value="x", actor="admin")
    with pytest.raises(DomainError):
        add_collection_item(client_id="CL-001", collection=CLIENT_DIVISIONS,
                            fields={"value": "Ops"}, actor="admin")
    with pytest.raises(DomainError):
        retire_client(client_id="CL-001", actor="admin")


def test_retire_unknown_client_rejected():
    with pytest.raises(DomainError):
        retire_client(client_id="CL-404", actor="admin")


def test_get_unknown_is_none_and_list_orders():
    assert get_client("CL-404") is None
    _register("Acme Bank")
    _register("Globex")
    assert [c["client_id"] for c in list_clients()] == ["CL-001", "CL-002"]


def test_projection_ignores_unrelated_event():
    from src.database import append_event

    _register()
    append_event(aggregate_type="Client", aggregate_id="CL-001",
                 event_type="Noise", payload={}, actor="system")
    rebuild_client_view()
    assert get_client("CL-001")["data"]["name"] == "Acme Bank"


def test_projection_skips_other_aggregates():
    # An event from another aggregate type sitting in the shared log must not
    # leak into the client view when it is rebuilt.
    from src.database import append_event

    _register()
    append_event(aggregate_type="Product", aggregate_id="Product-0001",
                 event_type="ProductRegistered", payload={"product": "Bond"}, actor="admin")
    rebuild_client_view()
    assert [c["client_id"] for c in list_clients()] == ["CL-001"]


def test_decide_register_rejects_an_already_registered_client():
    # Reachable only below the id-generating command (which always mints a fresh
    # id): the pure rule still guards against a double registration of one stream.
    from src.governance.client._rules import decide_register
    from src.governance.client._state import ClientState

    with pytest.raises(DomainError):
        decide_register(ClientState(exists=True), client_id="CL-001", name="Acme", fields={})
