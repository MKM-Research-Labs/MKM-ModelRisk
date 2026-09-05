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
"""The three enterprise-risk frameworks' clause tables.

Split from ``_frameworks``, which is now what its name says: the registry that
assembles every framework the coverage section reports. FINOS, SR 11-7 and the
regulatory regimes already lived in their own modules and were imported into it; these
three were the last ones still inline, and the file was carrying both the tables and
the assembly.

The clause references follow each framework's published structure. ISO 31000:2018 is a
purchased standard, so an adopter citing it in a report an assessor reads should check
the references against their own licensed copy — the mapping is the judgement here, the
numbering is not.
"""
from __future__ import annotations

from config.governance._frameworks_names import (BCBS_239, COSO_ERM,  # noqa: F401
                                                 ISO_31000)

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

__all__ = ["BCBS_239_PRINCIPLES", "COSO_ERM_PRINCIPLES", "ISO_31000_CLAUSES"]
