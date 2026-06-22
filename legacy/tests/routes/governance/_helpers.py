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

"""Non-fixture helpers and test data constants extracted from conftest.py.

Contains: _BASE_MODEL, _BASE_INVENTORY, _BASE_RACI constants and the
create_meeting() helper function.
"""

import copy


_BASE_MODEL = {
    "model_id": "MKM-TEST-001",
    "name": "Test Model",
    "short_name": "Test",
    "description": "A test model",
    "category": "Hazard",
    "tier": 2,
    "materiality": "Medium",
    "complexity": "Medium",
    "tier_rationale": "Test rationale",
    "status": "Active",
    "lifecycle_stage": "Production",
    "version": "1.0.0",
    "owner": "Test Owner",
    "model_owner_role": "Tester",
    "peer_reviewer": "TBD",
    "source_module": "src/models/test.py",
    "methodology": "Test methodology",
    "validation_status": "Validated",
    "next_review_date": "2027-01-15",
    "last_review_date": "2026-02-01",
    "rag_rating": "Green",
    "mrc_signoff_date": "2026-02-01",
    "recertification_date": "2027-02-01",
    "review_frequency": "Annual",
    "assumptions": [
        {"id": "T-A1", "description": "Test assumption", "impact": "High",
         "monitoring": "Check regularly", "mitigation": "Adjust if needed"},
    ],
    "limitations": [
        {"id": "T-L1", "description": "Test limitation", "impact": "High",
         "monitoring_trigger": "Threshold breach", "compensating_control": "Manual review"},
    ],
    "remediation_steps": [
        {"id": "T-R1", "description": "Fix something", "owner": "Test Owner",
         "priority": "High", "due_date": "2026-06-01", "status": "Open"},
    ],
    "validation_questions": [
        {"question_id": i, "short_label": f"Q{i}", "question": f"Question {i}?",
         "handbook_ref": f"Ch5 Q{i}", "status": "Not Addressed",
         "evidence": "", "last_reviewed": None, "reviewed_by": None}
        for i in range(1, 10)
    ],
    "overall_risk_rating": {
        "calculated_rating": "Not Rated",
        "calculated_score": None,
        "component_scores": {
            "validation_coverage": None, "remediation_health": None,
            "review_currency": None, "assumption_risk": None,
            "limitation_risk": None,
        },
        "effective_rating": "Not Rated",
        "mrc_override": None, "mrc_override_reason": None,
        "mrc_override_date": None, "mrc_override_by": None,
        "last_calculated": None,
    },
    "upstream_models": [],
    "downstream_models": [],
    "test_coverage": {"unit_tests": True, "integration_tests": False,
                      "benchmark_tests": False, "test_file": "tests/test.py"},
    "change_history": [],
    "version_history": [],
    "documents": [],
    "known_failure_modes": [],
    "key_parameters": [],
    "input_data": "",
    "output_data": "",
    "methodology_rationale": "",
    "alternatives_considered": [],
}

_BASE_INVENTORY = {
    "metadata": {
        "framework": "Test Framework",
        "version": "1.0.0",
        "last_updated": "2026-02-18",
        "handbook_reference": "Test Handbook",
        "tiering_methodology": "Test methodology",
    },
    "models": [copy.deepcopy(_BASE_MODEL)],
    "model_chain": {"description": "Test chain", "links": []},
    "tiering_matrix": {"description": "Test matrix", "matrix": {}},
    "audit_trail": [],
}

_BASE_RACI = {
    "metadata": {
        "framework": "Test RACI",
        "version": "1.0.0",
        "last_updated": "2026-02-18",
        "handbook_reference": "Chapter 10",
    },
    "roles": [
        {
            "role_id": "operations_lead",
            "label": "Operations Lead",
            "raci_code": "R",
            "description": "Responsible",
            "assigned_to": "TBD",
            "backup": None,
        },
        {
            "role_id": "model_owner",
            "label": "Model Owner",
            "raci_code": "A",
            "description": "Accountable",
            "assigned_to": "Test Owner",
            "backup": None,
        },
    ],
    "activities": [
        {
            "activity_id": "ACT-01",
            "category": "Production Operations",
            "activity": "Rerun failed jobs",
            "R": "operations_lead",
            "A": "model_owner",
            "C": None,
            "I": None,
            "tier_emphasis": None,
            "notes": "Routine",
        },
    ],
    "escalation_triggers": [
        {
            "trigger_id": "ESC-01",
            "trigger": "Results outside normal ranges",
            "from_role": "operations_lead",
            "to_role": "model_owner",
            "tier_threshold": {"1": "Immediate", "2": "Same day", "3": "Next business day"},
            "response_required": "Investigation",
        },
    ],
}


def create_meeting(client, **overrides):
    """Helper: POST to create a meeting and return parsed JSON."""
    data = {"title": "Test MRC Meeting", "date": "2026-03-07", **overrides}
    r = client.post(
        "/api/v1/governance/mrc/meetings",
        json=data,
        content_type="application/json",
    )
    return r, r.get_json()
