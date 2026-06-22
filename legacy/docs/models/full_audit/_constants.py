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

"""Paths, colours, and the base table style for the full audit report."""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_root / 'src'))

try:
    from reportlab.lib import colors
except ImportError:
    print("ERROR: reportlab is required.  pip install reportlab")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

from config import config
AUDIT_DIR = config.get_reports_dir('audit')
SRC_DIR = _root / 'src'
OUTPUT_PDF = AUDIT_DIR / 'full_audit_report.pdf'

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

NAVY = colors.HexColor('#1A237E')
STEEL = colors.HexColor('#37474F')
BLUE = colors.HexColor('#1565C0')
LIGHT_BG = colors.HexColor('#F5F5F5')
HEADER_BG = colors.HexColor('#E8EAF6')
GREEN = colors.HexColor('#2E7D32')
AMBER = colors.HexColor('#E65100')
RED = colors.HexColor('#B71C1C')
GREY = colors.HexColor('#90A4AE')

# ---------------------------------------------------------------------------
# Base table style — shared by all section tables
# ---------------------------------------------------------------------------

_TBL_STYLE_BASE = [
    ('FONTSIZE',       (0, 0), (-1, 0),  8.5),
    ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
    ('BACKGROUND',     (0, 0), (-1, 0),  NAVY),
    ('TEXTCOLOR',      (0, 0), (-1, 0),  colors.white),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
    ('GRID',           (0, 0), (-1, -1), 0.4, colors.HexColor('#CFD8DC')),
    ('BOX',            (0, 0), (-1, -1), 1.0, STEEL),
    ('FONTSIZE',       (0, 1), (-1, -1), 8),
    ('TOPPADDING',     (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING',  (0, 0), (-1, -1), 4),
    ('LEFTPADDING',    (0, 0), (-1, -1), 6),
    ('RIGHTPADDING',   (0, 0), (-1, -1), 6),
    ('VALIGN',         (0, 0), (-1, -1), 'MIDDLE'),
]
