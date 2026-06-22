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

"""Coverage expansion tests for Block 2 governance route files (part 2).

Targets audit.py edge cases and PDF serving.
"""

import json
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# audit.py — missing edge cases and PDF serving
# ---------------------------------------------------------------------------

class TestAuditLogEdgeCases:

    def test_log_model_usage_inventory_not_found(self, gov_client, governance_env):
        """Line 57: inventory file empty/missing → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "usage"})
        assert r.status_code == 404

    def test_log_model_usage_audit_overflow_trim(self, gov_client, governance_env):
        """Line 82: audit log > 10000 entries gets trimmed."""
        big_log = [{"model_id": "X", "event_type": "usage"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                            json={"event_type": "test"})
        assert r.status_code == 200

        with open(governance_env["audit_path"]) as f:
            log = json.load(f)
        assert len(log) <= 10000

    def test_log_model_usage_save_failure(self, gov_client, governance_env):
        """Line 85: save failure → 500."""
        with patch("routes.governance.audit._save_audit_log", return_value=False):
            r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/audit",
                                json={"event_type": "usage"})
            assert r.status_code == 500


class TestValidationQuestionEdgeCases:

    def test_update_vq_inventory_not_found(self, gov_client, governance_env):
        """Line 130: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "Addressed", "evidence": "e", "reviewed_by": "u"})
        assert r.status_code == 404

    def test_update_vq_save_failure(self, gov_client, governance_env):
        """Line 176: save failure → 500."""
        with patch("routes.governance.audit_validation._save_inventory", return_value=False):
            r = gov_client.post(
                "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
                json={"status": "Addressed", "evidence": "test", "reviewed_by": "u"})
            assert r.status_code == 500

    def test_update_vq_audit_overflow(self, gov_client, governance_env):
        """Line 196: audit log overflow during VQ update."""
        big_log = [{"model_id": "X"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "Addressed", "evidence": "e", "reviewed_by": "u"})
        assert r.status_code == 200


class TestRiskRatingEdgeCases:

    def test_get_risk_rating_inventory_not_found(self, gov_client, governance_env):
        """Line 210: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        assert r.status_code == 404


class TestOverrideRiskRatingEdgeCases:

    def test_override_inventory_not_found(self, gov_client, governance_env):
        """Line 248: inventory not found → 404."""
        with open(governance_env["inv_path"], "w") as f:
            json.dump(None, f)

        r = gov_client.post("/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
                            json={"rating": "Acceptable", "reason": "test", "user": "u"})
        assert r.status_code == 404

    def test_override_save_failure(self, gov_client, governance_env):
        """Line 282: save failure → 500."""
        with patch("routes.governance.audit_validation._save_inventory", return_value=False):
            r = gov_client.post(
                "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
                json={"rating": "Acceptable", "reason": "test reason", "user": "u"})
            assert r.status_code == 500

    def test_override_audit_overflow(self, gov_client, governance_env):
        """Line 301: audit overflow during override."""
        big_log = [{"model_id": "X"} for _ in range(10001)]
        with open(governance_env["audit_path"], "w") as f:
            json.dump(big_log, f)

        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "Conditional", "reason": "test reason", "user": "u"})
        assert r.status_code == 200


class TestPdfServing:

    def test_model_doc_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 325: model documentation PDF served when file exists."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()
        pdf_file = doc_dir / "gev_hazard.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/documentation/pdf")
        assert r.status_code == 200

    def test_model_doc_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 323: valid model dir but PDF file missing → 404."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()  # dir exists but no PDF inside

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/documentation/pdf")
        assert r.status_code == 404
        assert "not found" in r.get_json()["message"].lower()

    def test_test_results_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 339: test results PDF served when file exists."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()
        pdf_file = doc_dir / "test_results.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/test-results/pdf")
        assert r.status_code == 200

    def test_test_results_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 337: valid model dir but test_results.pdf missing → 404."""
        import routes.governance._constants as gc

        doc_dir = tmp_path / "gev_hazard"
        doc_dir.mkdir()

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/models/MKM-GH-001/test-results/pdf")
        assert r.status_code == 404

    def test_mrc_tor_pdf_served(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 359: MRC ToR PDF served."""
        import routes.governance._constants as gc

        tor_dir = tmp_path / "mrc_tor"
        tor_dir.mkdir()
        pdf_file = tor_dir / "mrc_terms_of_reference.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/mrc/terms-of-reference/pdf")
        assert r.status_code == 200

    def test_mrc_tor_pdf_not_found(self, gov_client, governance_env, tmp_path, monkeypatch):
        """Line 357: MRC ToR PDF missing → 404."""
        import routes.governance._constants as gc

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/mrc/terms-of-reference/pdf")
        assert r.status_code == 404
