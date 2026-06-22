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
Tests for routes.governance.compliance — RACI matrix routes (part 2).

Covers: update_raci_role, update_raci_activity, update_raci_escalation.
"""

import pytest


# ===========================================================================
# RACI endpoint coverage gaps (using raci_client from conftest)
# ===========================================================================

class TestUpdateRaciRoleExtra:
    """Additional tests for update_raci_role to hit missing branches."""

    def test_no_raci_file_returns_404(self, tmp_path, monkeypatch):
        import routes.governance._constants as gov_constants
        from config import config

        inv_path = str(tmp_path / "model_inventory.json")
        audit_path = str(tmp_path / "model_audit_log.json")
        import json
        with open(inv_path, "w") as f:
            json.dump({"metadata": {}, "models": []}, f)
        with open(audit_path, "w") as f:
            json.dump([], f)

        monkeypatch.setattr(gov_constants, "INVENTORY_PATH", inv_path)
        monkeypatch.setattr(gov_constants, "AUDIT_LOG_PATH", audit_path)
        monkeypatch.setattr(gov_constants, "RACI_PATH", "/nonexistent/raci.json")
        monkeypatch.setattr(config, "get_input_dir", lambda: tmp_path)

        from server import create_app
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        r = client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "New Person"}
        )
        assert r.status_code == 404

    def test_role_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/nonexistent_role/update",
            json={"assigned_to": "Someone"}
        )
        assert r.status_code == 404

    def test_valid_role_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "New Lead", "backup": "Deputy"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_backup_field_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/model_owner/update",
            json={"assigned_to": "Owner A", "backup": "Owner B"}
        )
        roles = r.get_json()["raci"]["roles"]
        owner = next(x for x in roles if x["role_id"] == "model_owner")
        assert owner["backup"] == "Owner B"

    def test_response_has_audit_entry(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/roles/operations_lead/update",
            json={"assigned_to": "X"}
        )
        assert "audit_entry" in r.get_json()


class TestUpdateRaciActivityExtra:
    """Additional tests for update_raci_activity to hit missing branches."""

    def test_activity_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-GHOST/update",
            json={"R": "operations_lead"}
        )
        assert r.status_code == 404

    def test_invalid_role_id_returns_400(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "nonexistent_role"}
        )
        assert r.status_code == 400

    def test_valid_activity_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"R": "model_owner", "notes": "Updated"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_notes_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"notes": "New note"}
        )
        activities = r.get_json()["raci"]["activities"]
        assert activities[0]["notes"] == "New note"

    def test_null_raci_code_allowed(self, raci_client):
        """Setting C or I to None (null) is valid."""
        r = raci_client.post(
            "/api/v1/governance/raci/activities/ACT-01/update",
            json={"C": None, "I": None}
        )
        assert r.status_code == 200


class TestUpdateRaciEscalationExtra:
    """Tests for update_raci_escalation."""

    def test_trigger_not_found_returns_404(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/GHOST/update",
            json={"tier_threshold": {"1": "Immediate"}}
        )
        assert r.status_code == 404

    def test_valid_escalation_update_returns_success(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"tier_threshold": {"1": "Immediate", "2": "Within 4 hours"},
                  "response_required": "Full investigation"}
        )
        assert r.status_code == 200
        assert r.get_json()["status"] == "success"

    def test_escalation_tier_threshold_updated(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"tier_threshold": {"1": "Immediate"}}
        )
        triggers = r.get_json()["raci"]["escalation_triggers"]
        assert triggers[0]["tier_threshold"]["1"] == "Immediate"

    def test_response_has_audit_entry(self, raci_client):
        r = raci_client.post(
            "/api/v1/governance/raci/escalation-triggers/ESC-01/update",
            json={"response_required": "Updated response"}
        )
        assert "audit_entry" in r.get_json()
