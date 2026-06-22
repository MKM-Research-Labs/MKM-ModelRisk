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

"""Code duplication analysis report generator.

Runs jscpd on src/ and produces a PDF summary saved to data/output/audit/.

Usage:
    python -m docs.models.duplication
"""

from ._paths import (
    ROOT_DIR,
    SRC_DIR,
    AUDIT_DIR,
    OUTPUT_PDF,
    MIN_LINES,
    MIN_TOKENS,
)
from .jscpd_runner import _find_node_env, _run_jscpd, _jscpd_version
from .analyse import _analyse
from .pdf import _make_pdf
from .report import main

__all__ = [
    'ROOT_DIR', 'SRC_DIR', 'AUDIT_DIR', 'OUTPUT_PDF', 'MIN_LINES', 'MIN_TOKENS',
    '_find_node_env', '_run_jscpd', '_jscpd_version', '_analyse', '_make_pdf', 'main',
]
