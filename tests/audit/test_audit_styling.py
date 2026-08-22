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

from audit.styling import (_COLOUR, _bare_hits, _without_comments,
                           colour_literal_findings, unconverted_colour_findings,
                           undefined_token_findings)


def test_no_colour_literal_outside_the_theme_module():
    # The R10 hard gate for the converted surfaces: the stylesheet, the templates and
    # every Python file bar config/theme.py itself.
    assert colour_literal_findings() == []


def test_every_design_token_referenced_is_defined():
    # The half that cannot be seen by reading the diff: a browser drops an undefined
    # custom property silently, so the element renders with whatever it inherits.
    assert undefined_token_findings() == []


def test_nothing_sits_outside_the_gate():
    # Every asset type scanned is now gated, so the reported bucket is empty. It stays
    # in place as the landing spot for a new asset type, which must surface rather than
    # be exempted in silence.
    assert unconverted_colour_findings() == []


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


def test_a_colour_spelled_without_a_hash_is_caught():
    # How LaTeX writes one. \definecolor{mkmblue}{HTML}{1565C0} sat in latex.py for
    # months and the "#"-anchored scan could not see it; nor could it see the bare
    # "9E9E9E" fallback in the risk-policy document.
    found = _bare_hits('c = "\\definecolor{brand}{HTML}{1565C0}"\nfallback = "9E9E9E"\n', "x.py")
    assert {f["snippet"] for f in found} == {"1565C0", "9E9E9E"}


def test_a_six_digit_number_is_not_mistaken_for_a_colour():
    # An all-digit string is an identifier or a count. Requiring a hex letter is what
    # keeps the gate off them.
    assert _bare_hits('ref = "123456"\n', "x.py") == []


def test_a_colour_named_in_a_python_comment_is_not_a_finding():
    # Explaining the drift must not count as committing it — the same reason the CSS
    # scan strips its comments. config/reporting.py names both blues in prose.
    assert "#1976d2" not in _without_comments("x = 1  # the old accent was #1976d2\n")


def test_a_colour_inside_a_python_string_survives_comment_stripping():
    # The stripping must be token-aware: cutting at the first "#" would blank the
    # literal itself and the gate would pass on exactly what it exists to catch.
    assert "#1976d2" in _without_comments('X = "#1976d2"  # named here too: #ff0000\n')
