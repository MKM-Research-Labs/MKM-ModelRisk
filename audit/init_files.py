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
"""__init__.py audit (coding rule R4): packages re-export, they do not compute."""
from __future__ import annotations

import ast

from config.audit import SOURCE_DIRS

from audit._walk import py_files, rel


def _substantive(tree: ast.Module) -> dict:
    functions, classes, decorated = [], [], 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            decorated += len(node.decorator_list)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {"functions": functions, "classes": classes, "decorated": decorated}


def init_file_findings() -> list[dict]:
    """Report ``__init__.py`` files that define functions, classes or routes."""
    findings = []
    for path in py_files(*SOURCE_DIRS):
        if path.name != "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        detail = _substantive(tree)
        if detail["functions"] or detail["classes"]:
            findings.append({"path": rel(path), **detail})
    return findings
