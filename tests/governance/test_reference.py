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
"""Tests for the admin-managed reference (menu) lists."""
from __future__ import annotations

import pytest

from src.governance.errors import DomainError
from src.governance.reference import add_option, get_reference_lists, remove_option, update_option


def test_update_option_edits_fields():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    update_option(list_name="division", item_id="DV-001",
                  fields={"value": "Global Markets"}, actor="admin")
    division = get_reference_lists()["division"][0]
    assert division["value"] == "Global Markets"


def test_lists_empty_initially():
    assert get_reference_lists() == {
        "people": [], "division": [], "department": [],
        "calculating_agent": [], "mrc": [],
    }


def test_add_menu_value_generates_id_and_appears():
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    lists = get_reference_lists()
    assert lists["division"][0]["item_id"] == "DV-001"
    assert lists["division"][0]["value"] == "Markets"


def test_add_person_record():
    add_option(
        list_name="people",
        fields={"name": "Jane Doe", "email": "jane@firm", "role": "Owner"},
        actor="admin",
    )
    person = get_reference_lists()["people"][0]
    assert person["item_id"] == "PE-001"
    assert person["name"] == "Jane Doe"
    assert person["role"] == "Owner"


def test_add_multiple_options_increment_ids():
    add_option(list_name="division", fields={"value": "Group Risk"}, actor="admin")
    add_option(list_name="division", fields={"value": "Markets"}, actor="admin")
    ids = [item["item_id"] for item in get_reference_lists()["division"]]
    assert ids == ["DV-001", "DV-002"]


def test_add_calculating_agent():
    add_option(list_name="calculating_agent", fields={"value": "Murex"}, actor="admin")
    agent = get_reference_lists()["calculating_agent"][0]
    assert agent["item_id"] == "CA-001" and agent["value"] == "Murex"


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
