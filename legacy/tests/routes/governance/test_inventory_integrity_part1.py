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
Structural integrity tests for the real model_inventory.json — part 1.

Covers: TestInventoryFileExists, TestModelIDs, TestRequiredDictFields,
TestTestCoverageStructure, TestOverallRiskRatingStructure.
"""

import json
import pathlib

import pytest


INVENTORY_PATH = (
    pathlib.Path(__file__).parents[3]
    / "docs" / "models" / "governance_data" / "model_inventory.json"
)

REQUIRED_DICT_FIELDS = ["test_coverage", "overall_risk_rating"]
TEST_COVERAGE_BOOL_FIELDS = ["unit_tests", "integration_tests", "benchmark_tests"]
OVERALL_RISK_RATING_KEYS = [
    "calculated_rating", "calculated_score", "component_scores",
    "effective_rating", "mrc_override",
]


@pytest.fixture(scope="module")
def inventory():
    assert INVENTORY_PATH.exists(), (
        f"model_inventory.json not found at {INVENTORY_PATH}. "
        "Run: python app.py port to generate it."
    )
    with open(INVENTORY_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def models(inventory):
    return inventory.get("models", [])


class TestInventoryFileExists:
    """Verify the inventory file is present and parseable."""

    def test_file_exists(self):
        assert INVENTORY_PATH.exists(), f"Missing: {INVENTORY_PATH}"

    def test_file_is_valid_json(self):
        with open(INVENTORY_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_models_key(self, inventory):
        assert "models" in inventory

    def test_has_at_least_one_model(self, models):
        assert len(models) > 0, "model_inventory.json has no models"

    def test_has_metadata(self, inventory):
        assert "metadata" in inventory
        assert "framework" in inventory["metadata"]

    def test_has_model_chain(self, inventory):
        assert "model_chain" in inventory


class TestModelIDs:
    """Every model must have a unique, non-empty model_id."""

    def test_all_models_have_model_id(self, models):
        for m in models:
            assert "model_id" in m, f"Model missing model_id: {m.get('name', '?')}"
            assert isinstance(m["model_id"], str), f"model_id not str: {m['model_id']}"
            assert m["model_id"].strip(), f"model_id is blank: {m}"

    def test_model_ids_are_unique(self, models):
        ids = [m["model_id"] for m in models]
        assert len(ids) == len(set(ids)), f"Duplicate model_ids: {[x for x in ids if ids.count(x) > 1]}"

    def test_model_ids_follow_naming_convention(self, models):
        for m in models:
            mid = m["model_id"]
            assert mid.startswith("MKM-"), f"{mid}: model_id must start with 'MKM-'"


class TestRequiredDictFields:
    """test_coverage and overall_risk_rating must be dicts, not strings."""

    @pytest.mark.parametrize("field", REQUIRED_DICT_FIELDS)
    def test_field_is_dict(self, models, field):
        for m in models:
            mid = m.get("model_id", "?")
            assert field in m, f"{mid}: missing field '{field}'"
            assert isinstance(m[field], dict), (
                f"{mid}: '{field}' must be a dict, got {type(m[field]).__name__!r} "
                f"(value: {m[field]!r}). "
                f"This causes GET /api/v1/governance/models to return 500."
            )


class TestTestCoverageStructure:
    """test_coverage must have the required boolean fields."""

    def test_test_coverage_has_required_keys(self, models):
        for m in models:
            mid = m.get("model_id", "?")
            tc = m.get("test_coverage", {})
            if not isinstance(tc, dict):
                pytest.fail(f"{mid}: test_coverage is not a dict")
            for key in TEST_COVERAGE_BOOL_FIELDS:
                assert key in tc, f"{mid}: test_coverage missing key '{key}'"

    def test_test_coverage_booleans_are_bool(self, models):
        for m in models:
            mid = m.get("model_id", "?")
            tc = m.get("test_coverage", {})
            if not isinstance(tc, dict):
                continue
            for key in TEST_COVERAGE_BOOL_FIELDS:
                val = tc.get(key)
                assert isinstance(val, bool), (
                    f"{mid}: test_coverage['{key}'] must be bool, got {type(val).__name__!r}"
                )

    def test_test_coverage_has_test_file(self, models):
        for m in models:
            mid = m.get("model_id", "?")
            tc = m.get("test_coverage", {})
            if not isinstance(tc, dict):
                continue
            assert "test_file" in tc, f"{mid}: test_coverage missing 'test_file'"
            assert isinstance(tc["test_file"], str), f"{mid}: test_file must be a string"


class TestOverallRiskRatingStructure:
    """overall_risk_rating must have the required keys."""

    def test_overall_risk_rating_has_required_keys(self, models):
        for m in models:
            mid = m.get("model_id", "?")
            orr = m.get("overall_risk_rating", {})
            if not isinstance(orr, dict):
                pytest.fail(f"{mid}: overall_risk_rating is not a dict")
            for key in OVERALL_RISK_RATING_KEYS:
                assert key in orr, f"{mid}: overall_risk_rating missing key '{key}'"

    def test_overall_risk_rating_has_component_scores(self, models):
        for m in models:
            mid = m.get("model_id", "?")
            orr = m.get("overall_risk_rating", {})
            if not isinstance(orr, dict):
                continue
            cs = orr.get("component_scores")
            assert isinstance(cs, dict), (
                f"{mid}: overall_risk_rating['component_scores'] must be a dict, "
                f"got {type(cs).__name__!r}"
            )

    def test_effective_rating_is_valid(self, models):
        valid_ratings = {"Not Rated", "Acceptable", "Conditional", "Unacceptable"}
        for m in models:
            mid = m.get("model_id", "?")
            orr = m.get("overall_risk_rating", {})
            if not isinstance(orr, dict):
                continue
            rating = orr.get("effective_rating", "Not Rated")
            if rating is not None:
                assert rating in valid_ratings, (
                    f"{mid}: effective_rating '{rating}' not in {valid_ratings}"
                )
