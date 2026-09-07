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
"""Filing an existing estate under functional groups, without inventing anybody's filing.

This backfill is the one that derives nothing, so what has to hold is the opposite of
the usual: that it does exactly what the mapping says and NOTHING else. Three ways it
could quietly do more — overturning a filing somebody made on the screen, accepting a
group the division never ratified, or writing twice on a re-run — are what these pin.
"""
from __future__ import annotations

from scripts.backfill_functional_groups import backfill, load_mapping, plan
from src.governance.functional_groups import (approve_functional_groups,
                                              propose_functional_groups)
from src.governance.model_inventory import (get_model, list_models, register_model,
                                            rebuild_inventory_view)
from src.governance.product import (register_product, rebuild_product_view)

DIV = "PhysicalRisk"
OTHER = "Analytics"


def _ratify(groups, division=DIV):
    propose_functional_groups(division=division, groups=groups, actor="admin")
    approve_functional_groups(division=division, actor="chair")


def _model(model_id, division=DIV):
    register_model(model_id=model_id, name=model_id, actor="admin",
                   fields={"division": division})
    rebuild_inventory_view()


def _filed(model_id):
    return ((get_model(model_id) or {}).get("data") or {}).get("functional_group")


def _verdicts(rows):
    return {r["id"]: r["verdict"] for r in rows}


# --- It does what the mapping says -------------------------------------------

def test_a_mapping_files_records_by_group_name():
    _ratify([{"name": "Storm Generation"}, {"name": "Flood Simulation"}])
    _model("M1"); _model("M2")
    backfill([("M1", "Storm Generation"), ("M2", "Flood Simulation")],
             actor="admin", apply=True)
    assert _filed("M1") == "FG-001"
    assert _filed("M2") == "FG-002"


def test_a_group_can_be_named_by_its_id_or_case_insensitively():
    _ratify([{"name": "Storm Generation"}])
    _model("M1"); _model("M2")
    backfill([("M1", "FG-001"), ("M2", "sTorM gEnErAtIoN")], actor="admin", apply=True)
    assert _filed("M1") == _filed("M2") == "FG-001"


def test_a_dry_run_writes_nothing():
    _ratify([{"name": "Storm Generation"}])
    _model("M1")
    rows = backfill([("M1", "Storm Generation")], actor="admin", apply=False)
    assert _verdicts(rows) == {"M1": "file"}
    assert _filed("M1") is None, "a dry run that writes is not a dry run"


def test_re_running_writes_nothing_because_it_is_already_filed():
    _ratify([{"name": "Storm Generation"}])
    _model("M1")
    mapping = [("M1", "Storm Generation")]
    backfill(mapping, actor="admin", apply=True)
    again = backfill(mapping, actor="admin", apply=True)
    assert _verdicts(again) == {"M1": "already"}


# --- And nothing else ---------------------------------------------------------

def test_a_record_somebody_already_filed_elsewhere_is_left_alone():
    """The decision on the screen outranks the mapping: a backfill that overturned it
    would move records nobody asked it to touch."""
    _ratify([{"name": "Storm Generation"}, {"name": "Flood Simulation"}])
    _model("M1")
    backfill([("M1", "Storm Generation")], actor="admin", apply=True)
    rows = backfill([("M1", "Flood Simulation")], actor="admin", apply=True)
    assert _verdicts(rows) == {"M1": "filed-elsewhere"}
    assert _filed("M1") == "FG-001"


def test_refile_is_what_moves_one_and_it_has_to_be_asked_for():
    _ratify([{"name": "Storm Generation"}, {"name": "Flood Simulation"}])
    _model("M1")
    backfill([("M1", "Storm Generation")], actor="admin", apply=True)
    backfill([("M1", "Flood Simulation")], actor="admin", apply=True, refile=True)
    assert _filed("M1") == "FG-002"


def test_a_group_the_division_never_ratified_is_refused_not_created():
    _ratify([{"name": "Storm Generation"}])
    _model("M1")
    rows = backfill([("M1", "Wind Farm Yield")], actor="admin", apply=True)
    assert _verdicts(rows) == {"M1": "no-such-group"}
    assert _filed("M1") is None


def test_another_divisions_group_name_does_not_reach_across():
    """Resolution is per the RECORD's division, so a name only that division uses
    cannot file a record belonging to another."""
    _ratify([{"name": "Storm Generation"}], division=DIV)
    _ratify([{"name": "Instrument Pricer"}], division=OTHER)
    _model("M1", division=DIV)
    rows = backfill([("M1", "Instrument Pricer")], actor="admin", apply=True)
    assert _verdicts(rows) == {"M1": "no-such-group"}


def test_a_division_with_no_ratified_groups_is_reported_rather_than_skipped_silently():
    _model("M1")
    rows = backfill([("M1", "Storm Generation")], actor="admin", apply=True)
    assert _verdicts(rows) == {"M1": "no-groups"}
    assert "ratified no functional groups" in rows[0]["detail"]


def test_an_id_that_names_no_live_record_is_reported():
    _ratify([{"name": "Storm Generation"}])
    rows = backfill([("GHOST-1", "Storm Generation")], actor="admin", apply=True)
    assert _verdicts(rows) == {"GHOST-1": "unknown"}


def test_it_covers_the_other_registers_not_only_the_inventory():
    _ratify([{"name": "Storm Generation"}])
    register_product(product_id="P1", product="Pricer", actor="admin",
                     fields={"division": DIV, "calculating_agent": "In-house"})
    rebuild_product_view()
    rows = backfill([("P1", "Storm Generation")], actor="admin", apply=True)
    assert _verdicts(rows) == {"P1": "file"}
    assert rows[0]["noun"] == "Product"


# --- The mapping file ---------------------------------------------------------

def test_the_csv_skips_a_header_and_keeps_the_order_somebody_wrote(tmp_path):
    path = tmp_path / "groups.csv"
    path.write_text("record_id,group\nM2,Flood Simulation\nM1,Storm Generation\n\n",
                    encoding="utf-8")
    assert load_mapping(str(path)) == [("M2", "Flood Simulation"),
                                       ("M1", "Storm Generation")]


def test_plan_reports_every_row_including_the_ones_it_will_not_touch():
    """A backfill whose refusals you cannot read is one you have to run to understand."""
    _ratify([{"name": "Storm Generation"}])
    _model("M1")
    rows = plan([("M1", "Storm Generation"), ("GHOST", "Storm Generation"),
                 ("M1", "Nonexistent")])
    assert [r["verdict"] for r in rows] == ["file", "unknown", "no-such-group"]
    assert len(rows) == 3, "every mapping row gets a verdict"


def test_the_estate_is_read_live_only():
    """A hibernated record is out of the estate, so the backfill does not reach it."""
    _ratify([{"name": "Storm Generation"}])
    _model("M1")
    assert len(list_models()) == 1
    rows = backfill([("M1", "Storm Generation")], actor="admin", apply=False)
    assert rows[0]["verdict"] == "file"
