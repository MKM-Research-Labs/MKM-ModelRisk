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
"""Tests for the model-inventory command handlers (against the event store)."""
from __future__ import annotations

import pytest

from src.database import read_stream
from src.governance.model_inventory import (
    AGGREGATE_TYPE,
    DomainError,
    register_model,
    retire_model,
    update_model_field,
)


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
    assert event.stream_seq == 2
    assert event.event_type == "ModelFieldUpdated"
    assert event.actor == "carol"
    assert event.reason == "reassigned"


def test_full_stream_records_lifecycle():
    register_model(model_id="M1", name="Alpha", actor="alice")
    update_model_field(model_id="M1", field="tier", value=1, actor="alice")
    retire_model(model_id="M1", actor="alice", reason="decommissioned")
    stream = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1")
    assert [e.event_type for e in stream] == [
        "ModelRegistered",
        "ModelFieldUpdated",
        "ModelRetired",
    ]


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
    with pytest.raises(DomainError):
        update_model_field(
            model_id="M1", field="rag_rating", value="Purple", actor="alice"
        )
    # Nothing extra was appended.
    stream = read_stream(aggregate_type=AGGREGATE_TYPE, aggregate_id="M1")
    assert len(stream) == 1
