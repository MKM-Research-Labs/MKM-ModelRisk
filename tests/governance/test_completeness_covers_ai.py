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
"""The completeness audit counts AI Systems — in both halves of the report.

An AI System had no completeness findings at all until 2026-09-07: no gaps, no score,
no row in the register. It was in ``coverage_population``, which backs the framework
coverage table, and absent from ``scan``, which backs the findings. So the two halves
of one report described two different estates, with nothing on the page to say so —
the exact failure ``render_completeness_pdf`` warns about in its own docstring.

Nobody noticed because the live estate has no AI Systems yet. The populations agree
right up to the moment somebody registers one.
"""
from __future__ import annotations

from datetime import date

import pytest

from src.governance.ai_system import (list_ai_systems, rebuild_ai_system_view,
                                      register_ai_system)
from src.governance.completeness.scan import (AI_SYSTEM_KIND, coverage_population,
                                              scan)
from src.governance.ml_application import (rebuild_ml_application_view,
                                           register_ml_application)
from src.governance.model_inventory import rebuild_inventory_view, register_model

_AS_OF = date.today().isoformat()
_AI = {"name": "Client mail summariser", "division": "Risk", "owner": "David K Kelly",
       "use_case": "Summarises inbound client correspondence for the desk.",
       "deployment_pattern": "Agentic (tool-using)"}
_ML = {"name": "Retail PD scorecard", "division": "Risk", "owner": "David K Kelly",
       "estimator": "GradientBoostingClassifier",
       "use_case": "Ranks retail applicants by probability of default."}


@pytest.fixture
def estate():
    """One of each governed record type, with the read models rebuilt.

    A bare command leaves the projection stale — the API rebuilds after every write,
    a test calling the command directly has to do it itself.
    """
    register_model(model_id="M-CS-1", name="Alpha",
                   fields={"division": "Risk", "owner": "David K Kelly"}, actor="admin")
    register_ml_application(ml_application_id="MLA-CS-1", fields=_ML, actor="admin")
    register_ai_system(ai_system_id="AIS-CS-1", fields=_AI, actor="admin")
    rebuild_inventory_view()
    rebuild_ml_application_view()
    rebuild_ai_system_view()
    assert len(list_ai_systems()) == 1


def _kinds(rows):
    return {r["entity_kind"] for r in rows}


def test_an_ai_system_is_audited_for_completeness(estate):
    """It gets gaps and a score, like every other governed record."""
    rows = scan(_AS_OF)
    assert AI_SYSTEM_KIND in _kinds(rows)
    row = next(r for r in rows if r["entity_id"] == "AIS-CS-1")
    assert row["gaps"], "an AI System with almost nothing recorded reports no gaps"
    assert row["completeness"] < 100


def test_the_findings_and_the_coverage_table_count_the_same_estate(estate):
    """The two halves of one report. A record in the coverage table and absent from
    the findings is two populations with nothing to tell them apart."""
    audited = {r["entity_id"] for r in scan(_AS_OF)}
    def _id(record):
        return (record.get("model_id") or record.get("ml_application_id")
                or record.get("ai_system_id"))
    counted = {_id(r) for r in coverage_population()}
    # Products are audited but are not part of the clause population, so the coverage
    # side is a subset — never the other way round.
    assert counted <= audited, f"counted but not audited: {sorted(counted - audited)}"
    assert "AIS-CS-1" in counted and "AIS-CS-1" in audited


def test_scoping_to_one_ai_system_audits_only_it(estate):
    """What a committee meeting needs: the audit narrowed to what it has in scope.

    An empty sequence for a kind audits nothing of that kind — so a committee that
    oversees only AI Systems gets an AI-only report rather than the whole estate.
    """
    rows = scan(_AS_OF, model_ids=[], product_ids=[], ml_application_ids=[],
                ai_system_ids=["AIS-CS-1"])
    assert [r["entity_id"] for r in rows] == ["AIS-CS-1"]


def test_scoping_the_coverage_population_the_same_way(estate):
    """Both halves take the same scope, or the report contradicts itself."""
    counted = coverage_population([], [], ["AIS-CS-1"])
    assert [r["ai_system_id"] for r in counted] == ["AIS-CS-1"]


def test_scoping_to_an_ml_application_leaves_the_ai_systems_out(estate):
    """The filters are independent — narrowing one kind does not narrow another by
    accident, which is what makes a mixed-scope meeting audit correct."""
    rows = scan(_AS_OF, model_ids=[], product_ids=[],
                ml_application_ids=["MLA-CS-1"], ai_system_ids=[])
    assert [r["entity_id"] for r in rows] == ["MLA-CS-1"]
    counted = coverage_population([], ["MLA-CS-1"], [])
    assert [r["ml_application_id"] for r in counted] == ["MLA-CS-1"]


def test_an_unscoped_audit_still_covers_the_whole_estate(estate):
    """None means the whole estate — the global Audit Reports behaviour, unchanged."""
    ids = {r["entity_id"] for r in scan(_AS_OF)}
    assert {"M-CS-1", "MLA-CS-1", "AIS-CS-1"} <= ids
