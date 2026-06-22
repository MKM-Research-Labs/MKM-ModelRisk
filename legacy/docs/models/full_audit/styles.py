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

"""Paragraph style sheet for the full audit report."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from ._constants import NAVY, STEEL


def _styles():
    base = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle(
            'FATitle', parent=base['Heading1'],
            fontSize=26, textColor=NAVY, spaceAfter=8,
            alignment=TA_CENTER, fontName='Helvetica-Bold'),
        'cover_sub': ParagraphStyle(
            'FASub', parent=base['Normal'],
            fontSize=13, textColor=STEEL, spaceAfter=4,
            alignment=TA_CENTER),
        'cover_meta': ParagraphStyle(
            'FAMeta', parent=base['Normal'],
            fontSize=9, textColor=colors.HexColor('#546E7A'),
            alignment=TA_CENTER, spaceAfter=2),
        'h2': ParagraphStyle(
            'FAH2', parent=base['Heading2'],
            fontSize=13, textColor=NAVY,
            spaceBefore=14, spaceAfter=6, fontName='Helvetica-Bold'),
        'h3': ParagraphStyle(
            'FAH3', parent=base['Heading3'],
            fontSize=10, textColor=STEEL,
            spaceBefore=8, spaceAfter=4, fontName='Helvetica-Bold'),
        'body': ParagraphStyle(
            'FABody', parent=base['BodyText'],
            fontSize=9, leading=13),
        'small': ParagraphStyle(
            'FASmall', parent=base['Normal'],
            fontSize=7.5, textColor=colors.HexColor('#78909C'), leading=11),
        'tbl_hdr': ParagraphStyle(
            'FATHdr', parent=base['Normal'],
            fontSize=8.5, textColor=colors.white, fontName='Helvetica-Bold'),
        'tbl_cell': ParagraphStyle(
            'FATCell', parent=base['Normal'],
            fontSize=8, leading=11),
        'tbl_cell_r': ParagraphStyle(
            'FATCellR', parent=base['Normal'],
            fontSize=8, leading=11, alignment=TA_RIGHT),
        'metric_val': ParagraphStyle(
            'FAMetricV', parent=base['Normal'],
            fontSize=20, textColor=NAVY, fontName='Helvetica-Bold',
            alignment=TA_CENTER),
        'metric_lbl': ParagraphStyle(
            'FAMetricL', parent=base['Normal'],
            fontSize=8, textColor=STEEL, alignment=TA_CENTER),
    }
