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

"""Render the embedded JS/CSS findings into a PDF report."""

import sys
from datetime import datetime
from pathlib import Path

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

from docs.models.hardcoding.pdf_helpers import (
    _risk_label, _styles, _header_style, _section_rule,
)


def _violation_table(rows, count_label, count_key):
    data = [['File', 'Lines', count_label]]
    for item in rows:
        data.append([
            item['file'],
            f"{item['line']}–{item['end_line']}",
            str(item[count_key]),
        ])
    t = Table(data, colWidths=[4.6 * inch, 1.0 * inch, 0.9 * inch])
    t.setStyle(_header_style())
    return t


def create_pdf_report(findings: dict, output_path: Path, root: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    S = _styles()
    story = []

    scripts = findings['scripts']
    styles = findings['styles']
    factories = findings['factories']
    total = len(scripts) + len(styles) + len(factories)

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    story.append(Paragraph("Embedded JS/CSS Audit Report", S['title']))
    story.append(Paragraph("Front-End Asset Governance — All Non-Test Source", S['h3']))
    story.append(Spacer(1, 0.1 * inch))

    meta = (
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&nbsp;&nbsp;&nbsp;"
        f"<b>Project Root:</b> {root}<br/>"
        f"<b>Scope:</b> All non-test .py files (src/, app/, config/, tools/, docs/; "
        f"excluding __pycache__ and the audit tooling itself)<br/>"
        f"<b>Files Scanned:</b> {findings['files_scanned']}&nbsp;&nbsp;&nbsp;"
        f"<b>Files With Embedded Assets:</b> {findings['files_flagged']}<br/>"
        f"<b>Policy:</b> JavaScript and CSS must live in companion .js/.css files "
        f"under src/static/ and be loaded at render time, not authored as Python "
        f"string literals."
    )
    story.append(Paragraph(meta, S['body']))

    # ------------------------------------------------------------------
    # Executive summary
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("Executive Summary", S['h2']))

    summary_data = [
        ['Category', 'Violations', 'Severity', 'Status'],
        ['Inline <script> blocks (hand-written JS)',
         str(len(scripts)), 'HIGH', _risk_label(len(scripts))],
        ['Inline <style> blocks (hand-written CSS)',
         str(len(styles)), 'MEDIUM', _risk_label(len(styles))],
        ['JS factory strings (no <script> wrapper)',
         str(len(factories)), 'HIGH', _risk_label(len(factories))],
        ['TOTAL ACTION ITEMS', str(total), '', _risk_label(total)],
    ]
    tbl = Table(summary_data,
                colWidths=[3.0 * inch, 1.0 * inch, 1.0 * inch, 1.5 * inch])
    ts = _header_style()
    for row_idx, row in enumerate(summary_data[1:], 1):
        status = row[3]
        if status == 'COMPLIANT':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#27ae60'))
            ts.add('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold')
        elif status == 'ACTION REQUIRED':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#c0392b'))
            ts.add('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold')
        elif status == 'REVIEW':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#e67e22'))
            ts.add('FONTNAME', (3, row_idx), (3, row_idx), 'Helvetica-Bold')
    last = len(summary_data) - 1
    ts.add('BACKGROUND', (0, last), (-1, last), colors.HexColor('#ecf0f1'))
    ts.add('FONTNAME', (0, last), (-1, last), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 0.2 * inch))

    if total == 0:
        story.append(Paragraph(
            "<b>RESULT: COMPLIANT.</b>  No JavaScript or CSS is embedded as Python "
            "string literals in src/.  All front-end assets live in companion files.",
            S['body']))
    else:
        story.append(Paragraph(
            f"<b>RESULT: {_risk_label(total)}.</b>  {total} embedded-asset block(s) "
            f"across {findings['files_flagged']} file(s).  Each should be moved to a "
            "companion .js/.css file under src/static/ and loaded at render time.",
            S['body']))

    # ------------------------------------------------------------------
    # Section 1 — inline <script>
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("1. Inline &lt;script&gt; Blocks", S['h2']))
    story.append(Paragraph(
        "Each block below is a ``&lt;script&gt;`` element whose body is "
        "JavaScript written directly in a Python string.  External CDN includes "
        "(``&lt;script src=...&gt;``) and the thin wrapper that only injects "
        "``window.__X_CONFIG`` and reads the body from disk are not counted.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))
    if not scripts:
        story.append(Paragraph("No inline script blocks found. COMPLIANT.", S['note']))
    else:
        story.append(_violation_table(scripts, 'JS lines', 'js_lines'))

    # ------------------------------------------------------------------
    # Section 2 — inline <style>
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("2. Inline &lt;style&gt; Blocks", S['h2']))
    story.append(Paragraph(
        "CSS authored inside Python string literals.  Move these rules to a "
        "companion .css file under src/static/css/.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))
    if not styles:
        story.append(Paragraph("No inline style blocks found. COMPLIANT.", S['note']))
    else:
        story.append(_violation_table(styles, 'CSS lines', 'css_lines'))

    # ------------------------------------------------------------------
    # Section 3 — JS factory strings
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("3. JavaScript Factory Strings", S['h2']))
    story.append(Paragraph(
        "Large runs of JavaScript assembled in a Python string with no "
        "``&lt;script&gt;`` wrapper (for example, a panel factory that returns "
        "a JS fragment).  These are the hardest to maintain and must be moved "
        "to a companion .js file.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))
    if not factories:
        story.append(Paragraph("No JS factory strings found. COMPLIANT.", S['note']))
    else:
        story.append(_violation_table(factories, 'JS lines', 'js_lines'))

    # ------------------------------------------------------------------
    # Section 4 — Remediation guidance
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("4. Remediation Guidance", S['h2']))
    story.append(Spacer(1, 0.08 * inch))
    steps = [
        ("<b>Step 1 — Move the asset to a companion file</b><br/>"
         "Cut the JavaScript into src/static/js/&lt;name&gt;.js and any CSS into "
         "src/static/css/&lt;name&gt;.css.  The .js/.css file must contain no "
         "Python ``{interpolation}`` placeholders."),

        ("<b>Step 2 — Inject parameters via a config object</b><br/>"
         "Replace each Python interpolation with a field on a ``window.__X_CONFIG`` "
         "object emitted by the .py.  The static .js reads from that object instead "
         "of being f-string-formatted."),

        ("<b>Step 3 — Load the file at render time</b><br/>"
         "Read the companion file from disk and inline it, following the existing "
         "pattern (e.g. js_sibling(__file__) or the static/ loader used by "
         "notifications.py / backend_handler.py).  Preserve the fragment shape: a "
         "fragment spliced into a parent IIFE must stay a bare fragment."),

        ("<b>Step 4 — Re-run the audit</b><br/>"
         "Run ``python app.py test --audit`` to regenerate this report.  The "
         "Executive Summary totals should reach zero."),
    ]
    for step in steps:
        story.append(Paragraph(step, S['body']))
        story.append(Spacer(1, 0.12 * inch))

    _section_rule(story)
    story.append(Paragraph(
        "<i>Report generated by docs.models.embedded_js — "
        "MKM Research Labs Physical Risk Platform</i>",
        S['note']))

    doc.build(story)
    print(f"  embedded_js_report.pdf written to {output_path}")
