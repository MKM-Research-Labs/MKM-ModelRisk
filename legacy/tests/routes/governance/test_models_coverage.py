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

"""Coverage expansion tests for routes/governance/models.py.

Targets uncovered lines: 51, 63, 71, 136, 176, 197, 224.
- 51: _load_inventory returns empty/None for get_models → 404
- 63: review_status = "Overdue" (next_review_date in the past)
- 71: review_status = "Not Scheduled" (no next_review_date)
- 136: _load_inventory returns None for update → 404
- 176: _save_inventory returns False → 500
- 197: audit log exceeds 10000 entries → truncation
- 224: _load_inventory returns None for get_model_detail → 404
"""

import copy
import json
import pathlib

import pytest


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture
def gov_client_no_inventory(tmp_path, monkeypatch):
    """Flask test client where the inventory file does not exist."""
    import routes.governance._constants as gov_constants
    from config import config

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", str(tmp_path / "audit.json"))
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def gov_client_overdue(tmp_path, monkeypatch):
    """Flask test client with a model that has an overdue review date."""
    import routes.governance._constants as gov_constants
    from config import config
    from tests.routes.governance.conftest import _BASE_INVENTORY, _BASE_MODEL

    inv = copy.deepcopy(_BASE_INVENTORY)
    inv["models"][0]["next_review_date"] = "2020-01-01"  # In the past → Overdue

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")
    with open(inv_path, "w") as f:
        json.dump(inv, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def gov_client_no_review_date(tmp_path, monkeypatch):
    """Flask test client with a model that has no next_review_date."""
    import routes.governance._constants as gov_constants
    from config import config
    from tests.routes.governance.conftest import _BASE_INVENTORY

    inv = copy.deepcopy(_BASE_INVENTORY)
    inv["models"][0]["next_review_date"] = None  # Not scheduled

    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")
    with open(inv_path, "w") as f:
        json.dump(inv, f)
    with open(audit_path, "w") as f:
        json.dump([], f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def gov_client_large_audit(tmp_path, monkeypatch):
    """Flask test client with an audit log that has exactly 10000 entries."""
    import routes.governance._constants as gov_constants
    from config import config
    from tests.routes.governance.conftest import _BASE_INVENTORY

    inv = copy.deepcopy(_BASE_INVENTORY)
    inv_path = str(tmp_path / "model_inventory.json")
    audit_path = str(tmp_path / "model_audit_log.json")

    with open(inv_path, "w") as f:
        json.dump(inv, f)
    # Create exactly 10000 audit entries to trigger truncation on next append
    audit_entries = [{"timestamp": f"2026-01-01T00:00:{i:05d}", "model_id": "X",
                      "event_type": "test"} for i in range(10000)]
    with open(audit_path, "w") as f:
        json.dump(audit_entries, f)

    monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
    monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
    monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

    from server import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client(), audit_path


# ===========================================================================
# Line 51: get_models → inventory not found → 404
# ===========================================================================

class TestGetModelsNoInventory:

    def test_no_inventory_returns_404(self, gov_client_no_inventory):
        r = gov_client_no_inventory.get("/api/v1/governance/models")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"


# ===========================================================================
# Line 63: review_status = "Overdue"
# ===========================================================================

class TestGetModelsOverdueReview:

    def test_overdue_review_status(self, gov_client_overdue):
        r = gov_client_overdue.get("/api/v1/governance/models")
        assert r.status_code == 200
        model = r.get_json()["models"][0]
        assert model["review_status"] == "Overdue"


# ===========================================================================
# Line 71: review_status = "Not Scheduled"
# ===========================================================================

class TestGetModelsNotScheduled:

    def test_not_scheduled_review_status(self, gov_client_no_review_date):
        r = gov_client_no_review_date.get("/api/v1/governance/models")
        assert r.status_code == 200
        model = r.get_json()["models"][0]
        assert model["review_status"] == "Not Scheduled"


# ===========================================================================
# Line 136: update_model_field → no inventory → 404
# ===========================================================================

class TestUpdateModelNoInventory:

    def test_no_inventory_returns_404(self, gov_client_no_inventory):
        r = gov_client_no_inventory.post(
            "/api/v1/governance/models/MKM-TEST-001/update",
            json={"field": "owner", "value": "X", "reason": "Test"}
        )
        assert r.status_code == 404


# ===========================================================================
# Line 176: _save_inventory returns False → 500
# ===========================================================================

class TestUpdateModelSaveFailure:

    def test_save_failure_returns_500(self, gov_client, monkeypatch):
        import routes.governance.models as models_mod
        monkeypatch.setattr(models_mod, "_save_inventory", lambda data: False)
        r = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/update",
            json={"field": "owner", "value": "New Owner", "reason": "Transfer"}
        )
        assert r.status_code == 500
        assert r.get_json()["status"] == "error"


# ===========================================================================
# Line 197: audit log > 10000 entries → truncation
# ===========================================================================

class TestAuditLogTruncation:

    def test_audit_log_truncated_to_10000(self, gov_client_large_audit):
        client, audit_path = gov_client_large_audit
        # This update will append to the 10000-entry log, triggering truncation
        r = client.post(
            "/api/v1/governance/models/MKM-TEST-001/update",
            json={"field": "owner", "value": "Truncation Test", "reason": "Test truncation"}
        )
        assert r.status_code == 200
        # Verify audit log was truncated
        with open(audit_path) as f:
            entries = json.load(f)
        assert len(entries) == 10000
        # The last entry should be our new one
        assert entries[-1]["event_type"] == "field_update"


# ===========================================================================
# Line 224: get_model_detail → no inventory → 404
# ===========================================================================

class TestGetModelDetailNoInventory:

    def test_no_inventory_returns_404(self, gov_client_no_inventory):
        r = gov_client_no_inventory.get("/api/v1/governance/models/MKM-TEST-001")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"
