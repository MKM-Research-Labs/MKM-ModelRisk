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

"""Cover page and executive summary sections of the full audit report."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import (
    NAVY, BLUE, GREEN, AMBER, RED, GREY, _TBL_STYLE_BASE,
)
from .helpers import (
    _metric_box, _load_json_report, _status, _status_inv, _status_colour,
)


def _build_cover(junit: dict, cov: dict, git_sha: str,
                 report_date: datetime, styles) -> list:
    elems = []

    elems.append(Spacer(1, 18 * mm))
    elems.append(Paragraph('MKM Physical Risk Platform', styles['cover_sub']))
    elems.append(Paragraph('Full Audit Report', styles['cover_title']))
    elems.append(Spacer(1, 4 * mm))
    elems.append(HRFlowable(width='100%', thickness=2, color=NAVY))
    elems.append(Spacer(1, 6 * mm))

    elems.append(Paragraph(
        f'Report Date: {report_date.strftime("%d %B %Y")}',
        styles['cover_meta']))
    elems.append(Paragraph(
        f'Git SHA: {git_sha}',
        styles['cover_meta']))
    elems.append(Paragraph(
        'Governance Framework: SR 11-7 / SS1/23 Model Risk Management',
        styles['cover_meta']))

    elems.append(Spacer(1, 10 * mm))

    # Summary metrics row
    cov_pct = cov['line_rate'] * 100
    total_tests = junit['total']
    # Pass Rate is of *executed* tests (passed + failed). Skipped tests — most
    # of which are data-dependent (port/blotter/PRS data not on disk) — would
    # otherwise drag a 0-failure suite below 100%. Skips are surfaced
    # separately in the exec summary and section 2.2.
    executed = junit['passed'] + junit['failed']
    pass_rate = (junit['passed'] / executed * 100) if executed else 0

    cov_col = GREEN if cov_pct >= 90 else (AMBER if cov_pct >= 70 else RED)
    pass_col = GREEN if pass_rate >= 99 else (AMBER if pass_rate >= 95 else RED)

    # Load supplementary results for cover metrics
    dl_cov = _load_json_report('data_lineage_results.json')
    e2e_cov = _load_json_report('e2e/e2e_results.json')
    dl_ok = dl_cov.get('failed', 0) == 0 if dl_cov else True
    dl_label = 'PASS' if dl_ok else 'FAIL'
    dl_col = GREEN if dl_ok else RED

    e2e_total = e2e_cov.get('total', 0) if e2e_cov else 0
    e2e_failed = e2e_cov.get('failed', 0) if e2e_cov else 0
    e2e_status = e2e_cov.get('status', '') if e2e_cov else ''
    if e2e_status == 'SKIPPED':
        e2e_label = 'SKIP'
        e2e_col = GREY
    elif e2e_total > 0:
        e2e_label = f'{e2e_total - e2e_failed}/{e2e_total}'
        e2e_col = GREEN if e2e_failed == 0 else RED
    else:
        e2e_label = 'N/A'
        e2e_col = GREY

    metrics = Table([
        [
            _metric_box(f'{total_tests:,}',  'Total Tests',     BLUE,     styles),
            _metric_box(f'{pass_rate:.1f}%', 'Pass Rate',       pass_col, styles),
            _metric_box(f'{cov_pct:.1f}%',   'Line Coverage',   cov_col,  styles),
            _metric_box(dl_label,             'Data Lineage',    dl_col,   styles),
            _metric_box(e2e_label,            'E2E Tests',       e2e_col,  styles),
        ],
    ], colWidths=[34 * mm] * 5)
    metrics.setStyle(TableStyle([
        ('ALIGN',   (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',  (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    elems.append(metrics)

    elems.append(Spacer(1, 10 * mm))

    elems.append(Paragraph('Report Contents', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))

    toc = [
        ('1', 'Executive Summary',
         'Key metrics, pass/fail totals, coverage headline, and test run metadata.'),
        ('2', 'Test Suite Detail',
         'Test counts by package, the list of individual failing unit tests '
         '(2.1), and skipped tests grouped by reason (2.2).'),
        ('3', 'Code Coverage Analysis',
         'Line coverage by package, files with coverage gaps.'),
        ('4', 'Code Modularisation',
         'Files exceeding 300 lines, plus the __init__.py substantive-code audit.'),
        ('5', 'Hard-Coding Audit',
         'Parameter governance scan — constants outside config.py.'),
        ('6', 'Embedded JavaScript / CSS in Python',
         'Zero-tolerance scan — inline scripts/styles and JS factory strings in .py files.'),
        ('7', 'Data Lineage Consistency',
         'BCBS 239 Principle 3 pre-flight checks — ID consistency across pipeline data.'),
        ('8', 'E2E Browser Tests',
         'Playwright end-to-end tests — full-stack UI verification.'),
        ('9', 'Remediation Roadmap',
         'Prioritised action list for identified quality issues.'),
    ]
    toc_data = [['§', 'Section', 'Description']]
    for num, title, desc in toc:
        toc_data.append([
            Paragraph(f'<b>{num}</b>', styles['tbl_cell']),
            Paragraph(f'<b>{title}</b>', styles['tbl_cell']),
            Paragraph(desc, styles['tbl_cell']),
        ])
    toc_tbl = Table(toc_data, colWidths=[8 * mm, 52 * mm, 108 * mm])
    toc_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(toc_tbl)

    elems.append(Spacer(1, 6 * mm))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        'This report is generated automatically as part of the MKM Research Labs '
        'model governance pipeline (app.py test --audit). It covers the Python '
        'source codebase under src/ and the tests/ directory. All figures reflect '
        'the state of the repository at the git SHA shown above.',
        styles['small']))

    return elems


def _build_exec_summary(junit: dict, cov: dict, report_date: datetime,
                        styles) -> list:
    elems = []
    elems.append(Paragraph('1. Executive Summary', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    total = junit['total']
    passed = junit['passed']
    failed = junit['failed']
    skipped = junit['skipped']
    t_secs = junit['time_s']
    cov_pct = cov['line_rate'] * 100
    lines_valid = cov['lines_valid']
    lines_cov = cov['lines_covered']

    # Load supplementary results for exec summary
    dl_data = _load_json_report('data_lineage_results.json')
    e2e_data = _load_json_report('e2e/e2e_results.json')

    dl_status_str = 'Not run'
    if dl_data:
        dl_f = dl_data.get('failed', 0)
        dl_t = dl_data.get('total', 0)
        dl_status_str = f'{dl_t} checks, {dl_f} failed'

    e2e_status_str = 'Not run'
    if e2e_data:
        e2e_st = e2e_data.get('status', '')
        if e2e_st == 'SKIPPED':
            e2e_status_str = f'Skipped ({e2e_data.get("reason", "")})'
        elif e2e_st in ('TIMEOUT', 'ERROR'):
            e2e_status_str = e2e_st
        else:
            e2e_t = e2e_data.get('total', 0)
            e2e_f = e2e_data.get('failed', 0)
            e2e_status_str = f'{e2e_t} tests, {e2e_f} failed'

    rows = [
        ['Metric',                     'Value',         'Status'],
        ['Total tests',                f'{total:,}',    _status(total >= 5000, total >= 3000)],
        ['Tests passed',               f'{passed:,}',   _status(failed == 0, failed <= 5)],
        ['Tests failed',               f'{failed:,}',   _status_inv(failed == 0, failed <= 5)],
        ['Tests skipped',              f'{skipped:,}',  'INFO'],
        ['Test suite run time',        f'{t_secs:.1f}s', 'INFO'],
        ['Lines analysed (src/)',       f'{lines_valid:,}', 'INFO'],
        ['Lines covered',              f'{lines_cov:,}', 'INFO'],
        ['Line coverage',              f'{cov_pct:.2f}%',
         _status(cov_pct >= 90, cov_pct >= 75)],
        ['Data lineage consistency',   dl_status_str,
         _status_inv(dl_data.get('failed', 0) == 0, True) if dl_data else 'INFO'],
        ['E2E browser tests',          e2e_status_str,
         _status_inv(e2e_data.get('failed', 0) == 0,
                     e2e_data.get('failed', 0) <= 3) if (
             e2e_data and e2e_data.get('status') not in ('SKIPPED', None)) else 'INFO'],
        ['Report generated',           report_date.strftime('%Y-%m-%d %H:%M:%S'), 'INFO'],
    ]

    tbl_data = []
    for i, row in enumerate(rows):
        if i == 0:
            tbl_data.append([Paragraph(f'<b>{c}</b>', styles['tbl_hdr']) for c in row])
        else:
            status_str = row[2]
            status_col = _status_colour(status_str)
            tbl_data.append([
                Paragraph(row[0], styles['tbl_cell']),
                Paragraph(f'<b>{row[1]}</b>', styles['tbl_cell_r']),
                Paragraph(f'<b>{status_str}</b>',
                          ParagraphStyle('S', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=7.5, textColor=status_col,
                                         fontName='Helvetica-Bold')),
            ])

    tbl = Table(tbl_data, colWidths=[90 * mm, 50 * mm, 28 * mm])
    tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
    elems.append(tbl)

    elems.append(Spacer(1, 4 * mm))
    executed = passed + failed
    exec_rate = (passed / executed * 100) if executed else 0
    elems.append(Paragraph(
        f'The test suite comprises <b>{total:,} tests</b> across all packages '
        f'with <b>{passed:,} passing</b>, <b>{failed} failing</b>, and '
        f'<b>{skipped} skipped</b>. The headline <b>Pass Rate ({exec_rate:.1f}%)</b> '
        f'is measured over the <b>{executed:,} executed</b> tests — skipped tests '
        f'are excluded so they do not mask the true pass/fail health. Most skips '
        f'are data-dependent (port/blotter/PRS data not generated on disk); see '
        f'<b>section 2.2</b> for the breakdown by reason. '
        f'Line coverage stands at <b>{cov_pct:.1f}%</b> across '
        f'{lines_valid:,} analysed source lines.',
        styles['body']))

    return elems
