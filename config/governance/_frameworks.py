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
ISO_31000 = "ISO 31000:2018"
COSO_ERM = "COSO ERM (2017)"
BCBS_239 = "BCBS 239 (2013)"

# (reference, clause title, probe, note)
#
# The note is printed as the evidence when the probe is declared rather than
# measured, and appended to the count when it is measured.
ISO_31000_CLAUSES = (
    ("4", "Principles", "institution",
     "Evidenced through the framework and process clauses below rather than "
     "asserted in its own right."),
    ("5.2", "Leadership and commitment", "committee",
     "Committee sign-off recorded against the model."),
    ("5.3", "Integration", "institution",
     "Whether risk management is embedded in the firm's decision-making is an "
     "organisational fact, not a record the platform can hold."),
    ("5.4.1", "Understanding the organisation and its context", "absent",
     "No context record exists. Internal and external context would have to be "
     "recorded, versioned and reviewed on a cycle."),
    ("5.4.2", "Articulating risk management commitment", "partial",
     "The per-division risk policy is ratified and versioned, but it states the "
     "rating criteria rather than a firm-wide commitment to manage risk."),
    ("5.4.3", "Assigning roles, authorities, responsibilities, accountabilities",
     "accountability", "Named owner on the record."),
    ("5.4.4", "Allocating resources", "institution",
     "Budget, headcount and tooling are recorded outside the platform."),
    ("5.4.5", "Establishing communication and consultation", "challenge",
     "Attributed, append-only challenge and sign-off record."),
    ("5.5", "Implementing the framework", "inventory",
     "Models on the register and under governance."),
    ("5.6", "Evaluation of the framework", "absent",
     "The division policies are ratified but never re-reviewed on a cycle, and "
     "the audit keeps no history of its own results, so no trend can be shown."),
    ("5.7", "Improvement", "absent",
     "Nothing records a change made to the framework in response to a finding."),
    ("6.2", "Communication and consultation", "challenge",
     "Attributed, append-only challenge and sign-off record."),
    ("6.3.2", "Defining the scope", "absent",
     "The scope of the risk management activity itself is not recorded."),
    ("6.3.3", "External and internal context", "absent",
     "See 5.4.1 -- no context record exists."),
    ("6.3.4", "Defining risk criteria", "criteria",
     "Division risk policy ratified by its committee."),
    ("6.4.2", "Risk identification", "identification",
     "Assumptions, limitations and weaknesses recorded."),
    ("6.4.3", "Risk analysis", "analysis",
     "Mission-criticality, materiality and complexity all rated."),
    ("6.4.4", "Risk evaluation", "evaluation",
     "Rating assigned against the ratified criteria."),
    ("6.5.2", "Selection of risk treatment options", "absent",
     "A remediation step records what will be done, but not which option was "
     "chosen -- accept, reduce, transfer or avoid -- nor the residual risk left "
     "after it, nor who accepted that residual and until when."),
    ("6.5.3", "Preparing and implementing treatment plans", "treatment",
     "Remediation recorded where the rating calls for it."),
    ("6.6", "Monitoring and review", "monitoring",
     "Review scheduled and not overdue."),
    ("6.7", "Recording and reporting", "reporting",
     "Append-only event log, issued governance documents and this audit."),
)

# COSO principle titles keep their published spelling rather than being
# anglicised: they are citations, and an assessor searches for the exact wording.
COSO_ERM_PRINCIPLES = (
    ("1", "Exercises Board Risk Oversight", "committee",
     "Committee sign-off recorded against the model."),
    ("2", "Establishes Operating Structures", "independence",
     "Reviewer recorded and distinct from the owner."),
    ("3", "Defines Desired Culture", "institution",
     "A cultural assessment is not a platform record."),
    ("4", "Demonstrates Commitment to Core Values", "institution",
     "Evidenced by conduct and policy outside the platform."),
    ("5", "Attracts, Develops and Retains Capable Individuals", "institution",
     "Competence and training records sit in the firm's HR system."),
    ("6", "Analyzes Business Context", "absent",
     "See ISO 5.4.1 -- no context record exists."),
    ("7", "Defines Risk Appetite", "absent",
     "Appetite exists only as prose in a rating band description. There is no "
     "ratified, versioned threshold, so no breach can be detected and no "
     "aggregate position can be stated against it."),
    ("8", "Evaluates Alternative Strategies", "institution",
     "A strategy decision, taken outside the platform."),
    ("9", "Formulates Business Objectives", "institution",
     "Objectives are set outside the platform."),
    ("10", "Identifies Risk", "identification",
     "Assumptions, limitations and weaknesses recorded."),
    ("11", "Assesses Severity of Risk", "analysis",
     "Mission-criticality, materiality and complexity all rated."),
    ("12", "Prioritizes Risks", "prioritisation",
     "Every finding scored, banded and given a remediation date by this audit."),
    ("13", "Implements Risk Responses", "treatment",
     "Remediation recorded where the rating calls for it."),
    ("14", "Develops Portfolio View", "partial",
     "The audit aggregates the estate and ranks it, but with no ratified "
     "appetite to compare against it cannot say whether the portfolio position "
     "is acceptable -- only what it is."),
    ("15", "Assesses Substantial Change", "change",
     "Version history recorded against the model."),
    ("16", "Reviews Risk and Performance", "review",
     "Review under way or signed off."),
    ("17", "Pursues Improvement in Enterprise Risk Management", "absent",
     "See ISO 5.7 -- no record of a framework change made in response to a "
     "finding, and no audit history to show movement."),
    ("18", "Leverages Information and Technology", "inventory",
     "Models on the register and under governance."),
    ("19", "Communicates Risk Information", "challenge",
     "Attributed, append-only challenge and sign-off record."),
    ("20", "Reports on Risk, Culture and Performance", "reporting",
     "Append-only event log, issued governance documents and this audit."),
)

# BCBS 239's fourteen principles, in the Committee's own grouping. Principles 12-14
# are addressed to SUPERVISORS rather than to the bank, so they are reported as
# outside the platform rather than scored -- marking a product down for not holding a
# supervisor's review is measuring the wrong thing, and pretending otherwise would
# inflate the count with rows nobody can act on.
#
# The lineage principles are the ones the ML Training tab actually moves: a snapshot
# identifier and a source-dataset reference are what 3 and 4 ask for, and free-text
# training notes cannot supply either.
BCBS_239_PRINCIPLES = (
    ("1", "Governance", "committee",
     "Committee sign-off recorded against the record."),
    ("2", "Data architecture and IT infrastructure", "partial",
     "A record names its data sources and its place in the model chain, but the "
     "firm's data architecture is not described here and no probe could stand for it."),
    ("3", "Accuracy and integrity", "identification",
     "Assumptions, limitations and weaknesses recorded. For an ML Application the "
     "train's snapshot identifier ties a reported figure to the data it came from."),
    ("4", "Completeness", "inventory",
     "Records on the register and under governance."),
    ("5", "Timeliness", "monitoring",
     "Review scheduled and not overdue. Note this measures the governance cycle, not "
     "the latency of the underlying risk data, which the platform does not see."),
    ("6", "Adaptability", "absent",
     "Nothing here answers an ad hoc request for risk data. The register is queryable "
     "by record, not by exposure."),
    ("7", "Accuracy (reporting)", "reporting",
     "Append-only event log, issued governance documents and this audit."),
    ("8", "Comprehensiveness", "analysis",
     "Every dimension rated on every record."),
    ("9", "Clarity and usefulness", "reporting",
     "Issued documents are generated from the record rather than transcribed from it."),
    ("10", "Frequency", "review",
     "Review under way or signed off, on the cycle the record carries."),
    ("11", "Distribution", "partial",
     "Documents are filed against the record and tabled at the committee, but who "
     "received a report, and when, is not tracked."),
    ("12", "Review", "institution",
     "A supervisory principle: addressed to the supervisor, not to the bank."),
    ("13", "Remedial actions and supervisory measures", "treatment",
     "Remediation recorded where the rating calls for it."),
    ("14", "Home/host cooperation", "institution",
     "A supervisory principle, and one between authorities rather than within a firm."),
)

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
)

# What a framework's table needs said before its rows, where the shared basis
# paragraph is not enough on its own. Keyed by framework name; a framework with
# nothing to add simply does not appear.
FRAMEWORK_NOTES = {**FINOS_NOTES, **SR_11_7_NOTES}

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
