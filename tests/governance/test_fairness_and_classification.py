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
"""Data classification on a feed, and a fairness assessment on anything that scores
people.

Two additions that FINOS asks for and that the estate needed anyway. The tests worth
holding are the ones about WHERE each fact lives: a feed's sensitivity belongs to the
feed rather than to each model that reads it, and a fairness assessment belongs to
every record type that scores people rather than only to the AI ones.
"""
from __future__ import annotations

import pytest

from config.governance import COLLECTION_SPECS, REFERENCE_SPECS
from config.governance._collections import (FAIRNESS_COLLECTION, VALID_DATA_EGRESS,
                                            VALID_DATA_SENSITIVITY)
from src.governance.errors import DomainError
from src.governance.model_inventory import (add_collection_item, get_model,
                                            rebuild_inventory_view, register_model)


# --- Where a feed's classification lives ------------------------------------

def test_sensitivity_and_egress_are_properties_of_the_feed():
    """On the admin Data Source list, beside ``kind`` -- not on each model's row.

    A feed's sensitivity does not change with who reads it. Recording it per record
    would mean the same feed classified two ways on two models, and no answer to
    "what confidential data does this firm hold" that could be trusted.
    """
    fields = {f["key"] for f in REFERENCE_SPECS["data_source"]["fields"]}
    assert {"kind", "sensitivity", "egress"} <= fields

    per_record = {f["key"] for f in COLLECTION_SPECS["data_sources"]["fields"]}
    assert "sensitivity" not in per_record and "egress" not in per_record


def test_blank_is_not_a_classification():
    """"Not classified" and "not sensitive" are different, and the vocabulary must
    not offer a word that blurs them -- the absence is the finding."""
    assert "Unclassified" not in VALID_DATA_SENSITIVITY
    assert "Not sensitive" not in VALID_DATA_SENSITIVITY
    assert VALID_DATA_SENSITIVITY[0] == "Public"


def test_egress_says_whether_it_may_leave_at_all():
    """AIR-RC-001 turns on this being answerable about the feed before it can be
    answered about any system that sends it somewhere."""
    assert any("not leave" in v for v in VALID_DATA_EGRESS)
    assert any("under contract" in v for v in VALID_DATA_EGRESS)


# --- Fairness belongs to every record type that scores people ---------------

def test_all_three_record_types_carry_the_same_fairness_collection():
    """One shape, one name. Three shapes would make "what has this firm assessed for
    bias" unobtainable across the estate."""
    from config.governance._ai_system import AI_SYSTEM_COLLECTION_SPECS
    from config.governance._ml_application import ML_APPLICATION_COLLECTION_SPECS
    for specs in (COLLECTION_SPECS, ML_APPLICATION_COLLECTION_SPECS,
                  AI_SYSTEM_COLLECTION_SPECS):
        assert FAIRNESS_COLLECTION in specs
        assert specs[FAIRNESS_COLLECTION] is COLLECTION_SPECS[FAIRNESS_COLLECTION]


def test_an_assessment_names_the_attribute_and_what_it_showed():
    """Not a pass/fail flag. "No disparity above the threshold" and "not measured"
    are different answers and a boolean collapses them."""
    fields = {f["key"] for f in COLLECTION_SPECS[FAIRNESS_COLLECTION]["fields"]}
    assert {"attribute", "how_assessed", "metric", "finding", "assessed_on"} == fields
    attribute = next(f for f in COLLECTION_SPECS[FAIRNESS_COLLECTION]["fields"]
                     if f["key"] == "attribute")
    assert attribute.get("required")
    # Free text on purpose: which characteristics are protected is a matter of law
    # and differs by jurisdiction, so a fixed list of ours would be wrong somewhere.
    assert "options" not in attribute


def test_a_model_records_one():
    register_model(model_id="M-FAIR", name="Retail scorecard", actor="admin")
    add_collection_item(model_id="M-FAIR", collection=FAIRNESS_COLLECTION,
                        fields={"attribute": "Age", "metric": "Demographic parity",
                                "finding": "Within the 5pp threshold across bands.",
                                "assessed_on": "2026-08-01"}, actor="admin")
    rebuild_inventory_view()
    rows = get_model("M-FAIR")["data"][FAIRNESS_COLLECTION]
    assert len(rows) == 1 and rows[0]["attribute"] == "Age"


def test_an_assessment_without_an_attribute_is_refused():
    register_model(model_id="M-FAIR2", name="X", actor="admin")
    with pytest.raises(DomainError):
        add_collection_item(model_id="M-FAIR2", collection=FAIRNESS_COLLECTION,
                            fields={"finding": "Looked fine."}, actor="admin")


# --- What it does to the FINOS bias row -------------------------------------

def test_the_bias_row_now_counts_the_whole_estate():
    """It was AI-only while the record had nowhere else to live, and that limit was
    a gap the row could not report about itself. A model that ranks retail applicants
    raises bias exactly as a generative system does."""
    from src.governance.completeness.framework import coverage
    from config.governance import COVERAGE_ABSENT, COVERAGE_EVIDENCED
    from config.governance._finos import FINOS_RISKS

    def _row(estate):
        rows = coverage([], estate, "2026-08-26", (), [])
        return next(r for r in rows
                    if r["framework"] == FINOS_RISKS and r["ref"] == "AIR-OP-016")

    plain = [{"model_id": "M1", "data": {"name": "Retail scorecard"}}]
    assert _row(plain)["state"] == COVERAGE_ABSENT

    assessed = [{"model_id": "M1", "data": {
        "name": "Retail scorecard",
        FAIRNESS_COLLECTION: [{"attribute": "Age", "finding": "Within threshold."}]}}]
    assert _row(assessed)["state"] == COVERAGE_EVIDENCED
