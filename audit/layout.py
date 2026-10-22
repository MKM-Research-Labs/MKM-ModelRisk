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
"""Layout audit (coding rule R11): screens are built from the shared layout vocabulary.

A screen that invents its own heading or its own kind of tab bar looks fine on its own
and wrong beside every other screen, and nothing else in the audit would notice: the
colours it uses are tokens, so R10 is satisfied. Three gated findings:

- a screen building a heading other than a card's or a modal's title (``h3``/``h2``).
  Inside a card, a title is ``.section-header``.
- a stylesheet rule for a heading beyond the three the console defines
  (``LAYOUT_HEADING_SELECTORS``) -- a second, larger heading style is how a screen
  starts to look unlike the others (``.card h3.vocab-group`` on Admin, 2026-10-22).
- a tab bar carrying a modifier class (``class="dtabs something"``). A second level is
  another plain ``dtabs`` row beneath the first, never a variant of the bar itself --
  that is how a column of section labels down the side of Admin got in.
"""
from __future__ import annotations

import re

from config.audit import (LAYOUT_ASSET_DIRS, LAYOUT_HEADING_SELECTORS,
                          LAYOUT_SCREEN_HEADINGS, LAYOUT_STYLESHEET_DIR)

from audit._walk import REPO_ROOT, rel, walk

_HEADING = re.compile(r"<(h[1-6])[\s>]", re.IGNORECASE)
_TAB_BAR_VARIANT = re.compile(r"""class=\\?["']dtabs\s+[^"'\\]""")
_LINE_COMMENT = re.compile(r"^\s*//")
_CSS_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_CSS_RULE = re.compile(r"([^{}]+)\{")
_HEADING_SELECTOR = re.compile(r"\bh[1-6]\b")


def _finding(path, line: int, kind: str, snippet: str) -> dict:
    return {"path": rel(path), "line": line, "kind": kind, "snippet": snippet.strip()[:80]}


def _screen_findings() -> list[dict]:
    findings = []
    for directory in LAYOUT_ASSET_DIRS:
        for path in walk(REPO_ROOT / directory, ".js"):
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if _LINE_COMMENT.match(line):
                    continue
                if any(m.group(1).lower() not in LAYOUT_SCREEN_HEADINGS
                       for m in _HEADING.finditer(line)):
                    findings.append(_finding(path, index, "heading", line))
                if _TAB_BAR_VARIANT.search(line):
                    findings.append(_finding(path, index, "tab_bar_variant", line))
    return findings


def _stylesheet_findings() -> list[dict]:
    findings = []
    for path in walk(REPO_ROOT / LAYOUT_STYLESHEET_DIR, ".css"):
        text = _CSS_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"),
                                path.read_text(encoding="utf-8"))
        for match in _CSS_RULE.finditer(text):
            group = match.group(1)
            start = match.start(1) + len(group) - len(group.lstrip())
            line = text.count("\n", 0, start) + 1
            for selector in match.group(1).split(","):
                selector = " ".join(selector.split())
                if _HEADING_SELECTOR.search(selector) and \
                        selector not in LAYOUT_HEADING_SELECTORS:
                    findings.append(_finding(path, line, "heading_style", selector))
    return findings


def layout_findings() -> list[dict]:
    """Gated: markup or a stylesheet rule outside the shared layout vocabulary."""
    return _screen_findings() + _stylesheet_findings()
