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
"""SR 11-7 as a second data set for the coverage engine, not a second engine.

The mapping engine already answers "what does the platform hold that evidences this
clause, and how much of the estate carries it" for ISO 31000, COSO, BCBS 239 and the
two FINOS catalogues. SR 11-7 is the supervisory guidance this platform is most
directly built around, and it enters the same way every other framework does: a list of
clauses, each naming a probe the counting already knows. Nothing here computes
anything.

That is the whole point of the step. A second evidencing mechanism -- SR 11-7 coverage
resolved some other way -- is how two reports come to disagree about whether the same
model is validated, and then neither is used.

**No compliance claim.** SR 11-7 is supervisory guidance addressed to banks and their
examiners; a software product is not examined against it and cannot conform to it. What
these rows state is narrower and checkable: this clause is evidenced by this record,
and this share of the estate carries it. Several clauses are marked ``institution``
because they are about people -- an internal audit function, competent staff,
management attention -- and a platform that scored itself on those would be measuring
the wrong thing.

The section references follow the published structure of the 2011 guidance (Federal
Reserve SR 11-7 / OCC 2011-12). An adopter citing them in a document an examiner reads
should check them against their own copy: the MAPPING is the judgement offered here,
the numbering is not.
"""
from __future__ import annotations

SR_11_7 = "SR 11-7 -- Supervisory guidance on model risk management"

# (reference, title, probe or declared outcome, note)
#
# ``institution`` and ``absent`` are declared rather than measured, exactly as they are
# for every other framework: measuring them would be a lie of precision. The note on a
# declared row says what would have to exist, because an assessor reading a blank cell
# learns nothing.
SR_11_7_CLAUSES = (
    ("III", "Model risk management framework", "criteria",
     "The division's own risk criteria, ratified by its committee. A division still "
     "running on the firm-wide seed has criteria but not criteria it has adopted, and "
     "this counts only the adopted ones."),
    ("IV.A", "Model development and implementation", "analysis",
     "The record's own account of what it is and how it is rated: tier, materiality "
     "and complexity, each with the rationale beside it."),
    ("IV.B", "Model use", "identification",
     "What the model assumes, where it may not be used, and what it does badly. Use is "
     "governed by the limitations agreed on the record rather than by a statement that "
     "it is used appropriately."),
    ("V.A", "Validation: evaluation of conceptual soundness", "challenge",
     "The record of challenge between owner and reviewer, and the committee sign-offs "
     "that followed it. Conceptual soundness is evidenced by the argument, not by a "
     "box saying it was evaluated."),
    ("V.B", "Validation: ongoing monitoring", "monitoring",
     "Whether the record's monitoring is in date as at the report date. A monitoring "
     "approach nobody has exercised is not ongoing monitoring."),
    ("V.C", "Validation: outcomes analysis", "evaluation",
     "The rating the outcome analysis produced. What the platform does NOT yet read "
     "here is a backtest result against realised outcomes -- the measures exist "
     "(src/governance/monitoring/measures) but nothing files their output against a "
     "record, so this row counts the rating rather than the arithmetic behind it."),
    ("V.D", "Validation of vendor and third-party products", "absent",
     "The vendor is named on the record and vendor documents can be filed against it, "
     "but nothing distinguishes a vendor model's validation obligations from an "
     "in-house one's -- no record of what the vendor supplied, what was withheld, or "
     "what the institution tested for itself."),
    ("VI.A", "Governance: policies and procedures", "criteria",
     "The division's ratified risk policy is the procedure this platform holds. The "
     "firm's wider model risk policy is a document it files, not a record it keeps."),
    ("VI.B", "Governance: roles and responsibilities", "accountability",
     "A named owner on every record. Roles beyond ownership are held as RACI entries "
     "and are not counted here, because a record may legitimately carry none."),
    ("VI.C", "Governance: internal audit", "institution",
     "Whether internal audit assesses the framework's effectiveness is a fact about "
     "the institution's audit function. A platform reporting on its own audit coverage "
     "would be marking its own homework."),
    ("VI.D", "Governance: external resources", "institution",
     "Whether outsourced validation work is overseen appropriately is a judgement "
     "about how the firm manages its suppliers."),
    ("VI.E", "Model inventory", "inventory",
     "Every registered record. The guidance's central requirement and the one the "
     "platform answers most directly -- an inventory is what it is."),
    ("VI.F", "Documentation", "reporting",
     "Every audited record appears in this report, scored and banded. Documentation "
     "SUFFICIENCY is a separate question the completeness audit asks record by record; "
     "this row says only that the record is documented at all."),
    # Independence is not a numbered section of its own — it runs through V and VI —
    # but it is the single most-cited expectation in the guidance and the platform
    # measures it directly, so it is reported rather than folded into V.A.
    ("V", "Validation: independence of the reviewer", "independence",
     "The reviewer is somebody other than the owner. Measured on the record rather "
     "than asserted in a policy document."),
)

SR_11_7_COVERAGE = ((SR_11_7, SR_11_7_CLAUSES),)

SR_11_7_NOTES = {
    SR_11_7: (
        "SR 11-7 is supervisory guidance addressed to banks and their examiners, not a "
        "standard a product conforms to. These rows state what the platform holds "
        "against each section and how much of the estate carries it; the institution's "
        "own assessment is what an examiner reads. Sections VI.C and VI.D are marked "
        "as evidenced outside any tool because they are about the firm's audit "
        "function and its suppliers."
    ),
}

__all__ = ["SR_11_7", "SR_11_7_CLAUSES", "SR_11_7_COVERAGE", "SR_11_7_NOTES"]
