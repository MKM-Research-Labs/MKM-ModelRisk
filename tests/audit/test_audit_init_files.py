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
"""Audit gate: substantive code in __init__.py (coding rule R4)."""
from __future__ import annotations

import ast

from audit.init_files import _substantive, init_file_findings


def test_substantive_detects_functions_and_classes():
    detail = _substantive(ast.parse("import os\ndef build():\n    pass\nclass Engine:\n    pass"))
    assert detail["functions"] == ["build"]
    assert detail["classes"] == ["Engine"]


def test_substantive_allows_imports_and_reexports():
    detail = _substantive(ast.parse("from x import y\nBLUEPRINT = 1\n__all__ = ['y']"))
    assert detail["functions"] == [] and detail["classes"] == []


def test_repo_init_files_only_reexport():
    assert init_file_findings() == []
