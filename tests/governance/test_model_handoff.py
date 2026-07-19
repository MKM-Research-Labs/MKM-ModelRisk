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
"""The model-handoff aggregate: pure rules and DB-backed command + projection.

A handoff carries the field lineage of a chain edge. It can only be declared on an
edge that actually exists in the derived chain — the cross-aggregate guard — and
its field lineage rides the generic collection machinery.
"""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.model_handoff import (
    add_collection_item,
    declare_handoff,
    get_handoff_for_edge,
    handoff_id,
    list_handoffs,
    rebuild_handoff_view,
    update_handoff_field,
)
from src.governance.model_handoff._rules import (
    decide_add_item,
    decide_declare,
    decide_remove_item,
    decide_update_field,
    decide_update_item,
)
from src.governance.model_handoff._state import EVENT_DECLARED, apply, initial_state
from src.governance.model_handoff.commands import split_handoff_id
from src.governance.model_inventory import (
    add_collection_item as declare_dependency_item,
    rebuild_inventory_view,
    register_model,
)

FL = "field_lineage"


def _edge(from_model, to_model):
    """Register both models and declare the from->to dependency edge."""
    for m in (from_model, to_model):
        register_model(model_id=m, name=m, actor="alice")
    rebuild_inventory_view()
    declare_dependency_item(
        model_id=from_model, collection="dependencies",
        fields={"direction": "downstream", "model_id": to_model}, actor="alice",
    )
    rebuild_inventory_view()


# --- pure ---

def test_decide_declare_sets_endpoints():
    _, payload = decide_declare(initial_state(), from_model="A", to_model="B")
    assert payload["from_model"] == "A" and payload["to_model"] == "B"
    # A fresh handoff carries no MRC sign-off stamp — its status is derived as Draft.
    assert "mrc_signoff_meeting" not in payload


def test_decide_declare_rejects_self_edge():
    with pytest.raises(DomainError):
        decide_declare(initial_state(), from_model="A", to_model="A")


def test_decide_declare_on_existing_raises():
    state = apply(initial_state(), EVENT_DECLARED, {"from_model": "A", "to_model": "B"})
    with pytest.raises(DomainError):
        decide_declare(state, from_model="A", to_model="B")


def test_decide_declare_requires_both_endpoints():
    with pytest.raises(DomainError, match="required"):
        decide_declare(initial_state(), from_model="A", to_model="")


def test_decide_update_field_rejects_non_editable():
    state = apply(initial_state(), EVENT_DECLARED, {"from_model": "A", "to_model": "B"})
    with pytest.raises(DomainError):
        decide_update_field(state, field="from_model", value="X")


def test_collection_decisions_require_an_existing_handoff():
    empty = initial_state()
    with pytest.raises(DomainError, match="does not exist"):
        decide_update_field(empty, field="compatibility", value="x")
    with pytest.raises(DomainError, match="does not exist"):
        decide_add_item(empty, collection="field_lineage", fields={"name": "x"})
    with pytest.raises(DomainError, match="does not exist"):
        decide_update_item(empty, collection="field_lineage", item_id="FL-001", fields={"units": "x"})
    with pytest.raises(DomainError, match="does not exist"):
        decide_remove_item(empty, collection="field_lineage", item_id="FL-001")


def test_apply_ignores_an_unknown_event():
    assert apply(initial_state(), "SomethingElse", {}) == initial_state()


def test_split_handoff_id_round_trips():
    assert split_handoff_id("MKM-PR-001~MKM-DE-001") == ("MKM-PR-001", "MKM-DE-001")


# --- DB-backed ---

def test_declare_on_a_real_edge_then_project():
    _edge("A", "B")
    declare_handoff(from_model="A", to_model="B", actor="alice")
    rebuild_handoff_view()
    doc = get_handoff_for_edge("A", "B")["data"]
    assert doc["from_model"] == "A" and doc["to_model"] == "B"
    assert not doc.get("mrc_signoff_meeting")  # not yet signed off


def test_declare_on_a_missing_edge_is_refused():
    for m in ("A", "B"):
        register_model(model_id=m, name=m, actor="alice")
    rebuild_inventory_view()  # both models exist, but no A->B dependency declared
    with pytest.raises(DomainError, match="no declared dependency"):
        declare_handoff(from_model="A", to_model="B", actor="alice")


def test_declare_with_unknown_consumer_is_refused():
    register_model(model_id="A", name="A", actor="alice")
    rebuild_inventory_view()
    with pytest.raises(DomainError, match="unknown model"):
        declare_handoff(from_model="A", to_model="ghost", actor="alice")


def test_declare_with_unknown_producer_is_refused():
    register_model(model_id="B", name="B", actor="alice")
    rebuild_inventory_view()
    with pytest.raises(DomainError, match="unknown model"):
        declare_handoff(from_model="ghost", to_model="B", actor="alice")


def test_declaring_the_same_edge_twice_is_refused():
    _edge("A", "B")
    declare_handoff(from_model="A", to_model="B", actor="alice")
    with pytest.raises(DomainError, match="already declared"):
        declare_handoff(from_model="A", to_model="B", actor="alice")


def test_field_lineage_and_prose_ride_the_handoff():
    _edge("A", "B")
    declare_handoff(from_model="A", to_model="B", actor="alice")
    hid = handoff_id("A", "B")
    update_handoff_field(handoff_id=hid, field="compatibility", value="units aligned", actor="alice")
    add_collection_item(
        handoff_id=hid, collection=FL,
        fields={"name": "spread", "type": "float", "units": "bps"}, actor="alice",
    )
    rebuild_handoff_view()
    doc = get_handoff_for_edge("A", "B")["data"]
    assert doc["compatibility"] == "units aligned"
    assert doc[FL][0]["name"] == "spread" and doc[FL][0]["item_id"] == "FL-001"


def test_field_lineage_requires_a_field_name():
    _edge("A", "B")
    declare_handoff(from_model="A", to_model="B", actor="alice")
    with pytest.raises(DomainError, match="required"):
        add_collection_item(
            handoff_id=handoff_id("A", "B"), collection=FL,
            fields={"type": "float"}, actor="alice",
        )


def test_list_handoffs_returns_each_declared_edge():
    _edge("A", "B")
    declare_handoff(from_model="A", to_model="B", actor="alice")
    rebuild_handoff_view()
    assert [h["handoff_id"] for h in list_handoffs()] == [handoff_id("A", "B")]


def test_get_handoff_absent_returns_none():
    assert get_handoff_for_edge("A", "B") is None
