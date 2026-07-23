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
"""HTML views (the single-page governance console)."""
from __future__ import annotations

from flask import Blueprint, render_template, request

from src.identity import resolve_principal
from src.web._assets import asset_version

views_bp = Blueprint("views", __name__)


@views_bp.get("/")
def index():
    # Pre-fill the "Acting as" field with the resolved principal: the SSO user in
    # a deployment, or the configured dev fallback (IDENTITY_DEV_FALLBACK)
    # locally — so a demo attributes changes to the operator, not david.kelly@mkmresearchlabs.com.
    # asset_version busts any stale CSS/JS a browser cached under an earlier
    # policy; without it a served-but-unseen console is indistinguishable from a
    # missing feature.
    return render_template(
        "index.html",
        actor_default=resolve_principal(request.headers).actor,
        asset_version=asset_version(),
    )
