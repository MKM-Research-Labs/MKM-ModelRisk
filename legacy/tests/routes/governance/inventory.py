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

"""Tests for model inventory, validation questions, and risk rating endpoints."""

import json


class TestInventorySummary:
    """Test enhanced model inventory summary."""

    def test_get_models_includes_risk_fields(self, gov_client, governance_env):
        response = gov_client.get("/api/v1/governance/models")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        model = data["models"][0]
        assert "risk_rating" in model
        assert "validation_coverage" in model
        assert model["risk_rating"] == "Not Rated"
        assert model["validation_coverage"] == "0/9"


class TestValidationQuestions:
    """Test validation question update endpoint."""

    def test_update_validation_question(self, gov_client, governance_env):
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={
                "status": "Addressed",
                "evidence": "Model documentation demonstrates correct implementation",
                "reviewed_by": "Test Reviewer",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        q1 = next(q for q in data["model"]["validation_questions"] if q["question_id"] == 1)
        assert q1["status"] == "Addressed"
        assert q1["evidence"] == "Model documentation demonstrates correct implementation"
        assert q1["reviewed_by"] == "Test Reviewer"
        assert q1["last_reviewed"] is not None
        assert data["audit_entry"]["event_type"] == "validation_question_update"

    def test_update_validation_question_invalid_status(self, gov_client, governance_env):
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "InvalidStatus", "evidence": "test", "reviewed_by": "test"},
        )
        assert response.status_code == 400

    def test_update_validation_question_not_found(self, gov_client, governance_env):
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/99/update",
            json={"status": "Addressed", "evidence": "test", "reviewed_by": "test"},
        )
        assert response.status_code == 404

    def test_update_triggers_risk_recalculation(self, gov_client, governance_env):
        gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/validation-questions/1/update",
            json={"status": "Addressed", "evidence": "Done", "reviewed_by": "Tester"},
        )
        response = gov_client.get("/api/v1/governance/models/MKM-TEST-001")
        data = json.loads(response.data)
        rr = data["model"]["overall_risk_rating"]
        assert rr["calculated_score"] is not None
        assert rr["calculated_rating"] in ["Acceptable", "Conditional", "Unacceptable"]
        assert rr["component_scores"]["validation_coverage"] is not None


class TestRiskRating:
    """Test risk rating calculation and override endpoints."""

    def test_get_risk_rating_calculation(self, gov_client, governance_env):
        response = gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        rr = data["risk_rating"]
        assert rr["calculated_rating"] in ["Acceptable", "Conditional", "Unacceptable"]
        assert isinstance(rr["calculated_score"], float)
        assert 0.0 <= rr["calculated_score"] <= 1.0

        for key in ["validation_coverage", "remediation_health", "review_currency",
                    "assumption_risk", "limitation_risk"]:
            assert key in rr["component_scores"]
            assert 0.0 <= rr["component_scores"][key] <= 1.0

    def test_risk_rating_override(self, gov_client, governance_env):
        gov_client.get("/api/v1/governance/models/MKM-TEST-001/risk-rating")
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "Unacceptable", "reason": "MRC determined model needs remediation",
                  "user": "MRC Chair"},
        )
        assert response.status_code == 200
        rr = json.loads(response.data)["model"]["overall_risk_rating"]
        assert rr["mrc_override"] == "Unacceptable"
        assert rr["effective_rating"] == "Unacceptable"
        assert rr["mrc_override_reason"] == "MRC determined model needs remediation"
        assert rr["mrc_override_by"] == "MRC Chair"

    def test_risk_rating_clear_override(self, gov_client, governance_env):
        gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "Unacceptable", "reason": "Test", "user": "Chair"},
        )
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": None, "reason": "Override no longer needed", "user": "Chair"},
        )
        assert response.status_code == 200
        rr = json.loads(response.data)["model"]["overall_risk_rating"]
        assert rr["mrc_override"] is None
        assert rr["mrc_override_reason"] is None

    def test_risk_rating_override_requires_reason(self, gov_client, governance_env):
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "Conditional", "reason": "", "user": "Chair"},
        )
        assert response.status_code == 400

    def test_risk_rating_override_invalid_rating(self, gov_client, governance_env):
        response = gov_client.post(
            "/api/v1/governance/models/MKM-TEST-001/risk-rating/override",
            json={"rating": "InvalidRating", "reason": "Test", "user": "Chair"},
        )
        assert response.status_code == 400
