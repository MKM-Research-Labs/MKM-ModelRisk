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

"""Full audit report generator (SR 11-7 / SS1/23 model governance).

This package assembles a 9-section PDF audit covering test results, code
coverage, modularisation (incl. the __init__.py audit), hard-coding, embedded
JavaScript/CSS in Python, data lineage, and E2E browser tests. Invoke via
``python -m docs.models.full_audit``. All functional code lives in the
submodules below; this file is a pure re-export façade.
"""

from ._constants import (
    AUDIT_DIR, SRC_DIR, OUTPUT_PDF,
    NAVY, STEEL, BLUE, LIGHT_BG, HEADER_BG, GREEN, AMBER, RED, GREY,
    _TBL_STYLE_BASE, _root,
)
from .styles import _styles
from .parsers import _parse_junit, _parse_coverage, _git_sha
from .helpers import (
    _metric_box, _load_json_report, _status, _status_inv, _status_colour,
    _map_sev, _header_footer,
)
from .sections_overview import _build_cover, _build_exec_summary
from .sections_tests import (
    _build_test_detail, _build_coverage, _build_modularisation,
    _build_init_audit, _build_copyright_headers, _build_path_definitions,
    _build_data_access,
)
from .sections_hardcoding import _build_hardcoding
from .sections_embedded_js import _build_embedded_js
from .sections_lineage import _build_data_lineage
from .sections_e2e import _build_e2e, _build_roadmap
from .report import create_pdf_report, main

__all__ = [
    'AUDIT_DIR', 'SRC_DIR', 'OUTPUT_PDF',
    'NAVY', 'STEEL', 'BLUE', 'LIGHT_BG', 'HEADER_BG',
    'GREEN', 'AMBER', 'RED', 'GREY', '_TBL_STYLE_BASE', '_root',
    '_styles',
    '_parse_junit', '_parse_coverage', '_git_sha',
    '_metric_box', '_load_json_report', '_status', '_status_inv',
    '_status_colour', '_map_sev', '_header_footer',
    '_build_cover', '_build_exec_summary',
    '_build_test_detail', '_build_coverage', '_build_modularisation',
    '_build_init_audit', '_build_copyright_headers', '_build_path_definitions',
    '_build_data_access', '_build_hardcoding', '_build_embedded_js',
    '_build_data_lineage', '_build_e2e', '_build_roadmap',
    'create_pdf_report', 'main',
]
