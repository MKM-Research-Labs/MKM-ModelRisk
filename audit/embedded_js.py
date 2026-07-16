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
"""Embedded-JavaScript audit (coding rule R7): no JS/CSS inside ``.py`` files."""
from __future__ import annotations

import re
from pathlib import Path

from config.audit import SOURCE_DIRS

from audit._walk import py_files, rel

# Tokens that strongly indicate a JavaScript payload assembled in Python.
_JS_TOKEN = re.compile(
    r"\b(document\.|window\.|addEventListener|querySelector|getElementById|"
    r"createElement|appendChild|innerHTML|console\.(log|error|warn)|"
    r"function\s*\(|=>|const |let |var )")
_SCRIPT_BLOCK = re.compile(r"<script\b[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
_STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)

_MIN_JS_LINES = 3
_MIN_FACTORY_LINES = 8
_GAP_TOLERANCE = 2
# The scanner's own regexes contain JS tokens; never flag the audit package.
_SELF_PKG = "audit/"


def _js_line_count(block: str) -> int:
    return sum(1 for line in block.splitlines() if _JS_TOKEN.search(line))


def _scan_blocks(text: str, pattern: re.Pattern, kind: str, path: str) -> list[dict]:
    out = []
    for match in pattern.finditer(text):
        js_lines = _js_line_count(match.group(1))
        if js_lines >= _MIN_JS_LINES:
            line = text.count("\n", 0, match.start()) + 1
            out.append({"path": path, "line": line, "kind": kind, "js_lines": js_lines})
    return out


def _scan_factories(text: str, path: str) -> list[dict]:
    """JS built line-by-line in Python strings, outside any <script> tag."""
    lines = text.splitlines()
    out, run, start, gap = [], 0, 0, 0
    for index, line in enumerate(lines, start=1):
        if _JS_TOKEN.search(line):
            if run == 0:
                start = index
            run += 1
            gap = 0
        elif run and gap < _GAP_TOLERANCE:
            gap += 1
        elif run:
            if run >= _MIN_FACTORY_LINES:
                out.append({"path": path, "line": start, "kind": "factory", "js_lines": run})
            run, gap = 0, 0
    if run >= _MIN_FACTORY_LINES:
        out.append({"path": path, "line": start, "kind": "factory", "js_lines": run})
    return out


def embedded_js_findings() -> list[dict]:
    """Report ``.py`` files that embed JavaScript or CSS payloads."""
    findings = []
    for path in py_files(*SOURCE_DIRS):
        relpath = rel(path)
        if relpath.startswith(_SELF_PKG):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        without_scripts = _SCRIPT_BLOCK.sub("", text)
        findings.extend(_scan_blocks(text, _SCRIPT_BLOCK, "script", relpath))
        findings.extend(_scan_blocks(text, _STYLE_BLOCK, "style", relpath))
        findings.extend(_scan_factories(without_scripts, relpath))
    return findings
