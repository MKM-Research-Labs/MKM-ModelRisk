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

"""E2E browser test results and remediation roadmap sections."""

from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, STEEL, GREEN, AMBER, RED, GREY, _TBL_STYLE_BASE
from .helpers import (
    _load_json_report, _status, _status_inv, _status_colour, _map_sev,
)


def _build_e2e(styles) -> list:
    """Section 8: E2E Browser Tests (Playwright)."""
    elems = []
    elems.append(Paragraph('8. E2E Browser Tests', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'End-to-end browser tests exercising the full application stack via '
        'Playwright (headless Chromium). These tests verify that the UI loads, '
        'panels open, data renders, and user workflows complete successfully.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = _load_json_report('e2e/e2e_results.json')
    if not data:
        elems.append(Paragraph(
            'E2E test results not available — tests were not run or '
            'e2e_results.json is missing.', styles['body']))
        return elems

    status = data.get('status', 'UNKNOWN')
    reason = data.get('reason', '')
    total = data.get('total', 0)
    passed = data.get('passed', 0)
    failed = data.get('failed', 0)
    skipped_count = data.get('skipped', 0)

    if status == 'SKIPPED':
        elems.append(Paragraph(
            f'E2E tests were <b>skipped</b>: {reason}. '
            'Install Playwright to enable: pip install playwright && playwright install chromium',
            styles['body']))
        return elems

    if status == 'TIMEOUT':
        elems.append(Paragraph(
            f'E2E tests <b>timed out</b>: {reason}.',
            styles['body']))
        return elems

    if status == 'ERROR':
        elems.append(Paragraph(
            f'E2E tests encountered an <b>error</b>: {reason}.',
            styles['body']))
        return elems

    # Summary table
    pass_rate = (passed / total * 100) if total > 0 else 0
    pass_col = GREEN if pass_rate >= 99 else (AMBER if pass_rate >= 90 else RED)

    tbl_data = [
        [Paragraph('<b>Metric</b>', styles['tbl_hdr']),
         Paragraph('<b>Value</b>', styles['tbl_hdr']),
         Paragraph('<b>Status</b>', styles['tbl_hdr'])],
        [Paragraph('Total E2E tests', styles['tbl_cell']),
         Paragraph(f'<b>{total}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('E2I', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Passed', styles['tbl_cell']),
         Paragraph(f'<b>{passed}</b>', styles['tbl_cell_r']),
         Paragraph(_status(failed == 0, passed > 0),
                   ParagraphStyle('E2P', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=GREEN if failed == 0 else AMBER,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Failed', styles['tbl_cell']),
         Paragraph(f'<b>{failed}</b>', styles['tbl_cell_r']),
         Paragraph(_status_inv(failed == 0, failed <= 3),
                   ParagraphStyle('E2F', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=GREEN if failed == 0 else RED,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Skipped', styles['tbl_cell']),
         Paragraph(f'<b>{skipped_count}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('E2S', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Pass rate', styles['tbl_cell']),
         Paragraph(f'<b>{pass_rate:.1f}%</b>', styles['tbl_cell_r']),
         Paragraph(_status(pass_rate >= 99, pass_rate >= 90),
                   ParagraphStyle('E2R', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5, textColor=pass_col,
                                   fontName='Helvetica-Bold'))],
    ]
    tbl = Table(tbl_data, colWidths=[90 * mm, 40 * mm, 38 * mm])
    style_cmds = list(_TBL_STYLE_BASE)
    if failed > 0:
        style_cmds.append(('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#FFEBEE')))
    tbl.setStyle(TableStyle(style_cmds))
    elems.append(tbl)

    # Failure details
    failures = data.get('failures', [])
    if failures:
        elems.append(Spacer(1, 3 * mm))
        elems.append(Paragraph('Failed E2E Tests:', styles['h3']))
        fail_data = [[
            Paragraph('<b>Test</b>', styles['tbl_hdr']),
            Paragraph('<b>Error</b>', styles['tbl_hdr']),
        ]]
        for f in failures[:15]:
            name = _xml_escape(f.get('name', 'unknown'))
            msg = _xml_escape(f.get('message', ''))
            if len(msg) > 300:
                msg = msg[:300] + '...'
            fail_data.append([
                Paragraph(name, styles['tbl_cell']),
                Paragraph(msg, styles['tbl_cell']),
            ])
        fail_tbl = Table(fail_data, colWidths=[60 * mm, 108 * mm])
        fail_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(fail_tbl)

    return elems


def _build_roadmap(junit: dict, cov: dict, styles) -> list:
    elems = []
    elems.append(Paragraph('9. Remediation Roadmap', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Prioritised actions derived from this audit cycle. '
        'Items are ranked by risk impact under SR 11-7 / SS1/23.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    cov_pct = cov['line_rate'] * 100
    n_failed = junit['failed']

    actions = []
    if n_failed > 0:
        actions.append(('P1', 'CRITICAL',
                         f'Fix {n_failed} failing test(s)',
                         'Failing tests indicate broken or regressed functionality. '
                         'Address immediately before any release.'))
    if cov_pct < 80:
        actions.append(('P2', 'HIGH',
                         f'Increase line coverage from {cov_pct:.1f}% to ≥90%',
                         'Low coverage leaves model logic unverified. '
                         'Add targeted tests for uncovered packages first.'))
    elif cov_pct < 90:
        actions.append(('P2', 'MEDIUM',
                         f'Increase line coverage from {cov_pct:.1f}% to ≥90%',
                         'Close remaining gaps to meet the 90% governance target.'))
    else:
        actions.append(('P2', 'OK',
                         f'Maintain coverage at {cov_pct:.1f}%',
                         'Coverage meets or exceeds the 90% governance target. '
                         'Continue enforcing --cov-fail-under=90 in CI.'))

    # Data lineage check
    dl_road = _load_json_report('data_lineage_results.json')
    if dl_road and dl_road.get('failed', 0) > 0:
        dl_n = dl_road['failed']
        actions.append(('P1', 'CRITICAL',
                         f'Fix {dl_n} data lineage inconsistency(ies)',
                         'Pipeline data is inconsistent. Regenerate in order: '
                         'port --gauge → port --stressm → port --hazard → port --blotter'))

    # E2E check
    e2e_road = _load_json_report('e2e/e2e_results.json')
    if e2e_road and e2e_road.get('failed', 0) > 0:
        e2e_n = e2e_road['failed']
        actions.append(('P2', 'HIGH',
                         f'Fix {e2e_n} failing E2E browser test(s)',
                         'End-to-end tests detect UI regressions visible to users. '
                         'Review tests/e2e/ for details.'))

    actions += [
        ('P3', 'MEDIUM',
         'Migrate ALL_CAPS constants to config.py',
         'Distributed hard-coded parameters create recalibration risk. '
         'Run python -m docs.models.hardcoding for the full list.'),
        ('P4', 'MEDIUM',
         'Modularise files over 600 lines',
         'Large files are harder to test and review. '
         'See Section 4 for the current priority list.'),
        ('P5', 'LOW',
         'Review code duplication hotspots',
         'See code_duplication_report.pdf in data/output/audit/ '
         'for clone-pair details and refactoring recommendations.'),
        ('P6', 'LOW',
         'Run full audit before each model governance review',
         'Execute: python app.py test --audit to regenerate all artefacts.'),
    ]

    tbl_data = [[
        Paragraph('<b>Priority</b>', styles['tbl_hdr']),
        Paragraph('<b>Severity</b>', styles['tbl_hdr']),
        Paragraph('<b>Action</b>', styles['tbl_hdr']),
        Paragraph('<b>Detail</b>', styles['tbl_hdr']),
    ]]
    row_extras = []
    for i, (pri, sev, action, detail) in enumerate(actions, 1):
        sev_col = _status_colour(_map_sev(sev))
        tbl_data.append([
            Paragraph(f'<b>{pri}</b>', styles['tbl_cell']),
            Paragraph(f'<b>{sev}</b>',
                      ParagraphStyle('Sev', parent=getSampleStyleSheet()['Normal'],
                                     fontSize=8, textColor=sev_col,
                                     fontName='Helvetica-Bold')),
            Paragraph(action, styles['tbl_cell']),
            Paragraph(detail, styles['tbl_cell']),
        ])
        if sev == 'CRITICAL':
            row_extras.append(('BACKGROUND', (0, i), (-1, i),
                                colors.HexColor('#FFEBEE')))
        elif sev == 'HIGH':
            row_extras.append(('BACKGROUND', (0, i), (-1, i),
                                colors.HexColor('#FFF8E1')))

    tbl = Table(tbl_data, colWidths=[16 * mm, 20 * mm, 60 * mm, 72 * mm])
    tbl.setStyle(TableStyle(list(_TBL_STYLE_BASE) + row_extras))
    elems.append(tbl)

    elems.append(Spacer(1, 6 * mm))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 3 * mm))
    elems.append(Paragraph(
        'Supporting artefacts in data/output/audit/: '
        'test_report.pdf &nbsp;|&nbsp; '
        'large_file_report.pdf &nbsp;|&nbsp; large_test_report.txt &nbsp;|&nbsp; '
        'code_duplication_report.pdf &nbsp;|&nbsp; '
        'hardcoding_report.pdf &nbsp;|&nbsp; '
        'embedded_js_report.pdf &nbsp;|&nbsp; '
        'coverage/ (HTML) &nbsp;|&nbsp; '
        'junit.xml &nbsp;|&nbsp; coverage.xml',
        styles['small']))
    elems.append(Spacer(1, 2 * mm))
    elems.append(Paragraph(
        'Model Governance Reference: SR 11-7 (Federal Reserve), SS1/23 (PRA) — '
        'Model Risk Management. This report is produced automatically; '
        'human review is required before formal model approval.',
        styles['small']))

    return elems
