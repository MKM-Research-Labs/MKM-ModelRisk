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

from src.governance.mrc.pack import TectonicNotFound
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
