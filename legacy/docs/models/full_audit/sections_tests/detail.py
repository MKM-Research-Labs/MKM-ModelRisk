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

"""Section 2: test-suite detail — per-package counts, failures and skips."""

from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from .._constants import NAVY, GREEN, AMBER, RED, GREY, _TBL_STYLE_BASE
from ..helpers import _load_json_report


def _build_test_detail(junit: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('2. Test Suite Detail', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Tests broken down by top-level package directory. '
        'Package names correspond to subdirectories of tests/.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    by_pkg = junit['by_package']
    rows_sorted = sorted(by_pkg.items(), key=lambda x: -x[1]['total'])

    tbl_data = [[
        Paragraph('<b>Package</b>', styles['tbl_hdr']),
        Paragraph('<b>Total</b>', styles['tbl_hdr']),
        Paragraph('<b>Passed</b>', styles['tbl_hdr']),
        Paragraph('<b>Failed</b>', styles['tbl_hdr']),
        Paragraph('<b>Skipped</b>', styles['tbl_hdr']),
        Paragraph('<b>Pass%</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for pkg, counts in rows_sorted:
        t = counts['total']
        f = counts['fail']
        s = counts['skip']
        p = t - f - s
        pct = p / t * 100 if t else 0
        pct_col = GREEN if pct >= 99 else (AMBER if pct >= 95 else RED)

        tbl_data.append([
            Paragraph(pkg, styles['tbl_cell']),
            Paragraph(str(t), styles['tbl_cell_r']),
            Paragraph(str(p), styles['tbl_cell_r']),
            Paragraph(str(f) if f else '—',
                      ParagraphStyle('Fail', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=RED if f else GREY)),
            Paragraph(str(s) if s else '—', styles['tbl_cell_r']),
            Paragraph(f'{pct:.1f}%',
                      ParagraphStyle('Pct', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, alignment=TA_RIGHT,
                                     textColor=pct_col, fontName='Helvetica-Bold')),
        ])
        if f > 0:
            idx = len(tbl_data) - 1
            row_extras.append(('BACKGROUND', (0, idx), (-1, idx),
                                colors.HexColor('#FFEBEE')))

    tbl = Table(tbl_data, colWidths=[58 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm])
    style_cmds = list(_TBL_STYLE_BASE) + row_extras
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)

    # 2.1 — individual unit-test failures
    elems.extend(_build_unit_failures(styles))
    # 2.2 — skipped tests, grouped by reason
    elems.extend(_build_skipped_tests(styles))

    return elems


def _build_skipped_tests(styles) -> list:
    """Subsection 2.2: skipped tests grouped by reason, sourced from
    test_failures_report.json (written by ``app.py test --unit``). Most skips
    are data-dependent (port/blotter/PRS data not generated on disk), so
    grouping by reason — with an example test — is far more useful than a flat
    list of 50+ test names."""
    from collections import defaultdict

    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('2.2 Skipped Tests', styles['h3']))
    elems.append(Spacer(1, 2 * mm))

    report = _load_json_report('test_failures_report.json')
    skipped = report.get('skipped', []) if report else []
    n_skip = (report.get('summary', {}) or {}).get('skipped', len(skipped))

    if not skipped:
        elems.append(Paragraph(
            'No tests were skipped.' if not n_skip else
            f'{n_skip} test(s) skipped — per-test reasons unavailable (regenerate '
            'with <b>python app.py test --unit</b> to capture them).',
            styles['body']))
        return elems

    elems.append(Paragraph(
        f'<b>{len(skipped)}</b> test(s) skipped, grouped by reason. Skips are '
        'usually conditional (data not generated on disk, or a known issue '
        'gated behind <b>pytest.skip</b>) — they are excluded from the Pass Rate '
        'but tracked here so nothing is silently dropped.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    # Group by reason, keeping count + one example test per reason.
    groups = defaultdict(lambda: {'count': 0, 'example': ''})
    for s in skipped:
        reason = s.get('reason', '') or '(no reason given)'
        g = groups[reason]
        g['count'] += 1
        if not g['example']:
            g['example'] = s.get('name', '') or s.get('file', '')

    data = [[
        Paragraph('<b>Skip reason</b>', styles['tbl_hdr']),
        Paragraph('<b>Example test</b>', styles['tbl_hdr']),
        Paragraph('<b>Count</b>', styles['tbl_hdr']),
    ]]
    for reason, g in sorted(groups.items(), key=lambda kv: -kv[1]['count']):
        rtext = reason if len(reason) <= 90 else reason[:88] + '…'
        ex = g['example']
        ex = ex if len(ex) <= 40 else ex[:38] + '…'
        data.append([
            Paragraph(_xml_escape(rtext), styles['tbl_cell']),
            Paragraph(_xml_escape(ex), styles['tbl_cell']),
            Paragraph(str(g['count']), styles['tbl_cell_r']),
        ])
    tbl = Table(data, colWidths=[104 * mm, 46 * mm, 18 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF8E1')),
    ]))
    elems.append(tbl)
    return elems


def _short_msg(longrepr: str) -> str:
    """Pull a concise one-line message from a pytest longrepr blob.

    The last non-empty line of a pytest traceback is usually the assertion or
    error (e.g. ``AssertionError: ...``), which is the most useful summary.
    """
    if not longrepr:
        return '—'
    lines = [ln.strip() for ln in longrepr.splitlines() if ln.strip()]
    if not lines:
        return '—'
    msg = lines[-1]
    return msg[:160] + ('…' if len(msg) > 160 else '')


def _build_unit_failures(styles) -> list:
    """Subsection 2.1: list the individual failing unit tests, sourced from
    test_failures_report.json (written by ``app.py test --unit``). Section 2's
    table only gives per-package counts — this names the actual failures."""
    elems = []
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('2.1 Failed Unit Tests', styles['h3']))
    elems.append(Spacer(1, 2 * mm))

    report = _load_json_report('test_failures_report.json')
    if not report:
        elems.append(Paragraph(
            'test_failures_report.json not found — run '
            '<b>python app.py test --unit</b> to generate it.', styles['body']))
        return elems

    summary = report.get('summary', {})
    failures = report.get('failures', [])
    total = summary.get('total', 0)
    failed = summary.get('failed', len(failures))

    if not failures:
        elems.append(Paragraph(
            f'All <b>{total:,}</b> unit tests passed — <b>0 failures</b>. '
            '<b>PASS</b>', styles['body']))
        return elems

    elems.append(Paragraph(
        f'<b>{failed}</b> of {total:,} unit tests failed (showing up to 60):',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = [[
        Paragraph('<b>Test</b>', styles['tbl_hdr']),
        Paragraph('<b>File</b>', styles['tbl_hdr']),
        Paragraph('<b>Message</b>', styles['tbl_hdr']),
    ]]
    for f in failures[:60]:
        fpath = f.get('file', '') or f.get('class', '')
        data.append([
            Paragraph(_xml_escape(f.get('name', '')), styles['tbl_cell']),
            Paragraph(_xml_escape(fpath), styles['tbl_cell']),
            Paragraph(_xml_escape(_short_msg(f.get('longrepr', ''))), styles['tbl_cell']),
        ])
    tbl = Table(data, colWidths=[50 * mm, 53 * mm, 65 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + [
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFEBEE')),
    ]))
    elems.append(tbl)

    if len(failures) > 60:
        elems.append(Spacer(1, 2 * mm))
        elems.append(Paragraph(
            f'… and {len(failures) - 60} more. See '
            '<b>test_failures_report.json</b> for the full list.', styles['body']))
    return elems
