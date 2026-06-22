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
Tests for governance helpers: BCBS239, RACI, gov documents, bibliography I/O.
"""

import json


def _write_json(path, data):
    path.write_text(json.dumps(data))


# ===========================================================================
# _load_bcbs239 / _save_bcbs239
# ===========================================================================

class TestLoadBcbs239:

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_bcbs239
        monkeypatch.setattr(c, "BCBS239_PATH", str(tmp_path / "no.json"))
        assert _load_bcbs239() is None

    def test_loads_valid_data(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_bcbs239
        p = tmp_path / "bcbs.json"
        _write_json(p, {"principles": []})
        monkeypatch.setattr(c, "BCBS239_PATH", str(p))
        result = _load_bcbs239()
        assert "principles" in result


class TestSaveBcbs239:

    def test_saves_data(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_bcbs239
        p = tmp_path / "bcbs.json"
        monkeypatch.setattr(c, "BCBS239_PATH", str(p))
        assert _save_bcbs239({"principles": []}) is True

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_bcbs239
        monkeypatch.setattr(c, "BCBS239_PATH", str(tmp_path))
        assert _save_bcbs239({}) is False


# ===========================================================================
# _load_raci / _save_raci
# ===========================================================================

class TestLoadRaci:

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_raci
        monkeypatch.setattr(c, "RACI_PATH", str(tmp_path / "no.json"))
        assert _load_raci() is None

    def test_loads_valid_data(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_raci
        p = tmp_path / "raci.json"
        _write_json(p, {"roles": []})
        monkeypatch.setattr(c, "RACI_PATH", str(p))
        result = _load_raci()
        assert "roles" in result


class TestSaveRaci:

    def test_saves_data(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_raci
        p = tmp_path / "raci.json"
        monkeypatch.setattr(c, "RACI_PATH", str(p))
        assert _save_raci({"roles": []}) is True

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_raci
        monkeypatch.setattr(c, "RACI_PATH", str(tmp_path))
        assert _save_raci({}) is False


# ===========================================================================
# _load_gov_documents / _save_gov_documents
# ===========================================================================

class TestLoadGovDocuments:

    def test_returns_empty_list_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_gov_documents
        monkeypatch.setattr(c, "GOV_DOCUMENTS_PATH", str(tmp_path / "no.json"))
        assert _load_gov_documents() == []

    def test_loads_documents(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_gov_documents
        p = tmp_path / "gov_docs.json"
        _write_json(p, [{"doc_id": "D1"}])
        monkeypatch.setattr(c, "GOV_DOCUMENTS_PATH", str(p))
        assert _load_gov_documents()[0]["doc_id"] == "D1"


class TestSaveGovDocuments:

    def test_saves_documents(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_gov_documents
        p = tmp_path / "gov_docs.json"
        monkeypatch.setattr(c, "GOV_DOCUMENTS_PATH", str(p))
        assert _save_gov_documents([{"doc_id": "D1"}]) is True

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_gov_documents
        monkeypatch.setattr(c, "GOV_DOCUMENTS_PATH", str(tmp_path))
        assert _save_gov_documents([]) is False


# ===========================================================================
# _load_bibliography / _save_bibliography
# ===========================================================================

class TestLoadBibliography:

    def test_returns_default_when_missing(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_bibliography
        monkeypatch.setattr(c, "BIBLIOGRAPHY_PATH", str(tmp_path / "no.json"))
        result = _load_bibliography()
        assert result == {"references": [], "categories": []}

    def test_loads_bibliography(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _load_bibliography
        p = tmp_path / "bib.json"
        _write_json(p, {"references": [{"id": "R1"}], "categories": ["A"]})
        monkeypatch.setattr(c, "BIBLIOGRAPHY_PATH", str(p))
        result = _load_bibliography()
        assert result["references"][0]["id"] == "R1"


class TestSaveBibliography:

    def test_saves_bibliography(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_bibliography
        p = tmp_path / "bib.json"
        monkeypatch.setattr(c, "BIBLIOGRAPHY_PATH", str(p))
        assert _save_bibliography({"references": [], "categories": []}) is True

    def test_returns_false_on_oserror(self, tmp_path, monkeypatch):
        import routes.governance._constants as c
        from routes.governance._helpers import _save_bibliography
        monkeypatch.setattr(c, "BIBLIOGRAPHY_PATH", str(tmp_path))
        assert _save_bibliography({}) is False
