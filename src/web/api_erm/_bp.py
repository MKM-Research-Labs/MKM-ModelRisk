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
"""The ERM blueprint and its guard.

Machine-to-machine and read-only, so it is protected by a shared token rather than
the SSO identity the console uses — the same guard the ingest surface uses, with
its own credential.
"""
from __future__ import annotations

from flask import Blueprint

from config.erm import ERM_API_PREFIX, ERM_DEV_TOKEN, ERM_TOKEN_HEADER
from src.web._token_auth import token_guard

erm_bp = Blueprint("erm", __name__, url_prefix=ERM_API_PREFIX)

erm_bp.before_request(token_guard(ERM_TOKEN_HEADER, ERM_DEV_TOKEN, "ERM"))
