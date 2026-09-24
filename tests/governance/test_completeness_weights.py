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
"""A division's own criticality weights, and the bounds its committee may set them in.

The weights reach the audit on the risk envelope (``audit_policy``), exactly as the
escalation factors do. What these tests hold on to is that the missing and the held
are weighed on one scale: a re-weighted field must move the gap *and* the
denominator, or the completeness figure is computed on two policies at once.
See docs/design/completeness-weights.md.
"""
from __future__ import annotations

import pytest

from config.governance import (
    BROKEN_DOC_ESCALATION,
    COLLECTION_CRITICALITY,
    COLLECTION_SPECS,
    DEFAULT_FIELD_CRITICALITY,
    DOC_CATEGORIES,
    DOC_CRITICALITY,
    EXEMPT_FIELDS,
    FIELD_CRITICALITY,
    MODEL_FIELD_SPECS,
)
from config.governance._completeness_weights import (AUDIT_WEIGHT_KEYS,
                                                     AUDIT_WEIGHT_MAX,
                                                     AUDIT_WEIGHT_MIN)
from src.governance.completeness import build_completeness_tex
from src.governance.completeness._method_departures import departures, departures_table
from src.governance.completeness._rules import _carried, audit_entity
from src.governance.completeness._weights import criticality
from src.governance.errors import DomainError
from src.governance.risk_policy import default_policy
from src.governance.risk_policy.commands import _validate_policy

AS_OF = "2026-09-24"
FIELD = next(k for k in FIELD_CRITICALITY if k in MODEL_FIELD_SPECS and k not in EXEMPT_FIELDS)
COLLECTION = next(n for n in COLLECTION_CRITICALITY if n in COLLECTION_SPECS)
DOC = "Core Documentation"


def _audit(data, audit_policy=None, *, collections=None, available=None):
    risk = {"heatmap": {"rag": None}, "events_in_window": 0}
    if audit_policy is not None:
        risk["audit_policy"] = audit_policy
    return audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha", data=data,
        field_specs=MODEL_FIELD_SPECS, collection_specs=collections or {},
        doc_categories=DOC_CATEGORIES, risk=risk, as_of=AS_OF, available=available)


def _gap(result, key):
    return next(g for g in result["gaps"] if g["key"] == key)


# --- The resolver --------------------------------------------------------------

def test_an_unset_name_reads_the_firm_wide_table():
    assert criticality("field", FIELD) == FIELD_CRITICALITY[FIELD]
    assert criticality("field", FIELD, {"field_weights": {}}) == FIELD_CRITICALITY[FIELD]


def test_a_name_the_table_does_not_list_reads_the_default():
    assert criticality("field", "not_in_the_table") == DEFAULT_FIELD_CRITICALITY


def test_a_malformed_weight_falls_back_rather_than_raising_mid_audit():
    """A policy approved before the validator existed must still be auditable."""
    for bad in ("0.5", True, None):
        assert criticality("field", FIELD, {"field_weights": {FIELD: bad}}) \
            == FIELD_CRITICALITY[FIELD]


# --- The audit reads the division's weights -------------------------------------

def test_a_division_that_sets_nothing_is_audited_exactly_as_before():
    """The regression guard: the seed's empty sections change no number."""
    seeded = {key: {} for key in AUDIT_WEIGHT_KEYS}
    scored, before = _audit({}, seeded), _audit({})
    # The row carries the policy it was scored on, which differs by construction.
    assert scored.pop("audit_policy") != before.pop("audit_policy")
    assert scored == before


def test_a_field_weight_moves_the_gap():
    result = _audit({}, {"field_weights": {FIELD: 1.9}})
    assert _gap(result, FIELD)["criticality"] == 1.9


def test_a_field_weight_moves_the_denominator_too():
    """A held field is credited on the division's weight, so re-weighting it moves
    the completeness figure even though it raises no gap."""
    data = {FIELD: "recorded"}
    policy = {"field_weights": {FIELD: 1.9}}
    firm = _carried(data, MODEL_FIELD_SPECS, {}, ())
    division = _carried(data, MODEL_FIELD_SPECS, {}, (), None, policy)
    assert division - firm == pytest.approx(1.9 - FIELD_CRITICALITY[FIELD])
    assert _audit(data, policy)["completeness"] > _audit(data)["completeness"]


def test_a_collection_weight_moves_the_gap():
    specs = {COLLECTION: COLLECTION_SPECS[COLLECTION]}
    result = _audit({}, {"collection_weights": {COLLECTION: 0.2}}, collections=specs)
    assert _gap(result, COLLECTION)["criticality"] == 0.2


def test_a_document_weight_moves_the_gap_and_the_credit():
    policy = {"doc_weights": {DOC: 1.5}}
    assert _gap(_audit({}, policy), DOC)["criticality"] == 1.5
    held = {"documents": [{"category": DOC, "filename": "f.pdf"}]}
    assert (_carried(held, {}, {}, (DOC,), None, policy)
            - _carried(held, {}, {}, (DOC,))) == pytest.approx(1.5 - DOC_CRITICALITY[DOC])


def test_a_divisions_broken_document_escalation_is_applied():
    """It was offered per division and accepted by the validator, but the gap read
    the firm-wide constant, so a committee's value was silently ignored."""
    cited = {"documents": [{"category": DOC, "filename": "f.pdf"}]}
    gone = lambda doc: False  # noqa: E731
    firm = _gap(_audit(cited, available=gone), DOC)
    assert firm["criticality"] == round(DOC_CRITICALITY[DOC] * BROKEN_DOC_ESCALATION, 4)
    division = _gap(_audit(cited, {"broken_doc_escalation": 1.4}, available=gone), DOC)
    assert division["criticality"] == round(DOC_CRITICALITY[DOC] * 1.4, 4)


# --- What a committee may ratify --------------------------------------------------

def _with_audit(**audit):
    policy = default_policy()
    policy["audit"].update(audit)
    return policy


def test_the_seed_carries_empty_weight_sections_and_validates():
    audit = default_policy()["audit"]
    assert all(audit[key] == {} for key in AUDIT_WEIGHT_KEYS)
    _validate_policy(default_policy())


def test_weights_within_bounds_on_known_names_are_accepted():
    _validate_policy(_with_audit(
        field_weights={FIELD: AUDIT_WEIGHT_MIN}, collection_weights={COLLECTION: 1},
        doc_weights={DOC: AUDIT_WEIGHT_MAX}))


def test_a_weight_section_that_is_not_an_object_is_refused():
    with pytest.raises(DomainError, match="field_weights' must be an object"):
        _validate_policy(_with_audit(field_weights=[0.5]))


def test_a_weight_on_a_name_the_audit_does_not_score_is_refused():
    """A committee that ratified a weight on a misspelt field would believe it had
    re-weighted something it had not."""
    with pytest.raises(DomainError, match="'ownr' is not scored by the audit"):
        _validate_policy(_with_audit(field_weights={"ownr": 0.5}))


def test_an_exempt_field_cannot_be_weighted():
    with pytest.raises(DomainError, match="is not scored by the audit"):
        _validate_policy(_with_audit(field_weights={EXEMPT_FIELDS[0]: 0.5}))


@pytest.mark.parametrize("weight", [0, AUDIT_WEIGHT_MIN - 0.01, AUDIT_WEIGHT_MAX + 0.01,
                                    True, "0.5"])
def test_a_weight_out_of_bounds_or_not_a_number_is_refused(weight):
    """The floor is the point: a weight near zero makes a real gap vanish."""
    with pytest.raises(DomainError, match="must be a number from 0.10 to 2.00"):
        _validate_policy(_with_audit(doc_weights={DOC: weight}))


# --- The report states each division's basis ---------------------------------------

def _row(division, audit):
    return {**_audit({"division": division}, audit), "gaps": []}


def test_a_scored_row_carries_the_basis_it_was_scored_on():
    row = _audit({"division": "Rates"}, {"field_weights": {FIELD: 1.9}})
    assert row["division"] == "Rates"
    assert row["audit_policy"] == {"field_weights": {FIELD: 1.9}}


def test_the_seed_departs_from_nothing():
    """Compared by value: the seed copies every firm-wide setting onto the policy."""
    assert departures(default_policy()["audit"]) == []


def test_a_changed_setting_and_weight_are_both_departures():
    audit = {"untiered_weight": 0.5, "field_weights": {FIELD: 1.9}}
    assert departures(audit) == [
        ["Untiered weight", "0.90", "0.50"],
        [f"Field weight: {FIELD}", f"{FIELD_CRITICALITY[FIELD]:.2f}", "1.90"]]


def test_a_weight_restating_the_firm_wide_value_is_not_a_departure():
    assert departures({"doc_weights": {DOC: DOC_CRITICALITY[DOC]}}) == []


def test_no_division_departing_is_said_rather_than_left_blank():
    table = departures_table([_row("Rates", None), _row("", {"untiered_weight": 0.5})])
    assert "No division in this report departs" in table


def test_departures_are_listed_under_the_division_that_ratified_them():
    table = departures_table([_row("Rates", {"doc_weights": {DOC: 0.2}}),
                              _row("Credit", None)])
    assert "Rates" in table and "0.20" in table and "Credit" not in table


def test_the_report_prints_a_divisions_departures_in_its_appendix():
    rows = [_row("Rates", {"collection_weights": {COLLECTION: 0.2}})]
    tex = (build_completeness_tex(rows, {"fields": {}}, AS_OF)
           .replace("\\allowbreak{}", "").replace("\\_", "_"))
    assert "Division departures" in tex
    assert f"Collection weight: {COLLECTION}" in tex
