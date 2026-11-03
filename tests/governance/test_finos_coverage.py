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
"""FINOS coverage: two catalogues, read two different ways.

The risk catalogue is exposures, counted from the register. The mitigation
catalogue is controls, and lists only the ones the register itself evidences. The
failure worth guarding is a merged table, which would let an exposure read as a
control.
"""
from __future__ import annotations

from config.governance import (COVERAGE_ABSENT, COVERAGE_EVIDENCED,
                               FRAMEWORK_COVERAGE, FRAMEWORK_NOTES)
from config.governance._finos import (FINOS_COVERAGE, FINOS_MITIGATIONS,
                                      FINOS_RISKS)
from src.governance.completeness.framework import coverage, tally

AS_OF = "2026-08-25"


def _model(model_id="M1", **data):
    return {"model_id": model_id, "data": {"name": "Alpha", **data}}


def _cover(models=None):
    models = [_model()] if models is None else models
    return coverage(models, models, AS_OF, ())


def _row(clauses, framework, ref):
    return next(c for c in clauses if c["framework"] == framework and c["ref"] == ref)


# ---------------------------------------------------------------------------
# The two catalogues are two tables, and stay two tables.
# ---------------------------------------------------------------------------

def test_the_catalogues_are_reported_separately():
    """Never merged. A reader who cannot tell an exposure from a response to one
    has been given a table that means nothing."""
    names = [name for name, _rows in FRAMEWORK_COVERAGE]
    assert FINOS_RISKS in names and FINOS_MITIGATIONS in names
    assert FINOS_RISKS != FINOS_MITIGATIONS

    clauses = _cover()
    risks = {c["ref"] for c in clauses if c["framework"] == FINOS_RISKS}
    mitigations = {c["ref"] for c in clauses if c["framework"] == FINOS_MITIGATIONS}
    assert not risks & mitigations
    assert len(risks) == 23 and len(mitigations) == 2


def test_each_catalogue_carries_its_own_note():
    """The shared basis paragraph describes clause lists read one way. These two
    are read differently from each other, and say so above their own rows."""
    for name in (FINOS_RISKS, FINOS_MITIGATIONS):
        assert FRAMEWORK_NOTES[name].strip()
    # The mitigation note must say the catalogue is partial, or a reader will take
    # two rows for the whole of it.
    assert "not reported here" in FRAMEWORK_NOTES[FINOS_MITIGATIONS]


def test_every_reference_is_a_finos_identifier_and_unique():
    refs = [ref for _name, rows in FINOS_COVERAGE for ref, *_ in rows]
    assert len(set(refs)) == len(refs) == 25
    assert all(ref.startswith("AIR-") for ref in refs)


# ---------------------------------------------------------------------------
# Mitigations: only those the register evidences.
# ---------------------------------------------------------------------------

def test_acceptance_testing_is_evidenced_from_the_register():
    """Counted from the record, like any other register-evidenced row."""
    tested = _model(unit_tests="Yes", integration_tests="Yes", benchmark_tests="Yes")
    row = _row(_cover([tested]), FINOS_MITIGATIONS, "AIR-PREV-005")
    assert row["state"] == COVERAGE_EVIDENCED
    assert _row(_cover([_model()]), FINOS_MITIGATIONS,
                "AIR-PREV-005")["state"] == COVERAGE_ABSENT


# ---------------------------------------------------------------------------
# Risks: counted from the register, and honest that most cannot be.
# ---------------------------------------------------------------------------

def test_the_agentic_risks_are_named_as_unevidenced_rather_than_omitted():
    """The platform has no record for a generative or agentic system. That is a
    finding an assessor is owed in words, not an absence they have to notice."""
    clauses = _cover()
    for ref in ("AIR-SEC-010", "AIR-SEC-026", "AIR-OP-028", "AIR-OP-016"):
        row = _row(clauses, FINOS_RISKS, ref)
        assert row["state"] == COVERAGE_ABSENT
        assert row["evidence"].strip()


def test_a_risk_row_counted_from_the_estate_moves_with_the_estate():
    """The three measured rows are measured, not declared: a better-kept register
    moves them, which is the whole basis on which this table is worth reading."""
    empty = _row(_cover([_model()]), FINOS_RISKS, "AIR-RC-022")
    signed = _row(_cover([_model(mrc_signoff_date="2026-07-01")]), FINOS_RISKS,
                  "AIR-RC-022")
    assert empty["state"] == COVERAGE_ABSENT
    assert signed["state"] == COVERAGE_EVIDENCED
