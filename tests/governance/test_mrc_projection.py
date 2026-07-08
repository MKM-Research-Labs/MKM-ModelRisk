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
"""Tests for the MRC-meeting read-model projection."""
from __future__ import annotations

from src.database import append_event
from src.governance.mrc import (
    add_collection_item,
    get_meeting,
    list_meetings,
    meeting_items_for_model,
    rebuild_meeting_view,
    schedule_meeting,
    update_meeting_field,
)


def test_rebuild_reflects_meeting_and_collections():
    schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="a")
    update_meeting_field(meeting_id="MTG1", field="status", value="Completed", actor="a")
    add_collection_item(meeting_id="MTG1", collection="agenda",
                        fields={"title": "Review", "presenter": "bob"}, actor="a")
    add_collection_item(meeting_id="MTG1", collection="participants",
                        fields={"name": "Carol", "status": "Attended"}, actor="a")
    assert rebuild_meeting_view() == 1

    meeting = get_meeting("MTG1")
    assert meeting["status"] == "Completed"
    assert meeting["data"]["title"] == "Q2 MRC"
    assert meeting["data"]["agenda"][0]["item_id"] == "AG-001"
    assert meeting["data"]["participants"][0]["name"] == "Carol"


def test_list_meetings_is_ordered():
    schedule_meeting(meeting_id="MTG2", title="B", date="2026-07-01", actor="a")
    schedule_meeting(meeting_id="MTG1", title="A", date="2026-06-30", actor="a")
    rebuild_meeting_view()
    assert [m["meeting_id"] for m in list_meetings()] == ["MTG1", "MTG2"]


def test_get_meeting_returns_none_when_absent():
    rebuild_meeting_view()
    assert get_meeting("missing") is None


def test_rebuild_ignores_other_aggregate_types():
    schedule_meeting(meeting_id="MTG1", title="Q2", date="2026-06-30", actor="a")
    append_event(aggregate_type="SomethingElse", aggregate_id="X",
                 event_type="Noted", payload={}, actor="system")
    assert rebuild_meeting_view() == 1
    assert [m["meeting_id"] for m in list_meetings()] == ["MTG1"]


def test_meeting_items_for_model_finds_linked_decisions_and_actions():
    schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="a")
    add_collection_item(
        meeting_id="MTG1", collection="decisions",
        fields={"description": "Approve recal", "model_id": "MDL-A"}, actor="a",
    )
    add_collection_item(
        meeting_id="MTG1", collection="decisions",
        fields={"description": "General process update"}, actor="a",  # unlinked
    )
    add_collection_item(
        meeting_id="MTG1", collection="actions",
        fields={"description": "Backtest", "model_id": "MDL-A"}, actor="a",
    )
    rebuild_meeting_view()

    decisions = meeting_items_for_model("decisions", "MDL-A")
    assert [d["description"] for d in decisions] == ["Approve recal"]
    assert decisions[0]["meeting_id"] == "MTG1"
    assert decisions[0]["meeting_title"] == "Q2 MRC"

    actions = meeting_items_for_model("actions", "MDL-A")
    assert [a["description"] for a in actions] == ["Backtest"]

    # A model with no linked items returns an empty list (not an error).
    assert meeting_items_for_model("decisions", "MDL-Z") == []


# --- Phase MRC-2: org-scope derivation from the MRC binding -----------------

def test_derive_org_scope_department_resolves_division_from_parent():
    """A department-level MRC resolves department → division."""
    from src.governance.mrc import derive_org_scope
    refs = {
        "mrc": [{"value": "MRC-DEPT", "level": "Department",
                 "scope_value": "Rates Trading", "chair": "Priya", "frequency": "Monthly"}],
        "department": [{"value": "Rates Trading", "division": "Markets"}],
        "division": [{"value": "Markets"}],
    }
    assert derive_org_scope("MRC-DEPT", refs) == {
        "chair": "Priya", "frequency": "Monthly",
        "department": "Rates Trading", "division": "Markets",
    }


def test_derive_org_scope_division_returns_the_division():
    from src.governance.mrc import derive_org_scope
    refs = {
        "mrc": [{"value": "MRC-DIV", "level": "Division", "scope_value": "Markets"}],
        "division": [{"value": "Markets"}],
    }
    assert derive_org_scope("MRC-DIV", refs) == {"division": "Markets"}


def test_derive_org_scope_company_level_returns_only_frequency_and_chair():
    from src.governance.mrc import derive_org_scope
    refs = {"mrc": [{"value": "MRC-CO", "level": "Company", "chair": "David"}]}
    assert derive_org_scope("MRC-CO", refs) == {"chair": "David"}


def test_derive_org_scope_no_binding_returns_empty():
    from src.governance.mrc import derive_org_scope
    assert derive_org_scope(None, {}) == {}
    assert derive_org_scope("MRC-MISSING", {"mrc": []}) == {}


def test_get_meeting_enriched_folds_org_scope_into_data():
    """The enriched read merges the MRC's derived scope onto the meeting."""
    from src.governance.mrc import get_meeting_enriched, schedule_meeting
    from src.governance.reference import add_option
    add_option(list_name="division", fields={"value": "Markets"}, actor="a")
    add_option(list_name="mrc",
               fields={"value": "MRC-DIV", "name": "Markets MRC",
                       "level": "Division", "scope_value": "Markets", "chair": "Priya"},
               actor="a")
    schedule_meeting(meeting_id="MTG1", title="Q1", date="2026-03-15",
                     fields={"mrc": "MRC-DIV"}, actor="a")
    rebuild_meeting_view()
    m = get_meeting_enriched("MTG1")
    assert m["data"]["mrc"] == "MRC-DIV"
    assert m["data"]["division"] == "Markets"
    assert m["data"]["chair"] == "Priya"
