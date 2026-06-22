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

"""Coverage expansion tests for routes/governance/compliance.py.

Targets uncovered lines: 86, 96, 136, 164, 190, 195, 224, 244.
- 86: _save_bcbs239 returns False → 500
- 96: BCBS 239 PDF not found → 404
- 136: _save_raci returns False for role update → 500
- 164: _load_raci returns None for activity update → 404
- 190: tier_emphasis field updated on activity
- 195: _save_raci returns False for activity update → 500
- 224: _load_raci returns None for escalation update → 404
- 244: _save_raci returns False for escalation update → 500
"""

import copy
import json
from pathlib import Path

import pytest


# ===========================================================================
# Local fixtures (bcbs_client/bcbs_client_no_data are not in conftest.py)
# ===========================================================================

_BASE_BCBS239 = {
    "assessment_date": "2026-01-01",
    "principles": [
        {
            "id": 1, "name": "Governance", "description": "Board oversight",
            "score": 3, "status": "Largely Compliant",
            "evidence": "", "gaps": "", "remediation": "", "target_date": "",
        },
    ],
}


@pytest.fixture
def bcbs_env(tmp_path, monkeypatch):
    import routes.governance._constants as gov_constants
    bcbs_path = str(tmp_path / "bcbs239_assessment.json")
    Path(bcbs_path).write_text(json.dumps(copy.deepcopy(_BASE_BCBS239)))
    monkeypatch.setattr(gov_constants, "BCBS239_PATH", bcbs_path)
    return {"bcbs_path": bcbs_path, "tmp_path": tmp_path}


@pytest.fixture
def bcbs_client(bcbs_env, monkeypatch):
    from config import config
    monkeypatch.setattr(config, "get_input_dir", lambda: bcbs_env["tmp_path"])
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), bcbs_env


@pytest.fixture
def no_data_client(tmp_path, monkeypatch):
    """Flask test client where BCBS 239 and RACI files do not exist."""
    import routes.governance._constants as gov_constants
    from config import config
    monkeypatch.setattr(gov_constants, "BCBS239_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(gov_constants, "RACI_PATH", str(tmp_path / "missing_raci.json"))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)
    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# ===========================================================================
# Line 86: _save_bcbs239 returns False → 500
# ===========================================================================

class TestBcbs239SaveFailure:

    def test_save_failure_returns_500(self, bcbs_client, monkeypatch):
        client, env = bcbs_client
        import routes.governance.compliance as compliance_mod
        monkeypatch.setattr(compliance_mod, "_save_bcbs239", lambda data: False)
        r = client.post(
            "/api/v1/governance/bcbs239/principles/1/update",
            json={"score": 4}
        )
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


# ===========================================================================
# Line 96: BCBS 239 PDF not found → 404
# ===========================================================================

class TestBcbs239PdfNotFound:

    def test_pdf_not_generated_returns_404(self, bcbs_client, monkeypatch):
        client, env = bcbs_client
        # _docs_dir is imported into compliance.py from _constants at module level,
        # so we must patch it on the compliance module itself.
        import routes.governance.compliance as compliance_mod
        monkeypatch.setattr(compliance_mod, "_docs_dir", str(env["tmp_path"] / "docs"))
        r = client.get("/api/v1/governance/bcbs239/pdf")
        assert r.status_code == 404
        assert "not yet generated" in r.get_json()["message"]


# ===========================================================================
# Line 136: _save_raci returns False for role update → 500
# ===========================================================================

class TestRaciRoleSaveFailure:

    def test_save_raci_failure_returns_500(self, raci_client, monkeypatch):
        import routes.governance.compliance as compliance_mod
        monkeypatch.setattr(compliance_mod, "_save_raci", lambda data: False)
        r = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "New Person"}
        )
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


# ===========================================================================
# Line 164: _load_raci returns None for activity update → 404
# ===========================================================================

class TestRaciActivityNoData:

    def test_no_raci_data_returns_404(self, no_data_client, monkeypatch):
        r = no_data_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "operations_lead"}
        )
        assert r.status_code == 404


# ===========================================================================
# Line 190: tier_emphasis field updated
# ===========================================================================

class TestRaciActivityTierEmphasis:

    def test_tier_emphasis_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"tier_emphasis": "Tier 1 focus"}
        )
        assert r.status_code == 200
        activities = r.get_json()["raci"]["activities"]
        assert activities[0]["tier_emphasis"] == "Tier 1 focus"


# ===========================================================================
# Line 195: _save_raci returns False for activity update → 500
# ===========================================================================

class TestRaciActivitySaveFailure:

    def test_save_raci_failure_returns_500(self, raci_client, monkeypatch):
        import routes.governance.compliance as compliance_mod
        monkeypatch.setattr(compliance_mod, "_save_raci", lambda data: False)
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"notes": "Updated note"}
        )
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


# ===========================================================================
# Line 224: _load_raci returns None for escalation update → 404
# ===========================================================================

class TestRaciEscalationNoData:

    def test_no_raci_data_returns_404(self, no_data_client, monkeypatch):
        r = no_data_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"tier_threshold": {"1": "Immediate"}}
        )
        assert r.status_code == 404


# ===========================================================================
# Line 244: _save_raci returns False for escalation update → 500
# ===========================================================================

class TestRaciEscalationSaveFailure:

    def test_save_raci_failure_returns_500(self, raci_client, monkeypatch):
        import routes.governance.compliance as compliance_mod
        monkeypatch.setattr(compliance_mod, "_save_raci", lambda data: False)
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"response_required": "Escalate"}
        )
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"
