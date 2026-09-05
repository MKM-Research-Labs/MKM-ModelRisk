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
"""Coverage across all three record types, and the boundary around them.

Two things carry this phase. The record type is the FILTER — there is no separate
classification column, because two answers to what a record is drift the first time
somebody edits one. And "out of scope" is always printed beside what is governed
elsewhere, because read alone it looks like "ungoverned".
"""
from __future__ import annotations

from config.governance._ai_system import AI_SYSTEM_FIELD_SPECS
from config.governance._inventory import MODEL_FIELD_SPECS
from config.governance._ml_application import ML_APPLICATION_FIELD_SPECS
from config.governance._mrm_scope import (GOVERNED_ELSEWHERE, IN_SCOPE_KINDS,
                                          IN_SCOPE_RECORD_TYPES, NOT_THE_FIRMS,
                                          RECORD_TYPE_ID_FIELDS)
from src.governance.completeness import framework_section
from src.governance.completeness.framework import PROBES, coverage
from src.governance.completeness.scope import (coverage_by_record_type,
                                               population_by_record_type,
                                               record_type_of, scope_statement)
from src.web._signoff_subject import SUBJECTS

_ESTATE = [
    {"model_id": "M-1", "data": {"owner": "A", "peer_reviewer": "B"}},
    {"model_id": "M-2", "data": {}},
    {"ml_application_id": "MLA-1", "data": {"owner": "C"}},
    {"ai_system_id": "AIS-1", "data": {}},
]


# --- The record type is the filter --------------------------------------------

def test_no_model_class_field_exists():
    """No duplicate classification field crept in for reporting convenience. A record's
    type is what it IS; a column repeating it gives two answers that differ the first
    time somebody edits one.
    """
    for specs in (MODEL_FIELD_SPECS, ML_APPLICATION_FIELD_SPECS, AI_SYSTEM_FIELD_SPECS):
        assert "model_class" not in specs
        assert "record_class" not in specs
        assert "record_type" not in specs


def test_the_type_is_read_from_the_id_field_not_from_a_column():
    """Which is why no such column is needed: a row already says what it is by the id
    it carries."""
    assert record_type_of({"model_id": "M-1"}) == "model"
    assert record_type_of({"ml_application_id": "MLA-1"}) == "ml_application"
    assert record_type_of({"ai_system_id": "AIS-1"}) == "ai_system"
    assert record_type_of({"product_id": "P-1"}) is None


def test_the_in_scope_types_are_subjects_the_platform_governs():
    kinds = {s.kind for s in SUBJECTS}
    assert set(IN_SCOPE_KINDS) <= kinds
    assert set(RECORD_TYPE_ID_FIELDS) == set(IN_SCOPE_KINDS)


# --- Counted across all three --------------------------------------------------

def test_coverage_counts_all_three_record_types():
    counted = population_by_record_type(_ESTATE)
    assert counted == {"model": 2, "ml_application": 1, "ai_system": 1}

    clauses = coverage([{"record_id": "M-1"}], _ESTATE, "2026-09-05")
    inventory = next(c for c in clauses if c["probe"] == "inventory")
    assert inventory["total"] == len(_ESTATE), \
        "the inventory clause counted a slice of the estate"


def test_a_per_type_breakdown_shows_what_the_estate_figure_hides():
    """If every model has an owner and no AI System does, the estate figure reads
    comfortable and the finding — that the newest record type is the one nobody has
    assigned — is invisible."""
    estate = {"rows": [], "as_of": "2026-09-05", "ratified": set(), "evidence": []}
    by_type = coverage_by_record_type(PROBES["accountability"], _ESTATE, estate)

    assert by_type["model"] == (1, 2)
    assert by_type["ml_application"] == (1, 1)
    assert by_type["ai_system"] == (0, 1), "the gap the estate figure would hide"


def test_a_record_type_with_no_records_reads_zero_of_zero_not_an_error():
    estate = {"rows": [], "as_of": "2026-09-05", "ratified": set(), "evidence": []}
    only_models = [{"model_id": "M-1", "data": {"owner": "A"}}]
    by_type = coverage_by_record_type(PROBES["accountability"], only_models, estate)
    assert by_type["ai_system"] == (0, 0)


# --- The boundary --------------------------------------------------------------

def test_out_of_scope_is_never_stated_without_how_it_is_governed():
    """Read alone, "out of scope" looks like "ungoverned", and they are not the same
    thing."""
    statement = scope_statement()
    assert statement["governed_elsewhere"] and statement["not_the_firms"]
    for group in statement.values():
        for row in group:
            assert len(row["because"].strip()) > 40, f"{row['key']} is not explained"


def test_the_two_reasons_for_being_outside_are_kept_apart():
    """A Product the firm governs as a product and a foundation model it cannot
    validate are both outside this report, for completely different reasons."""
    elsewhere = {key for key, _, _ in GOVERNED_ELSEWHERE}
    not_ours = {key for key, _, _ in NOT_THE_FIRMS}
    assert not elsewhere & not_ours
    assert "product" in elsewhere and "FOUNDATION_MODEL" in not_ours


def test_the_things_the_firm_cannot_validate_are_the_external_lineage_kinds():
    """The chain already distinguishes what the institution owns from what it depends
    on; the scope statement reuses that rather than deciding it again."""
    from config.governance._lineage import EXTERNAL_NODE_KINDS
    assert {key for key, _, _ in NOT_THE_FIRMS} == set(EXTERNAL_NODE_KINDS)


def test_the_report_states_the_scope_before_any_clause_table():
    tex = framework_section([{"record_id": "M-1"}], _ESTATE, "2026-09-05")
    assert "In model risk management scope" in tex
    assert "Governed outside this report" in tex
    assert tex.index("Scope") < tex.index("ISO 31000"), \
        "a clause figure was printed before the population it was counted over"


def test_every_in_scope_type_says_why_it_is_in_scope():
    for key, label, because in IN_SCOPE_RECORD_TYPES:
        assert key in RECORD_TYPE_ID_FIELDS
        assert label.strip() and len(because.strip()) > 40
