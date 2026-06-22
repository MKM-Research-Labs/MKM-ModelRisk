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

"""Cover, executive summary, topology, and quality-metrics report sections."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from ._constants import NAVY, GREEN, AMBER, RED, STEEL, STEP_OWNERS
from .collect import _compute_verdict, _compute_health, _health_colour
from .styles import (
    _header_style, _section_rule, _status_colour, _status_label,
)


def _build_cover(data: dict, story: list, S: dict):
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("Data Lineage Report", S['title']))
    story.append(Paragraph(
        "BCBS 239 — Data Quality, Reconciliation & Provenance",
        S['subtitle']))
    story.append(Spacer(1, 0.3 * inch))

    chain = data['chain_result']
    lr = data.get('lineage_results', {})
    health = _compute_health(chain, lr)
    health_col = _health_colour(health)

    story.append(Paragraph(
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        S['meta']))
    story.append(Paragraph(
        f"<b>Pipeline Steps:</b> {data['num_steps']} | "
        f"<b>Recorded:</b> {data['num_recorded']} | "
        f"<b>Runs:</b> {data['num_runs']}",
        S['meta']))
    story.append(Spacer(1, 0.15 * inch))

    # Overall health badge
    badge_data = [['Pipeline Health'],
                  [health]]
    badge = Table(badge_data, colWidths=[3 * inch])
    badge.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (0, 0), 10),
        ('FONTSIZE',      (0, 1), (0, 1), 16),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR',     (0, 1), (0, 1), health_col),
        ('BACKGROUND',    (0, 1), (0, 1), colors.HexColor('#FAFAFA')),
        ('BOX',           (0, 0), (-1, -1), 1, NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(badge)

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph(
        "<i>This report provides evidence for BCBS 239 compliance covering "
        "data quality metrics, reconciliation procedures, upstream source "
        "documentation, and data retention policy.</i>",
        S['note']))


def _build_exec_summary(data: dict, story: list, S: dict):
    """Section 1: Executive Summary."""
    story.append(Paragraph("1. Executive Summary", S['h2']))
    _section_rule(story)

    chain = data['chain_result']
    steps = data['step_details']
    fresh = sum(1 for s in steps if s['status'] == 'fresh')
    stale = sum(1 for s in steps if s['status'] == 'stale')
    missing = sum(1 for s in steps if s['status'] == 'missing')

    # Consistency test results
    lr = data['lineage_results']
    tests_total = lr.get('total', 0)
    tests_passed = lr.get('passed', 0)
    tests_failed = lr.get('failed', 0)

    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Pipeline steps', str(data['num_steps']),
         'INFO'],
        ['Steps recorded in manifest', str(data['num_recorded']),
         'PASS' if data['num_recorded'] == data['num_steps'] else 'GAPS'],
        ['Steps with fresh data', str(fresh),
         'PASS' if fresh == data['num_steps'] else 'REVIEW'],
        ['Steps with stale data', str(stale),
         'PASS' if stale == 0 else 'WARNING'],
        ['Steps with missing data', str(missing),
         'PASS' if missing == 0 else 'FAIL'],
        ['Hash-chain consistency',
         'Consistent' if chain['is_consistent'] else 'Broken',
         'PASS' if chain['is_consistent'] else 'FAIL'],
        ['ID consistency tests', f"{tests_passed}/{tests_total}",
         'PASS' if tests_failed == 0 and tests_total > 0 else (
             'FAIL' if tests_failed > 0 else 'NOT RUN')],
    ]

    tbl = Table(summary_data,
                colWidths=[3.0 * inch, 1.5 * inch, 1.5 * inch])
    ts = _header_style()
    for row_idx, row in enumerate(summary_data[1:], 1):
        status = row[2]
        col = (GREEN if status == 'PASS' else
               AMBER if status in ('WARNING', 'REVIEW', 'GAPS') else
               RED if status == 'FAIL' else STEEL)
        ts.add('TEXTCOLOR', (2, row_idx), (2, row_idx), col)
        ts.add('FONTNAME', (2, row_idx), (2, row_idx), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)

    # Overall BCBS 239 verdict
    verdict = _compute_verdict(chain, lr)
    verdict_col = (GREEN if verdict == 'COMPLIANT' else
                   AMBER if verdict == 'PARTIALLY COMPLIANT' else RED)

    story.append(Spacer(1, 0.15 * inch))
    verdict_data = [
        ['Overall BCBS 239 Data Lineage Verdict'],
        [verdict],
    ]
    v_tbl = Table(verdict_data, colWidths=[4.5 * inch])
    v_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (0, 0), 9),
        ('FONTSIZE',      (0, 1), (0, 1), 14),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR',     (0, 1), (0, 1), verdict_col),
        ('BACKGROUND',    (0, 1), (0, 1), colors.HexColor('#FAFAFA')),
        ('BOX',           (0, 0), (-1, -1), 1, NAVY),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(v_tbl)

    # Run history summary
    if data.get('num_runs', 0) > 0:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            f"<b>Run History:</b> {data['num_runs']} pipeline executions "
            f"recorded in manifest. BCBS 239 emphasises ongoing capability, "
            f"not single-run compliance; a sustained history of successful "
            f"runs demonstrates operational reliability.",
            S['note']))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "This report addresses the following BCBS 239 requirements:<br/>"
        "&bull; <b>Principle 2</b> — Data Architecture & Infrastructure<br/>"
        "&bull; <b>Principle 3</b> — Accuracy & Integrity (quality metrics, "
        "reconciliation)<br/>"
        "&bull; <b>Principle 6</b> — Timeliness (staleness monitoring)<br/>"
        "&bull; <b>Principle 7</b> — Comprehensiveness (source documentation)",
        S['body']))


def _build_topology(data: dict, story: list, S: dict):
    """Section 2: Pipeline Topology & Upstream Dependencies."""
    story.append(Paragraph(
        "2. Pipeline Topology &amp; Upstream Dependencies", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "The portfolio generation pipeline consists of "
        f"{data['num_steps']} steps with defined dependency ordering. "
        "Each step declares its inputs and outputs; the lineage system "
        "tracks content hashes (SHA-256) at each boundary to detect "
        "staleness.<br/><br/>"
        "<b>BCBS 239 Principle 2:</b> Data architecture is documented with "
        "clear ownership of each pipeline stage and its data artefacts.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Dependency table
    topo_data = [['Step', 'Depends On', 'Inputs', 'Outputs', 'Owner']]
    for sd in data['step_details']:
        deps = ', '.join(sd['dependencies']) if sd['dependencies'] else '(root)'
        inputs = ', '.join(sd['inputs']) if sd['inputs'] else '(none)'
        outputs = ', '.join(sd['outputs']) if sd['outputs'] else '(none)'
        owner = STEP_OWNERS.get(sd['step'], '—')
        topo_data.append([sd['step'], deps, inputs, outputs, owner])

    tbl = Table(topo_data,
                colWidths=[1.1 * inch, 1.3 * inch, 1.5 * inch,
                           1.6 * inch, 1.0 * inch])
    tbl.setStyle(_header_style())
    story.append(tbl)

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(
        "<b>Data Source Documentation:</b> All upstream dependencies are "
        "explicitly declared in <i>src/lineage/manifest.py</i> via the "
        "<i>DEPENDENCY_GRAPH</i> and <i>STEP_IO</i> constants. Each step's "
        "generator function, input files, and output artefacts are registered "
        "at code level and verified at runtime via SHA-256 content hashing.",
        S['body']))


def _build_quality_metrics(data: dict, story: list, S: dict):
    """Section 3: Data Quality Metrics (BCBS 239 P3)."""
    story.append(Paragraph("3. Data Quality Metrics", S['h2']))
    _section_rule(story)

    story.append(Paragraph(
        "<b>BCBS 239 Principle 3 — Accuracy &amp; Integrity:</b> "
        "Data quality is monitored through three complementary mechanisms:"
        "<br/><br/>"
        "<b>a) Content-hash freshness:</b> Every pipeline step records "
        "SHA-256 hashes of its inputs and outputs at execution time. "
        "A step is marked <b>STALE</b> when the hash it recorded for an "
        "input no longer matches the current output hash from the upstream "
        "producer — i.e. the upstream data has been regenerated since this "
        "step last ran. The <i>Freshness</i> column below reflects this "
        "hash-based check.<br/><br/>"
        "<b>b) Cross-file ID consistency:</b> Automated tests verify that "
        "gauge IDs, property IDs, storm IDs, and trade references are "
        "consistent across all data files in the pipeline.<br/><br/>"
        "<b>c) Time-based staleness:</b> A separate 72-hour staleness "
        "threshold (enforced via the governance API and the "
        "<i>--strict</i> CLI flag) flags data that has not been refreshed "
        "within the configured window, regardless of hash state.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    # Per-step quality table
    quality_data = [['Step', 'Last Run', 'Elapsed', 'Hash Status',
                     'Freshness']]
    for sd in data['step_details']:
        ts = sd['timestamp']
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts_display = dt.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                ts_display = ts[:16]
        else:
            ts_display = '—'

        elapsed = f"{sd['elapsed_s']:.1f}s" if sd['elapsed_s'] else '—'
        h_status = sd['hash_status'].upper() if sd['hash_status'] else '—'
        freshness = _status_label(sd['status'])

        quality_data.append([sd['step'], ts_display, elapsed,
                             h_status, freshness])

    tbl = Table(quality_data,
                colWidths=[1.3 * inch, 1.5 * inch, 0.8 * inch,
                           1.3 * inch, 1.3 * inch])
    ts = _header_style()
    for row_idx, sd in enumerate(data['step_details'], 1):
        col = _status_colour(sd['status'])
        ts.add('TEXTCOLOR', (4, row_idx), (4, row_idx), col)
        ts.add('FONTNAME', (4, row_idx), (4, row_idx), 'Helvetica-Bold')
        # Highlight hash status
        if sd['hash_status'] == 'success':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), GREEN)
        elif sd['hash_status']:
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), RED)
    tbl.setStyle(ts)
    story.append(tbl)

    # Stale step details
    chain = data['chain_result']
    if chain.get('details'):
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Staleness Details:", S['h3']))
        for step_name, issues in chain['details'].items():
            for issue in issues:
                story.append(Paragraph(
                    f"&bull; <b>{step_name}:</b> {issue}", S['note']))
