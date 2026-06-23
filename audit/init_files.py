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
