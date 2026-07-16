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

from config.audit import INIT_INVENTORY_DIRS, SOURCE_DIRS

from audit._walk import count_lines, py_files, rel


def _substantive(tree: ast.Module) -> dict:
    functions, classes, decorated = [], [], 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            decorated += len(node.decorator_list)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
    return {"functions": functions, "classes": classes, "decorated": decorated}


def _is_docstring(node: ast.stmt) -> bool:
    """The module docstring: a bare string-constant expression."""
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str))


def _is_dunder_reexport(node: ast.stmt) -> bool:
    """A dunder assignment (``__all__``/``__version__``) with a literal value."""
    if not isinstance(node, ast.Assign):
        return False
    names = [t.id for t in node.targets if isinstance(t, ast.Name)]
    if not names or not all(n.startswith("__") and n.endswith("__") for n in names):
        return False
    return isinstance(node.value, (ast.List, ast.Tuple, ast.Set, ast.Constant))


def _reexport_only(tree: ast.Module) -> bool:
    """True when a module is 100% aggregate: docstring, imports and ``__all__``.

    Stricter than :func:`_substantive` — it also rejects module-level logic
    (loops, conditionals, computed values, side-effecting calls), so only pure
    aggregator packages pass.
    """
    for index, node in enumerate(tree.body):
        if index == 0 and _is_docstring(node):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if _is_dunder_reexport(node):
            continue
        return False
    return True


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


def init_file_inventory() -> list[dict]:
    """Every first-party ``__init__.py`` with its length and re-export verdict.

    Where :func:`init_file_findings` reports only offenders (the R4 gate), this
    lists *all* package initialisers so the audit can show each is aggregate-only.
    ``lines`` is the file's length; ``reexport`` is ``True`` when the file is
    nothing but a docstring, imports and a literal ``__all__``.
    """
    inventory = []
    for path in py_files(*INIT_INVENTORY_DIRS):
        if path.name != "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        inventory.append({"path": rel(path), "lines": count_lines(path),
                          "reexport": _reexport_only(tree)})
    return sorted(inventory, key=lambda item: item["path"])
