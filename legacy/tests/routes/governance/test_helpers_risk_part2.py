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
Tests for governance helpers: _calculate_risk_rating and _vq_summary (part 2).
"""

from datetime import datetime, timedelta

import pytest


# ===========================================================================
# _stable_id / _pdf_entry / _discover_audit_docs / _discover_model_docs
# ===========================================================================

class TestStableId:

    def test_returns_8_char_hex(self):
        from routes.governance._helpers_risk import _stable_id
        result = _stable_id("/some/path.pdf")
        assert len(result) == 8
        assert all(c in "0123456789abcdef" for c in result)

    def test_deterministic(self):
        from routes.governance._helpers_risk import _stable_id
        assert _stable_id("x") == _stable_id("x")


class TestPdfEntry:

    def test_normal_file(self, tmp_path):
        from routes.governance._helpers_risk import _pdf_entry
        f = tmp_path / "test.pdf"
        f.write_bytes(b"x" * 42)
        entry = _pdf_entry(str(f), "My PDF", "audit")
        assert entry["filename"] == "test.pdf"
        assert entry["size"] == 42
        assert entry["description"] == "My PDF"
        assert entry["source"] == "audit"
        assert len(entry["id"]) == 8

    def test_oserror_gives_zero_size(self, monkeypatch):
        import os
        from routes.governance._helpers_risk import _pdf_entry
        monkeypatch.setattr(os.path, "getsize", lambda _: (_ for _ in ()).throw(OSError("boom")))
        entry = _pdf_entry("/nonexistent/file.pdf", "desc", "audit")
        assert entry["size"] == 0


class TestDiscoverAuditDocs:

    def test_missing_dir_returns_empty(self, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "AUDIT_REPORTS_DIR", "/tmp/nonexistent_audit_dir_test")
        result = _helpers_risk._discover_audit_docs()
        assert result == []

    def test_finds_known_pdfs(self, tmp_path, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "AUDIT_REPORTS_DIR", str(tmp_path))
        (tmp_path / "full_audit_report.pdf").write_bytes(b"pdf")
        (tmp_path / "some_other.pdf").write_bytes(b"pdf2")
        result = _helpers_risk._discover_audit_docs()
        assert len(result) == 2
        labels = [r["description"] for r in result]
        assert "Full Audit Report" in labels
        # Unknown PDF gets title-cased label
        assert any("Some Other" in l for l in labels)


class TestDiscoverModelDocs:

    def test_missing_dir_returns_empty(self, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "_docs_dir", "/tmp/nonexistent_docs_dir_test")
        result = _helpers_risk._discover_model_docs()
        assert result == []

    def test_finds_model_pdfs(self, tmp_path, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "_docs_dir", str(tmp_path))
        monkeypatch.setattr(_constants, "_MODEL_DOC_DIRS", {"MKM-TEST": "test_model"})
        model_dir = tmp_path / "test_model"
        model_dir.mkdir()
        (model_dir / "test_results.pdf").write_bytes(b"pdf")
        (model_dir / "analysis.pdf").write_bytes(b"pdf")
        result = _helpers_risk._discover_model_docs()
        assert len(result) == 2
        descs = [r["description"] for r in result]
        assert any("Test Results" in d for d in descs)
        assert any("Analysis" in d for d in descs)

    def test_skips_non_directory(self, tmp_path, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "_docs_dir", str(tmp_path))
        monkeypatch.setattr(_constants, "_MODEL_DOC_DIRS", {})
        (tmp_path / "stray_file.txt").write_text("not a dir")
        result = _helpers_risk._discover_model_docs()
        assert result == []

    def test_unknown_model_uses_dirname(self, tmp_path, monkeypatch):
        from routes.governance import _helpers_risk, _constants
        monkeypatch.setattr(_constants, "_docs_dir", str(tmp_path))
        monkeypatch.setattr(_constants, "_MODEL_DOC_DIRS", {})
        d = tmp_path / "my_new_model"
        d.mkdir()
        (d / "custom_report.pdf").write_bytes(b"pdf")
        result = _helpers_risk._discover_model_docs()
        assert len(result) == 1
        assert result[0]["description"].startswith("My New Model")
