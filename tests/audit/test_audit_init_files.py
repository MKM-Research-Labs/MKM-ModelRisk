# Copyright (c) 2022-2026 MKM Research Labs.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
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
