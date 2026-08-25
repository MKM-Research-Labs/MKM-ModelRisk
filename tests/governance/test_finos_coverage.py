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

The risk catalogue is counted from the register. The mitigation catalogue is not:
a mitigation is a control the institution runs, and what a governance record can
attest is that the firm has DESCRIBED it -- so those rows are evidenced by a
document filed on the FINOS shelf naming the reference.

The failures worth guarding are all failures of that distinction. A merged table
would let an exposure read as a control. A mitigation row evidenced by anything
other than a naming document would be a claim about a control operating, which
this platform cannot see. And a row that says "1 of 1" instead of naming its
document has told the assessor nothing they can check.
"""
from __future__ import annotations

from config.governance import (COVERAGE_ABSENT, COVERAGE_EVIDENCED,
                               FRAMEWORK_COVERAGE, FRAMEWORK_NOTES)
from config.governance._finos import (EVIDENCE_PROBE, FINOS_COVERAGE,
                                      FINOS_MITIGATIONS, FINOS_RISKS)
from src.governance.completeness.framework import coverage, tally

AS_OF = "2026-08-25"


def _model(model_id="M1", **data):
    return {"model_id": model_id, "data": {"name": "Alpha", **data}}


def _doc(name="finos-mitigations-2026.pdf", refs=(), uploaded="2026-08-25T09:12:00Z"):
    return {"original_name": name, "uploaded_at": uploaded, "finos_refs": list(refs)}


def _tested(model_id="M1"):
    """A record carrying the acceptance-testing evidence, so a test about the
    DOCUMENT-evidenced rows is not also measuring the one register-evidenced row."""
    return _model(model_id, unit_tests="Yes", integration_tests="Yes",
                  benchmark_tests="Yes")


def _cover(models=None, evidence=()):
    models = [_model()] if models is None else models
    return coverage(models, models, AS_OF, (), evidence)


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
    assert len(risks) == 23 and len(mitigations) == 23


def test_each_catalogue_carries_its_own_note():
    """The shared basis paragraph describes clause lists read one way. These two
    are read differently from each other, and say so above their own rows."""
    for name in (FINOS_RISKS, FINOS_MITIGATIONS):
        assert FRAMEWORK_NOTES[name].strip()
    assert "filed on the FINOS shelf" in FRAMEWORK_NOTES[FINOS_MITIGATIONS]
    # The mitigation note must not let the table be read as a control test.
    assert "not a statement that the control was" in FRAMEWORK_NOTES[FINOS_MITIGATIONS]


def test_every_reference_is_a_finos_identifier_and_unique():
    refs = [ref for _name, rows in FINOS_COVERAGE for ref, *_ in rows]
    assert len(set(refs)) == len(refs) == 46
    assert all(ref.startswith("AIR-") for ref in refs)


# ---------------------------------------------------------------------------
# Mitigations: evidenced by a filed document, and by nothing else.
# ---------------------------------------------------------------------------

def test_an_empty_shelf_leaves_every_mitigation_unevidenced():
    """An institution that has filed nothing has evidenced nothing. The register
    being well kept says nothing at all about the firm's AI controls."""
    counts = tally(_cover([_tested()], evidence=[]), FINOS_MITIGATIONS)
    assert counts["clauses"] == 23
    # All 22 document-evidenced rows, and only those: acceptance testing is
    # evidenced from the register and is unaffected by an empty shelf.
    assert counts[COVERAGE_ABSENT] == 22
    assert counts[COVERAGE_EVIDENCED] == 1


def test_one_document_moves_exactly_the_rows_it_names():
    """Many-to-one on purpose: one control paper covers what it covers, and
    tagging is how the firm says which. Nothing else may move."""
    clauses = _cover(evidence=[_doc(refs=["AIR-PREV-002", "AIR-PREV-017", "AIR-DET-011"])])
    named = {"AIR-PREV-002", "AIR-PREV-017", "AIR-DET-011"}
    evidenced = {c["ref"] for c in clauses
                 if c["framework"] == FINOS_MITIGATIONS
                 and c["state"] == COVERAGE_EVIDENCED and c["probe"] == EVIDENCE_PROBE}
    assert evidenced == named


def test_the_evidence_names_the_document_and_the_date_it_was_filed():
    """Not "1 of 1", which measures nothing. The assessor is owed something they
    can go and read, and the date it was written."""
    clauses = _cover(evidence=[_doc(name="agent-controls.pdf", refs=["AIR-PREV-018"],
                                    uploaded="2026-08-25T09:12:00Z")])
    evidence = _row(clauses, FINOS_MITIGATIONS, "AIR-PREV-018")["evidence"]
    assert "agent-controls.pdf" in evidence
    assert "filed 2026-08-25" in evidence
    assert "1 of 1" not in evidence


def test_several_documents_may_evidence_one_mitigation():
    clauses = _cover(evidence=[_doc(name="policy.pdf", refs=["AIR-PREV-014"]),
                               _doc(name="appendix.pdf", refs=["AIR-PREV-014"])])
    evidence = _row(clauses, FINOS_MITIGATIONS, "AIR-PREV-014")["evidence"]
    assert "policy.pdf" in evidence and "appendix.pdf" in evidence


def test_an_unrecognised_reference_is_inert():
    """Tags are normalised for shape and never checked for membership, so a
    catalogue edit cannot invalidate a document already filed. The cost of that
    is a tag nobody recognises, and it must simply count for nothing."""
    clauses = _cover([_tested()],
                     evidence=[_doc(refs=["AIR-PREV-999", "not a reference"])])
    counts = tally(clauses, FINOS_MITIGATIONS)
    assert counts[COVERAGE_ABSENT] == 22


def test_an_unevidenced_mitigation_says_where_the_document_would_go():
    """A blank cell teaches an assessor nothing; this row has to name the gap."""
    evidence = _row(_cover(), FINOS_MITIGATIONS, "AIR-PREV-003")["evidence"]
    assert "No document on the FINOS shelf names this reference." in evidence


def test_acceptance_testing_is_evidenced_from_the_register():
    """The one mitigation the platform holds itself. Reporting it unevidenced
    because nobody had also written a paper about it would be the register
    disowning evidence it already has."""
    tested = _model(unit_tests="Yes", integration_tests="Yes", benchmark_tests="Yes")
    row = _row(_cover([tested]), FINOS_MITIGATIONS, "AIR-PREV-005")
    assert row["state"] == COVERAGE_EVIDENCED
    assert row["probe"] != EVIDENCE_PROBE
    assert _row(_cover([_model()]), FINOS_MITIGATIONS,
                "AIR-PREV-005")["state"] == COVERAGE_ABSENT


# ---------------------------------------------------------------------------
# Risks: counted from the register, and honest that most cannot be.
# ---------------------------------------------------------------------------

def test_filed_documents_never_evidence_a_risk():
    """Risks are exposures, not controls. A paper describing a control does not
    make the exposure go away, and must not colour a single risk row."""
    with_docs = _cover(evidence=[_doc(refs=[ref for _n, rows in FINOS_COVERAGE
                                            for ref, *_ in rows])])
    without = _cover(evidence=[])
    assert (tally(with_docs, FINOS_RISKS) == tally(without, FINOS_RISKS))


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
