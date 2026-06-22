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

"""Tests for cdm_edit — schema-driven edit specs and value validation."""

import pytest

from cdm_edit import descriptor_at, field_spec, schema_specs, validate_value


# ---------------------------------------------------------------------------
# field_spec
# ---------------------------------------------------------------------------


class TestFieldSpec:

    def test_menu_becomes_select_with_options(self):
        s = field_spec("X.ValuationMethod", {"type": "menu", "options": ["A", "B"]})
        assert s["input"] == "select"
        assert s["options"] == ["A", "B"]

    def test_decimal_is_non_negative_number(self):
        s = field_spec("X.PropertyValue", {"type": "decimal"})
        assert s["input"] == "number"
        assert s["min"] == 0 and s["max"] is None and s["step"] == "any"

    def test_integer_step_is_one(self):
        assert field_spec("X.NumberBedrooms", {"type": "integer"})["step"] == 1

    def test_coordinate_allows_negative(self):
        assert field_spec("X.LongitudeDegrees", {"type": "decimal"})["min"] is None
        assert field_spec("X.GroundLevelMeters", {"type": "decimal"})["min"] is None

    def test_year_has_calendar_range(self):
        s = field_spec("X.ConstructionYear", {"type": "integer"})
        assert s["min"] == 1900 and s["max"] == 2100 and s["step"] == 1

    def test_bri_score_bounded_unit_interval(self):
        s = field_spec("X.BRIWindScore", {"type": "decimal"})
        assert s["min"] == 0 and s["max"] == 1

    def test_boolean_is_checkbox(self):
        assert field_spec("X.BasementPresent", {"type": "boolean"})["input"] == "checkbox"

    def test_date_input(self):
        assert field_spec("X.ValuationDate", {"type": "date"})["input"] == "date"


# ---------------------------------------------------------------------------
# schema_specs / descriptor_at
# ---------------------------------------------------------------------------


_SCHEMA = {
    "Header": {
        "PropertyID": {"type": "string"},
        "propertyType": {"type": "menu", "options": ["residential", "commercial"]},
    },
    "Valuation": {
        "PropertyValue": {"type": "decimal"},
    },
}


class TestSchemaSpecs:

    def test_walks_to_dotted_leaf_paths(self):
        specs = schema_specs(_SCHEMA)
        assert "Header.PropertyID" in specs
        assert "Header.propertyType" in specs
        assert "Valuation.PropertyValue" in specs
        # only leaf fields, not the group nodes
        assert "Header" not in specs

    def test_root_prefix_applied(self):
        specs = schema_specs({"A": {"B": {"type": "string"}}}, root="Sec")
        assert "Sec.A.B" in specs


class TestDescriptorAt:

    def test_returns_descriptor_for_field(self):
        d = descriptor_at(_SCHEMA, "Header.propertyType")
        assert d and d["type"] == "menu"

    def test_group_path_returns_none(self):
        assert descriptor_at(_SCHEMA, "Header") is None

    def test_unknown_path_returns_none(self):
        assert descriptor_at(_SCHEMA, "Header.Nope") is None


# ---------------------------------------------------------------------------
# validate_value
# ---------------------------------------------------------------------------


class TestValidate:

    def test_positive_decimal_ok(self):
        assert validate_value("X.V", {"type": "decimal"}, "123.5") == (True, 123.5, None)

    def test_negative_rejected(self):
        ok, _, err = validate_value("X.V", {"type": "decimal"}, "-4")
        assert not ok and "≥ 0" in err

    def test_non_numeric_rejected(self):
        ok, _, err = validate_value("X.V", {"type": "decimal"}, "abc")
        assert not ok and "number" in err

    def test_empty_clears(self):
        assert validate_value("X.V", {"type": "decimal"}, "") == (True, None, None)

    def test_menu_membership_enforced(self):
        opts = {"type": "menu", "options": ["Good", "Poor"]}
        assert validate_value("X.M", opts, "Good")[0] is True
        ok, _, err = validate_value("X.M", opts, "Nope")
        assert not ok and "one of" in err

    def test_integer_coerced(self):
        assert validate_value("X.N", {"type": "integer"}, "7") == (True, 7, None)

    def test_year_range_enforced(self):
        assert validate_value("X.ConstructionYear", {"type": "integer"}, "1850")[0] is False

    def test_bri_unit_interval_enforced(self):
        ok, _, err = validate_value("X.BRIWindScore", {"type": "decimal"}, "1.5")
        assert not ok and "≤ 1" in err

    def test_boolean_coercion(self):
        assert validate_value("X.B", {"type": "boolean"}, "yes") == (True, True, None)
        assert validate_value("X.B", {"type": "boolean"}, "no") == (True, False, None)
        assert validate_value("X.B", {"type": "boolean"}, "maybe")[0] is False

    def test_date_format(self):
        assert validate_value("X.D", {"type": "date"}, "2026-01-02")[0] is True
        assert validate_value("X.D", {"type": "date"}, "02/01/2026")[0] is False

    def test_string_passthrough(self):
        assert validate_value("X.S", {"type": "string"}, "hello") == (True, "hello", None)
