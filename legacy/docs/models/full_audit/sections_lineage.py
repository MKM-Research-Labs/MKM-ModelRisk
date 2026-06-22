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

"""Data lineage consistency section (BCBS 239 Principle 3) of the audit."""

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, STEEL, GREEN, AMBER, RED, _root, _TBL_STYLE_BASE
from .helpers import _load_json_report, _status, _status_inv


def _build_data_lineage(styles) -> list:
    """Section 7: Data Lineage Consistency (BCBS 239 Principle 3)."""
    elems = []
    elems.append(Paragraph('7. Data Lineage Consistency', styles['h2']))
    elems.append(HRFlowable(width='100%', thickness=1, color=NAVY))
    elems.append(Spacer(1, 3 * mm))

    elems.append(Paragraph(
        'Pre-flight checks verifying that gauge IDs, property IDs, and trade '
        'references are consistent across all pipeline data files '
        '(BCBS 239 Principle 3 — Accuracy). Failures indicate stale or '
        'out-of-order pipeline data.',
        styles['body']))
    elems.append(Spacer(1, 2 * mm))

    data = _load_json_report('data_lineage_results.json')
    if not data:
        elems.append(Paragraph(
            'Data lineage results not available — tests were not run or '
            'data_lineage_results.json is missing.', styles['body']))
        return elems

    total = data.get('total', 0)
    passed = data.get('passed', 0)
    failed = data.get('failed', 0)
    skipped = data.get('skipped', 0)

    # Summary table
    tbl_data = [
        [Paragraph('<b>Metric</b>', styles['tbl_hdr']),
         Paragraph('<b>Value</b>', styles['tbl_hdr']),
         Paragraph('<b>Status</b>', styles['tbl_hdr'])],
        [Paragraph('Total checks', styles['tbl_cell']),
         Paragraph(f'<b>{total}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('DLI', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
                                           fontName='Helvetica-Bold'))],
        [Paragraph('Passed', styles['tbl_cell']),
         Paragraph(f'<b>{passed}</b>', styles['tbl_cell_r']),
         Paragraph(_status(passed == total, passed > 0),
                   ParagraphStyle('DLP', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5,
                                   textColor=GREEN if passed == total else AMBER,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Failed', styles['tbl_cell']),
         Paragraph(f'<b>{failed}</b>', styles['tbl_cell_r']),
         Paragraph(_status_inv(failed == 0, failed <= 2),
                   ParagraphStyle('DLF', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=7.5,
                                   textColor=GREEN if failed == 0 else RED,
                                   fontName='Helvetica-Bold'))],
        [Paragraph('Skipped', styles['tbl_cell']),
         Paragraph(f'<b>{skipped}</b>', styles['tbl_cell_r']),
         Paragraph('INFO', ParagraphStyle('DLS', parent=getSampleStyleSheet()['Normal'],
                                           fontSize=7.5, textColor=STEEL,
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
        elems.append(Paragraph('Failed Consistency Checks:', styles['h3']))
        fail_data = [[
            Paragraph('<b>Test</b>', styles['tbl_hdr']),
            Paragraph('<b>Error</b>', styles['tbl_hdr']),
        ]]
        for f in failures[:10]:
            name = f.get('name', 'unknown')
            msg = f.get('message', '')
            if len(msg) > 200:
                msg = msg[:200] + '...'
            fail_data.append([
                Paragraph(name, styles['tbl_cell']),
                Paragraph(msg, styles['tbl_cell']),
            ])
        fail_tbl = Table(fail_data, colWidths=[60 * mm, 108 * mm])
        fail_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(fail_tbl)

    if failed > 0:
        elems.append(Spacer(1, 3 * mm))
        elems.append(Paragraph(
            '<b>Remediation:</b> Regenerate data in the correct order: '
            'python app.py port --gauge → port --stressm → port --hazard → port --blotter',
            styles['body']))

    # ------------------------------------------------------------------
    # Generation Manifest (from data/data_lineage.json)
    # ------------------------------------------------------------------
    import json as _json
    _lineage_path = _root / 'data' / 'data_lineage.json'
    _manifest = {}
    if _lineage_path.exists():
        try:
            with open(_lineage_path) as _lf:
                _manifest = _json.load(_lf)
        except Exception:
            _manifest = {}

    if _manifest.get('steps'):
        elems.append(Spacer(1, 5 * mm))
        elems.append(Paragraph('Generation Manifest', styles['h3']))

        manifest_data = [[
            Paragraph('<b>Step</b>', styles['tbl_hdr']),
            Paragraph('<b>Generator</b>', styles['tbl_hdr']),
            Paragraph('<b>Timestamp</b>', styles['tbl_hdr']),
            Paragraph('<b>Status</b>', styles['tbl_hdr']),
            Paragraph('<b>Run ID</b>', styles['tbl_hdr']),
        ]]
        for step_name, step_info in sorted(_manifest['steps'].items()):
            gen = step_info.get('generator', 'unknown')
            ts = step_info.get('timestamp', '')
            if len(ts) > 19:
                ts = ts[:19]  # trim to YYYY-MM-DDTHH:MM:SS
            st = step_info.get('status', 'unknown')
            rid = step_info.get('run_id', '')
            st_col = GREEN if st == 'success' else RED
            manifest_data.append([
                Paragraph(step_name, styles['tbl_cell']),
                Paragraph(gen, styles['tbl_cell']),
                Paragraph(ts, styles['tbl_cell']),
                Paragraph(f'<b>{st}</b>',
                          ParagraphStyle('MFSt', parent=getSampleStyleSheet()['Normal'],
                                         fontSize=8, textColor=st_col,
                                         fontName='Helvetica-Bold')),
                Paragraph(rid, styles['tbl_cell']),
            ])
        mf_tbl = Table(manifest_data, colWidths=[30 * mm, 35 * mm, 38 * mm, 22 * mm, 43 * mm])
        mf_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
        elems.append(mf_tbl)

    # ------------------------------------------------------------------
    # Staleness Assessment
    # ------------------------------------------------------------------
    elems.append(Spacer(1, 5 * mm))
    elems.append(Paragraph('Staleness Assessment', styles['h3']))

    try:
        from lineage.validation import validate_full_chain as _validate
        _val = _validate()
        if _val.get('is_consistent'):
            elems.append(Paragraph(
                '<b>All steps consistent</b> — no stale inputs detected.',
                ParagraphStyle('StaleOK', parent=getSampleStyleSheet()['Normal'],
                               fontSize=9, textColor=GREEN,
                               fontName='Helvetica-Bold')))
        else:
            stale_list = _val.get('stale_steps', [])
            missing_list = _val.get('missing_steps', [])
            detail_map = _val.get('details', {})

            if missing_list:
                elems.append(Paragraph(
                    f'<b>Missing steps</b> (never run): {", ".join(missing_list)}',
                    ParagraphStyle('StaleMiss', parent=getSampleStyleSheet()['Normal'],
                                   fontSize=9, textColor=AMBER,
                                   fontName='Helvetica-Bold')))
                elems.append(Spacer(1, 2 * mm))

            if stale_list:
                stale_data = [[
                    Paragraph('<b>Step</b>', styles['tbl_hdr']),
                    Paragraph('<b>Issue</b>', styles['tbl_hdr']),
                ]]
                for s in stale_list:
                    issues = detail_map.get(s, [])
                    issue_text = '; '.join(issues[:3])
                    if len(issue_text) > 150:
                        issue_text = issue_text[:150] + '...'
                    stale_data.append([
                        Paragraph(s, styles['tbl_cell']),
                        Paragraph(issue_text, styles['tbl_cell']),
                    ])
                stale_tbl = Table(stale_data, colWidths=[40 * mm, 128 * mm])
                stale_tbl.setStyle(TableStyle(_TBL_STYLE_BASE))
                elems.append(stale_tbl)
    except ImportError:
        elems.append(Paragraph(
            'Lineage validation package not available — staleness check skipped.',
            styles['body']))
    except Exception as _exc:
        elems.append(Paragraph(
            f'Staleness check failed: {_exc}', styles['body']))

    # ------------------------------------------------------------------
    # Dependency Chain
    # ------------------------------------------------------------------
    if _manifest.get('steps'):
        elems.append(Spacer(1, 5 * mm))
        elems.append(Paragraph('Dependency Chain', styles['h3']))

        try:
            from lineage.manifest import DEPENDENCY_GRAPH as _DEP_GRAPH
        except ImportError:
            _DEP_GRAPH = _manifest.get('dependency_graph', {})

        if _DEP_GRAPH:
            chain_lines = []
            for step, deps in sorted(_DEP_GRAPH.items()):
                if deps:
                    chain_lines.append(
                        f'{", ".join(deps)} &rarr; <b>{step}</b>')
                else:
                    chain_lines.append(f'<b>{step}</b> (root)')
            elems.append(Paragraph(
                '<br/>'.join(chain_lines), styles['body']))
        else:
            elems.append(Paragraph(
                'Dependency graph not available.', styles['body']))

    return elems
