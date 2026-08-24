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
"""Unit tests for structured-collection decision logic and folds (no I/O)."""
from __future__ import annotations

import pytest

from src.governance.model_inventory._rules import (
    DomainError,
    decide_add_item,
    decide_remove_item,
    decide_update_item,
)
from src.governance.model_inventory._state import (
    EVENT_REGISTERED,
    EVENT_RETIRED,
    apply,
    initial_state,
)


def _registered():
    return apply(initial_state(), EVENT_REGISTERED, {"model_id": "M1", "name": "Alpha"})


def _add(state, collection, fields):
    event_type, payload = decide_add_item(state, collection=collection, fields=fields)
    return apply(state, event_type, payload), payload


def test_add_generates_sequential_ids_and_stores_fields():
    state = _registered()
    state, first = _add(state, "assumptions", {"description": "Rates stable"})
    assert first["item_id"] == "AS-001"
    state, second = _add(state, "assumptions", {"description": "Liquidity", "impact": "High"})
    assert second["item_id"] == "AS-002"
    assert state.collections["assumptions"][1]["impact"] == "High"


def test_add_requires_existing_model():
    with pytest.raises(DomainError):
        decide_add_item(initial_state(), collection="assumptions", fields={"description": "x"})


def test_add_rejects_retired_model():
    retired = apply(_registered(), EVENT_RETIRED, {})
    with pytest.raises(DomainError):
        decide_add_item(retired, collection="assumptions", fields={"description": "x"})


def test_add_rejects_unknown_collection():
    with pytest.raises(DomainError):
        decide_add_item(_registered(), collection="nope", fields={"description": "x"})


def test_add_rejects_missing_required_field():
    with pytest.raises(DomainError):
        decide_add_item(_registered(), collection="assumptions", fields={"impact": "High"})


def test_add_rejects_unknown_field():
    with pytest.raises(DomainError):
        decide_add_item(
            _registered(), collection="assumptions",
            fields={"description": "x", "bogus": 1},
        )


def test_add_rejects_invalid_choice():
    """A choice with no reference list: its options ARE the vocabulary."""
    with pytest.raises(DomainError):
        decide_add_item(
            _registered(), collection="review_notes",
            fields={"text": "x", "kind": "Shouting"},
        )


def test_update_item_changes_fields():
    state, _ = _add(_registered(), "validation_questions", {"question": "Is it documented?"})
    event_type, payload = decide_update_item(
        state, collection="validation_questions", item_id="VQ-001",
        fields={"status": "Addressed"},
    )
    state = apply(state, event_type, payload)
    assert state.collections["validation_questions"][0]["status"] == "Addressed"


def test_update_unknown_item_raises():
    state, _ = _add(_registered(), "assumptions", {"description": "x"})
    with pytest.raises(DomainError):
        decide_update_item(state, collection="assumptions", item_id="AS-999", fields={})


def test_update_rejects_invalid_choice():
    """A choice with no reference list is the pure layer's to police: its options are
    the vocabulary, not a seed of one."""
    state, _ = _add(_registered(), "review_notes", {"stage": "scope", "text": "x", "kind": "Note"})
    with pytest.raises(DomainError):
        decide_update_item(
            state, collection="review_notes", item_id="RN-001",
            fields={"kind": "Shouting"},
        )


def test_a_reference_backed_choice_is_left_to_the_admin_list():
    """Its ``options`` are the words that SHIPPED, not the institution's vocabulary.
    Checking them here rejected every value an adopter added in Admin, so membership
    is checked in the command layer against the list as it actually stands."""
    state, _ = _add(_registered(), "assumptions", {"description": "x"})
    decide_update_item(state, collection="assumptions", item_id="AS-001",
                       fields={"impact": "Catastrophic"})


def test_update_requires_editable_model():
    with pytest.raises(DomainError):
        decide_update_item(initial_state(), collection="assumptions", item_id="AS-001", fields={})


def test_remove_item():
    state, _ = _add(_registered(), "assumptions", {"description": "x"})
    event_type, payload = decide_remove_item(state, collection="assumptions", item_id="AS-001")
    state = apply(state, event_type, payload)
    assert state.collections["assumptions"] == ()


def test_remove_unknown_item_raises():
    with pytest.raises(DomainError):
        decide_remove_item(_registered(), collection="assumptions", item_id="AS-001")


def test_update_only_touches_matching_item():
    state, _ = _add(_registered(), "assumptions", {"description": "first"})
    state, _ = _add(state, "assumptions", {"description": "second"})
    event_type, payload = decide_update_item(
        state, collection="assumptions", item_id="AS-002", fields={"impact": "Low"},
    )
    state = apply(state, event_type, payload)
    items = state.collections["assumptions"]
    assert "impact" not in items[0]
    assert items[1]["impact"] == "Low"


def test_next_item_id_follows_the_highest_number_not_the_count():
    """Numbering from the count reissues a live id as soon as one is removed —
    the fold then treats the two items as one (edit or delete hits both)."""
    from src.governance.collections import next_item_id
    assert next_item_id((), "DOC") == "DOC-001"
    # AS-001 removed: three items, but AS-004 is the next free number.
    items = ({"item_id": "AS-002"}, {"item_id": "AS-003"})
    assert next_item_id(items, "AS") == "AS-004"
    # An id that carries no number cannot claim one, and must not stop the scan.
    assert next_item_id(({"item_id": "legacy"},) + items, "AS") == "AS-004"
