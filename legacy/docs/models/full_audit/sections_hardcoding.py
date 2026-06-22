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

"""Hard-coding audit section of the full audit report."""

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, SRC_DIR, _root, _TBL_STYLE_BASE
from .helpers import _status_inv, _status_colour


def _build_hardcoding(styles) -> list:
    elems = []
    elems.append(Paragraph('5. Hard-Coding Audit', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Policy: every configurable domain parameter must be defined once in '
        'config.py and imported at every use site. '
        'This section reports parameters found as hard-coded literals outside '
        'config.py.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        from docs.models.hardcoding import collect_all
        findings = collect_all(SRC_DIR, _root)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run hard-coding scan: {exc}', styles['body']))
        return elems

    files_scanned = findings['files_scanned']
    n_dup = len(findings['duplicates'])
    allcaps = findings['allcaps']
    caps_action = [f for f in allcaps if not f.get('precision_ok', False)]
    n_infra = len(findings['infra'])
    n_inline = len(findings['inline'])

    # Summary table
    summary_data = [
        ['Category', 'Findings', 'Status'],
        ['Files scanned', str(files_scanned), 'INFO'],
        ['Duplicate constants (same name, multiple files)',
         str(n_dup), _status_inv(n_dup == 0, n_dup <= 3)],
        ['ALL_CAPS constants outside config.py (action required)',
         str(len(caps_action)), _status_inv(len(caps_action) == 0, len(caps_action) <= 10)],
        ['ALL_CAPS constants (precision/tolerance — acceptable)',
         str(len(allcaps) - len(caps_action)), 'OK'],
        ['Infrastructure literals (IP / port)',
         str(n_infra), _status_inv(n_infra == 0, n_infra <= 2)],
        ['Inline simulation parameters',
         str(n_inline), _status_inv(n_inline == 0, n_inline <= 3)],
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
                          ParagraphStyle('HCS', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=7.5, textColor=status_col,
                                         fontName='Helvetica-Bold')),
            ])
    tbl = Table(tbl_data, colWidths=[118 * mm, 20 * mm, 30 * mm])
    tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(tbl)
    elems.append(Spacer(1, 4 * mm))

    # Duplicate constants detail
    if findings['duplicates']:
        elems.append(Paragraph(
            'Duplicate Constants (defined in multiple files):', styles['h3']))
        dup_data = [['Constant', 'Files']]
        for item in findings['duplicates'][:15]:
            locs = item.get('locations', [])
            files_str = ', '.join(loc[0] for loc in locs[:4])
            if len(locs) > 4:
                files_str += f' (+{len(locs) - 4} more)'
            dup_data.append([
                Paragraph(f'<b>{item["name"]}</b>', styles['tbl_cell']),
                Paragraph(files_str, styles['tbl_cell']),
            ])
        dup_tbl = Table(dup_data, colWidths=[40 * mm, 128 * mm])
        dup_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(dup_tbl)
        elems.append(Spacer(1, 3 * mm))

    # ALL_CAPS action items
    if caps_action:
        elems.append(Paragraph(
            f'ALL_CAPS Constants Requiring Migration to config.py '
            f'(showing up to 20 of {len(caps_action)}):',
            styles['h3']))
        ac_data = [['File', 'Line', 'Constant', 'Value']]
        for item in caps_action[:20]:
            ac_data.append([
                Paragraph(item['file'][:50], styles['tbl_cell']),
                Paragraph(str(item['line']), styles['tbl_cell_r']),
                Paragraph(f'<b>{item["name"]}</b>', styles['tbl_cell']),
                Paragraph(str(item['value'])[:20], styles['tbl_cell']),
            ])
        ac_tbl = Table(ac_data, colWidths=[75 * mm, 12 * mm, 52 * mm, 29 * mm])
        ac_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(ac_tbl)

    return elems
