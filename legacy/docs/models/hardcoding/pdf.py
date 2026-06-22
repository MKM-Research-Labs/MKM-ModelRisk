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

"""Render the hard-coding audit findings into a PDF report."""

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

from .pdf_helpers import _risk_label, _styles, _header_style, _section_rule


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

    # ------------------------------------------------------------------
    # Title
    # ------------------------------------------------------------------
    story.append(Paragraph("Hard-Coding Audit Report", S['title']))
    story.append(Paragraph("Parameter Governance — src/ Directory", S['h3']))
    story.append(Spacer(1, 0.1 * inch))

    meta = (
        f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}&nbsp;&nbsp;&nbsp;"
        f"<b>Project Root:</b> {root}<br/>"
        f"<b>Scope:</b> All .py files in src/ (excluding __init__.py, __pycache__)<br/>"
        f"<b>Files Scanned:</b> {findings['files_scanned']}<br/>"
        f"<b>Policy:</b> Every configurable domain parameter must be defined once "
        f"in config.py and imported at every use site."
    )
    story.append(Paragraph(meta, S['body']))

    # ------------------------------------------------------------------
    # Executive summary table
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("Executive Summary", S['h2']))

    dups   = findings['duplicates']
    caps   = [f for f in findings['allcaps'] if not f['precision_ok']]
    caps_p = [f for f in findings['allcaps'] if f['precision_ok']]
    infra  = findings['infra']
    inline = findings['inline']
    total  = len(dups) + len(caps) + len(infra) + len(inline)

    summary_data = [
        ['Category', 'Violations', 'Severity', 'Status'],
        ['Duplicate constants across files',
         str(len(dups)), 'HIGH', _risk_label(len(dups))],
        ['ALL_CAPS parameters outside config.py',
         str(len(caps)), 'MEDIUM', _risk_label(len(caps))],
        ['Infrastructure literals (IP/port)',
         str(len(infra)), 'HIGH', _risk_label(len(infra))],
        ['Inline simulation literals',
         str(len(inline)), 'MEDIUM', _risk_label(len(inline))],
        ['Precision constants (acceptable)',
         str(len(caps_p)), 'INFO', 'ACKNOWLEDGED'],
        ['TOTAL ACTION ITEMS', str(total), '', _risk_label(total)],
    ]
    tbl = Table(summary_data,
                colWidths=[3.0 * inch, 1.0 * inch, 1.0 * inch, 1.5 * inch])
    ts = _header_style()
    # colour the status column
    for row_idx, row in enumerate(summary_data[1:], 1):
        status = row[3]
        if status == 'COMPLIANT':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#27ae60'))
            ts.add('FONTNAME',  (3, row_idx), (3, row_idx), 'Helvetica-Bold')
        elif status == 'ACTION REQUIRED':
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#c0392b'))
            ts.add('FONTNAME',  (3, row_idx), (3, row_idx), 'Helvetica-Bold')
        elif status in ('REVIEW', 'ACKNOWLEDGED'):
            ts.add('TEXTCOLOR', (3, row_idx), (3, row_idx), colors.HexColor('#e67e22'))
            ts.add('FONTNAME',  (3, row_idx), (3, row_idx), 'Helvetica-Bold')
    # highlight total row
    last = len(summary_data) - 1
    ts.add('BACKGROUND', (0, last), (-1, last), colors.HexColor('#ecf0f1'))
    ts.add('FONTNAME',   (0, last), (-1, last), 'Helvetica-Bold')
    tbl.setStyle(ts)
    story.append(tbl)
    story.append(Spacer(1, 0.2 * inch))

    if total == 0:
        story.append(Paragraph(
            "<b>RESULT: COMPLIANT.</b>  No hard-coded domain parameters detected in src/. "
            "All configurable values are defined in config.py.",
            S['body']))
    else:
        story.append(Paragraph(
            f"<b>RESULT: {_risk_label(total)}.</b>  {total} action item(s) identified. "
            "Each item should be resolved by migrating the constant to config.py "
            "and importing it at every use site.",
            S['body']))

    # ------------------------------------------------------------------
    # Section 1 — Duplicate constants
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("1. Duplicate Constants Across Files", S['h2']))
    story.append(Paragraph(
        "The following constants are defined with the same name in two or more src/ files. "
        "This is the highest-priority violation: divergence is certain over time. "
        "Each should have a single authoritative definition in config.py.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    if not dups:
        story.append(Paragraph("No duplicate constants found. COMPLIANT.", S['note']))
    else:
        for item in dups:
            story.append(Paragraph(
                f"<b>{item['name']}</b> — defined in {item['count']} files",
                S['h3']))
            loc_data = [['File', 'Line', 'Value']]
            for rel, lineno, val in item['locations']:
                loc_data.append([rel, str(lineno), repr(val)[:50]])
            t = Table(loc_data,
                      colWidths=[3.5 * inch, 0.6 * inch, 2.4 * inch])
            t.setStyle(_header_style())
            story.append(t)
            story.append(Spacer(1, 0.15 * inch))

    # ------------------------------------------------------------------
    # Section 2 — ALL_CAPS outside config
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("2. ALL_CAPS Parameters Outside config.py", S['h2']))
    story.append(Paragraph(
        "Module-level constants with ALL_CAPS names represent domain parameters. "
        "All such constants must live in config.py so they can be changed in one "
        "place and documented centrally. The table below excludes mathematical "
        "precision constants (e.g. LOG_EPS, BUMP_1BP) which are listed separately.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    if not caps:
        story.append(Paragraph("No undeclared ALL_CAPS constants found. COMPLIANT.", S['note']))
    else:
        cap_data = [['File', 'Line', 'Name', 'Value']]
        for item in caps:
            cap_data.append([item['file'], str(item['line']),
                             item['name'], item['value']])
        t = Table(cap_data,
                  colWidths=[2.8 * inch, 0.5 * inch, 1.8 * inch, 1.4 * inch])
        t.setStyle(_header_style())
        story.append(t)

    if caps_p:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(
            "2a. Acknowledged Precision Constants (not required to move to config.py)",
            S['h3']))
        story.append(Paragraph(
            "These constants are mathematical precision values tightly coupled "
            "to the formula that uses them.  They are documented here for completeness.",
            S['note']))
        story.append(Spacer(1, 0.06 * inch))
        p_data = [['File', 'Line', 'Name', 'Value', 'Rationale']]
        rationale = {
            'LOG_EPS':  'Numerical underflow guard in log transform',
            'BUMP_1BP': '1 bp bump for numerical differentiation of CDS price',
            'MIN_SLOPE': 'Hydraulic minimum slope for Manning equation',
        }
        for item in caps_p:
            p_data.append([item['file'], str(item['line']), item['name'],
                           item['value'],
                           rationale.get(item['name'], 'See source comment')])
        t = Table(p_data,
                  colWidths=[2.0 * inch, 0.5 * inch, 1.2 * inch, 0.8 * inch, 2.0 * inch])
        t.setStyle(_header_style())
        story.append(t)

    # ------------------------------------------------------------------
    # Section 3 — Infrastructure literals
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("3. Infrastructure Literals", S['h2']))
    story.append(Paragraph(
        "Hardcoded IP addresses and the server port (5013) must not appear as "
        "string or integer literals in src/ files.  Use config.SERVER_HOST and "
        "config.SERVER_PORT so that deployment configuration can be changed "
        "without editing source files.",
        S['body']))
    story.append(Spacer(1, 0.1 * inch))

    if not infra:
        story.append(Paragraph("No infrastructure literals found. COMPLIANT.", S['note']))
    else:
        inf_data = [['File', 'Line', 'Type', 'Snippet']]
        for item in infra:
            inf_data.append([item['file'], str(item['line']),
                             item['kind'].upper(), item['snippet']])
        t = Table(inf_data,
                  colWidths=[2.0 * inch, 0.5 * inch, 0.6 * inch, 3.4 * inch])
        t.setStyle(_header_style())
        story.append(t)

    # ------------------------------------------------------------------
    # Section 4 — Inline simulation literals
    # ------------------------------------------------------------------
    _section_rule(story)
    story.append(Paragraph("4. Inline Simulation Literals", S['h2']))
    story.append(Paragraph(
        "Simulation horizon and similar operational parameters must not be "
        "assigned as bare numeric literals.  Use a named constant (e.g. "
        "STORM_HOURS) imported from config.py so that changing the simulation "
        "window requires editing only one file.",
        S['body']))
    story.append(Paragraph(
        "Example violation:  <i>n_hours = 60</i><br/>"
        "Correct form:  <i>n_hours = config.STORM_HOURS</i>",
        S['note']))
    story.append(Spacer(1, 0.1 * inch))

    if not inline:
        story.append(Paragraph("No inline simulation literals found. COMPLIANT.", S['note']))
    else:
        inl_data = [['File', 'Line', 'Parameter', 'Value', 'Snippet']]
        for item in inline:
            inl_data.append([item['file'], str(item['line']),
                             item['param'], item['value'], item['snippet']])
        t = Table(inl_data,
                  colWidths=[2.2 * inch, 0.5 * inch, 1.0 * inch, 0.5 * inch, 2.3 * inch])
        t.setStyle(_header_style())
        story.append(t)

    # ------------------------------------------------------------------
    # Section 5 — Remediation guidance
    # ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("5. Remediation Guidance", S['h2']))
    story.append(Paragraph(
        "Follow these steps to resolve each violation:",
        S['body']))
    story.append(Spacer(1, 0.08 * inch))

    steps = [
        ("<b>Step 1 — Add the parameter to config.py</b><br/>"
         "Define the constant as a class attribute of <i>PortfolioConfig</i> with a "
         "descriptive comment.  Use an environment variable override where appropriate "
         "so the value can be changed at deployment without a code change:<br/>"
         "<i>STORM_HOURS: int = int(os.getenv('MKM_STORM_HOURS', '168'))  "
         "# 7-day storm simulation window</i>"),

        ("<b>Step 2 — Import at use sites</b><br/>"
         "Remove the local definition and import the constant from config:<br/>"
         "<i>from config import config<br/>"
         "n_hours = config.STORM_HOURS</i>"),

        ("<b>Step 3 — Eliminate duplicates</b><br/>"
         "If the same constant exists in multiple files (Section 1 violations), "
         "confirm all copies have the same value, keep only the config.py definition, "
         "and update all callers.  If the copies have drifted apart, treat that "
         "as a calibration finding requiring model review."),

        ("<b>Step 4 — Re-run the audit</b><br/>"
         "Run <i>python app.py test --audit</i> to regenerate this report.  "
         "The violation count in Section 1 of the Executive Summary should reach zero. "
         "Section 2 will reduce as parameters are migrated."),

        ("<b>Step 5 — Governance sign-off</b><br/>"
         "Once the duplicate-constants and infrastructure-literals counts are zero, "
         "obtain Model Risk sign-off on the parameter inventory in config.py. "
         "This ensures a single auditable source of truth aligned with SR 11-7 "
         "model documentation requirements."),
    ]
    for step in steps:
        story.append(Paragraph(step, S['body']))
        story.append(Spacer(1, 0.12 * inch))

    _section_rule(story)
    story.append(Paragraph(
        f"<i>Report generated by docs.models.hardcoding — "
        f"MKM Research Labs Physical Risk Platform</i>",
        S['note']))

    doc.build(story)
    print(f"  hardcoding_report.pdf written to {output_path}")
