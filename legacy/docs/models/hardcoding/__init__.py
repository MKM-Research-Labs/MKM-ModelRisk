# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.

# This software is licensed by MKM Research Labs for non-commercial 
# research and educational use only. Any commercial use, including 
# but not limited to use in or for products or services offered for sale, 
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.

# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Hard-Coding Audit — Parameter Governance Report.

Scans all src/*.py files for parameters that should live in config.py
but are defined as hard-coded literals elsewhere.  Generates a PDF
audit report aligned with the SR 11-7 / SS1/23 model governance framework.

Policy: every configurable domain parameter must be defined once in config.py
and imported at every use site.  Hard-coding distributes parameters across
files, making them easy to miss when recalibration or deployment changes
are required.

Output:  data/output/audit/hardcoding_report.pdf

Usage:
    python -m docs.models.hardcoding
"""

from .scanners import (
    _src_files,
    _rel,
    _parse_module_constants,
    _extract_value,
    _is_allcaps,
    _is_numeric_or_aggregate,
    _PRECISION_CONSTANTS,
    scan_duplicate_constants,
    scan_allcaps_outside_config,
    scan_infrastructure_literals,
    scan_inline_simulation_literals,
    collect_all,
)
from .pdf_helpers import (
    _risk_colour,
    _risk_label,
    _styles,
    _header_style,
    _severity_badge_colour,
    _section_rule,
)
from .pdf import create_pdf_report
from .report import main

__all__ = [
    'scan_duplicate_constants', 'scan_allcaps_outside_config',
    'scan_infrastructure_literals', 'scan_inline_simulation_literals',
    'collect_all', 'create_pdf_report', 'main',
]
