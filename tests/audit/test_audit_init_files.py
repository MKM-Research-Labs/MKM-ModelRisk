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

from audit.init_files import (_reexport_only, _substantive, init_file_findings,
                              init_file_inventory)


def test_substantive_detects_functions_and_classes():
    detail = _substantive(ast.parse("import os\ndef build():\n    pass\nclass Engine:\n    pass"))
    assert detail["functions"] == ["build"]
    assert detail["classes"] == ["Engine"]


def test_substantive_allows_imports_and_reexports():
    detail = _substantive(ast.parse("from x import y\nBLUEPRINT = 1\n__all__ = ['y']"))
    assert detail["functions"] == [] and detail["classes"] == []


def test_repo_init_files_only_reexport():
    assert init_file_findings() == []


def test_reexport_only_accepts_docstring_imports_and_dunder_all():
    src = '"""Package."""\nfrom x import y\nimport os\n__all__ = ["y"]\n'
    assert _reexport_only(ast.parse(src)) is True


def test_reexport_only_rejects_functions_classes_and_logic():
    assert _reexport_only(ast.parse("def f():\n    pass\n")) is False
    assert _reexport_only(ast.parse("class C:\n    pass\n")) is False
    # Module-level logic that _substantive (functions/classes only) would miss.
    assert _reexport_only(ast.parse("from x import y\nZ = [i for i in y]\n")) is False
    assert _reexport_only(ast.parse("import os\nos.mkdir('x')\n")) is False


def test_inventory_lists_every_init_with_length_and_verdict():
    inventory = init_file_inventory()
    assert inventory, "expected first-party __init__.py files"
    # Every entry carries a path, a positive line count and a boolean verdict.
    for item in inventory:
        assert item["path"].endswith("__init__.py")
        assert item["lines"] > 0
        assert isinstance(item["reexport"], bool)
    # Coverage spans packages beyond the app source (audit/ and packages/).
    paths = {item["path"] for item in inventory}
    assert "config/__init__.py" in paths
    assert "audit/__init__.py" in paths
    assert any(p.startswith("packages/") for p in paths)


def test_inventory_reports_every_repo_init_as_reexport():
    assert all(item["reexport"] for item in init_file_inventory())
