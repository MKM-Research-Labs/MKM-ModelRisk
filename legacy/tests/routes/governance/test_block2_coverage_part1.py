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

"""Coverage expansion tests for Block 2 governance route files (part 1).

Targets MRC save failures, document upload/serve.
"""

import io
import json
from unittest.mock import patch

import pytest

from tests.routes.governance.conftest import create_meeting


# ---------------------------------------------------------------------------
# mrc.py — save failures + document upload/serve (lines 108,144,164-186,196)
# ---------------------------------------------------------------------------

class TestMrcCreateSaveFailure:

    def test_create_meeting_save_failure(self, mrc_client, mrc_env):
        """Line 108: _save_meetings fails → 500."""
        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post("/api/v1/governance/mrc/meetings",
                                json={"title": "Failing"})
            assert r.status_code == 500
            assert "Failed" in r.get_json()["message"]


class TestMrcUpdateSaveFailure:

    def test_update_meeting_save_failure(self, mrc_client, mrc_env):
        """Line 144: _save_meetings fails on update → 500."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/update",
                                json={"title": "Updated"})
            assert r.status_code == 500


class TestMrcDocumentUpload:

    def test_upload_document_success(self, mrc_client, mrc_env):
        """Lines 164-186: upload a file to a meeting."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {
            "file": (io.BytesIO(b"test content"), "report.pdf"),
            "user": "Tester",
            "description": "Test doc",
        }
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 200
        doc = r.get_json()["document"]
        assert doc["filename"] == "report.pdf"

    def test_upload_document_meeting_not_found(self, mrc_client, mrc_env):
        """Line 155: meeting not found → 404."""
        data = {"file": (io.BytesIO(b"x"), "f.pdf")}
        r = mrc_client.post("/api/v1/governance/mrc/meetings/nonexistent/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 404

    def test_upload_document_no_file(self, mrc_client, mrc_env):
        """Line 158: no file in request → 400."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data={}, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_upload_document_empty_filename(self, mrc_client, mrc_env):
        """Line 162: file with empty filename → 400."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"x"), "")}
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 400

    def test_upload_document_save_failure(self, mrc_client, mrc_env):
        """Line 184: save failure after upload → 500."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"x"), "f.pdf")}
        with patch("routes.governance.mrc._save_meetings", return_value=False):
            r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                                data=data, content_type="multipart/form-data")
            assert r.status_code == 500


class TestMrcDocumentUploadNoDocsKey:

    def test_upload_creates_documents_list(self, mrc_client, mrc_env):
        """Line 179: meeting without 'documents' key gets it created."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        # Manually remove the documents key from the stored meeting
        import json
        with open(mrc_env["meetings_path"]) as f:
            meetings = json.load(f)
        del meetings[-1]["documents"]
        with open(mrc_env["meetings_path"], "w") as f:
            json.dump(meetings, f)

        data = {"file": (io.BytesIO(b"test"), "doc.pdf")}
        r = mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                            data=data, content_type="multipart/form-data")
        assert r.status_code == 200


class TestMrcDocumentServe:

    def test_get_meeting_document_success(self, mrc_client, mrc_env):
        """Line 196: serve an uploaded document."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        data = {"file": (io.BytesIO(b"PDF content"), "report.pdf")}
        mrc_client.post(f"/api/v1/governance/mrc/meetings/{mid}/documents",
                        data=data, content_type="multipart/form-data")

        r = mrc_client.get(f"/api/v1/governance/mrc/meetings/{mid}/documents/report.pdf")
        assert r.status_code == 200

    def test_get_meeting_document_not_found(self, mrc_client, mrc_env):
        """Line 195: document file not found → 404."""
        _, body = create_meeting(mrc_client)
        mid = body["meeting"]["id"]

        r = mrc_client.get(f"/api/v1/governance/mrc/meetings/{mid}/documents/nonexistent.pdf")
        assert r.status_code == 404
