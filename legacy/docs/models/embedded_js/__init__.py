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

"""
Embedded JS/CSS Audit — Front-End Asset Governance Report.

Scans all src/*.py files for JavaScript and CSS embedded as Python string
literals.  Front-end assets belong in companion .js/.css files under
src/static/ (loaded at render time), not hand-written inside Python.

Three classes of violation are detected:
  1. Inline ``<script>`` blocks containing real JavaScript (not external
     CDN ``<script src=...>`` includes, and not the accepted thin wrapper
     that injects ``window.__X_CONFIG`` and reads the body from a file).
  2. Inline ``<style>`` blocks containing CSS.
  3. JavaScript "factory" strings — large runs of JS built in a Python
     string with no ``<script>`` wrapper at all.

Output:  data/output/audit/embedded_js_report.pdf

Usage:
    python -m docs.models.embedded_js
"""

from .scanners import (
    MIN_JS_LINES,
    MIN_CSS_LINES,
    MIN_FACTORY_LINES,
    scan_inline_scripts,
    scan_inline_styles,
    scan_js_factories,
    collect_all,
    collect_all_repo,
)
from .pdf import create_pdf_report
from .report import main

__all__ = [
    'MIN_JS_LINES', 'MIN_CSS_LINES', 'MIN_FACTORY_LINES',
    'scan_inline_scripts', 'scan_inline_styles', 'scan_js_factories',
    'collect_all', 'collect_all_repo', 'create_pdf_report', 'main',
]
