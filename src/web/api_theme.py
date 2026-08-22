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
"""The theme API: the tokens, and which token each status is drawn in.

The stylesheet at ``/theme.css`` gives the browser the token VALUES. This gives it the
mapping the JavaScript needs — which token a rating, a meeting status or a version
lifecycle is drawn in — so no colour decision is written into a ``.js`` file.

Read-only and unauthenticated by design: it carries configuration, not governance
data, and the same values are already public in the served stylesheet.
"""
from __future__ import annotations

from flask import Blueprint, jsonify

from config.theme import STATUS_COLOUR_DEFAULTS, STATUS_COLOUR_TOKENS, THEME

theme_bp = Blueprint("theme", __name__)


@theme_bp.get("/api/theme")
def get_theme():
    return jsonify({
        "tokens": THEME,
        "status_colours": STATUS_COLOUR_TOKENS,
        "status_defaults": STATUS_COLOUR_DEFAULTS,
    })
