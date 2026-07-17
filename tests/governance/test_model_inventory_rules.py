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
"""Unit tests for the pure model-inventory decision logic and state fold."""
from __future__ import annotations

import pytest

from config.governance import SIGNOFF_REQUESTS_COLLECTION
from src.governance.model_inventory._rules import (
    DomainError,
    decide_add_item,
    decide_update_item,
    decide_reactivate,
    decide_register,
    decide_retire,
    decide_update_field,
)
from src.governance.model_inventory._state import (
    EVENT_FIELD_UPDATED,
    EVENT_REACTIVATED,
    EVENT_REGISTERED,
    EVENT_RETIRED,
    apply,
    initial_state,
)


def _registered():
    event_type, payload = decide_register(
        initial_state(), model_id="M1", name="Alpha", fields={}
    )
    return apply(initial_state(), event_type, payload)


def test_register_emits_event_with_identity():
    event_type, payload = decide_register(
        initial_state(), model_id="M1", name="Alpha", fields={"tier": 2}
    )
    assert event_type == EVENT_REGISTERED
    assert payload == {"model_id": "M1", "name": "Alpha", "tier": 2}


def test_register_rejects_duplicate():
    with pytest.raises(DomainError):
        decide_register(_registered(), model_id="M1", name="Alpha", fields={})


def test_register_requires_model_id_and_name():
    with pytest.raises(DomainError):
        decide_register(initial_state(), model_id="", name="Alpha", fields={})
    with pytest.raises(DomainError):
        decide_register(initial_state(), model_id="M1", name="", fields={})


def test_register_rejects_unknown_field():
    with pytest.raises(DomainError):
        decide_register(
            initial_state(), model_id="M1", name="Alpha", fields={"bogus": 1}
        )


def test_register_validates_field_values():
    with pytest.raises(DomainError):
        decide_register(
            initial_state(), model_id="M1", name="Alpha",
            fields={"rag_rating": "Purple"},
        )


# The require_company gate has been retired (Phase MRC-5): the instance is
# always a single institution, so ``company`` is no longer a per-model field.


def test_update_field_emits_event():
    event_type, payload = decide_update_field(
        _registered(), field="owner", value="bob"
    )
    assert event_type == EVENT_FIELD_UPDATED
    # The prior value is captured for the audit trail (None here — freshly
    # registered, owner unset).
    assert payload == {"field": "owner", "value": "bob", "from": None}


def test_update_field_requires_existing_model():
    with pytest.raises(DomainError):
        decide_update_field(initial_state(), field="owner", value="bob")


def test_update_field_rejects_retired_model():
    state = apply(_registered(), EVENT_RETIRED, {})
    with pytest.raises(DomainError):
        decide_update_field(state, field="owner", value="bob")


def test_update_field_rejects_non_editable_field():
    with pytest.raises(DomainError):
        decide_update_field(_registered(), field="model_id", value="X")


@pytest.mark.parametrize("value", [0, 6, "3", True])
def test_tier_validation_rejects_bad_values(value):
    with pytest.raises(DomainError):
        decide_update_field(_registered(), field="tier", value=value)


def test_tier_validation_accepts_valid_value():
    event_type, payload = decide_update_field(_registered(), field="tier", value=3)
    assert payload == {"field": "tier", "value": 3, "from": None}


def test_choice_field_accepts_valid_value():
    _, payload = decide_update_field(_registered(), field="rag_rating", value="Green")
    assert payload == {"field": "rag_rating", "value": "Green", "from": None}


def test_free_text_field_skips_choice_validation():
    # 'description' is editable but not constrained to a choice set.
    _, payload = decide_update_field(
        _registered(), field="description", value="anything goes"
    )
    assert payload["value"] == "anything goes"


def test_retire_emits_event():
    event_type, payload = decide_retire(_registered())
    assert event_type == EVENT_RETIRED
    assert payload == {}


def test_retire_requires_existing_model():
    with pytest.raises(DomainError):
        decide_retire(initial_state())


def test_retire_rejects_already_retired():
    state = apply(_registered(), EVENT_RETIRED, {})
    with pytest.raises(DomainError):
        decide_retire(state)


# Retirement is hibernation, so it reverses: the committee can bring a model back.


def test_reactivate_emits_event():
    state = apply(_registered(), EVENT_RETIRED, {})
    event_type, payload = decide_reactivate(state)
    assert event_type == EVENT_REACTIVATED
    assert payload == {}


def test_reactivate_returns_model_to_the_active_inventory():
    state = apply(_registered(), EVENT_RETIRED, {})
    assert apply(state, EVENT_REACTIVATED, {}).retired is False


def test_reactivate_requires_existing_model():
    with pytest.raises(DomainError):
        decide_reactivate(initial_state())


def test_reactivate_rejects_a_model_that_is_not_retired():
    with pytest.raises(DomainError):
        decide_reactivate(_registered())


def test_apply_ignores_unknown_event_type():
    state = _registered()
    assert apply(state, "SomethingElse", {}) == state


def test_apply_field_update_merges_fields():
    state = apply(_registered(), EVENT_FIELD_UPDATED, {"field": "owner", "value": "x"})
    assert state.fields["owner"] == "x"
    assert state.fields["name"] == "Alpha"


# The sign-off queue is exempt from the hibernated read-only rule, but it must
# still refuse a model that was never registered.


def test_signoff_queue_exemption_still_requires_the_model_to_exist():
    with pytest.raises(DomainError):
        decide_add_item(initial_state(), collection=SIGNOFF_REQUESTS_COLLECTION,
                        fields={"kind": "reactivate", "target_mrc": "MRC-CO"})
    with pytest.raises(DomainError):
        decide_update_item(initial_state(), collection=SIGNOFF_REQUESTS_COLLECTION,
                           item_id="SR-001", fields={"status": "Attached"})


def test_a_hibernated_model_accepts_signoff_items_but_nothing_else():
    retired = apply(_registered(), EVENT_RETIRED, {})
    # The committee's queue still works on it — the only way back.
    decide_add_item(retired, collection=SIGNOFF_REQUESTS_COLLECTION,
                    fields={"kind": "reactivate", "target_mrc": "MRC-CO"})
    # Everything else stays read-only.
    with pytest.raises(DomainError):
        decide_add_item(retired, collection="limitations", fields={"description": "x"})
