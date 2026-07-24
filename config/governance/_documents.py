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
DOC_TAB_CATEGORIES = ("Core Documentation", "Sensitivity", "Analysis", "Monitoring",
                      "History")

# Generated Model Risk Documents, filed under History. The document is rendered
# from the inventory as it stood at the moment it was issued, so a filed copy is
# the record of what the model looked like then — the second time axis alongside
# the audit trail's "when we were told". Written by the platform, not uploaded.
HISTORY_DOC_CATEGORY = "History"

# The categories the MRC can table for review against a model in scope. The paper
# lives on the model and is referenced from the meeting, so a committee always
# reviews the document the model actually holds rather than a copy of it.
MRC_REVIEWABLE_CATEGORIES = ("Sensitivity", "Analysis", "Test Results")

# The Testing tab. "Test Results" is the overall evidence pack; the other three back
# the in-context upload panel beside each unit / integration / benchmark test field.
TESTING_DOC_CATEGORIES = ("Test Results", "Unit Test", "Integration Test", "Benchmark Test")

# Attached in context on the Events and Remediation tabs, beside the item they
# evidence, so they are not offered as standalone Docs categories.
EVIDENCE_DOC_CATEGORIES = ("Event Evidence", "Remediation Evidence")

DOC_CATEGORIES = DOC_TAB_CATEGORIES + TESTING_DOC_CATEGORIES + EVIDENCE_DOC_CATEGORIES

# --- Ongoing monitoring -----------------------------------------------------
# The portfolio files a completed port run leaves in each catchment directory,
# and the label each carries in the monitoring document's activity table. Only
# these are counted: a catchment holds many derived variants (…bri, …baw, …hc)
# that restate the same population through one model's lens, and counting those
# would report the same portfolio several times over.
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
NO_PRODUCTION_STATEMENT = (
    "The portfolios below are generated test portfolios, not client business. "
    "Monitoring therefore records that the model has been exercised and against "
    "which population, rather than reporting exceptions from production use. "
    "Ongoing monitoring becomes substantive once real portfolios are onboarded, "
    "at which point the triggers recorded against each weakness and limitation "
    "below are the conditions this document will report against."
)
