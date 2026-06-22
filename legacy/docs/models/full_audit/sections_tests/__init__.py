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

"""Test suite detail, coverage analysis, and modularisation sections.

Split into cohesive submodules; the public surface (the ``_build_*`` section
builders imported by ``report.py`` / the package ``__init__``) is unchanged.
"""

from .detail import (
    _build_test_detail, _build_unit_failures, _build_skipped_tests, _short_msg,
)
from .coverage import _build_coverage
from .modularisation import _build_modularisation, _build_init_audit
from .copyright_headers import _build_copyright_headers
from .path_definitions import _build_path_definitions
from .data_access import _build_data_access

__all__ = [
    '_build_test_detail', '_build_unit_failures', '_build_skipped_tests',
    '_short_msg', '_build_coverage', '_build_modularisation', '_build_init_audit',
    '_build_copyright_headers', '_build_path_definitions', '_build_data_access',
]
