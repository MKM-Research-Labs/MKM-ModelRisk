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

"""Embedded JavaScript / CSS in Python audit section of the full audit report.

Zero-tolerance policy: front-end assets must live in companion ``.js`` / ``.css``
files under ``src/static/`` and be loaded at render time — never authored as
Python string literals. Any inline ``<script>`` block, inline ``<style>`` block,
or large JS "factory" string in a ``.py`` file is a violation.
"""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, _root, _TBL_STYLE_BASE
from .helpers import _status_colour


def _build_embedded_js(styles) -> list:
    elems = []
    elems.append(Paragraph(
        '6. Embedded JavaScript / CSS in Python (Zero Tolerance)', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Policy: front-end assets must live in companion <b>.js</b> / <b>.css</b> '
        'files under <b>src/static/</b> and be loaded at render time, never '
        'authored as Python string literals. This is a <b>zero-tolerance</b> '
        'check — any finding fails the audit. Three leak paths are scanned: '
        'inline <b>&lt;script&gt;</b> blocks of hand-written JavaScript, inline '
        '<b>&lt;style&gt;</b> blocks of CSS, and large JavaScript "factory" '
        'strings built without a <b>&lt;script&gt;</b> tag. Scope: all non-test '
        'source (src/, app/, config/, tools/, docs/).',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        from docs.models.embedded_js import collect_all_repo
        findings = collect_all_repo(_root)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run embedded JS/CSS scan: {exc}', styles['body']))
        return elems

    scripts = findings['scripts']
    stylesf = findings['styles']
    factories = findings['factories']
    n_total = len(scripts) + len(stylesf) + len(factories)
    overall = 'PASS' if n_total == 0 else 'FAIL'

    def _status(n):
        return 'OK' if n == 0 else 'FAIL'

    summary_data = [
        ['Category', 'Findings', 'Status'],
        ['.py files scanned', str(findings['files_scanned']), 'INFO'],
        ['Inline &lt;script&gt; blocks (JS in Python)', str(len(scripts)), _status(len(scripts))],
        ['Inline &lt;style&gt; blocks (CSS in Python)', str(len(stylesf)), _status(len(stylesf))],
        ['JS factory strings (no &lt;script&gt; tag)', str(len(factories)), _status(len(factories))],
        ['Files flagged', str(findings['files_flagged']), _status(findings['files_flagged'])],
        ['Overall', str(n_total) + ' violation(s)', overall],
    ]
    tbl_data = []
    for i, row in enumerate(summary_data):
        if i == 0:
            tbl_data.append([Paragraph(f'<b>{c}</b>', styles['tbl_hdr']) for c in row])
        else:
            status_str = row[2]
            status_col = _status_colour(status_str)
            tbl_data.append([
                Paragraph(row[0], styles['tbl_cell']),
                Paragraph(f'<b>{row[1]}</b>', styles['tbl_cell_r']),
                Paragraph(f'<b>{status_str}</b>',
                          ParagraphStyle('EJS', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=7.5, textColor=status_col,
                                         fontName='Helvetica-Bold')),
            ])
    tbl = Table(tbl_data, colWidths=[118 * mm, 20 * mm, 30 * mm])
    tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(tbl)
    elems.append(Spacer(1, 4 * mm))

    if n_total == 0:
        elems.append(Paragraph(
            'No JavaScript or CSS was found embedded in Python source. '
            '<b>PASS</b> — zero-tolerance policy satisfied.', styles['body']))
        return elems

    # Violation detail — one combined table, tagged by kind
    elems.append(Paragraph(
        f'Violations Requiring Extraction (showing up to 30 of {n_total}):',
        styles['h3']))
    det_data = [['File', 'Lines', 'Kind', 'JS/CSS lines']]
    rows = []
    for f in scripts:
        rows.append((f['file'], f['line'], f['end_line'], 'inline &lt;script&gt;', f['js_lines']))
    for f in stylesf:
        rows.append((f['file'], f['line'], f['end_line'], 'inline &lt;style&gt;', f['css_lines']))
    for f in factories:
        rows.append((f['file'], f['line'], f['end_line'], 'JS factory', f['js_lines']))
    rows.sort(key=lambda r: (r[0], r[1]))

    body_rows = [det_data[0]]
    for fname, ln, end, kind, n in rows[:30]:
        disp = fname if len(fname) <= 48 else '…' + fname[-46:]
        body_rows.append([
            Paragraph(disp, styles['tbl_cell']),
            Paragraph(f'{ln}–{end}', styles['tbl_cell_r']),
            Paragraph(kind, styles['tbl_cell']),
            Paragraph(str(n), styles['tbl_cell_r']),
        ])
    det_tbl_data = [
        [Paragraph(f'<b>{c}</b>', styles['tbl_hdr']) for c in body_rows[0]]
    ] + body_rows[1:]
    det_tbl = Table(det_tbl_data, colWidths=[88 * mm, 22 * mm, 36 * mm, 22 * mm])
    det_tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFEBEE')),
    ]))
    elems.append(det_tbl)

    return elems
