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

"""Section 3: code coverage analysis (per-package, lowest first)."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, STEEL, GREEN, AMBER, RED, _TBL_STYLE_BASE


def _build_coverage(cov: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('3. Code Coverage Analysis', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    all_pkg_rows = cov['by_package']
    if not all_pkg_rows:
        cov_pct = cov['line_rate'] * 100
        elems.append(Paragraph(
            f'Overall line coverage: <b>{cov_pct:.2f}%</b> '
            f'({cov["lines_covered"]:,} of {cov["lines_valid"]:,} lines).',
            styles['body']))
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph('No per-package coverage data available.', styles['body']))
        return elems

    full_cov_count = sum(1 for _, r, _, _ in all_pkg_rows if r >= 100)
    cov_pct = cov['line_rate'] * 100
    elems.append(Paragraph(
        f'Overall line coverage: <b>{cov_pct:.2f}%</b> '
        f'({cov["lines_covered"]:,} of {cov["lines_valid"]:,} lines). '
        'Packages are sorted by coverage rate ascending — lowest coverage first. '
        f'{full_cov_count} package(s) with 100% coverage are omitted.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    pkg_rows = all_pkg_rows

    # Exclude packages with 100% coverage — only show those needing attention
    pkg_rows = [(n, r, v, c) for n, r, v, c in pkg_rows if r < 100]
    if not pkg_rows:
        elems.append(Paragraph(
            'All packages have 100% line coverage.', styles['body']))
        return elems

    tbl_data = [[
        Paragraph('<b>Package</b>', styles['tbl_hdr']),
        Paragraph('<b>Coverage</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines Valid</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines Covered</b>', styles['tbl_hdr']),
        Paragraph('<b>Gap</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for name, rate, valid, covered in pkg_rows:
        gap = valid - covered
        rate_col = GREEN if rate >= 90 else (AMBER if rate >= 70 else RED)
        short_name = name if len(name) <= 55 else '…' + name[-52:]
        tbl_data.append([
            Paragraph(short_name, styles['tbl_cell']),
            Paragraph(f'{rate:.1f}%',
                      ParagraphStyle('CovPct', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, textColor=rate_col,
                                     fontName='Helvetica-Bold')),
            Paragraph(str(valid), styles['tbl_cell_r']),
            Paragraph(str(covered), styles['tbl_cell_r']),
            Paragraph(str(gap) if gap else '—',
                      ParagraphStyle('Gap', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=RED if gap > 50 else STEEL)),
        ])
        if rate < 70:
            idx = len(tbl_data) - 1
            row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                colors.HexColor('#FFEBEE')))

    tbl = Table(tbl_data, colWidths=[78 * mm, 22 * mm, 22 * mm, 26 * mm, 20 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
    elems.append(tbl)

    # Summary counts
    below_90 = sum(1 for _, r, v, _ in pkg_rows if r < 90 and v >= 10)
    below_70 = sum(1 for _, r, v, _ in pkg_rows if r < 70 and v >= 10)
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        f'Packages with &lt;90% coverage: <b>{below_90}</b> &nbsp;|&nbsp; '
        f'Packages with &lt;70% coverage: <b>{below_70}</b> '
        f'(excluding trivial packages with &lt;10 lines).',
        styles['body']))

    return elems
