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
"""How a generated document is coloured and set (coding rule R10).

``latex.py`` builds LaTeX structure — tables, sections, the title page. This holds the
visual language those pages are drawn in, so the one place a colour is chosen stays
``config/theme`` and the document layer only converts and applies it.
"""
from __future__ import annotations

from config.reporting import (DOCUMENT_CHROME_COLOUR, DOCUMENT_UNRATED_COLOUR,
                              STANDALONE_DOCUMENT_COLOURS)


def latex_hex(colour=None) -> str:
    """A 6-digit uppercase RRGGBB for xcolor's HTML model.

    Shared rather than per-document (rule R8): the risk-policy tables colour their
    swatches from a division's policy, and the page furniture colours itself from the
    theme, but both need the same conversion. An unusable value falls back to the
    theme's unrated colour rather than to a literal.
    """
    digits = str(colour or "").lstrip("#").upper()
    if len(digits) == 6 and all(c in "0123456789ABCDEF" for c in digits):
        return digits
    return str(DOCUMENT_UNRATED_COLOUR).lstrip("#").upper()


def coloured(colour, body: str) -> str:
    """``body`` set in ``colour``, which is a theme value rather than a LaTeX name."""
    return "\\textcolor[HTML]{" + latex_hex(colour) + "}{" + body + "}"


def chrome(body: str) -> str:
    """Running header/footer furniture: the same ink the console's muted text uses."""
    return coloured(DOCUMENT_CHROME_COLOUR, body)


# The body typeface. Empty keeps the LaTeX default; "sans" matches the console.
BODY_FONT_PACKAGES = {
    "sans": "\\usepackage{helvet}\\renewcommand{\\familydefault}{\\sfdefault}\n",
}


def colour_definitions() -> str:
    """The ``\\definecolor`` block a standalone document is handed.

    ``preamble()`` colours the documents this module assembles, but the integration
    guide is a hand-written ``.tex`` that has to build outside the app as well. It
    inputs this block when the platform provides it, so the published copy is drawn
    in whatever ``config/theme`` holds rather than in the values its source falls
    back to (rule R10).
    """
    return "".join(
        "\\definecolor{" + name + "}{HTML}{" + latex_hex(colour) + "}\n"
        for name, colour in STANDALONE_DOCUMENT_COLOURS.items()
    )
