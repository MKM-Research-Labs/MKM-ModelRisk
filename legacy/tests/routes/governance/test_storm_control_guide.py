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
Tests for GET /governance/<guide_key>/guide/pdf — User Guide PDF serving.

Covers all six user guides (storm-control + five workflow guides).
"""

import pytest


# All guides and their directory/file mappings
_ALL_GUIDES = {
    "storm-control":        ("storm_control",        "storm_control_guide.pdf"),
    "gauge-prs-pricing":    ("gauge_prs_pricing",    "gauge_prs_pricing_guide.pdf"),
    "property-prs-pricing": ("property_prs_pricing", "property_prs_pricing_guide.pdf"),
    "market-making":        ("market_making",        "market_making_guide.pdf"),
    "eod-process":          ("eod_process",          "eod_process_guide.pdf"),
    "stress-testing":       ("stress_testing",       "stress_testing_guide.pdf"),
}


class TestUserGuidePdfServing:
    """Generic user guide PDF serving endpoint."""

    @pytest.mark.parametrize("guide_key,doc_dir,pdf_name", [
        (k, v[0], v[1]) for k, v in _ALL_GUIDES.items()
    ])
    def test_serves_pdf_when_present(self, gov_client, governance_env,
                                     tmp_path, monkeypatch,
                                     guide_key, doc_dir, pdf_name):
        """Route returns 200 and application/pdf when the PDF exists."""
        import routes.governance._constants as gc

        guide_dir = tmp_path / doc_dir
        guide_dir.mkdir()
        pdf_file = guide_dir / pdf_name
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get(f"/api/v1/governance/{guide_key}/guide/pdf")
        assert r.status_code == 200, (
            f"{guide_key}: expected 200, got {r.status_code}"
        )
        assert r.content_type == "application/pdf"

    @pytest.mark.parametrize("guide_key,doc_dir,pdf_name", [
        (k, v[0], v[1]) for k, v in _ALL_GUIDES.items()
    ])
    def test_returns_404_when_missing(self, gov_client, governance_env,
                                      tmp_path, monkeypatch,
                                      guide_key, doc_dir, pdf_name):
        """Route returns 404 with build instructions when PDF missing."""
        import routes.governance._constants as gc

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get(f"/api/v1/governance/{guide_key}/guide/pdf")
        assert r.status_code == 404
        data = r.get_json()
        assert data["status"] == "error"
        assert doc_dir in data["message"], (
            f"{guide_key}: expected '{doc_dir}' in message, got: {data['message']}"
        )

    def test_unknown_guide_returns_404(self, gov_client, governance_env,
                                       tmp_path, monkeypatch):
        """Unknown guide key returns 404."""
        import routes.governance._constants as gc

        monkeypatch.setattr(gc, "_docs_dir", str(tmp_path))
        monkeypatch.setattr("routes.governance.audit._docs_dir", str(tmp_path))

        r = gov_client.get("/api/v1/governance/nonexistent-guide/guide/pdf")
        assert r.status_code == 404
        data = r.get_json()
        assert "unknown" in data["message"].lower()
