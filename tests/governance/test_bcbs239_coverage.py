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
"""BCBS 239 clause coverage, and who the framework population is.

Two things are being asserted. That the third framework reports on the same terms as
the other two — a clause, what evidences it, and how much of the estate carries it,
with no compliance claim. And that the estate it counts includes ML Applications:
counting the clauses over models alone would describe a shrinking slice of the estate
as the ML side grows, which is the failure the gap audit had.
"""
from __future__ import annotations

from config.governance import COVERAGE_BASIS, FRAMEWORK_COVERAGE
from config.governance._frameworks import BCBS_239, BCBS_239_PRINCIPLES
from src.governance.completeness.framework import PROBES, coverage, tally
from src.governance.completeness.review_programme import record_id
from src.governance.completeness.scan import coverage_population, scan
from src.governance.ml_application import (rebuild_ml_application_view,
                                           register_ml_application,
                                           retire_ml_application)
from src.governance.model_inventory import rebuild_inventory_view, register_model

_ML = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
       "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}
_AS_OF = "2026-08-21"


def test_the_third_framework_is_reported():
    names = [name for name, _rows in FRAMEWORK_COVERAGE]
    assert BCBS_239 in names
    assert len(BCBS_239_PRINCIPLES) == 14, "the Committee's fourteen principles"


def test_every_clause_names_a_probe_that_exists():
    """A clause pointing at a probe nobody wrote reports nothing and says nothing
    about why."""
    declared = {"institution", "absent", "partial"}
    for ref, _title, probe, note in BCBS_239_PRINCIPLES:
        assert probe in PROBES or probe in declared, f"{ref} names {probe}"
        assert note, f"{ref} must say what evidences it, or what would have to exist"


def test_the_supervisory_principles_are_not_scored():
    """12 to 14 are addressed to the supervisor, not the bank. Marking a product down
    for not holding a supervisor's review measures the wrong thing."""
    supervisory = {ref: probe for ref, _t, probe, _n in BCBS_239_PRINCIPLES
                   if ref in ("12", "14")}
    assert set(supervisory.values()) == {"institution"}


def test_the_basis_makes_no_compliance_claim():
    assert "no compliance claim" in COVERAGE_BASIS
    assert "BCBS 239" in COVERAGE_BASIS


def test_ml_applications_are_in_the_population_the_clauses_are_counted_over():
    register_model(model_id="M1", name="Alpha", actor="admin")
    rebuild_inventory_view()
    register_ml_application(ml_application_id="MLA-1", fields=_ML, actor="admin")
    rebuild_ml_application_view()
    ids = {record_id(r) for r in coverage_population()}
    assert {"M1", "MLA-1"} <= ids


def test_a_retired_ml_application_is_out_of_the_population():
    register_ml_application(ml_application_id="MLA-1", fields=_ML, actor="admin")
    register_ml_application(ml_application_id="MLA-2", fields=_ML, actor="admin")
    retire_ml_application(ml_application_id="MLA-2", actor="admin")
    rebuild_ml_application_view()
    ids = {record_id(r) for r in coverage_population()}
    assert "MLA-1" in ids and "MLA-2" not in ids


def test_the_clauses_are_counted_without_a_per_type_branch():
    """Decision 7: an ML Application spells the probe fields the way a model does, so
    one lambda over one population serves both."""
    register_ml_application(ml_application_id="MLA-1", fields=_ML, actor="admin")
    rebuild_ml_application_view()
    clauses = coverage(scan(_AS_OF), coverage_population(), _AS_OF, ())
    bcbs = [c for c in clauses if c["framework"] == BCBS_239]
    assert len(bcbs) == 14
    counts = tally(clauses, BCBS_239)
    assert counts["clauses"] == 14


def test_a_record_id_is_found_whichever_register_it_came_from():
    assert record_id({"model_id": "M1"}) == "M1"
    assert record_id({"ml_application_id": "MLA-1"}) == "MLA-1"
    assert record_id({"product_id": "P1"}) == "P1"
    assert record_id({}) == ""
