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
"""Meeting lifecycle: agenda lock, distribution ZIP, and analysis/agenda uploads."""
from __future__ import annotations

import io
import zipfile

from src.files import save_upload, upload_path
from tests.web.conftest import HEADERS
from tests.web.test_mrc_signoff_api import _add, _schedule_meeting, _seed_mrc


def _file(data=b"%PDF payload", name="doc.pdf"):
    return {"file": (io.BytesIO(data), name)}


def _upload(client, path, data=None, name="doc.pdf"):
    payload = _file(name=name) if data is None else data
    return client.post(path, data=payload, content_type="multipart/form-data", headers=HEADERS)


# --- agenda lock / unlock ---------------------------------------------------

def test_lock_and_unlock_agenda(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    locked = client.post("/api/meetings/MTG1/lock-agenda", json={"confirmed": True}, headers=HEADERS)
    assert locked.status_code == 200
    assert locked.get_json()["data"]["agenda_locked"] == "true"
    unlocked = client.post("/api/meetings/MTG1/unlock-agenda", json={"confirmed": True}, headers=HEADERS)
    assert unlocked.get_json()["data"]["agenda_locked"] == "false"


def test_lock_agenda_unknown_meeting_is_404(client):
    assert client.post("/api/meetings/none/lock-agenda",
                       json={"confirmed": True}, headers=HEADERS).status_code == 404


# --- distribution ZIP -------------------------------------------------------

def test_distribution_zip_bundles_agenda_and_uploads(client, monkeypatch):
    monkeypatch.setattr("src.governance.mrc.pack.compile_tex", lambda tex, assets=None: b"%PDF-agenda")
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    _add(client, "agenda", {"title": "Discussion"})
    agenda_id = [a for a in client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
                 if a.get("title") == "Discussion"][0]["item_id"]
    _upload(client, "/api/meetings/MTG1/models/M-A/analysis", name="analysis.pdf")
    _upload(client, f"/api/meetings/MTG1/agenda/{agenda_id}/document", name="paper.pdf")

    response = client.get("/api/meetings/MTG1/distribution.zip")
    assert response.status_code == 200
    assert response.mimetype == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.data)) as zf:
        names = zf.namelist()
    assert "agenda.pdf" in names
    assert any(n.startswith("documents/") for n in names)


def test_distribution_zip_unknown_meeting_is_404(client):
    assert client.get("/api/meetings/none/distribution.zip").status_code == 404


# --- model analysis upload / download --------------------------------------

def test_model_analysis_upload_download_roundtrip(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    up = _upload(client, "/api/meetings/MTG1/models/M-A/analysis", name="analysis.pdf")
    assert up.status_code == 201
    down = client.get("/api/meetings/MTG1/models/M-A/analysis")
    assert down.status_code == 200
    assert down.data == b"%PDF payload"


def test_uploaded_analysis_is_also_filed_on_the_model(client):
    """Uploading a model's analysis at a meeting also files it on the model, under
    Docs / Analysis, so it lives with the model's record."""
    _seed_mrc(client)
    _schedule_meeting(client)
    client.post("/api/models", json={"model_id": "MKM-XA-001", "name": "X", "confirmed": True}, headers=HEADERS)
    _add(client, "models_in_scope", {"model_id": "MKM-XA-001"})
    up = _upload(client, "/api/meetings/MTG1/models/MKM-XA-001/analysis", name="analysis.pdf")
    assert up.status_code == 201
    docs = client.get("/api/models/MKM-XA-001").get_json()["data"]["documents"]
    analysis = [d for d in docs if d.get("category") == "Analysis"]
    assert analysis, "the presented analysis should be filed on the model under Analysis"
    assert analysis[0].get("original_name") == "analysis.pdf"


def test_model_analysis_unknown_meeting_is_404(client):
    assert _upload(client, "/api/meetings/none/models/M-A/analysis").status_code == 404


def test_model_analysis_not_in_scope_is_400(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    resp = _upload(client, "/api/meetings/MTG1/models/GHOST/analysis")
    assert resp.status_code == 400
    assert "not in scope" in resp.get_json()["error"]


def test_model_analysis_no_file_is_400(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    resp = _upload(client, "/api/meetings/MTG1/models/M-A/analysis", data={})
    assert resp.status_code == 400
    assert "no file" in resp.get_json()["error"]


def test_model_analysis_bad_file_type_is_400(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    resp = _upload(client, "/api/meetings/MTG1/models/M-A/analysis", name="virus.exe")
    assert resp.status_code == 400


def test_model_analysis_download_missing_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    # In scope but nothing uploaded yet.
    assert client.get("/api/meetings/MTG1/models/M-A/analysis").status_code == 404


def test_model_analysis_download_file_gone_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    _add(client, "models_in_scope", {"model_id": "M-A"})
    _upload(client, "/api/meetings/MTG1/models/M-A/analysis", name="analysis.pdf")
    item = [m for m in client.get("/api/meetings/MTG1").get_json()["data"]["models_in_scope"]
            if m["model_id"] == "M-A"][0]
    upload_path("meeting_analysis", item["analysis_filename"]).unlink()
    assert client.get("/api/meetings/MTG1/models/M-A/analysis").status_code == 404


# --- agenda document upload / download -------------------------------------

def _agenda_item_id(client, title="Discussion"):
    _add(client, "agenda", {"title": title})
    return [a for a in client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
            if a.get("title") == title][0]["item_id"]


def test_agenda_document_upload_download_roundtrip(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    up = _upload(client, f"/api/meetings/MTG1/agenda/{item_id}/document", name="paper.pdf")
    assert up.status_code == 201
    down = client.get(f"/api/meetings/MTG1/agenda/{item_id}/document")
    assert down.status_code == 200
    assert down.data == b"%PDF payload"


def test_agenda_document_falls_back_to_the_previous_minutes_scope(client):
    """The minutes sign-off item references the previous meeting's minutes, stored
    under meeting_minutes (not uploaded as an agenda document), so the download
    must find it there rather than 404."""
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    meta = save_upload("meeting_minutes", "minutes_prev.pdf", b"%PDF prev minutes")
    r = client.post(f"/api/meetings/MTG1/collections/agenda/{item_id}",
                    json={"fields": {"document_filename": meta["filename"],
                                     "document_original_name": "minutes_prev.pdf"}}, headers=HEADERS)
    assert r.status_code in (200, 201)
    down = client.get(f"/api/meetings/MTG1/agenda/{item_id}/document")
    assert down.status_code == 200
    assert down.data == b"%PDF prev minutes"


def test_agenda_document_unknown_item_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    assert _upload(client, "/api/meetings/MTG1/agenda/AG-999/document").status_code == 404


def test_agenda_document_no_file_is_400(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    resp = _upload(client, f"/api/meetings/MTG1/agenda/{item_id}/document", data={})
    assert resp.status_code == 400
    assert "no file" in resp.get_json()["error"]


def test_agenda_document_bad_file_type_is_400(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    assert _upload(client, f"/api/meetings/MTG1/agenda/{item_id}/document",
                   name="script.exe").status_code == 400


def test_agenda_document_download_missing_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    assert client.get(f"/api/meetings/MTG1/agenda/{item_id}/document").status_code == 404


def test_agenda_document_download_file_gone_is_404(client):
    _seed_mrc(client)
    _schedule_meeting(client)
    item_id = _agenda_item_id(client)
    _upload(client, f"/api/meetings/MTG1/agenda/{item_id}/document", name="paper.pdf")
    item = [a for a in client.get("/api/meetings/MTG1").get_json()["data"]["agenda"]
            if a["item_id"] == item_id][0]
    upload_path("meeting_agenda", item["document_filename"]).unlink()
    assert client.get(f"/api/meetings/MTG1/agenda/{item_id}/document").status_code == 404


def test_analysis_presentations_lists_meetings_the_model_was_in_scope_for(client):
    """The model-side read view lists every meeting where its analysis was
    presented (it was in scope), for the MRC Linkage tab."""
    _seed_mrc(client)
    _schedule_meeting(client)
    client.post("/api/models", json={"model_id": "MKM-XP-001", "name": "X", "confirmed": True}, headers=HEADERS)
    _add(client, "models_in_scope", {"model_id": "MKM-XP-001"})
    pres = client.get("/api/models/MKM-XP-001/analysis-presentations").get_json()
    assert [p["meeting_id"] for p in pres] == ["MTG1"]


def test_analysis_presentations_unknown_model_is_404(client):
    assert client.get("/api/models/NOPE/analysis-presentations").status_code == 404


def test_model_analysis_remove_detaches_it_from_the_meeting(client):
    """Remove clears the meeting's analysis reference; the download then 404s."""
    _seed_mrc(client)
    _schedule_meeting(client)
    client.post("/api/models", json={"model_id": "MKM-XR-001", "name": "X", "confirmed": True}, headers=HEADERS)
    _add(client, "models_in_scope", {"model_id": "MKM-XR-001"})
    _upload(client, "/api/meetings/MTG1/models/MKM-XR-001/analysis", name="analysis.pdf")
    assert client.post("/api/meetings/MTG1/models/MKM-XR-001/analysis/remove",
                       json={}, headers=HEADERS).status_code == 200
    item = [m for m in client.get("/api/meetings/MTG1").get_json()["data"]["models_in_scope"]
            if m["model_id"] == "MKM-XR-001"][0]
    assert not item.get("analysis_filename")
    assert client.get("/api/meetings/MTG1/models/MKM-XR-001/analysis").status_code == 404


def test_model_analysis_remove_unknown_meeting_is_404(client):
    assert client.post("/api/meetings/none/models/M-A/analysis/remove",
                       json={}, headers=HEADERS).status_code == 404


def test_model_analysis_remove_for_a_model_not_in_scope_is_400(client):
    """Nothing to detach: the model was never tabled at this meeting, and saying so
    is more useful than clearing a field on a row that does not exist."""
    _seed_mrc(client)
    _schedule_meeting(client)
    client.post("/api/models", json={"model_id": "MKM-XR-001", "name": "X",
                                     "confirmed": True}, headers=HEADERS)
    refused = client.post("/api/meetings/MTG1/models/MKM-XR-001/analysis/remove",
                          json={}, headers=HEADERS)
    assert refused.status_code == 400
    assert "not in scope" in refused.get_json()["error"]
