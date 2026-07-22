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
DOC_TAB_CATEGORIES = ("Core Documentation", "Analysis", "Monitoring")

# The Testing tab. "Test Results" is the overall evidence pack; the other three back
# the in-context upload panel beside each unit / integration / benchmark test field.
TESTING_DOC_CATEGORIES = ("Test Results", "Unit Test", "Integration Test", "Benchmark Test")

# Attached in context on the Events and Remediation tabs, beside the item they
# evidence, so they are not offered as standalone Docs categories.
EVIDENCE_DOC_CATEGORIES = ("Event Evidence", "Remediation Evidence")

DOC_CATEGORIES = DOC_TAB_CATEGORIES + TESTING_DOC_CATEGORIES + EVIDENCE_DOC_CATEGORIES
