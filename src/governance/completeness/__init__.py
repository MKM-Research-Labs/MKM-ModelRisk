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
"""The completeness audit: which governance fields and documents are missing,
scored so the register reads as a remediation plan rather than a list.
"""
from src.governance.completeness.report import (
    build_completeness_tex,
    render_completeness_pdf,
)
from src.governance.completeness.framework import coverage, tally
from src.governance.completeness.framework_report import framework_section
from src.governance.completeness.scan import findings, ratified_divisions, scan
from src.governance.completeness._rules import (
    audit_entity,
    band,
    event_pressure,
    rag_multiplier,
    staleness,
    tier_weight,
)

__all__ = [
    "audit_entity", "band", "build_completeness_tex", "coverage",
    "event_pressure", "findings", "framework_section", "rag_multiplier",
    "ratified_divisions", "render_completeness_pdf", "scan", "staleness",
    "tally", "tier_weight",
]
