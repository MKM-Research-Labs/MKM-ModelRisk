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
"""The framework-coverage section says what the estate evidences, not what the
platform could evidence.

The failure this section exists to avoid is a table of green rows that an
assessor takes at face value. So the tests hold three things: a clause is
evidenced by records that exist rather than by a capability nobody has used, a
clause nothing could evidence is named in the report rather than left blank, and
no arithmetic can turn either of those into a compliance claim.
"""
from __future__ import annotations

from src.governance.latex import _wrappable
from config.governance import (
    COSO_ERM,
    COVERAGE_ABSENT,
    COVERAGE_EVIDENCED,
    COVERAGE_EVIDENCED_AT,
    COVERAGE_OUTSIDE,
    COVERAGE_PARTIAL,
    COVERAGE_STATES,
    FRAMEWORK_COVERAGE,
    ISO_31000,
    TREATABLE_RATINGS,
)
from src.governance.completeness.framework import (DECLARED, PROBES,
                                                   coverage, tally)
from src.governance.completeness.framework_report import framework_section

AS_OF = "2026-08-11"


def _model(model_id="M1", **data):
    return {"model_id": model_id, "data": {"name": "Alpha", **data}}


def _clause(clauses, framework, ref):
    return next(c for c in clauses if c["framework"] == framework and c["ref"] == ref)


def _cover(models, rows=None, ratified=()):
    return coverage(rows if rows is not None else [], models, AS_OF, ratified)


# ---------------------------------------------------------------------------
# The table itself.
# ---------------------------------------------------------------------------

def test_every_configured_clause_is_assessed_and_names_a_known_probe():
    """No clause may be listed and then quietly skipped: a citation with no
    outcome against it reads to an assessor as a clause that passed."""
    clauses = _cover([_model()])
    assert len(clauses) == sum(len(rows) for _name, rows in FRAMEWORK_COVERAGE)
    for clause in clauses:
        assert clause["state"] in COVERAGE_STATES
        assert clause["probe"] in PROBES or clause["probe"] in DECLARED
        assert clause["evidence"].strip()


def test_every_configured_framework_is_reported():
    frameworks = {c["framework"] for c in _cover([_model()])}
    assert frameworks == {name for name, _rows in FRAMEWORK_COVERAGE}


def test_tally_reconciles_to_the_clauses_it_counts():
    clauses = _cover([_model()])
    overall = tally(clauses)
    assert overall["clauses"] == len(clauses)
    assert sum(overall.get(state, 0) for state in COVERAGE_STATES) == len(clauses)
    per_framework = sum(tally(clauses, name)["clauses"] for name, _ in FRAMEWORK_COVERAGE)
    assert per_framework == len(clauses)


# ---------------------------------------------------------------------------
# Evidence is counted from records, never assumed from capability.
# ---------------------------------------------------------------------------

def test_an_empty_estate_evidences_nothing_it_would_have_to_count():
    """The reading this section must never produce: a platform that holds the
    capability reporting the clause as met while no record carries it."""
    clauses = _cover([])
    for clause in clauses:
        if clause["probe"] in PROBES:
            assert clause["state"] == COVERAGE_ABSENT, clause["ref"]
            assert "No applicable record" in clause["evidence"]


def test_a_populated_estate_evidences_the_clauses_it_carries():
    models = [_model(f"M{n}", tier=1, materiality="High", complexity="High",
                     rag_rating="Green", owner="Dana Cole")
              for n in range(3)]
    clauses = _cover(models)
    assert _clause(clauses, ISO_31000, "6.4.3")["state"] == COVERAGE_EVIDENCED
    assert _clause(clauses, ISO_31000, "5.4.3")["state"] == COVERAGE_EVIDENCED
    assert _clause(clauses, ISO_31000, "6.4.3")["evidence"].startswith("3 of 3")


def test_a_part_populated_estate_reads_partial_not_evidenced():
    """Two of three is progress, and must not print as compliance."""
    models = [_model("M1", owner="Dana Cole"), _model("M2", owner="Rob Ellis"),
              _model("M3")]
    clause = _clause(_cover(models), ISO_31000, "5.4.3")
    assert clause["state"] == COVERAGE_PARTIAL
    assert (clause["met"], clause["total"]) == (2, 3)
    assert 2 / 3 < COVERAGE_EVIDENCED_AT


def test_a_placeholder_is_not_evidence():
    """"TBD" reads to the register as filled and to an assessor as empty."""
    clause = _clause(_cover([_model("M1", owner="TBD")]), ISO_31000, "5.4.3")
    assert clause["state"] == COVERAGE_ABSENT


# ---------------------------------------------------------------------------
# The probes that carry a judgement of their own.
# ---------------------------------------------------------------------------

def test_a_model_reviewed_by_its_own_owner_is_not_independently_reviewed():
    """The check an assessor makes first, and the register cannot fail by itself."""
    same = _model("M1", owner="Dana Cole", peer_reviewer="dana cole ")
    assert _clause(_cover([same]), COSO_ERM, "2")["state"] == COVERAGE_ABSENT
    apart = _model("M1", owner="Dana Cole", peer_reviewer="Rob Ellis")
    assert _clause(_cover([apart]), COSO_ERM, "2")["state"] == COVERAGE_EVIDENCED


def test_inherited_criteria_are_not_adopted_criteria():
    """A division on the firm-wide seed default has criteria but has not defined
    any, which is what ISO 6.3.4 actually asks for."""
    models = [_model("M1", division="Markets")]
    assert _clause(_cover(models), ISO_31000, "6.3.4")["state"] == COVERAGE_ABSENT
    ratified = _cover(models, ratified={"Markets"})
    assert _clause(ratified, ISO_31000, "6.3.4")["state"] == COVERAGE_EVIDENCED


def test_only_the_ratings_that_oblige_treatment_are_counted_against_it():
    """A Green record with no remediation is not an untreated risk, and counting
    it would report the best-kept records as the gaps."""
    assert "Green" not in TREATABLE_RATINGS
    green = [_model("M1", rag_rating="Green")]
    clause = _clause(_cover(green), ISO_31000, "6.5.3")
    assert (clause["state"], clause["total"]) == (COVERAGE_ABSENT, 0)
    treated = [_model("M1", rag_rating="Red",
                      remediation_steps=[{"description": "Rebuild the calibration"}]),
               _model("M2", rag_rating="Green")]
    clause = _clause(_cover(treated), ISO_31000, "6.5.3")
    assert (clause["state"], clause["met"], clause["total"]) == (COVERAGE_EVIDENCED, 1, 1)


def test_a_review_overdue_at_the_report_date_is_not_monitoring():
    overdue = _model("M1", next_review_date="2026-01-01")
    assert _clause(_cover([overdue]), ISO_31000, "6.6")["state"] == COVERAGE_ABSENT
    scheduled = _model("M1", next_review_date="2026-12-01")
    assert _clause(_cover([scheduled]), ISO_31000, "6.6")["state"] == COVERAGE_EVIDENCED


def test_an_unparseable_review_date_is_not_treated_as_in_date():
    """A date the platform cannot read is not assurance that a review is booked."""
    clause = _clause(_cover([_model("M1", next_review_date="next spring")]),
                     ISO_31000, "6.6")
    assert clause["state"] == COVERAGE_ABSENT


def test_reporting_clauses_count_the_records_this_audit_covers():
    """Products count here as well as models: the report is the evidence."""
    rows = [{"entity_id": "M1"}, {"entity_id": "P1"}]
    clause = _clause(_cover([_model()], rows=rows), ISO_31000, "6.7")
    assert (clause["state"], clause["met"], clause["total"]) == (COVERAGE_EVIDENCED, 2, 2)
    assert _clause(_cover([_model()], rows=rows), COSO_ERM, "12")["met"] == 2


def test_a_review_under_way_counts_as_review_and_revision():
    started = _model("M1", review_progress=[{"stage": "Scoping"}])
    assert _clause(_cover([started]), COSO_ERM, "16")["state"] == COVERAGE_EVIDENCED
    assert _clause(_cover([_model()]), COSO_ERM, "16")["state"] == COVERAGE_ABSENT


def test_committee_and_challenge_read_the_records_that_carry_them():
    signed = _model("M1", mrc_signoff_date="2026-06-01")
    assert _clause(_cover([signed]), ISO_31000, "5.2")["state"] == COVERAGE_EVIDENCED
    challenged = _model("M1", review_notes=[{"kind": "Challenge"}])
    assert _clause(_cover([challenged]), ISO_31000, "6.2")["state"] == COVERAGE_EVIDENCED
    versioned = _model("M1", version_history=[{"version": "1.1"}])
    assert _clause(_cover([versioned]), COSO_ERM, "15")["state"] == COVERAGE_EVIDENCED
    identified = _model("M1", limitations=[{"description": "Extrapolates"}])
    assert _clause(_cover([identified]), ISO_31000, "6.4.2")["state"] == COVERAGE_EVIDENCED
    rated = _model("M1", rag_rating="Amber")
    assert _clause(_cover([rated]), ISO_31000, "6.4.4")["state"] == COVERAGE_EVIDENCED
    assert _clause(_cover([_model()]), ISO_31000, "5.5")["state"] == COVERAGE_EVIDENCED


# ---------------------------------------------------------------------------
# The clauses nothing can evidence.
# ---------------------------------------------------------------------------

def test_declared_outcomes_do_not_move_however_complete_the_estate_is():
    """Appetite, context and framework review are absent from the platform, not
    from the register: no amount of good record-keeping can close them, and a
    table that let them drift green would be the section's worst failure."""
    full = [_model(f"M{n}", tier=1, materiality="High", complexity="High",
                   rag_rating="Red", owner="Dana Cole", peer_reviewer="Rob Ellis",
                   division="Markets", next_review_date="2026-12-01",
                   mrc_signoff_date="2026-06-01", version_history=[{"version": "1.0"}],
                   review_notes=[{"kind": "Challenge"}], limitations=[{"d": "x"}],
                   remediation_steps=[{"description": "Fix"}],
                   review_signoffs=[{"signed_at": "2026-07-01"}])
            for n in range(5)]
    clauses = _cover(full, rows=[{"entity_id": "M1"}], ratified={"Markets"})
    assert _clause(clauses, COSO_ERM, "7")["state"] == COVERAGE_ABSENT      # appetite
    assert _clause(clauses, ISO_31000, "5.4.1")["state"] == COVERAGE_ABSENT  # context
    assert _clause(clauses, ISO_31000, "5.6")["state"] == COVERAGE_ABSENT    # evaluation
    assert _clause(clauses, ISO_31000, "5.7")["state"] == COVERAGE_ABSENT    # improvement
    assert _clause(clauses, COSO_ERM, "14")["state"] == COVERAGE_PARTIAL     # portfolio
    assert _clause(clauses, COSO_ERM, "3")["state"] == COVERAGE_OUTSIDE      # culture


def test_the_absent_clauses_say_what_would_have_to_be_built():
    """A blank cell teaches an assessor nothing; the finding is the sentence."""
    appetite = _clause(_cover([_model()]), COSO_ERM, "7")
    assert "ratified" in appetite["evidence"] and "threshold" in appetite["evidence"]


# ---------------------------------------------------------------------------
# The section as rendered.
# ---------------------------------------------------------------------------

def test_the_section_makes_no_compliance_claim():
    """ISO 31000 is guidance, not a certification, and COSO is assessed at the
    institution. The section must say so where a reader cannot miss it."""
    tex = framework_section([], [_model()], AS_OF)
    assert "compliance claim" in tex
    assert "certif" in tex


def test_the_section_lists_every_clause_and_repeats_the_unevidenced_ones():
    tex = framework_section([{"entity_id": "M1"}], [_model()], AS_OF)
    for framework, _rows in FRAMEWORK_COVERAGE:
        assert framework in tex
    for _framework, rows in FRAMEWORK_COVERAGE:
        for _ref, title, _probe, _note in rows:
            # Through _wrappable, because that is how the cell is rendered: a title
            # carrying a slash ("Home/host cooperation") gains a break hint, and a
            # citation keeps its published spelling rather than being reworded to
            # suit an assertion.
            assert _wrappable(title) in tex, title
    assert "Not evidenced" in tex
    assert tex.count("Defines Risk Appetite") == 2  # in its table, and again alone


def test_the_unevidenced_list_is_omitted_when_there_is_nothing_to_list(monkeypatch):
    """The one case where silence is right: an adopter whose framework the estate
    fully evidences gets the tables, not an empty "nothing is missing" heading."""
    covered = ((ISO_31000, (("5.5", "Implementing the framework", "inventory", "."),)),)
    monkeypatch.setattr("src.governance.completeness.framework_report."
                        "FRAMEWORK_COVERAGE", covered)
    monkeypatch.setattr("src.governance.completeness.framework."
                        "FRAMEWORK_COVERAGE", covered)
    tex = framework_section([], [_model()], AS_OF)
    assert "Implementing the framework" in tex
    assert "Not evidenced" not in tex


def test_the_section_disappears_rather_than_printing_an_empty_table(monkeypatch):
    """An adopter who configures no framework gets no section, not a heading with
    nothing under it."""
    monkeypatch.setattr("src.governance.completeness.framework_report."
                        "FRAMEWORK_COVERAGE", ())
    assert framework_section([], [_model()], AS_OF) == ""
