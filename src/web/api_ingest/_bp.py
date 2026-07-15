# Copyright (c) 2022-2026 MKM Research Labs. All rights reserved.
#
# This software is licensed by MKM Research Labs for non-commercial
# research and educational use only. Any commercial use, including
# but not limited to use in or for products or services offered for sale,
# internal business operations intended for commercial advantage, or
# research and development conducted for a commercial entity, is expressly
# prohibited unless separately authorized in writing by MKM Research Labs.
#
# Use, reproduction, distribution, or modification of this code is subject to the
# terms and conditions of the license agreement provided with this software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Ingest blueprint object and its producer-authentication guard.

Ingest is machine-to-machine, so it is protected by a shared token rather than
the SSO identity used by the console. This is a Phase 0 stub — a real API-key /
mTLS scheme replaces it before any external producer is onboarded.
"""
from __future__ import annotations

import hmac

from flask import Blueprint, jsonify, request

from config.ingest import INGEST_DEV_TOKEN, INGEST_TOKEN_HEADER

ingest_bp = Blueprint("ingest", __name__, url_prefix="/api/ingest")


@ingest_bp.before_request
def _require_token():
    """Reject any ingest request without the shared producer token."""
    presented = request.headers.get(INGEST_TOKEN_HEADER, "")
    if not hmac.compare_digest(presented, INGEST_DEV_TOKEN):
        return jsonify({"error": "invalid or missing ingest token"}), 401
