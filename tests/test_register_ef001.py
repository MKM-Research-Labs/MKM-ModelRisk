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

"""The MKM-EF-001 registration seed (``scripts.register_ef001``).

Registers the Event Frequency Model directly through the governance command API
— it post-dates the migrated PhysicalRisk inventory — and places it in the
model chain between the GEV hazard curve and PRS pricing.

The two properties worth protecting are that the chain edges only land once the
model is visible in the inventory view (the ordering bug this test would have
caught), and that a re-run is a no-op.
"""
from __future__ import annotations

from scripts import register_ef001
from src.governance.model_inventory import (
    derive_chain,
    get_model,
    rebuild_inventory_view,
    register_model,
)


def _register_neighbours():
    """The two models MKM-EF-001 sits between must exist for the edges to land."""
    for model_id, name in (("MKM-GH-001", "GEV Hazard"), ("MKM-PR-001", "PRS Pricing")):
        register_model(model_id=model_id, name=name, actor="test")
    rebuild_inventory_view()


def test_registers_the_model_with_its_governance_data():
    _register_neighbours()
    result = register_ef001.register()

    assert result["registered"] is True
    data = get_model("MKM-EF-001")["data"]
    assert data["name"] == "Event Frequency Model"
    assert data["tier"] == 1
    assert data["version"] == "1.0.0"
    assert data["type"] == "Analytical Model"
    assert len(data["assumptions"]) == 4
    assert len(data["limitations"]) == 4
    assert len(data["model_weaknesses"]) == 3
    # Registration seeds the nine SR 26-2 questions.
    assert len(data["validation_questions"]) == 9


def test_places_the_model_between_the_hazard_curve_and_pricing():
    _register_neighbours()
    register_ef001.register()

    links = derive_chain()["links"]
    assert ("MKM-GH-001", "MKM-EF-001") in {(l["from"], l["to"]) for l in links}
    assert ("MKM-EF-001", "MKM-PR-001") in {(l["from"], l["to"]) for l in links}


def test_reports_both_new_edges():
    _register_neighbours()
    assert register_ef001.register()["edges_declared"] == 2


def test_is_idempotent():
    _register_neighbours()
    register_ef001.register()

    again = register_ef001.register()
    assert again["registered"] is False
    assert again["edges_declared"] == 0
    # The assumptions were not duplicated on the second run.
    assert len(get_model("MKM-EF-001")["data"]["assumptions"]) == 4


def test_skips_edges_when_a_neighbour_is_absent():
    """With no MKM-GH-001 / MKM-PR-001 registered, the model still registers but
    neither edge is declared — the guard skips edges to a missing model rather
    than raising."""
    result = register_ef001.register()

    assert result["registered"] is True
    assert result["edges_declared"] == 0


def test_the_lambda_limitation_is_recorded():
    """The single most important governance fact about this model — that nothing
    validates lambda — must be in the limitations register, not just the plan."""
    _register_neighbours()
    register_ef001.register()

    limitations = " ".join(
        item["description"] for item in get_model("MKM-EF-001")["data"]["limitations"])
    assert "lambda is unvalidated" in limitations


def test_main_runs_the_migration_and_reports(capsys):
    """The CLI entry point migrates the schema, registers, and prints a summary."""
    _register_neighbours()
    assert register_ef001.main() == 0
    out = capsys.readouterr().out
    assert "MKM-EF-001" in out
    assert "chain edges declared" in out
