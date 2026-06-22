# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Tests for routes.governance.documents — part 1.

Covers: GET documents, POST upload, GET download, POST delete.
"""

import io
import json

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def doc_env(tmp_path, monkeypatch):
    """Governance documents environment with empty documents list."""
    import routes.governance._constants as gov_constants

    docs_path = str(tmp_path / "governance_documents.json")
    docs_dir = str(tmp_path / "governance_docs")

    with open(docs_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_PATH", docs_path)
    monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_DIR", docs_dir)

    # Isolate auto-discovery so it doesn't find real audit/model PDFs
    empty_audit = str(tmp_path / "empty_audit")
    empty_docs = str(tmp_path / "empty_docs")
    monkeypatch.setattr(gov_constants, "AUDIT_REPORTS_DIR", empty_audit)
    monkeypatch.setattr(gov_constants, "_docs_dir", empty_docs)

    return {"docs_path": docs_path, "docs_dir": docs_dir, "tmp_path": tmp_path}


@pytest.fixture
def doc_client(doc_env, monkeypatch):
    """Flask test client with isolated document storage."""
    import pathlib
    from config import config
    monkeypatch.setattr(config, "get_input_dir",
                        lambda: pathlib.Path(doc_env["docs_path"]).parent)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# GET /api/v1/governance/documents
# ===========================================================================

class TestGetDocuments:

    def test_empty_list_returns_success(self, doc_client):
        r = doc_client.get("/api/v1/governance/documents")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert data["documents"] == []


# ===========================================================================
# POST /api/v1/governance/documents/upload
# ===========================================================================

class TestUploadDocument:

    def test_no_file_returns_400(self, doc_client):
        r = doc_client.post("/api/v1/governance/documents/upload")
        assert r.status_code == 400
        data = json.loads(r.data)
        assert data["status"] == "error"

    def test_empty_filename_returns_400(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b""), "")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 400

    def test_valid_upload_returns_200(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={
                "file": (io.BytesIO(b"PDF content"), "test_doc.pdf"),
                "description": "Test governance document",
            },
            content_type="multipart/form-data",
        )
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"
        assert "document" in data

    def test_upload_response_has_id(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "report.pdf")},
            content_type="multipart/form-data",
        )
        data = json.loads(r.data)
        assert "id" in data["document"]

    def test_upload_appears_in_list(self, doc_client):
        doc_client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "myfile.pdf")},
            content_type="multipart/form-data",
        )
        r = doc_client.get("/api/v1/governance/documents")
        data = json.loads(r.data)
        assert len(data["documents"]) == 1

    def test_upload_stores_description(self, doc_client):
        r = doc_client.post(
            "/api/v1/governance/documents/upload",
            data={
                "file": (io.BytesIO(b"data"), "file.pdf"),
                "description": "My description",
            },
            content_type="multipart/form-data",
        )
        data = json.loads(r.data)
        assert data["document"]["description"] == "My description"


# ===========================================================================
# GET /api/v1/governance/documents/<doc_id>/download
# ===========================================================================

class TestDownloadDocument:

    def _upload(self, client, content=b"pdf bytes", name="test.pdf"):
        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(content), name)},
            content_type="multipart/form-data",
        )
        return json.loads(r.data)["document"]["id"]

    def test_not_found_returns_404(self, doc_client):
        r = doc_client.get("/api/v1/governance/documents/nonexistent/download")
        assert r.status_code == 404

    def test_valid_download_returns_200(self, doc_client):
        doc_id = self._upload(doc_client)
        r = doc_client.get(f"/api/v1/governance/documents/{doc_id}/download")
        assert r.status_code == 200


# ===========================================================================
# POST /api/v1/governance/documents/<doc_id>/delete
# ===========================================================================

class TestDeleteDocument:

    def _upload(self, client):
        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"data"), "del.pdf")},
            content_type="multipart/form-data",
        )
        return json.loads(r.data)["document"]["id"]

    def test_not_found_returns_404(self, doc_client):
        r = doc_client.post("/api/v1/governance/documents/nonexistent/delete")
        assert r.status_code == 404

    def test_valid_delete_returns_success(self, doc_client):
        doc_id = self._upload(doc_client)
        r = doc_client.post(f"/api/v1/governance/documents/{doc_id}/delete")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["status"] == "success"

    def test_deleted_doc_not_in_list(self, doc_client):
        doc_id = self._upload(doc_client)
        doc_client.post(f"/api/v1/governance/documents/{doc_id}/delete")
        r = doc_client.get("/api/v1/governance/documents")
        data = json.loads(r.data)
        ids = [d["id"] for d in data["documents"]]
        assert doc_id not in ids
