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

"""The MKM-XV-001 registration seed (``scripts.register_xv001``).

Registers the PRS XVA Model at WP0, before it is built, and places it in the
chain: it consumes the PRS pricer and the event draws and feeds the Trading
Desk. As with MKM-EF-001, the edges must land only once the model is in the
inventory view, and a re-run must be a no-op.
"""
from __future__ import annotations

from scripts import register_xv001
from src.governance.model_inventory import (
    derive_chain,
    get_model,
    rebuild_inventory_view,
    register_model,
)

_NEIGHBOURS = (("MKM-PR-001", "PRS Pricing"), ("MKM-EF-001", "Event Frequency"),
               ("MKM-TD-001", "Trading Desk"))


def _register_neighbours():
    """The three models MKM-XV-001 connects to must exist for the edges to land."""
    for model_id, name in _NEIGHBOURS:
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()


def _links():
    return {(l["from"], l["to"]) for l in derive_chain()["links"]}


def test_registers_the_model_with_its_governance_data():
    _register_neighbours()
    result = register_xv001.register()

    assert result["registered"] is True
    data = get_model("MKM-XV-001")["data"]
    assert data["name"] == "PRS XVA Model"
    assert data["tier"] == 1
    assert data["version"] == "0.9.0"
    assert data["lifecycle_stage"] == "Validation"
    assert data["validation_status"] == "Pending"
    assert len(data["assumptions"]) == 6
    assert len(data["limitations"]) == 6
    assert len(data["model_weaknesses"]) == 4
    # Registration seeds the nine SR 26-2 questions.
    assert len(data["validation_questions"]) == 9


def test_places_the_model_between_its_inputs_and_the_trading_desk():
    _register_neighbours()
    register_xv001.register()

    links = _links()
    assert ("MKM-PR-001", "MKM-XV-001") in links
    assert ("MKM-EF-001", "MKM-XV-001") in links
    assert ("MKM-XV-001", "MKM-TD-001") in links


def test_reports_all_three_new_edges():
    _register_neighbours()
    assert register_xv001.register()["edges_declared"] == 3


def test_is_idempotent():
    _register_neighbours()
    register_xv001.register()

    again = register_xv001.register()
    assert again["registered"] is False
    assert again["edges_declared"] == 0
    assert len(get_model("MKM-XV-001")["data"]["assumptions"]) == 6


def test_skips_edges_when_a_neighbour_is_absent():
    """With no neighbours registered the model still registers, with no edges."""
    result = register_xv001.register()

    assert result["registered"] is True
    assert result["edges_declared"] == 0


def test_the_two_gating_limitations_are_recorded():
    """The regulatory treatment and the synthetic inputs must be in the
    limitations register, not just the plan."""
    _register_neighbours()
    register_xv001.register()

    limitations = " ".join(
        item["description"] for item in get_model("MKM-XV-001")["data"]["limitations"])
    assert "regulatory characterisation" in limitations
    assert "synthetic" in limitations


def test_main_runs_the_migration_and_reports(capsys):
    """The CLI entry point migrates the schema, registers, and prints a summary."""
    _register_neighbours()
    assert register_xv001.main() == 0
    out = capsys.readouterr().out
    assert "MKM-XV-001" in out
    assert "chain edges declared" in out
