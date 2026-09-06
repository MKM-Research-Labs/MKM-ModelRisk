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
"""A model's peer reviewer may not be its own owner.

Two halves that have to agree. The domain rule refuses the write that would
create a breach; the audit reports the breaches an estate already has, because a
rule enforced only going forward leaves the existing register asserting an
independence it never had.

The case these tests exist for is the one a completeness score cannot see: owner
and reviewer both recorded, both the same person. The record reads as fully
governed on both fields, and is the first one an assessor pulls.
"""
from __future__ import annotations

import pytest

from config.governance import REVIEWER_INDEPENDENCE, RULE_SPECS, SEVERITY_BANDS
from src.governance.completeness._gaps import _rule_gaps, _rules_carried
from src.governance.completeness._rules import audit_entity
from src.governance.errors import DomainError
from src.governance.model_inventory._rules import (
    decide_register,
    decide_update_field,
)
from src.governance.model_inventory._state import ModelState
from src.identity import same_person


def _state(**fields):
    return ModelState(exists=True, retired=False, fields=fields)


# ---------------------------------------------------------------------------
# The matcher.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("one,other", [
    ("Dana Cole", "dana cole"),
    ("Dana Cole", "  Dana   Cole  "),
    ("dana@corp", "DANA@CORP"),
])
def test_the_same_person_recorded_differently_still_matches(one, other):
    """Casing and stray whitespace are how the breach gets past a naive check."""
    assert same_person(one, other)


@pytest.mark.parametrize("one,other", [
    ("Dana Cole", "Rob Ellis"),
    ("", ""),
    (None, None),
    ("Dana Cole", ""),
    ("R. Ellis", "Rob Ellis"),   # an alias this cannot catch, and must not claim to
])
def test_distinct_or_absent_identities_do_not_match(one, other):
    assert not same_person(one, other)


# ---------------------------------------------------------------------------
# The write is refused.
# ---------------------------------------------------------------------------

def test_a_reviewer_cannot_be_set_to_the_models_own_owner():
    with pytest.raises(DomainError) as raised:
        decide_update_field(_state(owner="Dana Cole"),
                            field="peer_reviewer", value="dana cole")
    assert "not an independent one" in str(raised.value)
    assert "Dana Cole" in str(raised.value)


def test_the_owner_cannot_be_moved_onto_the_existing_reviewer():
    """The other side of the pair. A rule enforced on one side is not enforced:
    the same breach is one edit away from the owner field."""
    with pytest.raises(DomainError):
        decide_update_field(_state(peer_reviewer="Rob Ellis"),
                            field="owner", value="Rob Ellis")


def test_a_model_cannot_be_registered_in_breach():
    with pytest.raises(DomainError):
        decide_register(ModelState(), model_id="M1", name="Alpha",
                        fields={"owner": "Dana Cole", "peer_reviewer": "Dana Cole"})


def test_a_distinct_reviewer_is_accepted_on_both_paths():
    event, payload = decide_update_field(_state(owner="Dana Cole"),
                                         field="peer_reviewer", value="Rob Ellis")
    assert payload["value"] == "Rob Ellis"
    _event, payload = decide_register(
        ModelState(), model_id="M1", name="Alpha",
        fields={"owner": "Dana Cole", "peer_reviewer": "Rob Ellis"})
    assert payload["peer_reviewer"] == "Rob Ellis"


def test_a_record_already_in_breach_stays_editable_everywhere_else():
    """Locking the record would leave its owner unable to correct anything about
    it, including the breach's own counterpart."""
    breached = _state(owner="Dana Cole", peer_reviewer="Dana Cole")
    _event, payload = decide_update_field(breached, field="description",
                                          value="A pricing model")
    assert payload["value"] == "A pricing model"
    # And the way out of the breach is open from either field.
    assert decide_update_field(breached, field="peer_reviewer", value="Rob Ellis")
    assert decide_update_field(breached, field="owner", value="Priya Anand")


def test_the_rule_can_be_stood_down_for_a_migration(monkeypatch):
    # Patched on src.governance.independence, which is where the rule lives since it
    # stopped being a model-only one. One switch stands it down for every record type,
    # which is the point of there being one implementation.
    monkeypatch.setattr("src.governance.independence."
                        "ENFORCE_REVIEWER_INDEPENDENCE", "never")
    _event, payload = decide_update_field(_state(owner="Dana Cole"),
                                          field="peer_reviewer", value="Dana Cole")
    assert payload["value"] == "Dana Cole"


# ---------------------------------------------------------------------------
# The breach is reported.
# ---------------------------------------------------------------------------

def test_a_breach_is_raised_as_a_finding_with_an_instruction():
    gaps = _rule_gaps({"owner": "Dana Cole", "peer_reviewer": "Dana Cole"})
    assert [g["key"] for g in gaps] == [REVIEWER_INDEPENDENCE]
    assert gaps[0]["kind"] == "rule"
    assert gaps[0]["criticality"] == RULE_SPECS[REVIEWER_INDEPENDENCE]["criticality"]
    assert "other than its owner" in gaps[0]["template"]


def test_a_clean_record_raises_nothing_and_is_credited_for_it():
    clean = {"owner": "Dana Cole", "peer_reviewer": "Rob Ellis"}
    assert _rule_gaps(clean) == []
    assert _rules_carried(clean) == RULE_SPECS[REVIEWER_INDEPENDENCE]["criticality"]


def test_a_rule_that_cannot_be_assessed_is_neither_a_finding_nor_credit():
    """With no owner recorded there is nothing to be independent of, and the
    missing owner is already a finding in its own right — charging for it twice
    would rank an unowned model above a self-reviewed one."""
    for data in ({"peer_reviewer": "Rob Ellis"}, {"owner": "Dana Cole"}, {}):
        assert _rule_gaps(data) == []
        assert _rules_carried(data) == 0


def test_a_breach_is_scored_and_ranked_alongside_the_absences():
    """It goes through the same escalation as every other finding, so it competes
    for the top of the remediation register instead of sitting in an annex."""
    scored = audit_entity(
        entity_kind="Model", entity_id="M1", entity_name="Alpha",
        data={"owner": "Dana Cole", "peer_reviewer": "Dana Cole"},
        field_specs={}, collection_specs={}, doc_categories=(),
        risk={"heatmap": {"rag": "Red"}, "events_in_window": 0}, as_of="2026-08-11")
    gap = next(g for g in scored["gaps"] if g["kind"] == "rule")
    assert gap["band"] in [label for label, _floor in SEVERITY_BANDS]
    assert gap["sla_days"] > 0
    # The instruction comes from the rule's own template, not the generic one.
    assert gap["action"] == ("Name a peer reviewer for the model other than its "
                             "owner, or record why the owner's review is treated "
                             "as independent.")
    # Rated Red, so it escalates above its bare criticality rather than sitting flat.
    assert gap["severity"] > gap["criticality"]


def test_a_breach_costs_the_record_exactly_what_a_clean_one_earns():
    """Otherwise the rule either depresses every score or flatters every record."""
    breach = {"owner": "Dana Cole", "peer_reviewer": "Dana Cole"}
    clean = {"owner": "Dana Cole", "peer_reviewer": "Rob Ellis"}
    assert sum(g["criticality"] for g in _rule_gaps(breach)) == _rules_carried(clean)
    assert _rules_carried(breach) == 0
