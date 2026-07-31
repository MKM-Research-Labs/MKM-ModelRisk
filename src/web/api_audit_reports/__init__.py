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
"""HTTP API for generated audit report files, split into focused submodules.

The Generate action produces the full audit-evidence package into a single
directory — the per-rule and consolidated PDFs plus the ``__init__`` JSON export
immediately, and then (in the background, since the suite takes ~1 min) the
coverage/JUnit artefacts and the Test Report, mirroring PhysicalRisk where the
audit run itself drops coverage, JUnit and the browsable coverage HTML alongside
the reports. The tab lists every artefact, not only the PDFs.
"""
from src.web.api_audit_reports._bp import audit_reports_bp

# Side-effect imports attach every endpoint to audit_reports_bp; the blueprint and
# the shared output directory exist first, in _bp.
from src.web.api_audit_reports import generate, reports  # noqa: F401

__all__ = ["audit_reports_bp"]
