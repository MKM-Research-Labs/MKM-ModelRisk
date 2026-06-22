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

"""Section 4: code modularisation + the __init__.py substantive-code audit."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, GREEN, AMBER, RED, _TBL_STYLE_BASE, _root


def _build_modularisation(styles) -> list:
    elems = []
    elems.append(Paragraph('4. Code Modularisation', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    try:
        from docs.models.project import analyze_repo_files
        all_files, large_files = analyze_repo_files(_root)
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run modularisation scan: {exc}', styles['body']))
        return elems

    total_files = len(all_files)
    total_large = len(large_files)

    elems.append(Paragraph(
        f'Scope: <b>all non-test source</b> (src/, app/, config/, tools/, docs/) '
        f'&nbsp;|&nbsp; Files scanned: <b>{total_files}</b> &nbsp;|&nbsp; '
        f'Files over 300 lines: <b>{total_large}</b>. '
        'Files exceeding 300 raw lines are candidates for modularisation.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    if not large_files:
        elems.append(Paragraph(
            'No files exceed the 300-line threshold.', styles['body']))
    else:
        tbl_data = [[
            Paragraph('<b>File (relative to project root)</b>', styles['tbl_hdr']),
            Paragraph('<b>Ext</b>', styles['tbl_hdr']),
            Paragraph('<b>Lines</b>', styles['tbl_hdr']),
            Paragraph('<b>Priority</b>', styles['tbl_hdr']),
        ]]
        row_extras = []
        for fi in large_files[:40]:
            rel = str(fi.relative_path)
            if len(rel) > 70:
                rel = '…' + rel[-68:]
            lc = fi.line_count
            priority = 'High' if lc > 600 else ('Medium' if lc > 400 else 'Low')
            p_col = RED if lc > 600 else (AMBER if lc > 400 else GREEN)

            tbl_data.append([
                Paragraph(rel, styles['tbl_cell']),
                Paragraph(fi.extension, styles['tbl_cell']),
                Paragraph(str(lc), styles['tbl_cell_r']),
                Paragraph(f'<b>{priority}</b>',
                          ParagraphStyle('Pri', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=8, textColor=p_col,
                                         fontName='Helvetica-Bold')),
            ])
            if lc > 600:
                idx = len(tbl_data) - 1
                row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                    colors.HexColor('#FFF3E0')))

        tbl = Table(tbl_data, colWidths=[108 * mm, 14 * mm, 18 * mm, 28 * mm])
        tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
        elems.append(tbl)

        if total_large > 40:
            elems.append(Spacer(1, 2 * mm))
            elems.append(Paragraph(
                f'Showing top 40 of {total_large} files over threshold.',
                styles['small']))

    # 4.1 — __init__.py substantive-code audit
    elems.extend(_build_init_audit(styles))

    # 4.2 — copyright/license-header audit
    from .copyright_headers import _build_copyright_headers
    elems.extend(_build_copyright_headers(styles))

    # 4.3 — path-definition audit (paths housed in config)
    from .path_definitions import _build_path_definitions
    elems.extend(_build_path_definitions(styles))

    # 4.4 — data-access audit (DB access housed in src/database)
    from .data_access import _build_data_access
    elems.extend(_build_data_access(styles))

    return elems


def _build_init_audit(styles) -> list:
    """Subsection 4.1: flag __init__.py files that contain functions, classes,
    or route decorators — substantive code that should live in a dedicated
    module, not in a package initialiser."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('4.1 __init__.py Substantive-Code Audit', styles['h3']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Policy: <b>__init__.py</b> files must only wire a package together — '
        'imports, re-exports, <b>__all__</b>, and Blueprint assignment. Any '
        'function, class, or route/view decorator defined directly in an '
        'initialiser should be moved to a dedicated module.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    try:
        from docs.models.project import analyze_init_files
        issues = analyze_init_files(_root / 'src')
    except Exception as exc:
        elems.append(Paragraph(
            f'Could not run __init__.py audit: {exc}', styles['body']))
        return elems

    if not issues:
        elems.append(Paragraph(
            'No __init__.py file contains substantive code. '
            '<b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'{len(issues)} __init__.py file(s) contain substantive code '
        f'(showing up to 25):', styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = [[
        Paragraph('<b>File (relative to src/)</b>', styles['tbl_hdr']),
        Paragraph('<b>Lines</b>', styles['tbl_hdr']),
        Paragraph('<b>Functions</b>', styles['tbl_hdr']),
        Paragraph('<b>Classes</b>', styles['tbl_hdr']),
        Paragraph('<b>Routes</b>', styles['tbl_hdr']),
    ]]
    for it in issues[:25]:
        rel = it.relative_path
        if len(rel) > 60:
            rel = '…' + rel[-58:]
        data.append([
            Paragraph(rel, styles['tbl_cell']),
            Paragraph(str(it.line_count), styles['tbl_cell_r']),
            Paragraph(str(len(it.functions)), styles['tbl_cell_r']),
            Paragraph(str(len(it.classes)), styles['tbl_cell_r']),
            Paragraph(str(it.routes), styles['tbl_cell_r']),
        ])
    tbl = Table(data, colWidths=[96 * mm, 16 * mm, 22 * mm, 18 * mm, 16 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
    ]))
    elems.append(tbl)

    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Full breakdown (with function/class names per file) in the standalone '
        '<b>init_audit_report.pdf</b> / <b>init_audit_results.json</b> under '
        'data/output/audit/.', styles['body']))

    return elems
