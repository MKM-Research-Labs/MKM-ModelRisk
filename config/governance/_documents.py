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
"""Document categories (coding rule R1)."""

# Every document category is surfaced in exactly one place, so a document is never
# listed twice in the console. The category still identifies the document wherever
# it is read back (the Model Risk Report groups by it), and uploads may use any of
# them; these tuples only decide which panel offers and lists each one.

# The Docs tab: the model's own documentation and the analysis supporting it.
# Sensitivity sits beside Core Documentation rather than inside Analysis: it is an
# adjunct to the model's own write-up — how the model responds as its inputs move —
# where Analysis is the wider work done about the model.
# Testing sits between Analysis and Monitoring: it is part of the documentation
# somebody reads about a model, not a separate concern with its own tab. It is a
# GROUP rather than a category — the evidence is filed under four categories (the
# overall pack plus one per test type) and they belong together on one panel.
TESTING_TAB_LABEL = "Testing"
# The Review tab lists the SIGNED reports a review produces — the issued document, not
# the reviewer's working papers, which stay beside the stage that produced them. It is a
# group for the same reason Testing is: the tab is called "Review", nothing is filed under
# that name here, and the panel resolves to the report category.
REVIEW_TAB_LABEL = "Review"
DOC_TAB_CATEGORIES = ("Core Documentation", "Sensitivity", "Analysis", TESTING_TAB_LABEL,
                      REVIEW_TAB_LABEL, "Monitoring", "History")

# The Review tab's first stage: the preliminary pack a reviewer works from, and
# whatever else the review generates as it runs. Offered beside the stage it
# belongs to rather than on the Docs tab, exactly as the testing evidence is, so
# a document is listed where the work that produced it happened — never twice.
# The signed output is filed apart from the working papers: the committee is given
# the report, not the reviewer's drafts, and only one of the two is a document
# anybody should be tabling.
REVIEW_REPORT_CATEGORY = "Model Review Report"
REVIEW_DOC_CATEGORIES = ("Review", REVIEW_REPORT_CATEGORY)

# Generated Model Risk Documents, filed under History. The document is rendered
# from the inventory as it stood at the moment it was issued, so a filed copy is
# the record of what the model looked like then — the second time axis alongside
# the audit trail's "when we were told". Written by the platform, not uploaded.
HISTORY_DOC_CATEGORY = "History"

# The categories the MRC can table for review against a model in scope. The paper
# lives on the model and is referenced from the meeting, so a committee always
# reviews the document the model actually holds rather than a copy of it.
MRC_REVIEWABLE_CATEGORIES = ("Sensitivity", "Analysis", "Test Results",
                             REVIEW_REPORT_CATEGORY)

# The Testing tab. "Test Results" is the overall evidence pack; the other three back
# the in-context upload panel beside each unit / integration / benchmark test field.
TESTING_DOC_CATEGORIES = ("Test Results", "Unit Test", "Integration Test", "Benchmark Test")

# Attached in context on the Events and Remediation tabs, beside the item they
# evidence, so they are not offered as standalone Docs categories.
EVIDENCE_DOC_CATEGORIES = ("Event Evidence", "Remediation Evidence")

# Which of the Docs tabs is a group, and over what. The label is not itself a
# category — nothing is ever filed under "Testing" — so anything counting or
# listing documents has to resolve the group to its real categories first.
# The Review panel lists every report a review has issued, the way History lists every
# Model Risk Document: the sign-off stage links the current one, and this is the archive.
DOC_TAB_GROUPS = {TESTING_TAB_LABEL: TESTING_DOC_CATEGORIES,
                  REVIEW_TAB_LABEL: (REVIEW_REPORT_CATEGORY,)}

# Every category a document can actually carry. The group label is excluded on
# purpose: it names a panel, not a filing place.
DOC_CATEGORIES = (tuple(c for c in DOC_TAB_CATEGORIES if c not in DOC_TAB_GROUPS)
                  + TESTING_DOC_CATEGORIES + EVIDENCE_DOC_CATEGORIES
                  + REVIEW_DOC_CATEGORIES)

# --- Artefacts: what the institution ISSUES ---------------------------------
# The Documents tab's second panel. Filed per division, plus a company-wide shelf for
# what belongs to the institution rather than to one division (the user guide, a
# firm-wide standard). The kinds are what an adopter files here in practice; they label
# a tile, so an unfamiliar one is a wording change, not a schema change.
COMPANY_WIDE_SHELF = "Company-wide"
ARTEFACT_KINDS = ("Terms of Reference", "Presentation", "Policy", "Guide", "Template",
                  "Other")

# --- Ongoing monitoring -----------------------------------------------------
# The artefacts an adopting institution's portfolio generator leaves behind, and
# the label each carries in the monitoring document's activity table. These
# names are ours; an adopter replaces them with its own, exactly as it replaces
# the classification banner and legal notice in config/reporting.py. Nothing
# below is a platform constant — it is the vocabulary of one estate.
#
# Only the canonical files are listed: a catchment holds many derived variants
# (…bri, …baw, …hc) that restate the same population through one model's lens,
# and counting those would report the same portfolio several times over.
PORTFOLIO_FILES = (
    ("property.json", "Properties"),
    ("commercial.json", "Commercial properties"),
    ("commercial_loan.json", "Commercial loans"),
    ("mortgage.json", "Mortgages"),
    ("gauge.json", "Gauges"),
    ("counterparty.json", "Counterparties"),
)

# What a monitoring document says where a catchment directory exists but holds no
# portfolio, and where the platform has no production activity at all. Ongoing
# monitoring is a real obligation, so the document states the position plainly
# rather than going quiet: an absent document and one that records "nothing yet"
# are very different things to an auditor.
NO_PORTFOLIO_STATEMENT = (
    "No portfolio has been generated for this catchment, so no monitoring "
    "observations arise from it."
)
# Said when the configured portfolio location does not resolve at all. Kept
# distinct from "the estate is empty": an adopter who has not yet pointed
# PRODUCER_PORTFOLIO_DIR at their generator would otherwise get a document
# reporting nought catchments as though that were the finding, rather than being
# told the platform never looked anywhere useful.
NO_SOURCE_STATEMENT = (
    "No portfolio source is configured for this installation, so no exercise "
    "record can be drawn. The monitoring position recorded below against each "
    "weakness and limitation therefore rests on the inventory alone. Point the "
    "platform at the portfolio generator's output to populate this section."
)
NO_PRODUCTION_STATEMENT = (
    "The portfolios below are generated test portfolios, not client business. "
    "Monitoring therefore records that the model has been exercised and against "
    "which population, rather than reporting exceptions from production use. "
    "Ongoing monitoring becomes substantive once real portfolios are onboarded, "
    "at which point the triggers recorded against each weakness and limitation "
    "below are the conditions this document will report against."
)
