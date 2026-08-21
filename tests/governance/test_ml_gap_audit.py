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
"""ML Applications appear in the gap audit.

They did not. ``scan`` iterated models and products, so an estate half of which is ML
would have been audited on the other half — reporting a gap picture that is wrong in
the direction that flatters, with nothing on the page to say so.
"""
from __future__ import annotations

from src.governance.completeness.scan import ML_APPLICATION_KIND, scan
from src.governance.ml_application import (rebuild_ml_application_view,
                                           register_ml_application,
                                           retire_ml_application)

_MINIMUM = {"name": "Retail PD scorecard", "division": "Risk", "owner": "Dana",
            "estimator": "GradientBoostingClassifier", "use_case": "Ranks applicants."}
_AS_OF = "2026-08-21"


def _register(ml_application_id="MLA-1"):
    register_ml_application(ml_application_id=ml_application_id, fields=_MINIMUM,
                            actor="admin")
    rebuild_ml_application_view()
    return ml_application_id


def _audited(rows):
    return {r["entity_id"] for r in rows if r["entity_kind"] == ML_APPLICATION_KIND}


def test_an_ml_application_is_audited():
    _register()
    rows = scan(_AS_OF)
    assert "MLA-1" in _audited(rows)


def test_it_is_scored_and_carries_its_gaps():
    _register()
    row = [r for r in scan(_AS_OF) if r["entity_id"] == "MLA-1"][0]
    assert 0 <= row["completeness"] <= 1
    assert row["gaps"], "a record with almost nothing filled in has gaps to report"
    assert row["entity_name"] == "Retail PD scorecard"


def test_a_retired_ml_application_is_out_of_the_audit():
    """Out of the estate and out of every figure, exactly as a hibernated model is.
    Auditing one reports gaps against a record nobody is running."""
    _register()
    _register("MLA-2")
    retire_ml_application(ml_application_id="MLA-2", actor="admin")
    rebuild_ml_application_view()
    audited = _audited(scan(_AS_OF))
    assert "MLA-1" in audited and "MLA-2" not in audited


def test_the_audit_can_be_scoped_to_named_records():
    """A committee that oversees some of the estate gets a report about that part of
    it, under the same rule models and products already follow."""
    _register()
    _register("MLA-2")
    assert _audited(scan(_AS_OF, ml_application_ids=["MLA-2"])) == {"MLA-2"}
    assert _audited(scan(_AS_OF, ml_application_ids=[])) == set()
    assert {"MLA-1", "MLA-2"} <= _audited(scan(_AS_OF))
