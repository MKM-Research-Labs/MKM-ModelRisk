# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""The feature register.

A register rather than a vocabulary: each entry is a thing with properties -- what
type it is, where it comes from, how it is derived -- not a word with a label.

It earns its keep beyond one dropdown. A feature used by several ML Applications is
the ML estate's version of "two models share a data source", and the same
correlated-failure question follows: a feature that turns out to be wrong, or to have
leaked, is wrong everywhere it is used at once. That is only askable if the uses are
recorded against one entry rather than typed into fifty.
"""
from __future__ import annotations

from config.governance import REFERENCE_LISTS, REFERENCE_SPECS, TRAINING_FIELD_SPECS
from config.governance._ml import FEATURE_LIST
from src.governance.reference import add_option, get_reference_lists
from tests.web.conftest import HEADERS  # noqa: F401  (client fixture lives here)


def test_the_register_records_what_a_feature_is():
    spec = REFERENCE_SPECS[FEATURE_LIST]
    keys = {f["key"] for f in spec["fields"]}
    assert keys == {"value", "data_type", "data_source", "derivation"}
    source = [f for f in spec["fields"] if f["key"] == "data_source"][0]
    assert source["reference"] == "data_source", "a feature comes from somewhere"


def test_it_ships_empty():
    """An institution's features are its own. A starter list of ours would be somebody
    else's model described in their register."""
    assert FEATURE_LIST in REFERENCE_LISTS
    assert not get_reference_lists().get(FEATURE_LIST)


def test_a_train_links_features_rather_than_pasting_them():
    spec = TRAINING_FIELD_SPECS["features"]
    assert spec["type"] == "multichoice"
    assert spec["reference"] == FEATURE_LIST
    assert spec["section"] == "A"


def test_the_count_survives_beside_the_links():
    """Two different facts: which features the register knows about, and how many the
    run actually fitted. A count larger than the links says the register is behind."""
    assert "feature_count" in TRAINING_FIELD_SPECS
    assert TRAINING_FIELD_SPECS["feature_count"]["type"] == "number"


def test_features_can_be_registered_and_are_offered_to_a_train(client):
    for name, kind in (("water_level_m", "Numeric"), ("storm_hour", "Numeric"),
                       ("parcel_grade", "Categorical")):
        add_option(list_name=FEATURE_LIST,
                   fields={"value": name, "data_type": kind, "data_source": "Simulated"},
                   actor="admin")
    res = client.get("/api/ml-applications/fields").get_json()
    train = [c for c in res["collections"] if c["key"] == "training_runs"][0]
    features = [f for f in train["fields"] if f["key"] == "features"][0]
    assert set(features["options"]) == {"water_level_m", "storm_hour", "parcel_grade"}


def test_the_register_reaches_admin(client):
    """A register the Admin screen does not list is one nobody can fill in."""
    res = client.get("/api/reference").get_json()
    labels = {c["key"]: c["label"] for c in res["collections"]}
    assert labels[FEATURE_LIST] == "Feature"
