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
Tests for routes.governance.documents — part 2.

Coverage expansion: save metadata failures, file missing on disk.
"""

import io
import json
import os

import pytest


# ===========================================================================
# Coverage expansion: save metadata failures (L76, L111), file missing on disk (L91)
# ===========================================================================

class TestUploadSaveMetadataFails:
    """Line 76: _save_gov_documents returns False -> 500."""

    def test_upload_save_failure_returns_500(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        import pathlib
        from config import config

        docs_path = str(tmp_path / "governance_documents.json")
        docs_dir = str(tmp_path / "governance_docs")
        with open(docs_path, "w") as f:
            json.dump([], f)
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_PATH", docs_path)
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_DIR", docs_dir)
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(docs_path).parent)

        # Patch _save_gov_documents where it's imported in the documents module
        import routes.governance.documents as docs_mod
        monkeypatch.setattr(docs_mod, "_save_gov_documents", lambda docs: False)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post(
            "/api/v1/governance/documents/upload",
            data={"file": (io.BytesIO(b"content"), "test.pdf")},
            content_type="multipart/form-data",
        )
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"
        assert "metadata" in data["message"].lower() or "save" in data["message"].lower()


class TestDownloadFileMissingOnDisk:
    """Line 91: document metadata exists but file is missing on disk -> 404."""

    def test_file_missing_on_disk_returns_404(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        import pathlib
        from config import config

        docs_path = str(tmp_path / "governance_documents.json")
        docs_dir = str(tmp_path / "governance_docs")
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_PATH", docs_path)
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_DIR", docs_dir)
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(docs_path).parent)

        # Write metadata for a document whose file does NOT exist on disk
        docs = [{"id": "ghost-doc", "filename": "ghost.pdf",
                 "stored_as": "ghost-doc_ghost.pdf",
                 "description": "", "uploaded_at": "2026-01-01T00:00:00",
                 "size": 100}]
        with open(docs_path, "w") as f:
            json.dump(docs, f)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.get("/api/v1/governance/documents/ghost-doc/download")
        assert r.status_code == 404
        data = json.loads(r.data)
        assert "not found" in data["message"].lower()


class TestDeleteSaveMetadataFails:
    """Line 111: _save_gov_documents returns False on delete -> 500."""

    def test_delete_save_failure_returns_500(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        import pathlib
        from config import config

        docs_path = str(tmp_path / "governance_documents.json")
        docs_dir = str(tmp_path / "governance_docs")
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_PATH", docs_path)
        monkeypatch.setattr(gov_constants, "GOV_DOCUMENTS_DIR", docs_dir)
        monkeypatch.setattr(config, "get_input_dir",
                            lambda: pathlib.Path(docs_path).parent)

        # First create a document via metadata
        os.makedirs(docs_dir, exist_ok=True)
        stored_name = "deltest_test.pdf"
        with open(os.path.join(docs_dir, stored_name), "w") as f:
            f.write("content")
        docs = [{"id": "deltest", "filename": "test.pdf",
                 "stored_as": stored_name,
                 "description": "", "uploaded_at": "2026-01-01T00:00:00",
                 "size": 7}]
        with open(docs_path, "w") as f:
            json.dump(docs, f)

        # Patch _save_gov_documents where it's imported in the documents module
        import routes.governance.documents as docs_mod
        monkeypatch.setattr(docs_mod, "_save_gov_documents", lambda docs: False)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post("/api/v1/governance/documents/deltest/delete")
        assert r.status_code == 500
        data = json.loads(r.data)
        assert data["status"] == "error"
