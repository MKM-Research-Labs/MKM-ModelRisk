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

"""Metric boxes, status helpers, JSON loading, and page furniture."""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Table, TableStyle

from ._constants import (
    AUDIT_DIR, NAVY, STEEL, GREEN, AMBER, RED, HEADER_BG,
)


def _metric_box(value: str, label: str, col: colors.Color, styles) -> Table:
    data = [
        [Paragraph(value, styles['metric_val'])],
        [Paragraph(label, styles['metric_lbl'])],
    ]
    tbl = Table(data, colWidths=[36 * mm])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HEADER_BG),
        ('BOX',        (0, 0), (-1, -1), 1.5, col),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return tbl


def _load_json_report(filename: str) -> dict:
    """Load a JSON report from the audit directory, returning {} on failure."""
    import json
    path = AUDIT_DIR / filename
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Status helpers
# ---------------------------------------------------------------------------

def _status(good: bool, ok: bool = True) -> str:
    if good:
        return 'OK'
    if ok:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _status_inv(good: bool, ok: bool = True) -> str:
    """For counts where 0 = good."""
    if good:
        return 'OK'
    if ok:
        return 'REVIEW'
    return 'ACTION REQUIRED'


def _status_colour(status: str) -> colors.Color:
    m = {'OK': GREEN, 'REVIEW': AMBER, 'ACTION REQUIRED': RED,
         'INFO': STEEL, 'CRITICAL': RED, 'HIGH': RED,
         'MEDIUM': AMBER, 'LOW': STEEL}
    return m.get(status, STEEL)


def _map_sev(sev: str) -> str:
    return {'CRITICAL': 'ACTION REQUIRED', 'HIGH': 'ACTION REQUIRED',
            'MEDIUM': 'REVIEW', 'LOW': 'INFO', 'OK': 'OK'}.get(sev, sev)


# ---------------------------------------------------------------------------
# Header/footer callback
# ---------------------------------------------------------------------------

def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header bar
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(20 * mm, h - 12 * mm, 'MKM Physical Risk Platform')
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(
        w - 20 * mm, h - 12 * mm,
        f'Full Audit Report  |  {datetime.now().strftime("%d %B %Y")}')
    # Footer
    canvas.setFillColor(STEEL)
    canvas.rect(0, 0, w, 8 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica', 7.5)
    canvas.drawString(
        20 * mm, 2.5 * mm,
        'CONFIDENTIAL — MKM Research Labs  |  SR 11-7 / SS1/23 Model Governance')
    canvas.drawRightString(
        w - 20 * mm, 2.5 * mm,
        f'Page {doc.page}')
    canvas.restoreState()
