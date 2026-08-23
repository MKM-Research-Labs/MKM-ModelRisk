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
"""A hibernated model is out of the estate, and out of every figure drawn from it.

Retiring a model is the committee's way of saying it is no longer part of the
estate. It carries no governance obligations afterwards, so counting it drags the
completeness score and the approval coverage against a record nobody is ever going
to complete — and which can never improve. These tests hold that line, and hold the
two deliberate exceptions to it: a read about one particular record, and the
integrity check that has to see the whole declared graph.
"""
from __future__ import annotations

from src.governance.completeness.scan import scan
from src.governance.ml_application import list_ml_applications
from src.governance.model_inventory import list_models
from src.governance.reference import ensure_default_estimators
from tests.web._signoff_flows import (
    _register_subject_model,
    _schedule_meeting,
    _seed_mrc,
    _signoff_item,
    decide,
    request_retire,
)
from tests.web.conftest import HEADERS


def _hibernate(client):
    """Take M1 through the committee to a hibernated state."""
    _seed_mrc(client)
    _register_subject_model(client)
    _schedule_meeting(client)
    request_retire(client)
    decide(client, _signoff_item(client)["item_id"])
    assert client.get("/api/models/M1").get_json()["retired"] is True


def test_the_inventory_leaves_hibernated_models_out(client):
    _hibernate(client)
    assert [m["model_id"] for m in list_models()] == []
    assert [m["model_id"] for m in list_models(include_retired=True)] == ["M1"]


def test_the_models_endpoint_leaves_them_out_unless_asked(client):
    """The console list, and therefore the summary tiles and the Approved count
    drawn from it, sees the live estate only."""
    _hibernate(client)
    assert client.get("/api/models").get_json() == []
    with_retired = client.get("/api/models?include_retired=1").get_json()
    assert [m["model_id"] for m in with_retired] == ["M1"]


def test_the_completeness_audit_does_not_score_them(client):
    """A hibernated model has no obligations left; scoring its empty record would
    hold the estate's completeness down for ever."""
    _hibernate(client)
    assert [row["entity_id"] for row in scan("2026-08-07")] == []


def test_a_hibernated_model_is_not_offered_in_a_model_dropdown(client):
    """It cannot be picked as a minute's or an action's subject: every dropdown fed
    by the inventory offers the live estate only."""
    _hibernate(client)
    specs = client.get("/api/meetings/fields").get_json()
    offered = [f["options"] for c in specs["collections"] for f in c["fields"]
               if f["key"] == "model_id"]
    assert offered, "the meeting specs should carry model dropdowns to check"
    for options in offered:
        assert "M1" not in options


def test_its_own_page_still_works(client):
    """The exception: reads about one particular record. A hibernated model must
    still open — otherwise nobody could look at it, let alone reactivate it."""
    _hibernate(client)
    assert client.get("/api/models/M1").status_code == 200
    assert client.get("/api/models/M1/neighbourhood").status_code == 200


# --- The same line, held for ML Applications --------------------------------
#
# An ML Application is retired directly rather than through the committee, but
# what retirement MEANS is identical: out of the estate, out of every figure.
# The projection used to return hibernated records to every caller, so three
# call sites each re-filtered them and the console list showed them anyway.


def _hibernate_ml(client):
    """Register MLA-0001 and retire it."""
    ensure_default_estimators()
    client.post("/api/ml-applications",
                json={"ml_application_id": "MLA-0001", "confirmed": True,
                      "fields": {"name": "Retail PD scorecard", "division": "Risk",
                                 "owner": "David K Kelly",
                                 "estimator": "GradientBoostingClassifier",
                                 "use_case": "Ranks applicants by PD."}},
                headers=HEADERS)
    client.post("/api/ml-applications/MLA-0001/retire",
                json={"confirmed": True}, headers=HEADERS)
    assert client.get("/api/ml-applications/MLA-0001").get_json()["retired"] is True


def test_the_ml_list_leaves_hibernated_records_out(client):
    _hibernate_ml(client)
    assert [r["ml_application_id"] for r in list_ml_applications()] == []
    assert [r["ml_application_id"]
            for r in list_ml_applications(include_retired=True)] == ["MLA-0001"]


def test_the_ml_endpoint_leaves_them_out_unless_asked(client):
    _hibernate_ml(client)
    assert client.get("/api/ml-applications").get_json() == []
    with_retired = client.get("/api/ml-applications?include_retired=1").get_json()
    assert [r["ml_application_id"] for r in with_retired] == ["MLA-0001"]


def test_a_hibernated_ml_application_is_not_offered_as_a_product_component(client):
    """It cannot be picked as a component, and the audit does not score it."""
    _hibernate_ml(client)
    fields = client.get("/api/products/fields").get_json()
    assert "MLA-0001" not in fields["ml_applications"]
    assert [row["entity_id"] for row in scan("2026-08-07")] == []
