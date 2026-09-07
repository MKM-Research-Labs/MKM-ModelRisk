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
"""Tests for the admin-managed reference (menu) lists."""
from __future__ import annotations

import pytest

from config.governance import (DEFAULT_DATA_SOURCES, DEFAULT_MODEL_TYPES,
                               DEFAULT_VENDORS, ML_TRAINING_VOCABULARIES,
                               MODEL_TYPE_LIST, REFERENCE_LISTS)

from src.governance.errors import DomainError
from src.governance.reference import (add_option, ensure_default_ml_training_vocabularies,
                                      ensure_default_model_types,
                                      ensure_default_reference_lists,
                                      get_reference_lists, model_type_roles,
                                      move_option, remove_option,
                                      update_option)


def test_update_option_edits_fields():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    update_option(list_name="division", item_id="DV-001",
                  fields={"value": "Global Markets"}, actor="admin")
    division = get_reference_lists()["division"][0]
    assert division["value"] == "Global Markets"


def test_lists_empty_initially():
    """Every reference list exists and is empty before anything is seeded. Derived
    from the config rather than copied into the test, so adding a list does not
    mean editing an assertion that says nothing about behaviour."""
    assert get_reference_lists() == {name: [] for name in REFERENCE_LISTS}


def test_add_menu_value_generates_id_and_appears():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    lists = get_reference_lists()
    assert lists["division"][0]["item_id"] == "DV-001"
    assert lists["division"][0]["value"] == "Markets"


def test_add_person_record():
    add_option(
        list_name="people",
        fields={"name": "Jane Doe", "email": "jane@firm",
                "division": "Markets", "line_of_business": "Rates"},
        actor="admin",
    )
    person = get_reference_lists()["people"][0]
    assert person["item_id"] == "PE-001"
    assert person["name"] == "Jane Doe"
    assert person["division"] == "Markets"
    assert person["line_of_business"] == "Rates"


def test_add_multiple_options_increment_ids():
    add_option(list_name="division", fields={"value": "Group Risk"}, actor="admin")
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    ids = [item["item_id"] for item in get_reference_lists()["division"]]
    assert ids == ["DV-001", "DV-002"]


def test_add_calculating_agent():
    add_option(list_name="calculating_agent", fields={"value": "Murex"}, actor="admin")
    agent = get_reference_lists()["calculating_agent"][0]
    assert agent["item_id"] == "CA-001" and agent["value"] == "Murex"


def test_ensure_default_reference_lists_seeds_and_is_idempotent():
    added = ensure_default_reference_lists()
    lists = get_reference_lists()
    # The catalogue itself is asserted in test_data_sources.py; what matters here is
    # that the seed lays it down whole and in order, carrying the fields it defines.
    assert [o["value"] for o in lists["data_source"]] == \
        [entry["value"] for entry in DEFAULT_DATA_SOURCES]
    assert lists["data_source"][0]["kind"] == DEFAULT_DATA_SOURCES[0]["kind"]
    # The vendor seed names no institution — a fresh install must not plant the
    # platform's author in an adopter's inventory. Bare values, unlike data sources:
    # the same loop seeds both, and it takes either shape.
    assert [o["value"] for o in lists["vendor"]] == ["In-house", "Other"]
    assert added == len(DEFAULT_DATA_SOURCES) + len(DEFAULT_VENDORS)
    # Seeds a vacuum only — a second run adds nothing and never repopulates a
    # list an adopter has since curated.
    assert ensure_default_reference_lists() == 0


def test_remove_option():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    remove_option(list_name="division", item_id="DV-001", actor="admin")
    assert get_reference_lists()["division"] == []


def test_add_requires_required_field():
    with pytest.raises(DomainError):
        add_option(list_name="people", fields={"email": "x@y"}, actor="admin")


def test_add_unknown_list_raises():
    with pytest.raises(DomainError):
        add_option(list_name="nope", fields={"value": "x"}, actor="admin")


def test_remove_unknown_item_raises():
    with pytest.raises(DomainError):
        remove_option(list_name="division", item_id="DV-999", actor="admin")


def test_the_model_type_seed_never_repopulates_a_curated_list():
    """Seeds a vacuum only. An adopter who has pruned the shipped types back to
    the three they use must not find them all back after a restart."""
    assert ensure_default_model_types() == len(DEFAULT_MODEL_TYPES)
    assert ensure_default_model_types() == 0


def test_the_training_vocabularies_are_seeded_one_list_at_a_time():
    """Each vocabulary is its own vacuum: adding a new one in a later release must
    reach an estate that already curated the others."""
    ensure_default_ml_training_vocabularies()
    first = next(iter(ML_TRAINING_VOCABULARIES))
    seeded = get_reference_lists()[first]
    remove_option(list_name=first, item_id=seeded[0]["item_id"], actor="admin")

    ensure_default_ml_training_vocabularies()
    assert len(get_reference_lists()[first]) == len(seeded) - 1, \
        "a list an adopter has curated is left alone"


def test_what_a_model_type_means_to_a_product_is_read_not_inferred():
    """Callers ask what a type IS rather than comparing its name, so renaming a
    type in Admin cannot change how the estate binds."""
    add_option(list_name=MODEL_TYPE_LIST,
               fields={"value": "Curve Model", "binding_role": "Market Data"},
               actor="admin")
    add_option(list_name=MODEL_TYPE_LIST,
               fields={"value": "Pricing Engine", "binding_role": "Neither"},
               actor="admin")
    assert model_type_roles() == {"Curve Model": "Market Data",
                                  "Pricing Engine": "Neither"}


# --- Reordering a list --------------------------------------------------------
#
# Order is meaningful: the review questionnaire is asked in the order it is listed,
# and that is the order every dropdown offers. The move path had no test of its
# refusals, so nothing checked that an impossible move said so rather than silently
# doing nothing.

def _two_divisions():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    add_option(list_name="division", fields={"value": "Retail"}, actor="admin")
    return [o["item_id"] for o in get_reference_lists()["division"]]


def test_an_option_moves_up_the_list():
    first, second = _two_divisions()
    move_option(list_name="division", item_id=second, direction="up", actor="admin")
    assert [o["item_id"] for o in get_reference_lists()["division"]] == [second, first]


def test_moving_an_item_that_is_not_in_the_list_is_refused():
    _two_divisions()
    with pytest.raises(DomainError, match="unknown item"):
        move_option(list_name="division", item_id="DV-999", direction="up",
                    actor="admin")


def test_moving_the_first_item_up_says_it_is_already_first():
    """Refused with the reason rather than silently doing nothing — a reorder that
    appears to work and does not is how a questionnaire ends up in an order nobody
    chose."""
    first, _second = _two_divisions()
    with pytest.raises(DomainError, match="already first"):
        move_option(list_name="division", item_id=first, direction="up", actor="admin")


def test_moving_the_last_item_down_says_it_is_already_last():
    _first, second = _two_divisions()
    with pytest.raises(DomainError, match="already last"):
        move_option(list_name="division", item_id=second, direction="down",
                    actor="admin")


def test_a_direction_that_is_not_up_or_down_is_refused():
    first, _second = _two_divisions()
    with pytest.raises(DomainError, match="direction must be one of"):
        move_option(list_name="division", item_id=first, direction="sideways",
                    actor="admin")

