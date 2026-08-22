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
"""Audit gate: colours live in ``config/theme`` (coding rule R10)."""
from __future__ import annotations

import re

from audit.styling import (_COLOUR, colour_literal_findings,
                           unconverted_colour_findings, undefined_token_findings)


def test_no_colour_literal_outside_the_theme_module():
    # The R10 hard gate for the converted surfaces: the stylesheet, the templates and
    # every Python file bar config/theme.py itself.
    assert colour_literal_findings() == []


def test_every_design_token_referenced_is_defined():
    # The half that cannot be seen by reading the diff: a browser drops an undefined
    # custom property silently, so the element renders with whatever it inherits.
    assert undefined_token_findings() == []


def test_the_javascript_backlog_is_reported_with_a_location():
    # Step 5 of docs/design/theme_config.md. Reported rather than gated, but each entry
    # has to be actionable — a bare count would not tell anyone where to go.
    backlog = unconverted_colour_findings()
    assert all(f["path"].endswith(".js") for f in backlog)
    assert all(f["line"] > 0 and f["snippet"] for f in backlog)


def test_the_scanner_recognises_every_css_colour_form():
    for value in ("#abc", "#aabbcc", "#aabbccdd", "rgb(1,2,3)", "rgba(1,2,3,.5)",
                  "hsl(1,2%,3%)", "hsla(1,2%,3%,.5)"):
        assert _COLOUR.search(value), value


def test_the_scanner_does_not_mistake_an_id_selector_for_a_colour():
    # "#abc" in "#abc-panel" is an element id whose first characters happen to be hex
    # digits. Without the trailing guard the gate would fail on markup it cannot fix.
    for value in ("#abc-panel", "#deface-me", "#fade_in", "#beadedThing"):
        assert not _COLOUR.search(value), value


def test_a_colour_inside_a_css_comment_is_not_a_finding():
    # app.css's own header warns against writing a literal; naming one must not count
    # as writing one.
    from audit.styling import _CSS_COMMENT
    assert not _COLOUR.search(_CSS_COMMENT.sub("", "/* never write #1976d2 here */"))
