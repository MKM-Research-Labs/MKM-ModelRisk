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

"""Shared styles and severity helpers for the hard-coding audit PDF."""

import sys

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Spacer, TableStyle
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)


def _risk_colour(count: int):
    if count == 0:
        return colors.HexColor('#27ae60')   # green
    if count <= 5:
        return colors.HexColor('#f39c12')   # amber
    return colors.HexColor('#c0392b')       # red


def _risk_label(count: int) -> str:
    if count == 0:
        return 'COMPLIANT'
    if count <= 5:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _styles():
    base = getSampleStyleSheet()
    return {
        'title': ParagraphStyle('HCTitle', parent=base['Heading1'],
                                fontSize=22, textColor=colors.HexColor('#1a1a1a'),
                                spaceAfter=20, alignment=TA_CENTER),
        'h2': ParagraphStyle('HCH2', parent=base['Heading2'],
                              fontSize=14, textColor=colors.HexColor('#2c3e50'),
                              spaceAfter=8, spaceBefore=14),
        'h3': ParagraphStyle('HCH3', parent=base['Heading3'],
                              fontSize=11, textColor=colors.HexColor('#34495e'),
                              spaceAfter=6, spaceBefore=10),
        'body': ParagraphStyle('HCBody', parent=base['BodyText'],
                               fontSize=9, leading=13),
        'code': ParagraphStyle('HCCode', parent=base['Code'],
                               fontSize=8, leading=11,
                               textColor=colors.HexColor('#333333')),
        'note': ParagraphStyle('HCNote', parent=base['BodyText'],
                               fontSize=8, leading=11,
                               textColor=colors.HexColor('#666666'),
                               leftIndent=12),
    }


def _header_style():
    return TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 9),
        ('ALIGN',         (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND',    (0, 1), (-1, -1), colors.white),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f6f9')]),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID',          (0, 0), (-1, -1), 0.4, colors.HexColor('#cccccc')),
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
    ])


def _severity_badge_colour(label: str):
    return {
        'HIGH':   colors.HexColor('#c0392b'),
        'MEDIUM': colors.HexColor('#e67e22'),
        'LOW':    colors.HexColor('#27ae60'),
        'INFO':   colors.HexColor('#3498db'),
    }.get(label, colors.grey)


def _section_rule(story):
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width='100%', thickness=1,
                             color=colors.HexColor('#bdc3c7')))
    story.append(Spacer(1, 0.1 * inch))
