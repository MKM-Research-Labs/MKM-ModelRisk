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
"""Unit tests for the pure model-inventory decision logic and state fold."""
from __future__ import annotations

import pytest

from src.governance.model_inventory._rules import (
    DomainError,
    decide_register,
    decide_retire,
    decide_update_field,
)
from src.governance.model_inventory._state import (
    EVENT_FIELD_UPDATED,
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
    assert payload == {"field": "owner", "value": "bob"}


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
    assert payload == {"field": "tier", "value": 3}


def test_choice_field_accepts_valid_value():
    _, payload = decide_update_field(_registered(), field="rag_rating", value="Green")
    assert payload == {"field": "rag_rating", "value": "Green"}


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


def test_apply_ignores_unknown_event_type():
    state = _registered()
    assert apply(state, "SomethingElse", {}) == state


def test_apply_field_update_merges_fields():
    state = apply(_registered(), EVENT_FIELD_UPDATED, {"field": "owner", "value": "x"})
    assert state.fields["owner"] == "x"
    assert state.fields["name"] == "Alpha"
