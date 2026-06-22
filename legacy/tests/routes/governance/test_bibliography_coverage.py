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

"""Coverage expansion tests for routes/governance/bibliography.py.

Targets uncovered lines: 74, 100, 112.
- 74: _save_bibliography returns False on add → 500
- 100: _save_bibliography returns False on update → 500
- 112: _save_bibliography returns False on delete → 500
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def bib_save_fail_client(tmp_path, monkeypatch):
    """Flask test client with bibliography data, where save always fails."""
    import routes.governance._constants as gov_constants

    bib_path = str(tmp_path / "bibliography.json")
    bib_data = {
        "references": [
            {"id": "ref-001", "author": "Smith", "year": 2024,
             "title": "Test", "journal": "", "doi": "", "url": "",
             "category": "Risk", "notes": ""}
        ],
        "categories": ["Risk"],
    }
    Path(bib_path).write_text(json.dumps(bib_data))
    monkeypatch.setattr(gov_constants, "BIBLIOGRAPHY_PATH", bib_path)

    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    return client, bib_path


class TestBibliographySaveFailures:
    """Exercise _save_bibliography returning False for all three write paths."""

    def test_add_save_failure_returns_500(self, bib_save_fail_client, monkeypatch):
        """Line 74: POST add when save fails."""
        client, _ = bib_save_fail_client
        import routes.governance.bibliography as bib_mod
        monkeypatch.setattr(bib_mod, "_save_bibliography", lambda data: False)
        r = client.post("/api/v1/governance/bibliography", json={
            "title": "New Paper", "author": "Doe"
        })
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"

    def test_update_save_failure_returns_500(self, bib_save_fail_client, monkeypatch):
        """Line 100: PUT update when save fails."""
        client, _ = bib_save_fail_client
        import routes.governance.bibliography as bib_mod
        monkeypatch.setattr(bib_mod, "_save_bibliography", lambda data: False)
        r = client.put("/api/v1/governance/bibliography/ref-001", json={
            "title": "Updated Title"
        })
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"

    def test_delete_save_failure_returns_500(self, bib_save_fail_client, monkeypatch):
        """Line 112: DELETE when save fails."""
        client, _ = bib_save_fail_client
        import routes.governance.bibliography as bib_mod
        monkeypatch.setattr(bib_mod, "_save_bibliography", lambda data: False)
        r = client.delete("/api/v1/governance/bibliography/ref-001")
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
