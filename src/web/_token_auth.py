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
"""Shared-token authentication for the machine-to-machine surfaces.

Two surfaces are called by systems rather than by people: the ingest collector,
which producers POST artifacts to, and the ERM read API, which an enterprise
risk platform pulls from. Neither carries the SSO identity the console uses, so
both are guarded by a shared token — and by the SAME guard, extracted here rather
than copied into each blueprint. Two copies of eight lines is how one of them
quietly stops comparing in constant time.

This remains the Phase 0 stub the ingest contract already describes: a real
API-key or mTLS scheme replaces it before any external party is onboarded. What
it does do correctly is compare in constant time, so the token cannot be
recovered a byte at a time from response timings.
"""
from __future__ import annotations

import hmac

from flask import jsonify, request


def token_guard(header: str, expected: str, surface: str):
    """A ``before_request`` guard rejecting anything without the shared token.

    ``surface`` names the token in the error ("ingest", "ERM") so an integrator
    reading a 401 knows which credential is wrong when a deployment carries both.

    Returns ``None`` when the request may proceed, which is what Flask requires of
    a ``before_request`` that does not intercept.
    """
    def guard():
        presented = request.headers.get(header, "")
        if not hmac.compare_digest(presented, expected):
            return jsonify({"error": f"invalid or missing {surface} token"}), 401
        return None
    return guard
