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
"""Tests for the MRC-meeting read-model projection."""
from __future__ import annotations

from src.database import append_event
from src.governance.mrc import (
    add_collection_item,
    get_meeting,
    list_meetings,
    meeting_items_for_model,
    outstanding_actions_for_committee,
    rebuild_meeting_view,
    schedule_meeting,
    update_collection_item,
    update_meeting_field,
)


def test_rebuild_reflects_meeting_and_collections():
    schedule_meeting(meeting_id="MTG1", title="Q2 MRC", date="2026-06-30", actor="a")
    add_collection_item(meeting_id="MTG1", collection="agenda",
                        fields={"title": "Review", "presenter": "bob"}, actor="a")
    add_collection_item(meeting_id="MTG1", collection="participants",
                        fields={"name": "Carol", "status": "Attended"}, actor="a")
    # Closed last: a sealed meeting accepts no further collection items.
    update_meeting_field(meeting_id="MTG1", field="status", value="Completed", actor="a")
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

def test_derive_org_scope_line_of_business_resolves_division_from_parent():
    """A line_of_business-level MRC resolves line_of_business → division."""
    from src.governance.mrc import derive_org_scope
    refs = {
        "mrc": [{"value": "MRC-DEPT", "level": "Line of Business",
                 "scope_value": "Rates Trading", "chair": "Priya", "frequency": "Monthly"}],
        "line_of_business": [{"value": "Rates Trading", "division": "Markets"}],
        "division": [{"value": "Markets"}],
    }
    assert derive_org_scope("MRC-DEPT", refs) == {
        "chair": "Priya", "frequency": "Monthly",
        "line_of_business": "Rates Trading", "division": "Markets",
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


def test_outstanding_actions_span_one_committee_only():
    """An action belongs to the committee that agreed it, not to every meeting."""
    schedule_meeting(meeting_id="A1", title="Alpha Q1", date="2026-01-05",
                     fields={"mrc": "MRC-A"}, actor="a")
    schedule_meeting(meeting_id="A2", title="Alpha Q2", date="2026-04-05",
                     fields={"mrc": "MRC-A"}, actor="a")
    schedule_meeting(meeting_id="B1", title="Beta Q1", date="2026-02-05",
                     fields={"mrc": "MRC-B"}, actor="a")
    add_collection_item(meeting_id="A1", collection="actions",
                        fields={"description": "Owed to Alpha"}, actor="a")
    add_collection_item(meeting_id="B1", collection="actions",
                        fields={"description": "Owed to Beta"}, actor="a")
    # Closed via the ratification path, the only writer of that status, and then
    # absent from the register — that is what "outstanding" means.
    add_collection_item(meeting_id="A1", collection="actions",
                        fields={"description": "Already done"}, actor="a")
    update_collection_item(meeting_id="A1", collection="actions", item_id="A-002",
                           fields={"status": "Closed"}, actor="a", ratifying=True)
    rebuild_meeting_view()

    rows = outstanding_actions_for_committee("A2")
    assert [r["description"] for r in rows] == ["Owed to Alpha"]
    assert rows[0]["meeting_id"] == "A1" and rows[0]["meeting_date"] == "2026-01-05"


def test_outstanding_actions_of_an_unassigned_meeting_stand_alone():
    """A meeting with no committee must not adopt every other unassigned meeting's
    actions — the join is on the committee, and a blank is not a committee."""
    schedule_meeting(meeting_id="L1", title="Loose one", date="2026-01-05", actor="a")
    schedule_meeting(meeting_id="L2", title="Loose two", date="2026-02-05", actor="a")
    add_collection_item(meeting_id="L1", collection="actions",
                        fields={"description": "Owed on L1"}, actor="a")
    rebuild_meeting_view()

    assert outstanding_actions_for_committee("L2") == []
    assert [r["description"] for r in outstanding_actions_for_committee("L1")] == ["Owed on L1"]


def test_outstanding_actions_of_an_unknown_meeting_is_empty():
    assert outstanding_actions_for_committee("nope") == []


def _standing(kind, title=None):
    return {"kind": kind, "title": title or kind}


def test_agenda_runs_standing_items_in_template_order():
    """A standing item backfilled onto a meeting already on the record is appended,
    and must still run where the committee's agenda puts it."""
    from src.governance.mrc.projection import _ordered_agenda
    agenda = [_standing("rollcall"), _standing("minutes_signoff"), _standing("aob"),
              _standing("actions_review")]
    refs = {"standing_agenda": [_standing("rollcall"), _standing("minutes_signoff"),
                                _standing("actions_review"), _standing("aob")]}
    assert [i["kind"] for i in _ordered_agenda(agenda, refs)] == [
        "rollcall", "minutes_signoff", "actions_review", "aob"]


def test_non_standing_business_runs_before_the_closing_item():
    """Business raised after a meeting was seeded must not end up after the chair has
    closed it — whatever order it was added in."""
    from src.governance.mrc.projection import _ordered_agenda
    review = {"title": "Event review — PRD-1", "subject_product_id": "PRD-1"}
    adhoc = {"title": "Raised from the floor"}
    # AOB seeded before either was added, so insertion order alone would run it early.
    agenda = [_standing("rollcall"), _standing("aob"), review, adhoc,
              _standing("minutes_signoff")]
    refs = {"standing_agenda": [_standing("rollcall"), _standing("minutes_signoff"),
                                _standing("aob")]}
    ordered = _ordered_agenda(agenda, refs)
    assert [i.get("kind") or i["title"] for i in ordered] == [
        "rollcall", "minutes_signoff", "Event review — PRD-1", "Raised from the floor",
        "aob"]


def test_non_standing_business_keeps_the_order_it_was_raised_in():
    from src.governance.mrc.projection import _ordered_agenda
    first = {"title": "First raised"}
    second = {"title": "Second raised"}
    ordered = _ordered_agenda([_standing("aob"), first, second, _standing("rollcall")],
                              {"standing_agenda": [_standing("rollcall"), _standing("aob")]})
    assert [i.get("kind") or i["title"] for i in ordered] == [
        "rollcall", "First raised", "Second raised", "aob"]


def test_agenda_ordering_falls_back_to_the_shipped_order():
    """A database with no curated agenda list still runs the shipped order."""
    from src.governance.mrc.projection import _ordered_agenda
    agenda = [_standing("aob"), _standing("rollcall")]
    assert [i["kind"] for i in _ordered_agenda(agenda, {})] == ["rollcall", "aob"]


def test_a_lone_standing_item_is_left_where_it_is():
    """Nothing to put it in order against, so nothing moves."""
    from src.governance.mrc.projection import _ordered_agenda
    agenda = [{"title": "Ad hoc"}, _standing("rollcall")]
    assert _ordered_agenda(agenda, {}) == agenda


def test_an_item_a_committee_curated_without_a_kind_keeps_its_place():
    """A committee may put its own item first in its running order. It looks exactly
    like an item raised from the floor here, so neither may be reordered."""
    from src.governance.mrc.projection import _ordered_agenda
    curated = {"title": "Regulatory horizon"}
    agenda = [curated, _standing("rollcall"), _standing("minutes_signoff")]
    refs = {"standing_agenda": [curated, _standing("rollcall"), _standing("minutes_signoff")]}
    assert [i.get("kind") or i["title"] for i in _ordered_agenda(agenda, refs)] == [
        "Regulatory horizon", "rollcall", "minutes_signoff"]
