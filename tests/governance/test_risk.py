# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Unit tests for the composite risk-rating computation (pure)."""
from __future__ import annotations

from src.governance.model_inventory.risk import compute_risk_rating

AS_OF = "2026-06-22"


def _component(result, key):
    return next(c for c in result["components"] if c["key"] == key)


def test_empty_model_is_conditional():
    # No items counts as "healthy", so an empty model lands mid-range.
    result = compute_risk_rating({}, as_of=AS_OF)
    assert result["rating"] == "Conditional"
    assert result["score"] == 0.5
    assert [c["key"] for c in result["components"]] == [
        "validation_coverage", "remediation_health", "review_currency",
        "assumption_risk", "limitation_risk",
    ]


def test_high_risk_model_is_unacceptable():
    data = {
        "validation_questions": [{"status": "Not Addressed"}],
        "next_review_date": "2020-01-01",
        "remediation_steps": [{"status": "Open"}],
        "assumptions": [{"impact": "High"}],
        "limitations": [{"impact": "High"}],
    }
    result = compute_risk_rating(data, as_of=AS_OF)
    assert result["rating"] == "Unacceptable"
    assert result["score"] == 0.0


def test_fully_addressed_model_is_acceptable():
    data = {
        "validation_questions": [{"status": "Addressed"} for _ in range(9)],
        "next_review_date": "2027-01-01",
        "remediation_steps": [{"status": "Closed"}],
        "assumptions": [{"impact": "Low"}],
        "limitations": [{"impact": "Low"}],
    }
    result = compute_risk_rating(data, as_of=AS_OF)
    assert result["rating"] == "Acceptable"
    assert result["score"] >= 0.75


def test_partial_model_is_conditional():
    data = {
        "validation_questions": [{"status": "Addressed"}, {"status": "Partially Addressed"}],
        "next_review_date": "2027-01-01",
        "remediation_steps": [{"status": "Open"}, {"status": "Closed"}],
        "assumptions": [{"impact": "High"}, {"impact": "Low"}],
        "limitations": [{"impact": "High"}],
    }
    result = compute_risk_rating(data, as_of=AS_OF)
    # 0.3*0.75 + 0.25*0.5 + 0.2*1 + 0.15*0.5 + 0.1*0 = 0.625
    assert result["rating"] == "Conditional"
    assert _component(result, "limitation_risk")["score"] == 0.0


def test_coverage_counts_each_status():
    data = {"validation_questions": [
        {"status": "Addressed"}, {"status": "Partially Addressed"}, {"status": "Not Addressed"},
    ]}
    result = compute_risk_rating(data, as_of=AS_OF)
    assert _component(result, "validation_coverage")["score"] == (1.0 + 0.5 + 0.0) / 3


def test_review_currency_future_is_one():
    result = compute_risk_rating({"next_review_date": "2030-01-01"}, as_of=AS_OF)
    assert _component(result, "review_currency")["score"] == 1.0


def test_review_currency_overdue_is_zero():
    result = compute_risk_rating({"next_review_date": "2020-01-01"}, as_of=AS_OF)
    assert _component(result, "review_currency")["score"] == 0.0


# --- W4a heatmap + events -----------------------------------------------------

def test_heatmap_reads_materiality_and_complexity():
    result = compute_risk_rating({"materiality": "High", "complexity": "Medium"}, as_of=AS_OF)
    assert result["heatmap"]["materiality"] == "High"
    assert result["heatmap"]["complexity"] == "Medium"
    assert result["heatmap"]["rag"] == "Red"


def test_heatmap_covers_every_diagonal():
    """Materiality outweighs complexity: HighMat-LowComp > LowMat-HighComp on RAG."""
    assert compute_risk_rating(
        {"materiality": "High", "complexity": "Low"}, as_of=AS_OF,
    )["heatmap"]["rag"] == "Amber"
    assert compute_risk_rating(
        {"materiality": "Low", "complexity": "High"}, as_of=AS_OF,
    )["heatmap"]["rag"] == "Amber"
    assert compute_risk_rating(
        {"materiality": "Low", "complexity": "Low"}, as_of=AS_OF,
    )["heatmap"]["rag"] == "Green"
    assert compute_risk_rating(
        {"materiality": "High", "complexity": "High"}, as_of=AS_OF,
    )["heatmap"]["rag"] == "Red"


def test_heatmap_rag_is_none_without_both_axes():
    assert compute_risk_rating(
        {"materiality": "High"}, as_of=AS_OF,
    )["heatmap"]["rag"] is None
    assert compute_risk_rating({}, as_of=AS_OF)["heatmap"]["rag"] is None


def test_heatmap_response_includes_full_grid():
    """The full mapping is echoed so the UI colours each cell from config."""
    result = compute_risk_rating({}, as_of=AS_OF)
    grid = result["heatmap"]["grid"]
    assert grid["High|High"] == "Red"
    assert grid["Low|Low"] == "Green"
    assert len(grid) == 9


def _hm(materiality, complexity, tier):
    return compute_risk_rating(
        {"materiality": materiality, "complexity": complexity, "tier": tier}, as_of=AS_OF,
    )["heatmap"]


def test_tier1_heatmap_is_the_critical_table():
    # A R R / G A R / G G A
    assert _hm("High", "Medium", 1)["rag"] == "Red"
    assert _hm("High", "Low", 1)["rag"] == "Amber"
    assert _hm("Low", "High", 1)["rag"] == "Amber"


def test_tier2_heatmap_is_pushed_one_step_right():
    # G A R / G G A / G G G
    assert _hm("High", "Low", 2)["rag"] == "Green"
    assert _hm("High", "Medium", 2)["rag"] == "Amber"
    assert _hm("High", "High", 2)["rag"] == "Red"
    assert _hm("Medium", "High", 2)["rag"] == "Amber"
    assert _hm("Low", "High", 2)["rag"] == "Green"


def test_tier3_heatmap_only_reddens_at_the_top_corner():
    # G G A / G G G / G G G — no Red anywhere; only High×High is Amber
    hm = _hm("High", "High", 3)
    assert hm["rag"] == "Amber"
    assert set(hm["grid"].values()) == {"Green", "Amber"}
    assert _hm("High", "Medium", 3)["rag"] == "Green"
    assert _hm("Medium", "High", 3)["rag"] == "Green"


def test_tiers_beyond_three_reuse_the_tier3_table():
    assert _hm("High", "High", 5)["rag"] == "Amber"
    assert _hm("High", "Medium", 4)["rag"] == "Green"


def test_heatmap_reports_its_tier_band_and_label():
    hm = _hm("High", "High", 2)
    assert hm["tier"] == 2 and hm["tier_band"] == 2 and hm["tier_label"] == "Important"
    # Missing tier is treated as the most conservative band (Tier 1).
    missing = compute_risk_rating({"materiality": "High", "complexity": "High"}, as_of=AS_OF)["heatmap"]
    assert missing["tier_band"] == 1 and missing["rag"] == "Red"


# --- W4c sign-off state -------------------------------------------------------

def _signed(data):
    return compute_risk_rating(data, as_of=AS_OF)["signed_off"]


def test_green_owner_and_table_still_needs_signoff_when_never_signed_off():
    # Low × Low is Green on the heatmap; owner also Green. Agreement is not
    # approval — with no sign-off history the rating is NOT signed off.
    assert _signed({"tier": 1, "materiality": "Low", "complexity": "Low",
                    "rag_rating": "Green"}) is False


def test_signed_off_when_latest_signoff_matches_heatmap():
    assert _signed({"tier": 1, "materiality": "Low", "complexity": "Low",
                    "rag_rating": "Green",
                    "rag_signoff_history": [{"to_rating": "Green"}]}) is True


def test_not_signed_off_when_heatmap_moved_since_last_signoff():
    # Signed off Green previously, but the heatmap is now Red (High × High, tier 1).
    assert _signed({"tier": 1, "materiality": "High", "complexity": "High",
                    "rag_rating": "Green",
                    "rag_signoff_history": [{"to_rating": "Green"}]}) is False


def test_not_signed_off_without_a_heatmap_placement():
    # No materiality/complexity → no heatmap rag → nothing to sign off yet.
    assert _signed({"tier": 1, "rag_rating": "Green"}) is False


def test_events_counted_when_within_365_days():
    data = {"operational_failure_events": [
        {"date": "2026-05-01", "description": "recent"},
        {"date": "2025-08-01", "description": "still within window"},
        {"date": "2024-01-01", "description": "outside window — stale"},
        {"date": "", "description": "no date — skipped"},
        {"date": "not-a-date", "description": "unparseable — skipped"},
    ]}
    result = compute_risk_rating(data, as_of="2026-06-22")
    assert result["events_in_window"] == 2
    assert result["events_window_days"] == 365


def test_events_zero_when_no_events():
    result = compute_risk_rating({}, as_of=AS_OF)
    assert result["events_in_window"] == 0


def test_events_zero_when_as_of_is_unparseable():
    """Bad as_of doesn't crash — window collapses to nothing."""
    data = {"operational_failure_events": [{"date": "2026-05-01"}]}
    assert compute_risk_rating(data, as_of="bogus")["events_in_window"] == 0
