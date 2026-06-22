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

"""Standalone __init__.py substantive-code audit report.

Scans every ``src/**/__init__.py`` for function/class/route definitions —
package initialisers should only wire a package together (imports, re-exports,
``__all__``, Blueprint assignment).  Produces two artefacts in the audit dir:

  init_audit_report.pdf      — standalone PDF, also surfaced in the
                               governance Risk tab and the consolidated
                               full_audit_report.pdf (section 4.1).
  init_audit_results.json    — machine-readable results for downstream
                               consumers.

The scan itself lives in ``docs.models.project.analysis.analyze_init_files``
and the table rendering in ``docs.models.project.pdf._add_init_audit_section``
so this report and the modularisation report stay in lock-step.
"""

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from docs.models.project.analysis import analyze_init_files
from docs.models.project.pdf import _add_init_audit_section


def _results_to_dict(issues: list) -> dict:
    """Serialise InitIssue namedtuples into a JSON-friendly summary."""
    return {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'files_with_substantive_code': len(issues),
            'total_functions': sum(len(i.functions) for i in issues),
            'total_classes': sum(len(i.classes) for i in issues),
            'total_routes': sum(i.routes for i in issues),
            'files_with_routes': sum(1 for i in issues if i.routes),
        },
        'files': [
            {
                'path': i.relative_path,
                'line_count': i.line_count,
                'functions': list(i.functions),
                'classes': list(i.classes),
                'routes': i.routes,
                'has_blueprint': i.has_blueprint,
            }
            for i in issues
        ],
    }


def _build_pdf(issues: list, output_path: Path) -> None:
    """Render the standalone __init__.py audit PDF."""
    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'InitAuditTitle', parent=base['Title'], fontSize=18, spaceAfter=6)
    sub_style = ParagraphStyle(
        'InitAuditSub', parent=base['Normal'], fontSize=9,
        textColor=ParagraphStyle('x', parent=base['Normal']).textColor)
    heading_style = ParagraphStyle(
        'InitAuditHeading', parent=base['Heading2'], fontSize=13, spaceBefore=6)
    body_style = ParagraphStyle(
        'InitAuditBody', parent=base['Normal'], fontSize=9, leading=13)

    story = []
    story.append(Paragraph('__init__.py Substantive-Code Audit', title_style))
    story.append(Paragraph(
        f'MKM Research Labs &mdash; generated {datetime.now():%Y-%m-%d %H:%M}',
        sub_style))
    story.append(Spacer(1, 0.25 * inch))

    _add_init_audit_section(story, issues, base, heading_style, body_style)

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    doc.build(story)


def main():
    """Scan src/**/__init__.py and write the standalone audit PDF + JSON."""
    from config import config

    here = Path(__file__).resolve().parent          # docs/models/init_audit/
    project_root = here.parent.parent.parent        # project root
    src_root = project_root / 'src'

    audit_dir = config.get_reports_dir('audit')
    audit_dir.mkdir(parents=True, exist_ok=True)

    pdf_output = audit_dir / 'init_audit_report.pdf'
    json_output = audit_dir / 'init_audit_results.json'

    print('Auditing __init__.py files for substantive code...')
    issues = analyze_init_files(src_root)
    print(f'  {len(issues)} __init__.py file(s) contain substantive code')

    payload = _results_to_dict(issues)
    json_output.write_text(json.dumps(payload, indent=2))
    print(f'  init_audit_results.json written to {json_output}')

    _build_pdf(issues, pdf_output)
    size_kb = pdf_output.stat().st_size / 1024
    print(f'  init_audit_report.pdf written to {pdf_output}  ({size_kb:.1f} KB)')
