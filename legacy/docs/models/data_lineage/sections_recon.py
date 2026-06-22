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

"""Reconciliation evidence and data-source documentation report sections."""

from datetime import datetime

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table

from ._constants import GREEN, RED, FAILURE_METADATA
from .styles import (
    _header_style, _section_rule, _status_colour, _status_label,
)


def _build_reconciliation(data: dict, story: list, S: dict):
    """Section 4: Data Reconciliation Evidence (BCBS 239 P3)."""
    story.append(Paragraph("4. Data Reconciliation Procedures", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 3 — Reconciliation:</b> "
        "The platform implements automated reconciliation between all "
        "pipeline data files. These checks run as part of the test suite "
        "and as a pre-flight gate before the audit package is generated."
        "<br/><br/>"
        "Reconciliation procedures are defined in "
        "<i>tests/data/test_id_consistency.py</i> and cover:",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Reconciliation checks documented
    recon_checks = [
        ['Check', 'Files Reconciled', 'Validation Rule',
         'BCBS Principle(s)'],
        ['Gauge ID consistency',
         'gauge.json ↔ gaugehc.json',
         'Every gauge in gauge.json has a matching hazard curve; '
         'no orphan IDs in gaugehc.json',
         'P3 (Accuracy)'],
        ['Trade gauge references',
         'prs/*.json ↔ gauge.json',
         'Every traded gauge_id exists in the gauge master file',
         'P3, P4 (Completeness)'],
        ['Trade hazard curves',
         'prs/*.json ↔ gaugehc.json',
         'Every traded gauge_id has an associated hazard curve',
         'P3, P4 (Completeness)'],
        ['Property ID consistency',
         'property.json ↔ propertyts/',
         'Property time-series files reference valid property IDs',
         'P3 (Accuracy)'],
        ['Storm ID consistency',
         'storm_sequences.json ↔ gaugets/ ↔ propertyts/',
         'All storm IDs in time-series originate from storm sequences',
         'P3 (Accuracy)'],
        ['Classifier gauge alignment',
         'GAUGE-*.joblib ↔ gauge.json',
         'Classifier model files reference current gauge IDs',
         'P3, P7 (Comprehensiveness)'],
        ['Manifest hash verification',
         'data_lineage.json ↔ filesystem',
         'Recorded output hashes match current file content on disk',
         'P3 (Integrity)'],
        ['Dependency chain integrity',
         'data_lineage.json (all steps)',
         'No step has stale inputs; all upstream steps are recorded',
         'P3, P6 (Timeliness)'],
        ['Deterministic IDs',
         'gauge.json',
         'Gauge IDs are derived from location, not randomly generated',
         'P3, P7 (Clarity)'],
    ]

    tbl = Table(recon_checks,
                colWidths=[1.4 * inch, 1.3 * inch, 2.4 * inch,
                           1.4 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    # Test results
    lr = data['lineage_results']
    if lr:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Latest Reconciliation Results:", S['h3']))
        total = lr.get('total', 0)
        passed = lr.get('passed', 0)
        failed = lr.get('failed', 0)
        skipped = lr.get('skipped', 0)

        result_data = [
            ['Total Checks', 'Passed', 'Failed', 'Skipped', 'Verdict'],
            [str(total), str(passed), str(failed), str(skipped),
             'PASS' if failed == 0 else 'FAIL'],
        ]
        rtbl = Table(result_data,
                     colWidths=[1.2 * inch, 1.2 * inch, 1.2 * inch,
                                1.2 * inch, 1.2 * inch])
        rts = _header_style()
        verdict_col = GREEN if failed == 0 else RED
        rts.add('TEXTCOLOR', (4, 1), (4, 1), verdict_col)
        rts.add('FONTNAME', (4, 1), (4, 1), 'Helvetica-Bold')
        if failed > 0:
            rts.add('TEXTCOLOR', (2, 1), (2, 1), RED)
            rts.add('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold')
        rtbl.setStyle(rts)
        story.append(rtbl)

        # Show failures with structured BCBS breakdown
        failures = lr.get('failures', [])
        if failures:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Failed Checks:", S['h3']))
            for f in failures[:15]:
                name = f.get('name', 'unknown')
                msg = f.get('message', '')
                if len(msg) > 200:
                    msg = msg[:200] + '...'
                meta = FAILURE_METADATA.get(name)
                if meta:
                    fail_data = [
                        ['Property', 'Detail'],
                        ['Check', name],
                        ['BCBS Principle', meta['principle']],
                        ['Description', meta['description']],
                        ['Result', msg or 'FAIL'],
                        ['Remediation', meta['remediation']],
                    ]
                    ftbl = Table(fail_data,
                                 colWidths=[1.3 * inch, 5.2 * inch])
                    fts = _header_style()
                    fts.add('TEXTCOLOR', (1, 4), (1, 4), RED)
                    fts.add('FONTNAME', (1, 4), (1, 4), 'Helvetica-Bold')
                    ftbl.setStyle(fts)
                    story.append(ftbl)
                    story.append(Spacer(1, 0.06 * inch))
                else:
                    story.append(Paragraph(
                        f"&bull; <b>{name}:</b> {msg}", S['note']))
    else:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "<i>Reconciliation test results not available. "
            "Run <b>python app.py test --audit</b> to generate.</i>",
            S['note']))


def _build_source_documentation(data: dict, story: list, S: dict):
    """Section 5: Data Source Documentation."""
    story.append(Paragraph("5. Data Source Documentation", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 7 — Comprehensiveness:</b> "
        "Each pipeline step's data sources, generator module, and "
        "parameterisation are documented below. This provides a complete "
        "audit trail of upstream dependencies for every data artefact "
        "in the portfolio risk system.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    for sd in data['step_details']:
        story.append(Paragraph(
            f"<b>{sd['step']}</b>", S['h3']))

        gen = sd['generator'] or '(not yet recorded)'
        run_id = sd['run_id'] or '—'
        ts = sd['timestamp']
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        else:
            ts = '—'

        info_data = [
            ['Property', 'Value'],
            ['Generator', gen],
            ['Last run ID', run_id],
            ['Last executed', ts],
            ['Dependencies',
             ', '.join(sd['dependencies']) if sd['dependencies'] else '(root — no upstream)'],
            ['Input files', ', '.join(sd['inputs']) if sd['inputs'] else '(none)'],
            ['Output files', ', '.join(sd['outputs']) if sd['outputs'] else '(none)'],
            ['Freshness', _status_label(sd['status'])],
        ]

        # Add parameters if recorded
        params = sd.get('parameters', {})
        if params:
            param_str = '; '.join(f"{k}={v}" for k, v in
                                  sorted(params.items())[:8])
            if len(params) > 8:
                param_str += f' ... (+{len(params) - 8} more)'
            info_data.append(['Parameters', param_str])

        tbl = Table(info_data, colWidths=[1.5 * inch, 5.0 * inch])
        ts_style = _header_style()
        # Colour freshness row
        freshness_row = len(info_data) - (2 if params else 1)
        col = _status_colour(sd['status'])
        ts_style.add('TEXTCOLOR', (1, freshness_row), (1, freshness_row), col)
        ts_style.add('FONTNAME', (1, freshness_row), (1, freshness_row),
                     'Helvetica-Bold')
        tbl.setStyle(ts_style)
        story.append(tbl)
        story.append(Spacer(1, 0.08 * inch))
