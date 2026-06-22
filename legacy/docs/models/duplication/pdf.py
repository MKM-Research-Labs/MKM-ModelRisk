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

"""Render the duplication analysis into a PDF byte string."""

import io
import sys
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

from ._paths import MIN_LINES, MIN_TOKENS
from .jscpd_runner import _jscpd_version


def _make_pdf(analysis: dict, run_at: datetime) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=25 * mm, bottomMargin=20 * mm,
        title='Code Duplication Analysis Report',
        author='MKM Research Labs',
    )

    styles = getSampleStyleSheet()
    BLUE = colors.HexColor('#1565c0')
    DARK = colors.HexColor('#212121')
    GREY = colors.HexColor('#757575')
    LIGHT_BG = colors.HexColor('#f5f5f5')
    RED = colors.HexColor('#c62828')
    GREEN = colors.HexColor('#2e7d32')
    AMBER = colors.HexColor('#e65100')

    title_s = ParagraphStyle('DupTitle', parent=styles['Title'],
                              fontSize=20, spaceAfter=4, textColor=BLUE)
    sub_s = ParagraphStyle('DupSub', parent=styles['Normal'],
                            fontSize=10, spaceAfter=2, textColor=GREY)
    h2_s = ParagraphStyle('DupH2', parent=styles['Heading2'],
                           fontSize=13, spaceBefore=16, spaceAfter=8,
                           textColor=BLUE)
    body_s = ParagraphStyle('DupBody', parent=styles['Normal'],
                             fontSize=10, leading=14, spaceAfter=4)
    small_s = ParagraphStyle('DupSmall', parent=styles['Normal'],
                              fontSize=8, leading=11, textColor=GREY)
    caption_s = ParagraphStyle('DupCaption', parent=styles['Normal'],
                                fontSize=9, leading=12, textColor=DARK)

    total = analysis['total']
    num_clones = analysis['num_clones']
    pct = total.get('percentage', 0)
    dup_lines = total.get('duplicatedLines', 0)
    total_lines = total.get('lines', 0)
    sources = total.get('sources', 0)

    if pct < 3:
        rating, rating_col = 'GOOD', GREEN
        rating_note = (
            'Duplication is within acceptable bounds for a codebase of this size. '
            'Most clones are structural (PDF page base classes, report generators) '
            'that share common patterns by design.'
        )
    elif pct < 8:
        rating, rating_col = 'MODERATE', AMBER
        rating_note = (
            'Duplication is moderate. Consider extracting shared base classes or '
            'utility helpers in the highest-offender files to reduce maintenance risk.'
        )
    else:
        rating, rating_col = 'HIGH', RED
        rating_note = (
            'Duplication is above recommended thresholds. Refactoring is advised '
            'to reduce maintenance risk and improve testability.'
        )

    elems = []

    elems.append(Paragraph('Code Duplication Analysis Report', title_s))
    elems.append(Paragraph(
        f'MKM Research Labs &nbsp;|&nbsp; PhysicalRisk Platform &nbsp;|&nbsp; '
        f'Generated: {run_at.strftime("%d %B %Y %H:%M")}', sub_s))
    elems.append(Paragraph(
        f'Tool: jscpd &nbsp;|&nbsp; Scope: src/ &nbsp;|&nbsp; '
        f'Min block: {MIN_LINES} lines / {MIN_TOKENS} tokens &nbsp;|&nbsp; '
        f'Languages: Python, JavaScript', small_s))
    elems.append(Spacer(1, 8))
    elems.append(HRFlowable(width='100%', thickness=1.5, color=BLUE))
    elems.append(Spacer(1, 10))

    elems.append(Paragraph('Executive Summary', h2_s))
    kpi_data = [
        ['Metric', 'Value'],
        ['Total files analysed', f'{sources:,}'],
        ['Total lines of code', f'{total_lines:,}'],
        ['Duplicate clone pairs detected', f'{num_clones:,}'],
        ['Duplicated lines', f'{dup_lines:,}'],
        ['Duplication percentage (lines)', f'{pct:.1f}%'],
        ['Overall rating', rating],
    ]
    kpi_table = Table(kpi_data, colWidths=[110 * mm, 60 * mm])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (1, -1), (1, -1), rating_col),
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    elems.append(kpi_table)
    elems.append(Spacer(1, 10))
    elems.append(Paragraph(f'<b>Rating: {rating}</b> — {rating_note}', body_s))
    elems.append(Spacer(1, 6))

    if analysis['fmt_stats']:
        elems.append(Paragraph('Breakdown by Language', h2_s))
        fmt_data = [['Language', 'Files', 'Total Lines', 'Clones', 'Dup. Lines']]
        for fmt, stat in sorted(analysis['fmt_stats'].items()):
            fmt_data.append([
                fmt.capitalize(),
                f"{stat.get('sources', 0):,}",
                f"{stat.get('lines', 0):,}",
                f"{stat.get('clones', 0):,}",
                f"{stat.get('duplicatedLines', 0):,}",
            ])
        fmt_table = Table(fmt_data, colWidths=[35 * mm, 30 * mm, 35 * mm, 30 * mm, 35 * mm])
        fmt_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ]))
        elems.append(fmt_table)
        elems.append(Spacer(1, 10))

    elems.append(Paragraph('Files with Most Clone Pairs', h2_s))
    elems.append(Paragraph(
        'Files appearing most frequently in clone pairs. These are the primary '
        'candidates for refactoring into shared base classes or utilities.', body_s))
    elems.append(Spacer(1, 4))
    worst_data = [['File (relative to src/)', 'Clone Pairs', 'Dup. Lines']]
    for fname, count, dup_l in analysis['worst']:
        short = fname[:72] + '…' if len(fname) > 72 else fname
        worst_data.append([Paragraph(short, caption_s), str(count), str(dup_l)])
    worst_table = Table(worst_data, colWidths=[120 * mm, 25 * mm, 25 * mm])
    worst_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elems.append(worst_table)
    elems.append(Spacer(1, 10))

    elems.append(Paragraph('Largest Clone Pairs (by line count)', h2_s))
    elems.append(Paragraph(
        'The 20 largest duplicate code blocks detected. Line numbers indicate '
        'where each clone starts in its respective file.', body_s))
    elems.append(Spacer(1, 4))
    large_data = [['File A', 'L#', 'File B', 'L#', 'Lines']]
    for f1, l1, f2, l2, lines, _tokens in analysis['largest']:
        def shorten(p, n=38):
            parts = p.split('/')
            s = '/'.join(parts[-3:]) if len(parts) >= 3 else p
            return (s[:n] + '…') if len(s) > n else s
        large_data.append([
            Paragraph(shorten(f1), caption_s), str(l1),
            Paragraph(shorten(f2), caption_s), str(l2),
            str(lines),
        ])
    large_table = Table(large_data, colWidths=[65 * mm, 12 * mm, 65 * mm, 12 * mm, 16 * mm])
    large_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (-1, -1), 'CENTER'),
    ]))
    elems.append(large_table)
    elems.append(Spacer(1, 12))

    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 8))
    elems.append(Paragraph('Recommended Actions', h2_s))
    recs = [
        ('<b>PDF base classes (reports/gauge, reports/property, reports/risk)</b> — '
         'The three *_page_00_base.py files share extensive header/footer/table-cell '
         'rendering logic. Consolidate into a single <i>reports/shared/pdf_base.py</i> '
         'base class with subclass hooks.'),
        ('<b>Report generators (gauge_generator, property_generator, generator)</b> '
         '— These share pipeline scaffolding (build, save, open PDF). Extract a '
         '<i>reports/shared/base_generator.py</i> with the common lifecycle.'),
        ('<b>Port data loaders (gauge.py, property.py, mortgage.py)</b> — '
         'The JSON field-extraction patterns are highly similar. A shared '
         '<i>port/src/base_entity.py</i> would reduce repetition.'),
        ('<b>Routes: propertyts/animation.py</b> — Contains self-duplication (4 clones). '
         'Extract repeated interpolation and response-building blocks into helper functions.'),
        ('<b>Routes: governance/audit.py + models.py</b> — Shared pagination/filtering '
         'patterns; extract a <i>_query_helpers.py</i> utility.'),
        ('<b>Note on acceptable duplication</b> — Some clones in PDF rendering '
         '(table cell formatters, MRC PDF sections) are acceptable structural repetition '
         'given the domain. Prioritise refactoring only where test coverage is low.'),
    ]
    for i, rec in enumerate(recs, 1):
        elems.append(Paragraph(f'{i}. {rec}', body_s))
        elems.append(Spacer(1, 4))

    elems.append(Spacer(1, 8))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=GREY))
    elems.append(Spacer(1, 4))
    elems.append(Paragraph(
        f'Report generated {run_at.strftime("%d %B %Y at %H:%M:%S")} &nbsp;|&nbsp; '
        f'jscpd v{_jscpd_version()} &nbsp;|&nbsp; '
        'Thresholds: min-lines=8, min-tokens=50 &nbsp;|&nbsp; '
        'SR 11-7 / SS1/23 Code Quality Evidence',
        small_s,
    ))

    doc.build(elems)
    return buf.getvalue()
