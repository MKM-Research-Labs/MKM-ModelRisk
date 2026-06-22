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

"""PDF assembly and entry point for the full audit report."""

from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, SimpleDocTemplate

from ._constants import AUDIT_DIR, OUTPUT_PDF
from .parsers import _parse_junit, _parse_coverage, _git_sha
from .styles import _styles
from .helpers import _header_footer
from .sections_overview import _build_cover, _build_exec_summary
from .sections_tests import (
    _build_test_detail, _build_coverage, _build_modularisation,
)
from .sections_hardcoding import _build_hardcoding
from .sections_embedded_js import _build_embedded_js
from .sections_lineage import _build_data_lineage
from .sections_e2e import _build_e2e, _build_roadmap


def create_pdf_report() -> Path:
    """Generate the full audit PDF and save to data/output/audit/."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    report_date = datetime.now()
    git_sha = _git_sha()

    print(' Parsing junit.xml …')
    junit = _parse_junit(AUDIT_DIR / 'junit.xml')

    print(' Parsing coverage.xml …')
    cov = _parse_coverage(AUDIT_DIR / 'coverage.xml')

    sty = _styles()

    story = []

    # Cover page
    story.extend(_build_cover(junit, cov, git_sha, report_date, sty))
    story.append(PageBreak())

    # Executive summary
    story.extend(_build_exec_summary(junit, cov, report_date, sty))
    story.append(PageBreak())

    # Test detail
    story.extend(_build_test_detail(junit, sty))
    story.append(PageBreak())

    # Coverage
    story.extend(_build_coverage(cov, sty))
    story.append(PageBreak())

    # Modularisation
    story.extend(_build_modularisation(sty))
    story.append(PageBreak())

    # Hard-coding audit
    story.extend(_build_hardcoding(sty))
    story.append(PageBreak())

    # Embedded JavaScript / CSS in Python (zero tolerance)
    story.extend(_build_embedded_js(sty))
    story.append(PageBreak())

    # Data lineage consistency
    story.extend(_build_data_lineage(sty))
    story.append(PageBreak())

    # E2E browser tests
    story.extend(_build_e2e(sty))
    story.append(PageBreak())

    # Roadmap
    story.extend(_build_roadmap(junit, cov, sty))

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=24 * mm,
        bottomMargin=14 * mm,
    )
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return OUTPUT_PDF


def main():
    print('Generating Full Audit Report …')
    out = create_pdf_report()
    size_kb = out.stat().st_size / 1024
    print(f' Written: {out}  ({size_kb:.1f} KB)')


if __name__ == '__main__':
    main()
