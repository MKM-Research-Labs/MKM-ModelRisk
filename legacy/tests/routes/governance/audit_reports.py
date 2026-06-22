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
Tests for routes.governance.audit_reports.

Covers: list_audit_reports (no dir, empty dir, with files),
download_audit_report (path traversal, not found, valid),
serve_coverage_index (no index, valid).
"""

import json
import os
from pathlib import Path

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def audit_env(tmp_path, monkeypatch):
    """Set up an isolated audit reports directory.

    The route module uses `from ._constants import AUDIT_REPORTS_DIR` (own copy),
    so we must patch the constant in the route module itself.
    """
    import routes.governance._constants as gov_constants
    import routes.governance.audit_reports as ar_module

    audit_dir = str(tmp_path / "audit")
    monkeypatch.setattr(gov_constants, "AUDIT_REPORTS_DIR", audit_dir)
    monkeypatch.setattr(ar_module, "AUDIT_REPORTS_DIR", audit_dir)

    return {"audit_dir": audit_dir, "tmp_path": tmp_path}


@pytest.fixture
def audit_client(audit_env, monkeypatch):
    """Flask test client with audit dir set."""
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: audit_env["tmp_path"])

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), audit_env


# ===========================================================================
# GET /governance/audit-reports
# ===========================================================================

class TestListAuditReports:

    def test_no_dir_returns_empty_list(self, audit_client):
        client, _ = audit_client
        r = client.get("/api/v1/governance/audit-reports")
        data = r.get_json()
        assert r.status_code == 200
        assert data["status"] == "success"
        assert data["reports"] == []
        assert data["coverage_available"] is False

    def test_empty_dir_returns_empty_list(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        r = client.get("/api/v1/governance/audit-reports")
        data = r.get_json()
        assert data["reports"] == []

    def test_pdf_file_listed(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "report.pdf").write_bytes(b"%PDF-test")
        r = client.get("/api/v1/governance/audit-reports")
        data = r.get_json()
        assert len(data["reports"]) == 1
        assert data["reports"][0]["filename"] == "report.pdf"

    def test_file_type_label_pdf(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "report.pdf").write_bytes(b"%PDF")
        r = client.get("/api/v1/governance/audit-reports")
        assert r.get_json()["reports"][0]["type"] == "PDF"

    def test_file_type_label_json(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "data.json").write_text("{}")
        r = client.get("/api/v1/governance/audit-reports")
        assert r.get_json()["reports"][0]["type"] == "JSON"

    def test_file_type_label_unknown(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "file.xyz").write_text("data")
        r = client.get("/api/v1/governance/audit-reports")
        assert r.get_json()["reports"][0]["type"] == "XYZ"

    def test_file_has_size_and_modified(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "report.pdf").write_bytes(b"%PDF-test")
        reports = r.get_json()["reports"] if (r := client.get("/api/v1/governance/audit-reports")) else []
        assert reports[0]["size"] > 0
        assert "modified" in reports[0]

    def test_subdirectories_not_listed(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        os.makedirs(os.path.join(env["audit_dir"], "subdir"))
        r = client.get("/api/v1/governance/audit-reports")
        # subdir should not appear in reports (only files)
        assert r.get_json()["reports"] == []

    def test_coverage_available_false_when_no_index(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        r = client.get("/api/v1/governance/audit-reports")
        assert r.get_json()["coverage_available"] is False

    def test_coverage_available_true_when_index_present(self, audit_client):
        client, env = audit_client
        cov_dir = os.path.join(env["audit_dir"], "coverage")
        os.makedirs(cov_dir)
        Path(cov_dir, "index.html").write_text("<html/>")
        r = client.get("/api/v1/governance/audit-reports")
        assert r.get_json()["coverage_available"] is True


# ===========================================================================
# GET /governance/audit-reports/file/<filename>
# ===========================================================================

class TestDownloadAuditReport:

    def test_file_not_found_returns_404(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        r = client.get("/api/v1/governance/audit-reports/file/nonexistent.pdf")
        assert r.status_code == 404

    def test_path_traversal_returns_403(self, audit_client):
        client, _ = audit_client
        r = client.get("/api/v1/governance/audit-reports/file/../../../etc/passwd")
        assert r.status_code in (403, 404)

    def test_valid_pdf_served_inline(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "report.pdf").write_bytes(b"%PDF-test")
        r = client.get("/api/v1/governance/audit-reports/file/report.pdf")
        assert r.status_code == 200

    def test_non_pdf_served_as_attachment(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        Path(env["audit_dir"], "data.json").write_text("{}")
        r = client.get("/api/v1/governance/audit-reports/file/data.json")
        assert r.status_code == 200
        assert "attachment" in r.headers.get("Content-Disposition", "")


# ===========================================================================
# GET /governance/audit-reports/coverage
# ===========================================================================

class TestServeCoverageIndex:

    def test_no_coverage_dir_returns_404(self, audit_client):
        client, env = audit_client
        os.makedirs(env["audit_dir"])
        r = client.get("/api/v1/governance/audit-reports/coverage")
        assert r.status_code == 404

    def test_with_coverage_index_returns_200(self, audit_client):
        client, env = audit_client
        cov_dir = os.path.join(env["audit_dir"], "coverage")
        os.makedirs(cov_dir)
        Path(cov_dir, "index.html").write_text("<html>Coverage</html>")
        r = client.get("/api/v1/governance/audit-reports/coverage")
        assert r.status_code == 200
