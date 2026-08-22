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

import io
import re
import tokenize

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
# A colour written WITHOUT a leading "#", which is how LaTeX spells one. Both forms
# below sat in the source for months and the "#"-anchored scan above could not see
# either: \definecolor{mkmblue}{HTML}{1565C0} in latex.py, and a bare "9E9E9E"
# fallback in the risk-policy document. Python only — a six-character hex string in
# JavaScript is far more likely to be an identifier than a colour.
_LATEX_COLOUR = re.compile(r"\{HTML\}\{([0-9A-Fa-f]{6})\}")
_BARE_COLOUR = re.compile(r"[\"'\']([0-9A-Fa-f]{6})[\"'\']")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_ASSET_SUFFIXES = (".css", ".js", ".html")
# The audit's own regexes contain colour-shaped text; never flag the audit package.
_SELF_PKG = "audit/"


def _asset_files():
    for directory in STYLING_ASSET_DIRS:
        root = REPO_ROOT / directory
        for suffix in _ASSET_SUFFIXES:
            yield from walk(root, suffix)


def _without_comments(text: str) -> str:
    """``text`` with Python comments blanked, keeping every line in place.

    Naming a colour while explaining why colours are not written down here must not
    itself be a finding — the same reason the CSS scan strips ``/* … */``. Tokenising
    rather than cutting at the first ``#`` is what keeps ``"#1976d2"`` inside a string
    visible: only a real COMMENT token is removed.
    """
    lines = text.splitlines(keepends=True)
    try:
        comments = [tok for tok in tokenize.generate_tokens(io.StringIO(text).readline)
                    if tok.type == tokenize.COMMENT]
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    for tok in reversed(comments):
        row, (start, end) = tok.start[0] - 1, (tok.start[1], tok.end[1])
        lines[row] = lines[row][:start] + " " * (end - start) + lines[row][end:]
    return "".join(lines)


def _bare_hits(text: str, path: str) -> list[dict]:
    """Colours spelled without a ``#`` — the LaTeX form the main scan cannot see."""
    out = []
    for index, line in enumerate(text.splitlines(), start=1):
        for match in _LATEX_COLOUR.finditer(line):
            out.append({"path": path, "line": index, "kind": "latex",
                        "snippet": match.group(1)})
        for match in _BARE_COLOUR.finditer(line):
            # All six digits and at least one a-f: "123456" is a number, not a colour.
            if any(c.isalpha() for c in match.group(1)):
                out.append({"path": path, "line": index, "kind": "bare",
                            "snippet": match.group(1)})
    return out


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
        text = _without_comments(path.read_text(encoding="utf-8"))
        findings.extend(_hits(text, relpath, "python"))
        findings.extend(_bare_hits(text, relpath))
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
