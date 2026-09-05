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
"""Enterprise-framework coverage: which clause is evidenced by what (rule R1).

The completeness audit asks whether each *record* is complete. This table asks a
question one level up: for each clause of an enterprise risk framework, what does
the platform hold that evidences it, and does the estate actually populate that?
It is the table an external assessor asks for and that nobody can answer from the
findings register alone.

Neither ISO 31000 nor COSO is a standard a *product* can be certified against --
ISO 31000 says in its own scope that it is guidance and not for certification,
and COSO is assessed at the institution. So nothing here claims compliance. What
it claims is narrower and checkable: this clause is evidenced by this record, and
this many models actually carry it.

Three clause outcomes are declared here rather than measured, because measuring
them would be a lie of precision:

``absent``       the platform holds no record that could evidence the clause. The
                 note says what would have to be built. An assessor reading a
                 blank cell learns nothing; reading "no ratified appetite
                 threshold exists" learns the finding.
``institution``  evidenced outside any tool -- culture, competence, resourcing.
                 Reported as out of scope rather than scored, because an audit
                 that marks a platform down for not holding the firm's training
                 records is measuring the wrong thing.
``partial``      the platform holds part of what the clause asks for. The note
                 says which part is missing.

Everything else names a probe in ``src.governance.completeness.framework``, which
counts the estate against it. The split is deliberate: the clause list and its
citations are an adopter's to re-set, the counting is not.

The clause references were taken from the published structure of each framework.
ISO 31000:2018 is a purchased standard, so an adopter citing it in a report an
assessor reads should check the references against their own licensed copy before
issue -- the mapping is the judgement here, the numbering is not.
"""
from __future__ import annotations

from config.governance._finos import FINOS_COVERAGE, FINOS_NOTES
from config.governance._ai_regimes import REGIME_COVERAGE, REGIME_NOTES
from config.governance._sr117 import SR_11_7_COVERAGE, SR_11_7_NOTES

# ---------------------------------------------------------------------------
# Outcome vocabulary.
# ---------------------------------------------------------------------------
# The four things the coverage table can say about a clause. Ordered best first;
# the report tallies them in this order.
COVERAGE_EVIDENCED = "Evidenced"
COVERAGE_PARTIAL = "Partially evidenced"
COVERAGE_ABSENT = "Not evidenced"
COVERAGE_OUTSIDE = "Outside the platform"

COVERAGE_STATES = (COVERAGE_EVIDENCED, COVERAGE_PARTIAL,
                   COVERAGE_ABSENT, COVERAGE_OUTSIDE)

# The share of the estate carrying a clause's evidence at which it reads
# Evidenced rather than Partially evidenced. Not 1.0: an estate is never all the
# way there on the day it is audited, and a table where every row reads Partial
# stops distinguishing "nearly done" from "not started" -- which is the one thing
# the reader wants from it. Anything above zero and below this is Partial; a
# clause no record evidences at all is Not evidenced.
COVERAGE_EVIDENCED_AT = 0.90

# Column widths for the coverage tables, as fractions of the text width. The
# evidence column carries the sentence a reader acts on, so it takes the room;
# the reference column is sized to hold the longest citation on one line, because
# a wrapped clause number reads as two clauses when the table is skimmed.
# Widened at the reference end when FINOS arrived: its citations are AIR-PREV-023
# rather than 5.4.3, and the rule above is that the column holds the longest citation
# in the report on one line. The room comes off the evidence column, which is wide
# enough to lose some -- a wrapped reference costs the reader more than a shorter
# line of prose does.
COVERAGE_CLAUSE_WEIGHTS = (0.20, 0.22, 0.14, 0.44)
# Same widening, and the framework column takes some too: it now has to hold
# "FINOS AIGF -- Mitigation catalogue" rather than "BCBS 239 (2013)". A framework
# NAME may wrap where a citation may not -- it reads as one name over two lines,
# where a wrapped reference reads as two references.
COVERAGE_ABSENT_WEIGHTS = (0.20, 0.20, 0.22, 0.38)

# Ratings that oblige a treatment plan, for the risk-treatment clauses. A Green
# record with no remediation against it is not an untreated risk, so counting it
# would report the best-kept records as the gaps. Which ratings oblige treatment
# is an institution's judgement, which is why it is data here.
TREATABLE_RATINGS = ("Red", "Amber")

# ---------------------------------------------------------------------------
# The frameworks.
# ---------------------------------------------------------------------------
from config.governance._frameworks_erm import (BCBS_239_PRINCIPLES,  # noqa: E402
                                               COSO_ERM_PRINCIPLES,
                                               ISO_31000_CLAUSES)
from config.governance._frameworks_names import BCBS_239, COSO_ERM, ISO_31000

# (reference, clause title, probe, note)
#
# The note is printed as the evidence when the probe is declared rather than
# measured, and appended to the count when it is measured.
# The frameworks the coverage section reports, in the order it reports them.
#
# FINOS enters as TWO entries rather than one, because it is two catalogues read
# differently -- see config/governance/_finos.py. The report renders one table per
# entry, so nothing here or in the counting needs to know that.
FRAMEWORK_COVERAGE = (
    (ISO_31000, ISO_31000_CLAUSES),
    (COSO_ERM, COSO_ERM_PRINCIPLES),
    (BCBS_239, BCBS_239_PRINCIPLES),
    *FINOS_COVERAGE,
    # SR 11-7 enters as a second DATA SET, not a second engine: its clauses name the
    # same probes every other framework's do, so both report through one code path.
    *SR_11_7_COVERAGE,
    # Regulatory regimes. Same shape, same engine, same row format — a
    # regime differs from a framework in that it APPLIES to some records and
    # not others, and that question is answered per record by
    # ``regimes_for``. The coverage table reports what the platform holds
    # against each obligation across the estate.
    *REGIME_COVERAGE,
)

# What a framework's table needs said before its rows, where the shared basis
# paragraph is not enough on its own. Keyed by framework name; a framework with
# nothing to add simply does not appear.
FRAMEWORK_NOTES = {**FINOS_NOTES, **SR_11_7_NOTES, **REGIME_NOTES}

# What the coverage section says it is and is not. Held here with the table it
# qualifies, because an adopter who re-points the table must re-word this with it.
COVERAGE_BASIS = (
    "No framework here certifies a software product: ISO 31000 states in its own "
    "scope that it is guidance rather than requirements, COSO is assessed at the "
    "institution, and BCBS 239 is supervisory guidance addressed to banks and their "
    "supervisors -- its own principles 12 to 14 are written for the supervisor. The "
    "FINOS AI Governance Framework is a catalogue contributed by member institutions "
    "and has no conformity scheme at all. This "
    "section therefore makes no compliance claim. It states, "
    "clause by clause, what the platform holds that evidences the clause and how "
    "much of the estate actually carries it -- so that the institution's own "
    "assessment has something to cite, and so that the clauses nothing evidences "
    "are named rather than left to be noticed."
)
