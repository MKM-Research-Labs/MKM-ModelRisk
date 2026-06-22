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
Tests for routes.governance.models — model inventory CRUD.

Covers: get_models (list + review status branches), update_model_field
(not found, invalid field, no reason, invalid choice value, valid),
get_editable_fields, get_model_detail (not found, found).
"""

import pytest


# All tests use the gov_client fixture from conftest.py.


# ===========================================================================
# GET /governance/models
# ===========================================================================

class TestGetModels:

    def test_returns_200(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        assert r.status_code == 200

    def test_returns_success_status(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        assert r.get_json()["status"] == "success"

    def test_returns_models_list(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        data = r.get_json()
        assert "models" in data
        assert data["total_models"] >= 1

    def test_model_has_review_status(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        model = r.get_json()["models"][0]
        assert "review_status" in model
        # MKM-TEST-001 has next_review_date: 2027-01-15 (future) → On Track or Upcoming
        assert model["review_status"] in ("On Track", "Upcoming", "Due Soon", "Overdue")

    def test_tier_distribution(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        data = r.get_json()
        assert "tier_distribution" in data

    def test_category_distribution(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        data = r.get_json()
        assert "category_distribution" in data

    def test_response_has_metadata(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        data = r.get_json()
        assert "metadata" in data

    def test_model_has_validation_coverage(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        model = r.get_json()["models"][0]
        assert "validation_coverage" in model

    def test_model_has_risk_rating(self, gov_client):
        r = gov_client.get("/api/v1/governance/models")
        model = r.get_json()["models"][0]
        assert "risk_rating" in model


# ===========================================================================
# POST /governance/models/<model_id>/update
# ===========================================================================

class TestUpdateModelField:

    _URL = "/api/v1/governance/models/MKM-TEST-001/update"

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.post(
            "/api/v1/governance/models/GHOST/update",
            json={"field": "owner", "value": "New Owner", "reason": "Reassignment"}
        )
        assert r.status_code == 404

    def test_invalid_field_returns_400(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "nonexistent_field", "value": "x", "reason": "test"
        })
        assert r.status_code == 400
        assert r.get_json()["status"] == "error"

    def test_no_reason_returns_400(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "owner", "value": "New Owner", "reason": ""
        })
        assert r.status_code == 400

    def test_empty_value_returns_400(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "owner", "value": "", "reason": "Test reason"
        })
        assert r.status_code == 400

    def test_invalid_choice_value_returns_400(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "rag_rating", "value": "Purple",
            "reason": "Testing invalid choice"
        })
        assert r.status_code == 400

    def test_valid_text_field_update_returns_success(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "owner", "value": "New Model Owner",
            "reason": "Transferred to new team"
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["field"] == "owner"
        assert data["new_value"] == "New Model Owner"

    def test_valid_choice_field_update_returns_success(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "rag_rating", "value": "Amber",
            "reason": "Downgraded due to issues"
        })
        assert r.status_code == 200
        assert r.get_json()["new_value"] == "Amber"

    def test_response_has_audit_entry(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "owner", "value": "Someone", "reason": "Transfer"
        })
        data = r.get_json()
        assert "audit_entry" in data
        assert data["audit_entry"]["event_type"] == "field_update"

    def test_update_lifecycle_stage(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "lifecycle_stage", "value": "Validation",
            "reason": "Moving to validation phase"
        })
        assert r.status_code == 200

    def test_update_validation_status(self, gov_client):
        r = gov_client.post(self._URL, json={
            "field": "validation_status", "value": "Pending",
            "reason": "Awaiting annual validation"
        })
        assert r.status_code == 200


# ===========================================================================
# GET /governance/editable-fields
# ===========================================================================

class TestGetEditableFields:

    def test_returns_200(self, gov_client):
        r = gov_client.get("/api/v1/governance/editable-fields")
        assert r.status_code == 200

    def test_returns_success_status(self, gov_client):
        r = gov_client.get("/api/v1/governance/editable-fields")
        assert r.get_json()["status"] == "success"

    def test_has_fields(self, gov_client):
        r = gov_client.get("/api/v1/governance/editable-fields")
        fields = r.get_json()["fields"]
        assert "owner" in fields
        assert "rag_rating" in fields


# ===========================================================================
# GET /governance/models/<model_id>
# ===========================================================================

class TestGetModelDetail:

    def test_model_not_found_returns_404(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/GHOST")
        assert r.status_code == 404
        assert r.get_json()["status"] == "error"

    def test_valid_model_returns_success(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "success"
        assert data["model"]["model_id"] == "MKM-TEST-001"

    def test_response_has_audit_entries(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001")
        assert "audit_entries" in r.get_json()

    def test_model_has_validation_questions(self, gov_client):
        r = gov_client.get("/api/v1/governance/models/MKM-TEST-001")
        model = r.get_json()["model"]
        assert "validation_questions" in model
        assert len(model["validation_questions"]) == 9
