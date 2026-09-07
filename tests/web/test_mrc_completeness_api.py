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
"""The per-MRC completeness audit: run it scoped to a committee, save and serve
the PDF, and gate the meeting close on signing it off."""
from __future__ import annotations

from src.files import upload_path
from src.governance.mrc.pack import TectonicNotFound
from src.web.api_mrc.completeness import AUDIT_SCOPE
from tests.web._signoff_flows import _add, _register_subject_model, _schedule_meeting, _seed_mrc
from tests.web.conftest import HEADERS

AUDIT_KIND = "completeness_audit"


def _stub_pdf(monkeypatch):
    # Avoid a real tectonic run — the completeness PDF renders from a stub, same
    # engine the minutes use (src.governance.mrc.pack.compile_tex).
    monkeypatch.setattr(
        "src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-audit")


def _audit_item(client, meeting_id="MTG1"):
    agenda = client.get(f"/api/meetings/{meeting_id}").get_json()["data"]["agenda"]
    return next((a for a in agenda if a.get("kind") == AUDIT_KIND), None)


def _scoped_meeting(client, monkeypatch):
    """A meeting whose committee has one model in scope, ready to audit."""
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _register_subject_model(client, model_id="M1")
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M1"})


def test_completeness_audit_item_seeded_on_schedule(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    assert _audit_item(client) is not None, "every meeting should seed the audit item"


def test_run_generates_and_stamps_item(client, monkeypatch):
    _scoped_meeting(client, monkeypatch)
    response = client.post("/api/meetings/MTG1/completeness-audit/run",
                           json={}, headers=HEADERS)
    assert response.status_code == 200
    item = _audit_item(client)
    assert item["audit_version"] == "1"
    assert item["audit_filename"]
    assert item["audit_entities"] == "1", "only the one in-scope model is audited"


def test_run_records_generator_by_name(client, monkeypatch):
    """The audit records who ran it by their People-directory name, not their login
    identity — committee records name people, not emails."""
    client.post("/api/reference/collections/people",
                json={"fields": {"name": "Alice Adams", "email": "alice@corp"},
                      "confirmed": True}, headers=HEADERS)
    _scoped_meeting(client, monkeypatch)
    client.post("/api/meetings/MTG1/completeness-audit/run", json={}, headers=HEADERS)
    assert _audit_item(client)["audit_generated_by"] == "Alice Adams"


def test_run_serves_latest_pdf(client, monkeypatch):
    _scoped_meeting(client, monkeypatch)
    client.post("/api/meetings/MTG1/completeness-audit/run", json={}, headers=HEADERS)
    response = client.get("/api/meetings/MTG1/completeness-audit.pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.data.startswith(b"%PDF")


def test_pdf_before_run_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    response = client.get("/api/meetings/MTG1/completeness-audit.pdf")
    assert response.status_code == 404
    assert "not generated" in response.get_json()["error"]


def test_rerun_increments_version(client, monkeypatch):
    _scoped_meeting(client, monkeypatch)
    for _ in range(2):
        client.post("/api/meetings/MTG1/completeness-audit/run", json={}, headers=HEADERS)
    assert _audit_item(client)["audit_version"] == "2"


def test_run_returns_503_without_tectonic(client, monkeypatch):
    _seed_mrc(client)
    _schedule_meeting(client)

    def _boom(tex, assets=None):
        raise TectonicNotFound("tectonic not installed")
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", _boom)
    response = client.post("/api/meetings/MTG1/completeness-audit/run",
                           json={}, headers=HEADERS)
    assert response.status_code == 503


def test_run_unknown_meeting_is_404(client):
    assert client.post("/api/meetings/none/completeness-audit/run",
                       json={}, headers=HEADERS).status_code == 404


def test_run_on_closed_meeting_is_400(client, monkeypatch):
    _scoped_meeting(client, monkeypatch)
    # Resolve every agenda item, then close the (quorum-off, so quorate) meeting.
    for item in client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]:
        client.post(f"/api/meetings/MTG1/collections/agenda/{item['item_id']}",
                    json={"fields": {"status": "Completed"}, "confirmed": True}, headers=HEADERS)
    client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    response = client.post("/api/meetings/MTG1/completeness-audit/run",
                           json={}, headers=HEADERS)
    assert response.status_code == 400
    assert "closed" in response.get_json()["error"]


def test_close_blocked_until_audit_item_resolved(client, monkeypatch):
    _scoped_meeting(client, monkeypatch)
    # Resolve every agenda item EXCEPT the completeness-audit item.
    agenda = client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
    for item in agenda:
        if item.get("kind") == AUDIT_KIND:
            continue
        client.post(f"/api/meetings/MTG1/collections/agenda/{item['item_id']}",
                    json={"fields": {"status": "Completed"}, "confirmed": True}, headers=HEADERS)
    response = client.post("/api/meetings/MTG1/close", json={"confirmed": True}, headers=HEADERS)
    assert response.status_code == 400
    assert "Governance completeness audit" in response.get_json()["error"]


def test_a_meeting_scheduled_before_the_audit_existed_says_so(client, monkeypatch):
    """Those meetings have no standing audit item until the backfill adds one, and
    the refusal names the missing item rather than reporting an empty audit."""
    _scoped_meeting(client, monkeypatch)
    item_id = _audit_item(client)["item_id"]
    client.post(f"/api/meetings/MTG1/collections/agenda/{item_id}/delete",
                json={"confirmed": True}, headers=HEADERS)
    refused = client.post("/api/meetings/MTG1/completeness-audit/run", json={},
                          headers=HEADERS)
    assert refused.status_code == 404
    assert "no completeness-audit item" in refused.get_json()["error"]


def test_the_audit_pdf_for_a_meeting_that_is_not_there_is_404(client):
    assert client.get("/api/meetings/NOPE/completeness-audit.pdf").status_code == 404


def test_an_audit_pdf_whose_file_has_gone_missing_is_404_not_a_500(client,
                                                                  monkeypatch):
    _scoped_meeting(client, monkeypatch)
    client.post("/api/meetings/MTG1/completeness-audit/run", json={}, headers=HEADERS)
    upload_path(AUDIT_SCOPE, _audit_item(client)["audit_filename"]).unlink()
    response = client.get("/api/meetings/MTG1/completeness-audit.pdf")
    assert response.status_code == 404
    assert "file missing" in response.get_json()["error"]


# --- What the committee actually has in scope ---------------------------------
#
# The audit used to collect models and products only, so a meeting holding an ML
# Application or an AI System audited neither: the record was on the agenda and
# absent from the audit the committee ran about it. Fixed 2026-09-07.

def _register_ai_system(client, ai_system_id="AIS-1"):
    return client.post("/api/ai-systems", json={
        "ai_system_id": ai_system_id, "confirmed": True,
        "fields": {"name": "Client mail summariser", "division": "Risk",
                   "owner": "David K Kelly",
                   "use_case": "Summarises inbound client correspondence.",
                   "deployment_pattern": "Agentic (tool-using)"}}, headers=HEADERS)


def _register_ml_application(client, ml_application_id="MLA-1"):
    return client.post("/api/ml-applications", json={
        "ml_application_id": ml_application_id, "confirmed": True,
        "fields": {"name": "Retail PD scorecard", "division": "Risk",
                   "owner": "David K Kelly",
                   "estimator": "GradientBoostingClassifier",
                   "use_case": "Ranks retail applicants."}}, headers=HEADERS)


def test_an_in_scope_ai_system_is_audited(client, monkeypatch):
    """One AI System in scope, nothing else: the audit covers exactly it."""
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _register_ai_system(client)
    _schedule_meeting(client)
    _add(client, "ai_systems_in_scope", {"ai_system_id": "AIS-1"})
    assert client.post("/api/meetings/MTG1/completeness-audit/run",
                       json={}, headers=HEADERS).status_code == 200
    assert _audit_item(client)["audit_entities"] == "1"


def test_every_record_type_in_scope_is_counted(client, monkeypatch):
    """A mixed agenda. The count is the committee's own population — not the firm's,
    and not the models half of it."""
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _register_subject_model(client, model_id="M1")
    _register_ml_application(client)
    _register_ai_system(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M1"})
    _add(client, "ml_applications_in_scope", {"ml_application_id": "MLA-1"})
    _add(client, "ai_systems_in_scope", {"ai_system_id": "AIS-1"})
    assert client.post("/api/meetings/MTG1/completeness-audit/run",
                       json={}, headers=HEADERS).status_code == 200
    assert _audit_item(client)["audit_entities"] == "3"


def test_a_record_the_committee_does_not_hold_is_not_audited(client, monkeypatch):
    """The scope is a filter, not a suggestion. An AI System registered but not put on
    this meeting's agenda stays out of this meeting's audit."""
    _stub_pdf(monkeypatch)
    _seed_mrc(client)
    _register_subject_model(client, model_id="M1")
    _register_ai_system(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M1"})
    assert client.post("/api/meetings/MTG1/completeness-audit/run",
                       json={}, headers=HEADERS).status_code == 200
    assert _audit_item(client)["audit_entities"] == "1"

