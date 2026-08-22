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
"""Serialise the design tokens as the stylesheet the console links first.

``config/theme.py`` holds the values; this renders them as a ``:root`` custom-property
block and stamps it. It writes no rules and no selectors of its own — only
``--name: value;`` pairs — so the stylesheet proper stays in ``src/static/css``
where rule R7 requires it, and this stays a serialiser of configuration.

Why a route rather than a checked-in file: a generated file would have to be
regenerated and committed whenever a token changed, and the two would drift the
first time somebody forgot. Serving it means ``config/theme.py`` is the only place
the values exist.
"""
from __future__ import annotations

import hashlib

from config.theme import THEME

CSS_MIMETYPE = "text/css"


def theme_css(tokens: dict[str, str] | None = None) -> str:
    """The design tokens as a ``:root`` custom-property block."""
    declared = THEME if tokens is None else tokens
    body = "".join(f"  --{name}: {value};\n" for name, value in declared.items())
    return ":root {\n" + body + "}\n"


def theme_version(tokens: dict[str, str] | None = None) -> str:
    """A stamp for the current token values, for the ``?v=`` on the link.

    ``asset_version`` cannot answer for this one: it watches file modification times
    under ``src/static``, and the theme is not a file there. Hashing the served text
    gives the same guarantee — the URL changes exactly when the bytes do, so a
    rebrand cannot be masked by a browser cache, and an unchanged theme keeps its
    cached copy across restarts.
    """
    return hashlib.sha256(theme_css(tokens).encode("utf-8")).hexdigest()[:12]
