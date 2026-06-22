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
Tests for governance helpers: _calculate_risk_rating and _vq_summary (part 1).
"""

from datetime import datetime, timedelta

import pytest


# ===========================================================================
# _calculate_risk_rating
# ===========================================================================

class TestCalculateRiskRating:

    def _make_model(self, addressed=9, not_applicable=0, open_rem=0,
                    overdue_rem=0, next_review_days=100,
                    high_assumptions=0, high_limitations=0):
        today = datetime.now()
        vq = []
        for i in range(9):
            if i < not_applicable:
                status = "Not Applicable"
            elif i < not_applicable + addressed:
                status = "Addressed"
            else:
                status = "Not Addressed"
            vq.append({"question_id": i + 1, "status": status})

        rem = []
        for j in range(open_rem):
            if j < overdue_rem:
                due = (today - timedelta(days=10)).strftime("%Y-%m-%d")
            else:
                due = (today + timedelta(days=60)).strftime("%Y-%m-%d")
            rem.append({"status": "Open", "due_date": due})

        review = (today + timedelta(days=next_review_days)).strftime("%Y-%m-%d")

        assumptions = [{"impact": "High"}] * high_assumptions
        limitations = [{"impact": "High"}] * high_limitations

        return {
            "validation_questions": vq,
            "remediation_steps": rem,
            "next_review_date": review,
            "assumptions": assumptions,
            "limitations": limitations,
        }

    def test_returns_dict_with_required_keys(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model()
        result = _calculate_risk_rating(model)
        assert "calculated_rating" in result
        assert "calculated_score" in result
        assert "component_scores" in result

    def test_high_coverage_acceptable(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=9, next_review_days=60)
        result = _calculate_risk_rating(model)
        assert result["calculated_rating"] == "Acceptable"

    def test_no_coverage_unacceptable(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=0, next_review_days=-5,
                                  open_rem=4, overdue_rem=4,
                                  high_assumptions=5, high_limitations=5)
        result = _calculate_risk_rating(model)
        assert result["calculated_rating"] == "Unacceptable"

    def test_overdue_review_gives_zero_score(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=0, next_review_days=-10)
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["review_currency"] == 0.0

    def test_due_soon_gives_half_score(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=0, next_review_days=20)
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["review_currency"] == 0.5

    def test_far_review_gives_full_score(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=0, next_review_days=100)
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["review_currency"] == 1.0

    def test_no_review_date_gives_zero(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = {
            "validation_questions": [],
            "remediation_steps": [],
            "next_review_date": None,
            "assumptions": [],
            "limitations": [],
        }
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["review_currency"] == 0.0

    def test_conditional_rating_middle_range(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(addressed=4, next_review_days=25,
                                  open_rem=2, high_assumptions=1)
        result = _calculate_risk_rating(model)
        assert result["calculated_rating"] in ("Conditional", "Unacceptable")

    def test_high_assumptions_penalised(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(high_assumptions=5)
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["assumption_risk"] == 0.0

    def test_high_limitations_penalised(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model(high_limitations=5)
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["limitation_risk"] == 0.0

    def test_score_is_float(self):
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model()
        result = _calculate_risk_rating(model)
        assert isinstance(result["calculated_score"], float)

    def test_remediation_steps_list_of_strings_ignored(self):
        """Freeform remediation_steps (list-of-strings) used to crash
        with AttributeError on r.get(). Now silently treated as zero
        open items so the wider rating calculation still runs."""
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model()
        model["remediation_steps"] = ["complete phase 2", "validate against history"]
        result = _calculate_risk_rating(model)
        # String entries don't contribute to open_count, so remediation_health = 1.0
        assert result["component_scores"]["remediation_health"] == 1.0

    def test_remediation_steps_none_treated_as_empty(self):
        """remediation_steps explicitly None (some legacy entries) must
        not raise TypeError on iteration."""
        from routes.governance._helpers import _calculate_risk_rating
        model = self._make_model()
        model["remediation_steps"] = None
        result = _calculate_risk_rating(model)
        assert result["component_scores"]["remediation_health"] == 1.0

    def test_remediation_steps_mixed_str_and_dict(self):
        """Some entries str, some dict — only dict entries count toward
        open/overdue. Defensive shape-handling shouldn't drop the dict."""
        from routes.governance._helpers import _calculate_risk_rating
        today = datetime.now()
        future = (today + timedelta(days=60)).strftime("%Y-%m-%d")
        model = self._make_model()
        model["remediation_steps"] = [
            "freeform descriptive remediation",
            {"status": "Open", "due_date": future},
            "another freeform item",
        ]
        result = _calculate_risk_rating(model)
        # Exactly 1 open dict item → small penalty (0.15) → 0.85
        assert result["component_scores"]["remediation_health"] == pytest.approx(0.85, abs=0.001)


# ===========================================================================
# _vq_summary
# ===========================================================================

class TestVqSummary:

    def test_all_addressed(self):
        from routes.governance._helpers import _vq_summary
        model = {
            "validation_questions": [
                {"status": "Addressed"},
                {"status": "Addressed"},
                {"status": "Addressed"},
            ]
        }
        assert _vq_summary(model) == "3/3"

    def test_some_not_applicable(self):
        from routes.governance._helpers import _vq_summary
        model = {
            "validation_questions": [
                {"status": "Addressed"},
                {"status": "Not Applicable"},
                {"status": "Not Addressed"},
            ]
        }
        assert _vq_summary(model) == "1/2"

    def test_empty_questions(self):
        from routes.governance._helpers import _vq_summary
        model = {"validation_questions": []}
        assert _vq_summary(model) == "0/0"

    def test_none_addressed(self):
        from routes.governance._helpers import _vq_summary
        model = {
            "validation_questions": [
                {"status": "Not Addressed"},
                {"status": "Not Addressed"},
            ]
        }
        assert _vq_summary(model) == "0/2"
