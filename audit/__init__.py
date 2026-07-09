# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Coding-rule audit suite (large files, hardcoding, embedded JS, __init__, duplication)."""
from audit.data_access import data_access_findings
from audit.duplication import duplication_report, jscpd_available
from audit.embedded_js import embedded_js_findings
from audit.hardcoding import hardcoding_findings
from audit.init_files import init_file_findings
from audit.large_files import large_source_files, large_test_files, large_web_files
from audit.path_definitions import path_definition_findings

__all__ = [
    "large_source_files",
    "large_web_files",
    "large_test_files",
    "hardcoding_findings",
    "embedded_js_findings",
    "init_file_findings",
    "data_access_findings",
    "path_definition_findings",
    "duplication_report",
    "jscpd_available",
]
