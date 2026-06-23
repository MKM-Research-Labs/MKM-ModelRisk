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
"""Hardcoded-parameter audit (coding rule R1): params belong in ``config/``."""
from __future__ import annotations

import ast
import re

from config.audit import CONFIG_DIR, SOURCE_DIRS

from audit._walk import py_files, rel

# Infrastructure literals that must come from config, never inline.
_INFRA_RE = re.compile(r"\b(127\.0\.0\.1|0\.0\.0\.0|localhost)\b")
_SELF_PKG = "audit/"


def _is_allcaps(name: str) -> bool:
    return name.isupper() and "_" in name and len(name) > 3


def _is_numeric(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float)) and not isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _is_numeric(node.operand)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and node.elts:
        return all(_is_numeric(elt) for elt in node.elts)
    return False


def _scan_allcaps(tree: ast.Module, path: str) -> list[dict]:
    out = []
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and _is_allcaps(target.id) and _is_numeric(node.value):
                out.append({"path": path, "line": node.lineno, "kind": "allcaps_numeric",
                            "name": target.id})
    return out


def _scan_infra(text: str, path: str) -> list[dict]:
    out = []
    for index, line in enumerate(text.splitlines(), start=1):
        code = line.split("#", 1)[0]
        if _INFRA_RE.search(code):
            out.append({"path": path, "line": index, "kind": "infra_literal",
                        "name": _INFRA_RE.search(code).group(0)})
    return out


def hardcoding_findings() -> list[dict]:
    """Report ALL-CAPS numeric constants and infra literals outside ``config/``."""
    findings = []
    for path in py_files(*SOURCE_DIRS):
        relpath = rel(path)
        if relpath.startswith((CONFIG_DIR + "/", _SELF_PKG)):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings.extend(_scan_allcaps(ast.parse(text), relpath))
        findings.extend(_scan_infra(text, relpath))
    return findings
