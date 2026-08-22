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
"""Styling audit (coding rule R10): colours live in ``config/theme.py``.

Two findings, and the second is the one that bites. A colour literal is visible — you
can read it and see it is wrong. A reference to a token that does not exist is not:
the browser drops the declaration silently, so the element renders with whatever it
inherits, and nobody notices until an adopter's rebrand leaves one control the old
colour. Both are checked here.

Every asset type the console serves — ``.css``, ``.js`` and ``.html`` — is gated as of
step 5 of docs/design/theme_config.md. The reported bucket holds anything scanned but
not yet gated, so adding a new asset type surfaces it rather than exempting it in
silence; see ``STYLING_GATED_SUFFIXES``.
"""
from __future__ import annotations

import re

from config.audit import (CONFIG_DIR, SOURCE_DIRS, STYLING_ASSET_DIRS,
                          STYLING_GATED_SUFFIXES, THEME_MODULE)
from config.theme import THEME

from audit._walk import REPO_ROOT, py_files, rel, walk

# A CSS colour. Two guards, both learned from false positives on this repo's own
# markup: the trailing one keeps ``#abc`` in the id selector ``#abc-panel`` out, and the
# leading one keeps the numeric character references out — ``&#9888;`` is the warning
# sign, not a colour, and its digits are all decimal.
_COLOUR = re.compile(r"(?<!&)#[0-9a-fA-F]{3,8}(?![-\w])|\b(?:rgba?|hsla?)\s*\(")
_VAR_REFERENCE = re.compile(r"var\(\s*--([a-zA-Z0-9_-]+)")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_ASSET_SUFFIXES = (".css", ".js", ".html")
# The audit's own regexes contain colour-shaped text; never flag the audit package.
_SELF_PKG = "audit/"


def _asset_files():
    for directory in STYLING_ASSET_DIRS:
        root = REPO_ROOT / directory
        for suffix in _ASSET_SUFFIXES:
            yield from walk(root, suffix)


def _hits(text: str, path: str, kind: str) -> list[dict]:
    out = []
    for index, line in enumerate(_CSS_COMMENT.sub("", text).splitlines(), start=1):
        for match in _COLOUR.finditer(line):
            out.append({"path": path, "line": index, "kind": kind,
                        "snippet": match.group(0).rstrip("(").strip()})
    return out


def colour_literal_findings() -> list[dict]:
    """Gated: a colour written down outside ``config/theme.py``.

    Covers the converted surfaces — the stylesheet, the templates, and every Python
    file bar the theme module itself.
    """
    findings = []
    for path in _asset_files():
        if path.suffix in STYLING_GATED_SUFFIXES:
            findings.extend(_hits(path.read_text(encoding="utf-8"), rel(path), "asset"))
    for path in py_files(*SOURCE_DIRS):
        relpath = rel(path)
        if relpath == THEME_MODULE or relpath.startswith(_SELF_PKG):
            continue
        findings.extend(_hits(path.read_text(encoding="utf-8"), relpath, "python"))
    return findings


def unconverted_colour_findings() -> list[dict]:
    """Reported: colour literals in the surfaces still awaiting conversion."""
    return [f for path in _asset_files() if path.suffix not in STYLING_GATED_SUFFIXES
            for f in _hits(path.read_text(encoding="utf-8"), rel(path), path.suffix[1:])]


def undefined_token_findings() -> list[dict]:
    """Gated: a ``var(--token)`` naming a token the theme does not define."""
    findings = []
    for path in _asset_files():
        text = path.read_text(encoding="utf-8")
        for index, line in enumerate(text.splitlines(), start=1):
            for match in _VAR_REFERENCE.finditer(line):
                if match.group(1) not in THEME:
                    findings.append({"path": rel(path), "line": index,
                                     "kind": "undefined_token",
                                     "snippet": "--" + match.group(1)})
    return findings
