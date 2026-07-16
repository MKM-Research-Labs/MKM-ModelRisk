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
"""Coding-rule audit suite (large files, hardcoding, embedded JS, __init__, duplication)."""
from audit.coverage import coverage_summary, low_coverage_packages
from audit.data_access import data_access_findings
from audit.duplication import duplication_report, jscpd_available
from audit.embedded_js import embedded_js_findings
from audit.hardcoding import hardcoding_findings
from audit.init_files import init_file_findings
from audit.large_files import large_source_files, large_test_files, large_web_files
from audit.path_definitions import path_definition_findings

__all__ = [
    "large_source_files",
    "large_web_files",
    "large_test_files",
    "hardcoding_findings",
    "embedded_js_findings",
    "init_file_findings",
    "data_access_findings",
    "path_definition_findings",
    "coverage_summary",
    "low_coverage_packages",
    "duplication_report",
    "jscpd_available",
]
