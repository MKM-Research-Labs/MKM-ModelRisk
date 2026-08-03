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
"""Tests for the model-inventory command handlers (against the event store)."""
from __future__ import annotations

import pytest

from src.database import read_stream
from src.governance.model_inventory import (
    AGGREGATE_TYPE,
    DomainError,
    add_collection_item,
    reactivate_model,
    register_model,
    retire_model,
    update_model_field,
)
from src.governance.reference import add_option


def test_register_appends_first_event():
    event = register_model(
        model_id="M1", name="Alpha", actor="alice", fields={"tier": 2}
    )
    assert event.stream_seq == 1
    assert event.event_type == "ModelRegistered"
    assert event.actor == "alice"
    assert event.payload == {"model_id": "M1", "name": "Alpha", "tier": 2}


def test_update_appends_chained_event_with_actor_and_reason():
    register_model(model_id="M1", name="Alpha", actor="alice")
    event = update_model_field(
        model_id="M1", field="owner", value="bob", actor="carol", reason="reassigned"
    )
    assert event.event_type == "ModelFieldUpdated"
    assert event.actor == "carol"
    assert event.reason == "reassigned"


def test_full_stream_records_lifecycle():
    register_model(model_id="M1", name="Alpha", actor="alice")
    update_model_field(model_id="M1", field="tier", value=1, actor="alice")
    retire_model(model_id="M1", actor="alice", reason="decommissioned")
    stream = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1")
    # Registration also seeds nine validation questions; ignore those here.
    non_seed = [e.event_type for e in stream if e.event_type != "CollectionItemAdded"]
    assert non_seed == ["ModelRegistered", "ModelFieldUpdated", "ModelRetired"]


def test_reactivate_appends_event_and_returns_model_to_active():
    register_model(model_id="M-RA", name="Hibernated", actor="alice")
    retire_model(model_id="M-RA", actor="alice")
    event = reactivate_model(model_id="M-RA", actor="alice", reason="Back in use")
    assert event.event_type == "ModelReactivated"
    assert event.reason == "Back in use"
    # The whole lifecycle stays in the log — hibernation is reversible, not a delete.
    types = [e.event_type for e in read_stream(
        aggregate_type=AGGREGATE_TYPE, aggregate_id="M-RA")]
    assert types[-2:] == ["ModelRetired", "ModelReactivated"]
    # Editing works again once it is back.
    update_model_field(model_id="M-RA", field="methodology", value="OLS", actor="alice")


def test_reactivate_a_model_that_is_not_retired_raises():
    register_model(model_id="M-RA2", name="Active", actor="alice")
    with pytest.raises(DomainError):
        reactivate_model(model_id="M-RA2", actor="alice")


def test_register_duplicate_raises():
    register_model(model_id="M1", name="Alpha", actor="alice")
    with pytest.raises(DomainError):
        register_model(model_id="M1", name="Alpha", actor="alice")


def test_update_unknown_model_raises():
    with pytest.raises(DomainError):
        update_model_field(model_id="ghost", field="owner", value="bob", actor="alice")


def test_cannot_edit_retired_model():
    register_model(model_id="M1", name="Alpha", actor="alice")
    retire_model(model_id="M1", actor="alice")
    with pytest.raises(DomainError):
        update_model_field(model_id="M1", field="owner", value="bob", actor="alice")


def test_invalid_value_is_rejected_before_append():
    register_model(model_id="M1", name="Alpha", actor="alice")
    before = len(read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1"))
    with pytest.raises(DomainError):
        update_model_field(
            model_id="M1", field="rag_rating", value="Purple", actor="alice"
        )
    # Nothing extra was appended.
    after = len(read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1"))
    assert after == before


def test_vendor_must_be_a_defined_reference_value():
    # Strict reference: once the Vendor list exists, a model cannot name a value
    # that is not on it (same guard as ``type``).
    add_option(list_name="vendor", fields={"value": "MKM Research Labs"}, actor="admin")
    register_model(model_id="M1", name="Alpha", actor="alice",
                   fields={"vendor": "MKM Research Labs"})
    with pytest.raises(DomainError):
        update_model_field(model_id="M1", field="vendor", value="Acme Corp", actor="alice")


def test_data_source_collection_item_is_strict_referenced():
    # A data_sources item's data_source must be a defined admin value — this is
    # what makes "two models share a source" a match on an id, not on spelling.
    add_option(list_name="data_source", fields={"value": "Bloomberg"}, actor="admin")
    register_model(model_id="M1", name="Alpha", actor="alice")
    add_collection_item(model_id="M1", collection="data_sources",
                        fields={"data_source": "Bloomberg"}, actor="alice")
    with pytest.raises(DomainError):
        add_collection_item(model_id="M1", collection="data_sources",
                            fields={"data_source": "Made Up Feed"}, actor="alice")
